"""
Precompute all model-scored and aggregated data the Streamlit dashboard needs.

Run this once (or whenever the source CSVs change) to produce:
  - forecast_scored.csv   : every planned acquisition + risk scores + oversight probability
  - office_summary.csv    : per-office workload / staffing shortage metrics
  - model_metrics.json    : headline model performance numbers for the "About the models" panel

The dashboard app itself only reads these three lightweight outputs, so it stays fast to
deploy and doesn't need to retrain models on every page load.
"""

import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, average_precision_score, roc_auc_score
from sklearn.cluster import KMeans

try:
    from xgboost import XGBRegressor, XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

RANDOM_STATE = 42

# ----------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------
forecast = pd.read_csv("VA_Acquisition_Forecast.csv", parse_dates=["Record_Created_Date"])
historical = pd.read_csv(
    "VA_Contract_Awards_Historical.csv",
    parse_dates=["Award_Date", "Period_of_Performance_Start", "Period_of_Performance_End"],
)
modeling = pd.read_csv("VA_Acquisition_Modeling_Data.csv")

fc_active = forecast[forecast["Status"] != "Cancelled"].copy()

# ----------------------------------------------------------------------
# Train/val split (stratified on rare Protest_Filed target)
# ----------------------------------------------------------------------
train, val = train_test_split(
    modeling, test_size=0.2, random_state=RANDOM_STATE, stratify=modeling["Protest_Filed"]
)

# Train-fold-only target encoding (avoids leakage)
cat_rates_train = train.groupby("Category").agg(
    Category_Historical_Protest_Rate=("Protest_Filed", "mean"),
    Category_Historical_OnTime_Rate=("On_Time_Award", "mean"),
)
comp_rates_train = train.groupby("Competition_Type").agg(
    Competition_Historical_Protest_Rate=("Protest_Filed", "mean"),
    Competition_Historical_OnTime_Rate=("On_Time_Award", "mean"),
)


def add_rate_features(df):
    df = df.merge(cat_rates_train, on="Category", how="left")
    df = df.merge(comp_rates_train, on="Competition_Type", how="left")
    for col in cat_rates_train.columns.tolist() + comp_rates_train.columns.tolist():
        fallback = train["Protest_Filed"].mean() if "Protest" in col else train["On_Time_Award"].mean()
        df[col] = df[col].fillna(fallback)
    return df


def engineer(df):
    df = df.copy()
    df["Estimated_Value_log"] = np.log1p(df["Estimated_Value"])
    df["Is_Full_And_Open"] = (df["Competition_Type"] == "Full and Open").astype(int)
    return df


train = engineer(add_rate_features(train))
val = engineer(add_rate_features(val))

numeric_features = [
    "Estimated_Value_log", "Number_of_Offers_Received", "Requirement_Complexity_Score",
    "Contracting_Office_Open_Actions", "Days_Since_Requirement_Posted",
    "Category_Historical_Protest_Rate", "Category_Historical_OnTime_Rate",
    "Competition_Historical_Protest_Rate", "Competition_Historical_OnTime_Rate",
]
categorical_features = ["Category", "Contract_Type", "Set_Aside_Type", "Competition_Type", "Vendor_Size"]

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numeric_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
])

X_train = train[numeric_features + categorical_features]
X_val = val[numeric_features + categorical_features]

# ----------------------------------------------------------------------
# Days_to_Award (regression)
# ----------------------------------------------------------------------
days_model_cls = (lambda: XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=RANDOM_STATE)) \
    if HAS_XGB else (lambda: RandomForestRegressor(n_estimators=300, max_depth=8, random_state=RANDOM_STATE))
days_pipe = Pipeline([("prep", preprocessor), ("model", days_model_cls())])
days_pipe.fit(X_train, train["Days_to_Award"])
days_mae = mean_absolute_error(val["Days_to_Award"], days_pipe.predict(X_val))

# ----------------------------------------------------------------------
# Award_Amount (regression, log target)
# ----------------------------------------------------------------------
award_pipe = Pipeline([("prep", preprocessor), ("model", days_model_cls())])
award_pipe.fit(X_train, np.log1p(train["Award_Amount"]))
award_pred_val = np.expm1(award_pipe.predict(X_val))
award_mape = float(np.mean(np.abs((val["Award_Amount"] - award_pred_val) / val["Award_Amount"])) * 100)

# ----------------------------------------------------------------------
# Protest_Filed (rare-event classification)
# ----------------------------------------------------------------------
if HAS_XGB:
    scale_pos_weight = (train["Protest_Filed"] == 0).sum() / max((train["Protest_Filed"] == 1).sum(), 1)
    protest_model = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                                   scale_pos_weight=scale_pos_weight, random_state=RANDOM_STATE)
else:
    protest_model = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE)
protest_pipe = Pipeline([("prep", preprocessor), ("model", protest_model)])
protest_pipe.fit(X_train, train["Protest_Filed"])
protest_proba_val = protest_pipe.predict_proba(X_val)[:, 1]
protest_prauc = float(average_precision_score(val["Protest_Filed"], protest_proba_val))
protest_rocauc = float(roc_auc_score(val["Protest_Filed"], protest_proba_val))

# ----------------------------------------------------------------------
# Needs_Oversight classifier
# ----------------------------------------------------------------------
high_value_threshold = train["Estimated_Value"].quantile(0.90)
for df in (train, val):
    df["Is_High_Complexity"] = (df["Requirement_Complexity_Score"] >= 7).astype(int)
    df["Needs_Oversight"] = (
        (df["Is_High_Complexity"] == 1) & ((df["Estimated_Value"] > high_value_threshold) | (df["Is_Full_And_Open"] == 1))
    ).astype(int)

oversight_features_num = ["Estimated_Value_log", "Requirement_Complexity_Score", "Number_of_Offers_Received",
                           "Category_Historical_Protest_Rate", "Category_Historical_OnTime_Rate"]
oversight_features_cat = ["Category", "Contract_Type", "Competition_Type"]
oversight_prep = ColumnTransformer([
    ("num", StandardScaler(), oversight_features_num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), oversight_features_cat),
])
oversight_pipe = Pipeline([("prep", oversight_prep),
                            ("model", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE))])
oversight_pipe.fit(train[oversight_features_num + oversight_features_cat], train["Needs_Oversight"])
oversight_prauc = float(average_precision_score(
    val["Needs_Oversight"], oversight_pipe.predict_proba(val[oversight_features_num + oversight_features_cat])[:, 1]
))

# ----------------------------------------------------------------------
# Score the live forecast pipeline
# ----------------------------------------------------------------------
fc_scoring = fc_active.copy()
fc_scoring["Estimated_Value"] = fc_scoring["Estimated_Value_Midpoint"]
fc_scoring["Estimated_Value_log"] = np.log1p(fc_scoring["Estimated_Value"])
fc_scoring["Set_Aside_Type"] = fc_scoring["Anticipated_Set_Aside"]
fc_scoring["Competition_Type"] = fc_scoring["Anticipated_Set_Aside"].apply(
    lambda x: "Full and Open" if x == "Full and Open (No Set-Aside)" else "Set-Aside"
)
fc_scoring["Vendor_Size"] = np.where(
    fc_scoring["Small_Business_Eligible"] == "Yes", "Small Business", "Other Than Small Business"
)
fc_scoring["Number_of_Offers_Received"] = modeling["Number_of_Offers_Received"].median()
fc_scoring["Requirement_Complexity_Score"] = modeling["Requirement_Complexity_Score"].median()
fc_scoring["Contracting_Office_Open_Actions"] = modeling["Contracting_Office_Open_Actions"].median()
fc_scoring["Days_Since_Requirement_Posted"] = 0
fc_scoring["Is_Full_And_Open"] = (fc_scoring["Competition_Type"] == "Full and Open").astype(int)

fc_scoring = add_rate_features(fc_scoring)

X_forecast = fc_scoring[numeric_features + categorical_features]
fc_days_pred = days_pipe.predict(X_forecast)
fc_award_pred = np.expm1(award_pipe.predict(X_forecast))
fc_protest_proba = protest_pipe.predict_proba(X_forecast)[:, 1]
fc_oversight_proba = oversight_pipe.predict_proba(fc_scoring[oversight_features_num + oversight_features_cat])[:, 1]


def composite_risk_score(days_pred, award_pred, protest_proba):
    days_norm = (days_pred - days_pred.min()) / (days_pred.max() - days_pred.min())
    log_award = np.log1p(award_pred)
    award_norm = (log_award - log_award.min()) / (log_award.max() - log_award.min())
    return ((0.35 * days_norm + 0.35 * award_norm + 0.30 * protest_proba) * 100).round(1)


fc_scoring["Predicted_Days_to_Award"] = fc_days_pred.round(0)
fc_scoring["Predicted_Award_Amount"] = fc_award_pred.round(0)
fc_scoring["Predicted_Protest_Probability"] = fc_protest_proba.round(3)
fc_scoring["Oversight_Probability"] = fc_oversight_proba.round(3)
fc_scoring["Composite_Risk_Score"] = composite_risk_score(fc_days_pred, fc_award_pred, fc_protest_proba)

output_cols = [
    "Forecast_ID", "Fiscal_Year", "VISN", "Facility_Name", "Contracting_Office", "Category",
    "Requirement_Title", "Estimated_Value_Midpoint", "Priority_Level", "Status", "Contract_Type",
    "Anticipated_Set_Aside", "Recompete", "Incumbent_Contractor", "Planned_Award_Quarter",
    "Predicted_Days_to_Award", "Predicted_Award_Amount", "Predicted_Protest_Probability",
    "Oversight_Probability", "Composite_Risk_Score",
]
forecast_scored = fc_scoring[output_cols].rename(columns={"Estimated_Value_Midpoint": "Estimated_Value"})
forecast_scored.to_csv("forecast_scored.csv", index=False)

# ----------------------------------------------------------------------
# Office workload + staffing shortage summary
# ----------------------------------------------------------------------
hist_complete = historical[historical["Fiscal_Year"].between(2019, 2025)]
office_annual = hist_complete.groupby(["Contracting_Office", "Fiscal_Year"]).size().reset_index(name="awards")
hist_avg = office_annual.groupby("Contracting_Office")["awards"].mean().rename("avg_annual_historical_awards")

fc_office = fc_active.groupby("Contracting_Office").agg(
    planned_actions=("Forecast_ID", "count"),
    planned_value=("Estimated_Value_Midpoint", "sum"),
    critical_high_count=("Priority_Level", lambda x: x.isin(["Critical", "High"]).sum()),
)
fc_office["planned_actions_per_year"] = fc_office["planned_actions"] / 3

office_summary = fc_office.join(hist_avg, how="left")
office_summary["workload_change_pct"] = (
    (office_summary["planned_actions_per_year"] / office_summary["avg_annual_historical_awards"]) - 1
) * 100

spec_share = (
    fc_active.assign(is_specialized=fc_active["Category"].isin(["IT Services", "Construction", "Medical Equipment"]))
    .groupby("Contracting_Office")["is_specialized"].mean()
    .rename("specialized_category_share") * 100
)
office_summary = office_summary.join(spec_share)

staffing_input = office_summary[["workload_change_pct", "specialized_category_share"]].dropna()
kmeans = KMeans(n_clusters=3, random_state=RANDOM_STATE, n_init=10)
staffing_input = staffing_input.copy()
staffing_input["cluster"] = kmeans.fit_predict(staffing_input)
cluster_order = staffing_input.groupby("cluster")["workload_change_pct"].mean().sort_values(ascending=False).index
tier_labels = {cluster_order[0]: "High shortage risk", cluster_order[1]: "Moderate shortage risk",
               cluster_order[2]: "Low shortage risk"}
staffing_input["Shortage_Tier"] = staffing_input["cluster"].map(tier_labels)

office_summary = office_summary.join(staffing_input["Shortage_Tier"])
office_summary = office_summary.reset_index().round(2)
office_summary.to_csv("office_summary.csv", index=False)

# ----------------------------------------------------------------------
# Model metrics for the "About the models" panel
# ----------------------------------------------------------------------
metrics = {
    "days_to_award_mae": round(float(days_mae), 1),
    "award_amount_mape": round(award_mape, 1),
    "protest_prauc": round(protest_prauc, 3),
    "protest_rocauc": round(protest_rocauc, 3),
    "oversight_prauc": round(oversight_prauc, 3),
    "protest_base_rate": round(float(modeling["Protest_Filed"].mean()), 3),
    "n_forecast_scored": int(len(forecast_scored)),
    "n_offices": int(len(office_summary)),
    "generated_from_n_historical_awards": int(len(modeling)),
}
with open("model_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("Done.")
print(json.dumps(metrics, indent=2))

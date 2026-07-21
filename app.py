"""
VA Acquisition Risk & Capacity Dashboard
-----------------------------------------
Interactive Streamlit dashboard for non-technical stakeholders, built on top of the
model-scored outputs from precompute_dashboard_data.py.

Run locally:   streamlit run app.py
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="VA Acquisition Risk & Capacity Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

# ----------------------------------------------------------------------
# Data loading (cached so filtering/re-renders don't reload from disk)
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    forecast = pd.read_csv("forecast_scored.csv")
    office = pd.read_csv("office_summary.csv")
    with open("model_metrics.json") as f:
        metrics = json.load(f)
    return forecast, office, metrics


try:
    forecast, office, metrics = load_data()
except FileNotFoundError:
    st.error(
        "Scored data files not found. Run `python precompute_dashboard_data.py` in this folder "
        "first — it generates forecast_scored.csv, office_summary.csv, and model_metrics.json."
    )
    st.stop()

CURRENCY = lambda v: f"${v:,.0f}"

# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.title("Filters")

fiscal_years = sorted(forecast["Fiscal_Year"].unique())
selected_fy = st.sidebar.multiselect("Fiscal year", fiscal_years, default=fiscal_years)

categories = sorted(forecast["Category"].unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

visns = sorted(forecast["VISN"].unique())
selected_visns = st.sidebar.multiselect("VISN", visns, default=visns)

priorities = ["Low", "Medium", "High", "Critical"]
selected_priority = st.sidebar.multiselect("Priority level", priorities, default=priorities)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data is synthetic, generated for practicing this analytics workflow. "
    "Figures illustrate the method, not real VA procurement activity."
)

filtered = forecast[
    forecast["Fiscal_Year"].isin(selected_fy)
    & forecast["Category"].isin(selected_categories)
    & forecast["VISN"].isin(selected_visns)
    & forecast["Priority_Level"].isin(selected_priority)
]

# ----------------------------------------------------------------------
# Header + KPI row
# ----------------------------------------------------------------------
st.title("VA Acquisition Risk & Capacity Dashboard")
st.caption(
    "Model-driven answers to: which acquisitions need oversight, which offices may become "
    "overloaded, where staffing shortages are likely, and which acquisitions carry the greatest "
    "financial and schedule risk."
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Planned acquisitions", f"{len(filtered):,}")
kpi2.metric("Planned value", CURRENCY(filtered["Estimated_Value"].sum()))
kpi3.metric("High oversight priority", f"{(filtered['Oversight_Probability'] > 0.5).sum():,}")
kpi4.metric("High risk score (>=70)", f"{(filtered['Composite_Risk_Score'] >= 70).sum():,}")
kpi5.metric(
    "Offices at overload risk",
    f"{(office['workload_change_pct'] > 20).sum():,} of {len(office)}",
)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Oversight priorities",
    "Office workload",
    "Staffing shortages",
    "Financial & schedule risk",
    "About the models",
])

# ----------------------------------------------------------------------
# TAB 1 — Oversight priorities (Question 1)
# ----------------------------------------------------------------------
with tab1:
    st.subheader("Which acquisitions should receive additional oversight?")
    st.write(
        "Each planned acquisition is scored with an oversight probability — how closely it "
        "matches the pattern of past acquisitions that combined high priority, high value, and "
        "open competition. Higher probability means a stronger case for early, active review."
    )

    top_oversight = filtered.sort_values("Oversight_Probability", ascending=False).head(25)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(
            top_oversight.head(15).sort_values("Oversight_Probability"),
            x="Oversight_Probability",
            y="Forecast_ID",
            orientation="h",
            color="Priority_Level",
            color_discrete_map={"Critical": "#e34948", "High": "#eda100", "Medium": "#2a78d6", "Low": "#5f5e5a"},
            hover_data=["Facility_Name", "Category", "Estimated_Value"],
            title="Top 15 acquisitions by oversight probability",
        )
        fig.update_layout(yaxis_title="", xaxis_title="Oversight probability", height=460)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.metric("Median oversight probability", f"{filtered['Oversight_Probability'].median():.1%}")
        priority_counts = filtered["Priority_Level"].value_counts()
        fig2 = px.pie(
            values=priority_counts.values, names=priority_counts.index,
            title="Priority mix (filtered view)", hole=0.5,
        )
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Full oversight priority list**")
    st.dataframe(
        top_oversight[[
            "Forecast_ID", "Facility_Name", "Category", "Priority_Level", "Estimated_Value",
            "Contracting_Office", "Status", "Oversight_Probability",
        ]].rename(columns={"Oversight_Probability": "Oversight probability"}),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Download oversight priority list (CSV)",
        top_oversight.to_csv(index=False),
        file_name="oversight_priority_list.csv",
    )

# ----------------------------------------------------------------------
# TAB 2 — Office workload (Question 2)
# ----------------------------------------------------------------------
with tab2:
    st.subheader("Which contracting offices may become overloaded?")
    st.write(
        "Planned actions per year (FY2026-28 forecast) compared to each office's historical "
        "average annual award volume (FY2019-25). Offices above 0% are trending toward more "
        "work than their recent track record."
    )

    office_sorted = office.sort_values("workload_change_pct", ascending=False)
    fig = px.bar(
        office_sorted,
        x="workload_change_pct",
        y="Contracting_Office",
        orientation="h",
        color="workload_change_pct",
        color_continuous_scale=["#1baf7a", "#eda100", "#e34948"],
        title="Projected workload change vs. historical baseline, by office",
        labels={"workload_change_pct": "Workload change (%)", "Contracting_Office": ""},
    )
    fig.update_layout(height=700, coloraxis_showscale=False)
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Highest growth office",
            office_sorted.iloc[0]["Contracting_Office"],
            f"{office_sorted.iloc[0]['workload_change_pct']:+.1f}%",
        )
    with col2:
        st.metric(
            "Most under-utilized office",
            office_sorted.iloc[-1]["Contracting_Office"],
            f"{office_sorted.iloc[-1]['workload_change_pct']:+.1f}%",
        )

    st.markdown("**Office workload detail**")
    st.dataframe(
        office_sorted[[
            "Contracting_Office", "planned_actions_per_year", "avg_annual_historical_awards",
            "workload_change_pct", "critical_high_count", "planned_value",
        ]].rename(columns={
            "planned_actions_per_year": "Planned actions/yr",
            "avg_annual_historical_awards": "Historical avg/yr",
            "workload_change_pct": "Change (%)",
            "critical_high_count": "Critical/High items",
            "planned_value": "Planned value ($)",
        }),
        use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------
# TAB 3 — Staffing shortages (Question 3)
# ----------------------------------------------------------------------
with tab3:
    st.subheader("Where are staffing shortages likely to occur?")
    st.write(
        "Offices are grouped into shortage-risk tiers based on two factors: how much their "
        "workload is growing, and how much of that work falls in specialized categories "
        "(IT, Construction, Medical Equipment) that are typically harder to staff quickly."
    )

    tier_order = ["High shortage risk", "Moderate shortage risk", "Low shortage risk"]
    tier_colors = {"High shortage risk": "#e34948", "Moderate shortage risk": "#eda100", "Low shortage risk": "#1baf7a"}

    fig = px.scatter(
        office, x="workload_change_pct", y="specialized_category_share",
        color="Shortage_Tier", color_discrete_map=tier_colors,
        category_orders={"Shortage_Tier": tier_order},
        hover_name="Contracting_Office",
        labels={"workload_change_pct": "Workload change (%)", "specialized_category_share": "Specialized-category share (%)"},
        title="Staffing shortage risk tiers by office",
        size=[20] * len(office),
    )
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)

    tier_counts = office["Shortage_Tier"].value_counts().reindex(tier_order).fillna(0).astype(int)
    c1, c2, c3 = st.columns(3)
    c1.metric("High shortage risk offices", int(tier_counts.get("High shortage risk", 0)))
    c2.metric("Moderate shortage risk offices", int(tier_counts.get("Moderate shortage risk", 0)))
    c3.metric("Low shortage risk offices", int(tier_counts.get("Low shortage risk", 0)))

    st.markdown("**Offices flagged as high shortage risk**")
    high_risk_offices = office[office["Shortage_Tier"] == "High shortage risk"].sort_values(
        "workload_change_pct", ascending=False
    )
    st.dataframe(
        high_risk_offices[[
            "Contracting_Office", "workload_change_pct", "specialized_category_share", "planned_actions_per_year",
        ]].rename(columns={
            "workload_change_pct": "Workload change (%)",
            "specialized_category_share": "Specialized share (%)",
            "planned_actions_per_year": "Planned actions/yr",
        }),
        use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------
# TAB 4 — Financial & schedule risk (Question 4)
# ----------------------------------------------------------------------
with tab4:
    st.subheader("Which acquisitions represent the greatest financial and schedule risk?")
    st.write(
        "Composite risk score (0-100) blends three model predictions: predicted award value, "
        "predicted days to award, and predicted protest probability. Higher scores indicate "
        "acquisitions worth watching most closely as they move through the pipeline."
    )

    top_risk = filtered.sort_values("Composite_Risk_Score", ascending=False).head(25)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.scatter(
            filtered, x="Predicted_Days_to_Award", y="Predicted_Award_Amount",
            color="Composite_Risk_Score", size="Estimated_Value",
            color_continuous_scale=["#1baf7a", "#eda100", "#e34948"],
            hover_data=["Forecast_ID", "Category", "Contracting_Office"],
            labels={"Predicted_Days_to_Award": "Predicted days to award", "Predicted_Award_Amount": "Predicted award amount ($)"},
            title="Risk landscape — schedule vs. value (color = composite risk score)",
        )
        fig.update_yaxes(type="log")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.histogram(
            filtered, x="Composite_Risk_Score", nbins=25,
            title="Risk score distribution", color_discrete_sequence=["#2a78d6"],
        )
        fig2.update_layout(height=500, xaxis_title="Composite risk score", yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Top 25 highest-risk acquisitions**")
    st.dataframe(
        top_risk[[
            "Forecast_ID", "Facility_Name", "Category", "Estimated_Value", "Contract_Type",
            "Predicted_Days_to_Award", "Predicted_Award_Amount", "Predicted_Protest_Probability",
            "Composite_Risk_Score",
        ]].rename(columns={
            "Predicted_Days_to_Award": "Pred. days to award",
            "Predicted_Award_Amount": "Pred. award amount ($)",
            "Predicted_Protest_Probability": "Pred. protest probability",
            "Composite_Risk_Score": "Risk score",
        }),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Download high-risk acquisitions (CSV)",
        top_risk.to_csv(index=False),
        file_name="high_risk_acquisitions.csv",
    )

# ----------------------------------------------------------------------
# TAB 5 — About the models
# ----------------------------------------------------------------------
with tab5:
    st.subheader("About the models behind this dashboard")
    st.write(
        "This dashboard reads pre-scored output from a modeling pipeline (see the companion "
        "notebook, `VA_Acquisition_DS_Project.ipynb`) rather than training models live, so it "
        "stays fast to load. Headline validation metrics from that pipeline:"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Days-to-award model — MAE", f"{metrics['days_to_award_mae']} days")
    m2.metric("Award-amount model — MAPE", f"{metrics['award_amount_mape']}%")
    m3.metric("Oversight classifier — PR-AUC", f"{metrics['oversight_prauc']}")

    m4, m5 = st.columns(2)
    m4.metric("Protest classifier — ROC-AUC", f"{metrics['protest_rocauc']}")
    m5.metric("Protest base rate", f"{metrics['protest_base_rate']:.1%}")

    st.markdown("---")
    st.markdown("""
**Honest limitation to flag:** the protest classifier's ROC-AUC (~0.50) is close to random —
in this synthetic dataset, protest filings carry only a weak, noisy relationship to the
available features. The composite risk score still leans on it for the protest component, so
treat low/high protest probabilities as a soft signal, not a reliable individual prediction.
The days-to-award and award-amount models perform considerably better and can be trusted with
more confidence.

**Data note:** all underlying data (`VA_Acquisition_Forecast.csv`, `VA_Contract_Awards_Historical.csv`,
`VA_Acquisition_Modeling_Data.csv`) is synthetic, generated to practice this analytics workflow.
Absolute figures shown here (protest rates, dollar amounts, office names) do not represent real
VA procurement activity — validate every threshold against subject-matter-expert judgment before
using this approach on real data.

**How to refresh the numbers:** re-run `python precompute_dashboard_data.py` after updating any of
the three source CSVs, then restart the dashboard (or click "Rerun" in Streamlit) to pick up the
new `forecast_scored.csv` / `office_summary.csv` / `model_metrics.json`.
""")

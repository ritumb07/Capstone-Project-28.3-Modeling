# Data Dictionary — VA Acquisition Synthetic Datasets

**Note:** All three files are 100% synthetic/fictional, generated for data science practice. Vendor names, UEIs, contract numbers, and PII (emails, POCs) are fabricated and do not represent real people, companies, or VA data.

---

## 1. VA_Acquisition_Forecast.csv
**2,000 records** — Simulated future/planned acquisitions (FY2026–FY2028).

| Column | Type | Description | Example / Domain |
|---|---|---|---|
| Forecast_ID | string | Unique record identifier | `FCST-000001` |
| Fiscal_Year | integer | Planned fiscal year of the requirement | 2026, 2027, 2028 |
| VISN | integer | Veterans Integrated Service Network (VA region) | 1–18 |
| Facility_Name | string | VA facility originating the requirement | `VISN 10 Medical Center Main` |
| Contracting_Office | string | Office expected to execute the acquisition | NCO 1–18, SAC, TAC, SAO West/East, DALC, NAC |
| Category | string | High-level requirement category | Medical/Clinical Services, Pharmaceuticals, Medical Equipment, IT Services, Construction, Professional Services, Facilities Management, Food Service, Security Services, Transportation |
| NAICS_Code | integer | North American Industry Classification System code | e.g. `621111` |
| NAICS_Description | string | Description of the NAICS code | `Offices of Physicians` |
| PSC_Code | string | Product/Service Code | e.g. `Q201`, `D302` |
| Requirement_Title | string | Descriptive title of the requirement | free text |
| Estimated_Value_Low | float | Lower bound of estimated contract value (USD) | e.g. 51804.26 |
| Estimated_Value_High | float | Upper bound of estimated contract value (USD) | e.g. 62477.74 |
| Estimated_Value_Midpoint | float | Point estimate of contract value (USD) | e.g. 56850.75 |
| Planned_Solicitation_Quarter | string | Quarter solicitation is expected to be released | `FY Q1`–`FY Q4` |
| Planned_Award_Quarter | string | Quarter award is expected | `FY Q1`–`FY Q4` |
| Contract_Type | string | Anticipated contract vehicle type | Firm Fixed Price, Time and Materials, Cost Plus Fixed Fee, IDIQ, BPA, Labor Hour |
| Anticipated_Set_Aside | string | Expected socioeconomic set-aside | SDVOSB, VOSB, 8(a), HUBZone, WOSB, Small Business, Full and Open |
| Small_Business_Eligible | string | Whether requirement is eligible for small business set-aside | `Yes` / `No` |
| Recompete | string | Whether this is a recompete of an expiring contract | `Yes` / `No` |
| Incumbent_Contractor | string | Name of current incumbent (blank if new requirement) | e.g. `Pinnacle Solutions`, or empty |
| Priority_Level | string | Internal priority ranking | Low, Medium, High, Critical |
| Status | string | Current stage in the acquisition lifecycle | Market Research, Planning, Draft Solicitation, Solicitation Released, On Hold, Cancelled |
| Point_of_Contact_Email | string | Fictional contracting POC email | `firstname.lastname@va.gov` |
| Record_Created_Date | date (ISO 8601) | Date the forecast record was created | `YYYY-MM-DD` |

---

## 2. VA_Contract_Awards_Historical.csv
**5,000 records** — Simulated historical contract awards (2019–2026).

| Column | Type | Description | Example / Domain |
|---|---|---|---|
| Award_ID | string | Unique record identifier | `AWD-000001` |
| Contract_Number | string | Simulated VA-style contract number | `36C102577O713` |
| Award_Date | date (ISO 8601) | Date contract was awarded | `YYYY-MM-DD` |
| Fiscal_Year | integer | Federal fiscal year of award (Oct–Sep) | 2019–2026 |
| VISN | integer | Veterans Integrated Service Network | 1–18 |
| Facility_Name | string | Requesting VA facility | e.g. `VISN 1 Medical Center North` |
| Contracting_Office | string | Office that executed the award | NCO 1–18, SAC, TAC, SAO West/East, DALC, NAC |
| Vendor_Name | string | Fictional awarded vendor name | e.g. `Summit Associates` |
| Vendor_UEI | string | Fictional 12-character Unique Entity Identifier | e.g. `DMDLUTEGDG7X` |
| Vendor_Size | string | Small vs. other than small business | `Small Business` / `Other Than Small Business` |
| Socioeconomic_Category | string | Socioeconomic set-aside category, if applicable | SDVOSB, VOSB, 8(a), HUBZone, WOSB, or `N/A` |
| Category | string | High-level requirement category | same list as Forecast dataset |
| NAICS_Code | integer | NAICS code | e.g. `237990` |
| NAICS_Description | string | NAICS code description | `Other Heavy and Civil Engineering Construction` |
| PSC_Code | string | Product/Service Code | e.g. `Y1AA` |
| Contract_Type | string | Contract vehicle type | Firm Fixed Price, Time and Materials, Cost Plus Fixed Fee, IDIQ, BPA, Labor Hour |
| Competition_Type | string | How the requirement was competed | Full and Open, Set-Aside, Sole Source, Limited Competition |
| Set_Aside_Type | string | Specific set-aside used (if any) | SDVOSB, VOSB, 8(a), HUBZone, WOSB, Small Business, Full and Open (No Set-Aside) |
| Number_of_Offers_Received | integer | Count of offers/proposals received | 1–10 |
| Award_Amount | float | Final award value (USD) | e.g. 128816.99 |
| Period_of_Performance_Start | date (ISO 8601) | Start of contract performance period | `YYYY-MM-DD` |
| Period_of_Performance_End | date (ISO 8601) | End of contract performance period | `YYYY-MM-DD` |
| Period_of_Performance_Months | integer | Length of performance period in months | 6, 12, 24, 36, 48, 60 |

---

## 3. VA_Acquisition_Modeling_Data.csv
**5,000 records** — ML-ready dataset combining engineered features and target variables, with realistic statistical relationships built in (not independently randomized) so models can find genuine signal.

### Identifiers / dimensions
| Column | Type | Description | Example / Domain |
|---|---|---|---|
| Record_ID | string | Unique record identifier | `MODEL-000001` |
| Fiscal_Year | integer | Fiscal year of the record | 2021–2026 |
| VISN | integer | Veterans Integrated Service Network | 1–18 |
| Category | string | High-level requirement category | same list as above |
| NAICS_Code | integer | NAICS code | e.g. `325412` |
| PSC_Code | string | Product/Service Code | e.g. `6508` |

### Categorical features
| Column | Type | Description | Domain |
|---|---|---|---|
| Contract_Type | string | Contract vehicle type | Firm Fixed Price, Time and Materials, Cost Plus Fixed Fee, IDIQ, BPA, Labor Hour |
| Set_Aside_Type | string | Set-aside category | SDVOSB, VOSB, 8(a), HUBZone, WOSB, Small Business, Full and Open (No Set-Aside) |
| Competition_Type | string | Competition method | Full and Open, Set-Aside, Sole Source, Limited Competition |
| Vendor_Size | string | Winning vendor's size status | `Small Business` / `Other Than Small Business` |
| Socioeconomic_Category | string | Specific socioeconomic category, if applicable | SDVOSB, VOSB, 8(a), HUBZone, WOSB, or `N/A` |
| Incumbent_Present | string | Whether an incumbent contractor exists | `Yes` / `No` |

### Numeric features
| Column | Type | Description |
|---|---|---|
| Estimated_Value | float | Government estimate of contract value (USD) before award |
| Number_of_Offers_Received | integer | Number of offers/proposals received (1–12) |
| Requirement_Complexity_Score | integer (1–10) | Synthetic complexity rating; higher = more complex requirement |
| Contracting_Office_Open_Actions | integer | Simulated contracting office workload (concurrent open actions) |
| Days_Since_Requirement_Posted | integer | Days between requirement posting and current reference point |
| Prior_Year_Spend_Same_Requirement | float | Prior-year spend on this requirement if incumbent exists (USD); 0 if no incumbent |

### Target variables (for supervised learning)
| Column | Type | Task | Description |
|---|---|---|---|
| Award_Amount | float | Regression | Final award amount (USD); correlated with `Estimated_Value`, complexity, and vendor size |
| Days_to_Award | integer | Regression | Days from solicitation to award; increases with complexity, value, offer count, and full-and-open competition; decreases with incumbent presence |
| Small_Business_Award | integer (0/1) | Binary classification | 1 if a small business won; probability driven mainly by `Set_Aside_Type` |
| Protest_Filed | integer (0/1) | Binary classification (imbalanced, ~4–5% positive) | 1 if a bid protest was filed; probability increases with award value, full-and-open competition, and offer count |
| On_Time_Award | integer (0/1) | Binary classification | 1 if `Days_to_Award` fell within 1.25× the complexity-based target timeline |

**Suggested modeling exercises:**
- Regression: predict `Award_Amount` or `Days_to_Award` from the categorical + numeric features.
- Classification: predict `Small_Business_Award` or `On_Time_Award` (balanced-ish classes).
- Imbalanced classification: predict `Protest_Filed` (~5% positive rate) — good for practicing resampling, class weighting, precision/recall tradeoffs, and ROC/PR-AUC evaluation.

---

## Shared reference values across all three files

**VISN:** 1–18 (Veterans Integrated Service Networks)

**Category:** Medical/Clinical Services, Pharmaceuticals, Medical Equipment, IT Services, Construction, Professional Services, Facilities Management, Food Service, Security Services, Transportation

**Contract_Type:** Firm Fixed Price, Time and Materials, Cost Plus Fixed Fee, IDIQ, Blanket Purchase Agreement (BPA), Labor Hour

**Set-aside / socioeconomic categories:** SDVOSB (Service-Disabled Veteran-Owned Small Business), VOSB (Veteran-Owned Small Business), 8(a), HUBZone, WOSB (Women-Owned Small Business), Small Business, Full and Open (No Set-Aside)

## Known data-generation notes
- Values were generated with `numpy`/`random` using a fixed seed for reproducibility; re-running the generation script with the same seed reproduces identical files.
- Monetary fields use log-normal distributions scaled by category to mimic realistic right-skewed contract value distributions.
- No missing values exist except `Incumbent_Contractor` in the Forecast file, which is intentionally blank when `Recompete = No`.
- This is **not real VA procurement data** — it is intended solely for practicing data cleaning, EDA, and modeling workflows.

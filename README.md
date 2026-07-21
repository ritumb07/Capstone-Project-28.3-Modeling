[README.md](https://github.com/user-attachments/files/30209942/README.md)
# Capstone-Project-28.3-Modeling
Contains all relevant artifacts in this Folder to successfully evaluate the Capstone Project
# VA Acquisition Risk & Capacity Dashboard

Interactive Streamlit dashboard for non-technical stakeholders, built on the model outputs from
`VA_Acquisition_DS_Project.ipynb`. It answers the four business questions from the analysis:

1. Which acquisitions should receive additional oversight?
2. Which contracting offices may become overloaded?
3. Where are staffing shortages likely to occur?
4. Which acquisitions represent the greatest financial and schedule risk?

## Project structure

```
.
├── app.py                          # Streamlit dashboard (reads precomputed data only — fast to load)
├── precompute_dashboard_data.py    # Trains the models and writes the scored CSVs the dashboard reads
├── VA_Acquisition_Forecast.csv     # Source data
├── VA_Contract_Awards_Historical.csv
├── VA_Acquisition_Modeling_Data.csv
├── forecast_scored.csv             # Generated — every forecast item + model scores
├── office_summary.csv              # Generated — per-office workload/staffing metrics
├── model_metrics.json              # Generated — headline model validation metrics
├── requirements.txt
└── Dockerfile
```

The dashboard is deliberately split in two: a **precompute step** that trains models and scores
data (run occasionally, whenever source data changes) and a **read-only app** that just renders
the precomputed CSVs. This keeps the deployed app lightweight and fast — no training happens on
page load, and the app doesn't need a GPU or long startup time.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate/refresh the scored data (only needed once, or after source data changes)
python precompute_dashboard_data.py

# Launch the dashboard
streamlit run app.py
```

Then open the URL Streamlit prints (default `http://localhost:8501`).

## Refreshing the data

Whenever `VA_Acquisition_Forecast.csv`, `VA_Contract_Awards_Historical.csv`, or
`VA_Acquisition_Modeling_Data.csv` changes, re-run:

```bash
python precompute_dashboard_data.py
```

then restart the Streamlit app (or click "Rerun" in the Streamlit UI) — it will pick up the new
`forecast_scored.csv`, `office_summary.csv`, and `model_metrics.json` automatically.

---

## Deployment options

Pick based on who needs access and what infrastructure you already have. Ordered roughly from
"fastest to stand up" to "most production-grade."

### 1. Streamlit Community Cloud (free, fastest — good for a demo or internal pilot)

Best for: sharing a working prototype with a small group quickly, no infrastructure to manage.

1. Push this folder to a GitHub repository (public, or private on a paid plan).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, and click "New app."
3. Point it at your repo, branch, and `app.py`.
4. Streamlit Cloud installs `requirements.txt` and runs `precompute_dashboard_data.py` for you if
   you add it as a one-time setup step, or simply commit the already-generated `forecast_scored.csv`,
   `office_summary.csv`, and `model_metrics.json` to the repo so the app has data immediately.

Limitations: free tier apps sleep after inactivity and cold-start on the next visit; not intended
for sensitive/real procurement data, since the app is public-internet-facing by default (you can
restrict access via viewer allowlists on paid tiers).

### 2. Hugging Face Spaces (free, similar profile to Streamlit Cloud)

Best for: same use case as above, if you'd rather not tie the demo to GitHub-only auth. Spaces
supports Streamlit natively — create a Space, choose the Streamlit SDK, and push this folder.

### 3. Docker container on any cloud (production-grade, this repo includes a Dockerfile)

Best for: an internal tool multiple teams will rely on, with your own domain and access control.

```bash
docker build -t va-acquisition-dashboard .
docker run -p 8501:8501 va-acquisition-dashboard
```

Then deploy that image to whichever platform your organization already uses:

- **AWS**: push the image to ECR, run it on ECS Fargate (serverless containers) or App Runner
  (simplest — points at a container image and gives you a URL + autoscaling out of the box).
- **Azure**: Azure Container Apps or Azure App Service (Web App for Containers) — both take a
  container image directly and handle scaling/HTTPS for you.
- **Google Cloud**: Cloud Run — same pattern, scales to zero when idle so it's cost-efficient for
  an internal tool with intermittent traffic.

All three give you a stable HTTPS URL, environment-based scaling, and integrate with your cloud
provider's IAM/SSO if you need to restrict access.

### 4. Internal/on-premises server

Best for: data that shouldn't leave your network, or an organization with existing internal
hosting (common for government/regulated environments).

- Run the Docker container on an internal VM or Kubernetes cluster.
- Put it behind a reverse proxy (Nginx or your existing load balancer) for HTTPS termination.
- Add authentication at the proxy layer (e.g., an OAuth2 proxy tied to your organization's SSO —
  Okta, Azure AD/Entra ID, PIV/CAC-based auth) rather than relying on Streamlit's own (limited)
  auth options.

---

## Security & access considerations before using this with real data

This project currently runs on **synthetic data**, so none of the deployment options above pose a
data-sensitivity risk. Before pointing this dashboard at real acquisition data, work through:

- **Authentication**: Streamlit Community Cloud and Hugging Face Spaces are public by default
  (with limited allowlisting on paid tiers) — not appropriate for real procurement or vendor data.
  Prefer the Docker + internal/cloud deployment path with SSO in front of it.
- **Authorization to operate (ATO) / compliance**: real deployments on federal systems (VA or
  otherwise) typically need to go through your agency's ATO, FedRAMP, and cloud-authorization
  process before hosting on any cloud platform — check with your ISSO/IT security team on current
  requirements rather than assuming any option above is pre-approved.
- **Data hosting boundary**: for a government use case, cloud deployments would typically need to
  use a government-community cloud region (e.g., AWS GovCloud, Azure Government) rather than
  standard commercial cloud regions.
- **PII/CUI handling**: if real vendor or personnel data is added later, confirm it's classified
  correctly (PII, CUI, etc.) and that the hosting environment matches that classification's
  requirements.
- **Audit logging**: add access logging at the proxy/auth layer so you have a record of who viewed
  which acquisitions' risk scores.

## Known model limitations (see the "About the models" tab in the app)

- The protest-prediction model performs close to random (ROC-AUC ~0.50) on this synthetic dataset
  — treat its output as a soft signal, not a reliable individual prediction.
- The days-to-award and award-amount models perform considerably better and can be trusted with
  more confidence.
- All thresholds (90th-percentile value cutoffs, complexity-score cutoffs, 3-tier staffing
  clusters) were chosen for a synthetic-data demonstration and should be re-validated with
  subject-matter experts before use on real data.

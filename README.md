# Sugar Cosmetics: Instagram Performance Analytics

Streamlit dashboard and preprocessing notebook for the Sugar Cosmetics Instagram project (50,000 posts, 19 Apr 2024 to 19 Apr 2025).

## Run it

```bash
# 1. Preprocessing notebook (writes the clean data the dashboard reads)
pip install -r notebooks/requirements.txt
cd notebooks && jupyter nbconvert --to notebook --execute --inplace 01_data_preprocessing.ipynb && cd ..

# 2. Dashboard
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

The clean files are already included in `dashboard/data/`, so step 1 is only needed if you change the raw data or the notebook.

## Layout

```
data/raw/                      raw Excel export
notebooks/01_data_preprocessing.ipynb   validation, feature engineering, signal checks, export
dashboard/
  app.py                       entry point, shared sidebar filters, navigation
  pages/                       overview, content, timing_audience, funnel_hashtags, findings
  utils/                       data.py (loading, filters), stats.py (tests), charts.py, theme.py
  data/                        sugar_ig_clean.csv, analysis_summary.json, data_dictionary.csv
  assets/                      logo variants and favicon
  .streamlit/config.toml       dark theme
```

## Pages and brief tasks

| Page | Brief tasks |
|---|---|
| Overview | 1 KPI summary, 2 monthly posting trend |
| Content performance | 3 top 10 by likes, 4 top 10 by engagement rate, 5 post type comparison |
| Timing and audience | 6 day of week analysis, plus month, audience emotion, engagement source, posting intensity |
| Funnel and hashtags | 7 engagement funnel, 8 hashtag analysis |
| Findings and recommendations | 10 strategic recommendation, limitations, data gaps |

Task 9 (the combined interactive dashboard) is the app itself: sidebar filters for date, post type, campaign type, hashtag, engagement source, audience emotion and partial months, applied to every page except Findings.

## Definitions

- **Engagement rate** = (likes + comments + shares + saves) / reach x 100. An impressions-based version is kept in the data as `engagement_rate_impr`.
- **Hidden gem** = engagement rate in the top 25% and reach in the bottom 25% of the full dataset (fixed thresholds).
- **Partial months** = April 2024 (12 days) and April 2025 (19 days).
- **Significance** = Welch z-test of each group against all other posts, Bonferroni corrected for the number of groups; Kruskal-Wallis for the overall test. Colour on dots and heatmaps appears only where a gap survives correction.

## Known limits

Read the Findings page before presenting. In short: the export contains no caption, posting time, follower count, demographics, spend or clicks, and it behaves like simulated data, so differences between groups are small and mostly within noise.

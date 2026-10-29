# 🎯 Data Science Technical Challenges & Interviews

Hello! Welcome to this repository where I document the technical assessments, assignments, and case studies I have tackled during interview processes for Data Science roles. 

For me, every interview is a learning milestone. I keep this repository public to track my growth, gather feedback, and showcase my hands-on approach to solving real-world business problems.

---

## 💡 My Approach: ELI5 (Explain Like I'm 5)
In technology, writing code is only half the battle; the other half is communication. In every project folder, you will find that I explain my analysis, hypotheses, and conclusions in a simple, straightforward manner—**avoiding over-complicated jargon**. If I can't explain it simply, I haven't understood it well enough.

---

## 📚 Projects

| Date | Role | Problem | Techniques |
|------|------|---------|------------|
| 2020-11 | [Marketing Data Analyst](<2020-11 Gambling Company - Marketing Data Analyst/README.md>) | Predict house prices + SQL test | Regression (Ridge, Lasso, Random Forest, XGBoost), data cleaning |
| 2020-12 | [Data Scientist](<2020-12 Gambling Company - Data Scientist/README.md>) | Find which betting customers will become VIP | Classification (Logistic, Random Forest, XGBoost), log loss | 
| 2020-12 | [Data Science Analyst](<2020-12 Startup - Data Science Analyst/README.md>) | Group users to target in a marketing campaign | Clustering (K-means, elbow method) |
| 2022-08 | [Senior Data Analyst](<2022-08 Real Estate Company - Senior Data Analyst/README.md>) | Rental listings: KPIs and how to improve them | EDA, maps (geopandas) | 
| 2023-05 | [Growth Data Analyst](<2023-05 Startup - Growth Data Analyst/README.md>) | Do users walk more after installing the app? | A/B style tests (t-test, Bayesian) |
| 2023-06 | [Data Automation Specialist](<2023-06 Anti Virus Company - Data Automation Specialist/README.md>) | API data, sales forecast, campaign dashboard | Time series (SARIMA), Tableau | 

> Company names are hidden on purpose (e.g. "Gambling Company"). Each report starts with a short TL;DR (a summary of the key points).

---

## 📂 Project Structure

Every folder follows the same layout:

```
YYYY-MM Company type - Role/
├── README.md        ← the report: problem, analysis and conclusions
├── analysis.ipynb   ← the notebook (originally run on Google Colab)
├── analysis.py      ← the same code as a plain Python script
├── assignment.docx  ← the original task, when available
├── data/            ← input data
├── outputs/         ← results and saved models (most models are not uploaded: the script trains them again)
└── plots/           ← charts used in the report
```

**How to run it:** install the libraries once with `pip install -r requirements.txt`, then open a project folder and run `python analysis.py` from inside it (the scripts read `data/` and write to `outputs/`, both relative to that folder).
The notebooks are the original Google Colab versions, so they still read the files from Google Drive.
 
---

## 💬 Feedback & Connect

If you are a recruiter, a hiring manager, or a fellow data enthusiast with suggestions on how to optimize my models, feel free to send me an email to joaquinamiel@gmail.com

📫 **Let's talk!** You can find me on [LinkedIn](https://www.linkedin.com/in/joaquin-amiel/) or explore my general portfolio.

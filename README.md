# Financial Statement Anomaly Detector

## Objective
Create a professional finance and data science notebook that detects unusual financial statement behaviour in public companies.

This project is designed to be useful for equity analysts, forensic accounting reviewers, valuation professionals, auditors, and corporate finance analysts.

## Output
A complete `.ipynb` notebook containing:
- Explanations and documentation
- Python code for data processing and analysis
- Charts and tables for visualization
- Final interpretations of the data

## Main Goal
Detect potential accounting anomalies using:
- Financial statement data
- Ratio analysis
- Peer comparison
- Trend analysis
- Simple unsupervised machine learning (Isolation Forest)

*Note: The notebook currently uses a realistic sample dataset. It is designed so that the sample data can be easily replaced with real company data.*

## Project Structure
1. **Project introduction:** Explains the purpose, limits, and scope of the notebook.
2. **Import libraries:** Standard data science stack (pandas, numpy, matplotlib, scikit-learn).
3. **Create/Load data:** Generates a realistic sample dataset with injected anomalies.
4. **Data cleaning:** Handles missing values and basic accounting validation rules.
5. **Feature engineering:** Calculates financial ratios and year-on-year changes.
6. **Beneish M Score:** Implements the probabilistic model for earnings manipulation.
7. **Rule based anomaly detection:** Assigns risk scores based on defined financial red flags.
8. **Peer comparison:** Compares companies against sector peers.
9. **Unsupervised machine learning:** Uses Isolation Forest to detect multivariate statistical outliers.
10. **Visualisation:** Generates charts highlighting trends and anomalies.
11. **Company level diagnostic report:** A function to summarize findings for specific companies in plain English.
12. **Final ranked table:** A risk-ranked summary table.
13. **Export outputs:** Code to save results and specific company diagnostic data to CSV.
14. **Documentation:** Instructions on use and replacing the dataset.
15. **Future improvements:** Suggestions for enhancing the model (e.g. real data APIs, NLP, SHAP).

## How to run the notebook
1. Ensure you have the required libraries installed (`pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`).
2. Open `financial_statement_anomaly_detector.ipynb` in Jupyter Notebook or JupyterLab.
3. Run all cells sequentially.

## Disclaimer
The output of this notebook should be treated strictly as a risk flag and a starting point for deeper fundamental research. High anomaly scores or ML outlier flags do **not** serve as proof of fraud or financial manipulation.

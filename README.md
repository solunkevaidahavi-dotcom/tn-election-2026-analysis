# Tamil Nadu Election 2026 Analysis
## Codebasics Resume Project Challenge

### Project Overview
This project analyzes Tamil Nadu Assembly Election data to identify key electoral trends, constituency-level shifts, regional performance, vote share changes, and the impact of emerging political parties.

The analysis is presented through an interactive Streamlit dashboard and a stakeholder presentation designed for data-driven storytelling.

---

## Business Objective

To decode the major trends shaping the 2026 Tamil Nadu Assembly Election and communicate them through clear, neutral, and evidence-based insights.

---

## Key Questions Answered

- Which constituencies changed hands between elections?
- How did seat distribution change across regions?
- Which regions experienced the largest seat swings?
- How did vote share change for major parties?
- What impact did TVK have on the electoral landscape?
- Which regions emerged as battlegrounds?
- Which constituencies witnessed the closest contests?

---

## Dashboard Features

### 1. Seat Distribution Analysis
Compare seats won by major parties across regions in 2021 and 2026.

### 2. Constituency Flip Analysis
Identify constituencies that changed winning parties between elections.

### 3. Vote Share Analysis
Analyze vote share changes across regions and election years.

### 4. TVK Impact Analysis
Evaluate TVK's regional performance through vote share and seats won.

### 5. Battleground Regions
Highlight regions with the highest electoral volatility.

### 6. Closest Contests
Identify constituencies with the smallest winning margins.

---

## Technology Stack

- Python
- Pandas
- Streamlit
- Plotly
- GitHub

---

## Repository Structure

```text
tn-election-2026-analysis
│
├── README.md
│
├── dashboard
│   └── app.py
│
├── data
│   ├── constituency_master.csv
│   ├── tn_2021_results.csv
│   └── tn_2026_results.csv
│
└── presentation
    └── election_ppt.pptx
```

---

## Data Sources

- Election Commission of India (ECI)
- Publicly available election datasets

---

## How to Run the Dashboard

### Install Dependencies

```bash
pip install streamlit pandas plotly
```

### Run Dashboard

```bash
streamlit run dashboard/app.py
```

---

## Key Insights

- Constituency-level flips reveal changing voter preferences.
- Regional seat shifts highlight evolving political dynamics.
- Vote share trends provide context for seat distribution changes.
- TVK emerged as a notable factor in several regions.
- Some constituencies were won by extremely narrow margins.

---

## Neutrality Statement

This project is strictly data-driven and non-partisan.

No political endorsements, predictions, causal claims, or opinion-based conclusions have been made. All findings are derived solely from election data.

---

## Limitations

- Historical election data cannot predict future election outcomes.
- Vote share alone cannot explain voter behavior.
- Candidate-level and local factors are not captured.
- Analysis depends on the completeness of available data.


Submitted as part of the Codebasics Resume Project Challenge:

**"Decoding the 2026 Tamil Nadu Assembly Election"**

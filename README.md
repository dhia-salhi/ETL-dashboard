# Business Analytics Dashboard

An end-to-end ETL pipeline and interactive analytics dashboard built with Python. Pulls e-commerce data from a public API, transforms it with pandas, stores it in SQLite, and presents it through a Streamlit dashboard with Plotly visualisations.

---

## Features

- **KPI summary** — Revenue, estimated profit, orders, units sold, average rating, and discount
- **Revenue by category** — Horizontal bar chart comparing product categories
- **Daily revenue trend** — Line chart with 7-day rolling average
- **Top 10 products** — Best-selling products ranked by revenue
- **Price vs rating** — Scatter plot to identify high-value products
- **Monthly revenue vs profit** — Grouped bar chart by month
- **Revenue share** — Donut chart showing category breakdown
- **Raw data table** — Filterable table with CSV export

**Filters:** category, date range, minimum product rating

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language |
| requests | Fetch data from the DummyJSON API |
| pandas | Data cleaning and transformation |
| sqlite3 | Local data storage |
| Streamlit | Interactive dashboard |
| Plotly | Charts and visualisations |

Data source: [DummyJSON API](https://dummyjson.com/) — no API key required.

---

## Project Structure

```
etl-dashboard/
├── etl.py           # ETL pipeline
├── app.py           # Streamlit dashboard
├── requirements.txt # Dependencies
└── README.md
```

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the ETL pipeline
python etl.py

# Launch the dashboard
streamlit run app.py
```

The dashboard runs at `http://localhost:8501`.

---

## How It Works

The pipeline follows a standard ETL pattern:

1. **Extract** — Fetches product and order data from the DummyJSON API
2. **Transform** — Cleans and reshapes the data using pandas (column renaming, revenue/profit calculations, date parsing, null handling)
3. **Load** — Writes the processed data to a local SQLite database (`data.db`)
4. **Visualise** — Streamlit reads from the database and renders interactive Plotly charts

---

## Deployment

To deploy on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Run `python etl.py` locally and commit `data.db` to your repository
2. Push the project to GitHub
3. Go to [share.streamlit.io](https://share.streamlit.io), connect your repo, set the main file to `app.py`, and deploy

---

## License

MIT

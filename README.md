# 📊 Business Analytics Dashboard

An end-to-end **ETL pipeline + interactive analytics dashboard** built with Python.
Extracts real e-commerce data from a public API, transforms it with pandas,
stores it in SQLite, and visualises it with a beautiful Streamlit dashboard.

---

## 🚀 Live Demo

> Deploy to [Streamlit Community Cloud](https://streamlit.io/cloud) for free — see **Deployment** section below.

---

## 📸 What It Shows

| Section | Description |
|---|---|
| **KPI Cards** | Total Revenue, Est. Profit, Orders, Units Sold, Avg Rating, Avg Discount |
| **Revenue by Category** | Horizontal bar chart comparing categories |
| **Daily Revenue Trend** | Line chart with 7-day rolling average |
| **Top 10 Products** | Best-selling products by revenue |
| **Price vs Rating** | Scatter plot to spot high-value products |
| **Monthly Revenue vs Profit** | Grouped bar chart by month |
| **Revenue Share** | Donut chart showing category breakdown |
| **Raw Data Table** | Filterable + downloadable CSV export |

**Interactive filters:**
- 📂 Category multi-select
- 📅 Date range picker
- ⭐ Minimum product rating slider

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| `Python 3.10+` | Programming language |
| `requests` | Download data from the DummyJSON API |
| `pandas` | Clean, reshape, and transform the data |
| `sqlite3` | Store clean data in a local database |
| `streamlit` | Build the interactive web dashboard |
| `plotly` | Create beautiful interactive charts |

**Data source:** [DummyJSON API](https://dummyjson.com/) — free, no API key needed

---

## 📁 Project Structure

```
etl-dashboard/
│
├── etl.py           # ETL pipeline: Extract → Transform → Load
├── app.py           # Streamlit dashboard
├── requirements.txt # Python dependencies
├── README.md        # This file
└── data.db          # SQLite database (auto-generated — do NOT commit this)
```

---

## ⚡ Quick Start (Run Locally)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the ETL pipeline (creates data.db)
```bash
python etl.py
```
You should see:
```
✅ ETL COMPLETE! data.db is ready for the dashboard.
```

### 3. Launch the dashboard
```bash
streamlit run app.py
```
Your browser will automatically open at `http://localhost:8501` 🎉

---

## ☁️ Deploy to Streamlit Community Cloud (Free Hosting)

1. **Push to GitHub** (see next section)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch (`main`), and set the **Main file** to `app.py`
5. Click **"Deploy!"** — your app will be live in ~2 minutes

> ⚠️ **Important**: Before deploying, run `python etl.py` locally and commit `data.db`
> to your GitHub repo — Streamlit Cloud needs it to load the dashboard.

---

## 📤 Push to GitHub

```bash
# Step 1: Initialise git in the project folder
git init

# Step 2: Add all files
git add .

# Step 3: Commit
git commit -m "Initial commit: ETL pipeline + Streamlit dashboard"

# Step 4: Connect to your GitHub repo (replace with your actual URL)
git remote add origin https://github.com/YOUR_USERNAME/etl-dashboard.git

# Step 5: Push
git push -u origin main
```

---

## 🧠 How It Works (ETL Explained for Beginners)

**ETL** stands for **Extract, Transform, Load** — a standard data engineering pattern:

| Phase | What happens |
|---|---|
| **Extract** | `requests.get()` downloads product & order data from the DummyJSON API as JSON |
| **Transform** | `pandas` cleans the data: rename columns, calculate revenue/profit, fix dates, drop nulls |
| **Load** | `sqlite3` saves the clean DataFrames as tables inside `data.db` |
| **Visualise** | `streamlit` + `plotly` read from `data.db` and render interactive charts |

---

## 📝 License

MIT — free to use, modify, and share.

---

*Built as a beginner-friendly portfolio project demonstrating ETL pipelines and data visualisation.*

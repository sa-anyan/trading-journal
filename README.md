# Trading Journal v0.6 — Premium UI

A private-first TradingView strategy research lab built with Python, Streamlit,
SQLite, pandas and Plotly.

## v0.6 visual upgrade

- Premium dark navy / gold design language
- Refined sidebar, cards, forms, upload areas and tables
- Green = profitable; red = losing
- Asset-class colour semantics:
  - commodities = gold
  - forex = blue
  - indices = purple
  - crypto = cyan
- Premium equity curves with area fills
- Sign-coloured P&L charts
- Win/loss time scatter plot
- Sample-size bubble plot
- Diverging green/red day × hour heatmap
- Asset-class overview
- Streamlit Cloud theme configuration
- Git-safe ignore rules for local databases and secrets

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Cloud note

`data/journal.db` is excluded from Git. Streamlit Community Cloud's local
filesystem is not a durable production database. Use PostgreSQL/Supabase before
relying on the cloud deployment as the only copy of your journal.

## Recommended Git workflow

- `main`: stable deployed app
- `develop`: ongoing improvements
- feature branches: larger experimental changes

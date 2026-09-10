# SIAG

Societal Impact Action Group — Streamlit admin app for the IIT Madras Alumni Association.

## Setup

1. Copy `.env.example` to `.env` and fill in your MySQL credentials.
2. Run `db_schema.sql` in your MySQL instance.
3. Install deps: `pip install -r requirements.txt`
4. Start: `streamlit run app.py`

Admin login: see `.env.example` for the default admin password setup.

## Stack

Streamlit + MySQL + bcrypt authentication. See `db_schema.sql` for the schema.

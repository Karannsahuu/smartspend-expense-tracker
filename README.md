# SmartSpend – Expense Tracker

A responsive personal finance tracker built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features
- Add, edit and delete income/expense transactions
- Category-wise spending chart using Chart.js
- Dashboard totals and current-month expenses
- Rule-based smart spending insights
- Export transaction history to CSV
- SQLite database for local development

## Tech stack
Python, Flask, SQLite, HTML5, CSS3, JavaScript, Chart.js

## Run locally
1. Install Python 3.10 or newer.
2. Clone this repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/smartspend-expense-tracker.git
   cd smartspend-expense-tracker
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python app.py
   ```
6. Open http://127.0.0.1:5000

## Deployment note
The included `render.yaml` can be used as a starting point for Render deployment. The default SQLite database is stored on the service's local filesystem. Free Render web services have ephemeral filesystems, so SQLite data can be lost after restarts, spin-downs or redeploys. For a persistent public demo, connect a database with suitable persistence or use a host with persistent storage. Do not store sensitive financial information in this demo.

## Future improvements
- User authentication and per-user data isolation
- Monthly budgets and alerts
- Search and date filters
- Persistent hosted database
- Optional local/open-source language model for natural-language financial summaries

## Resume description
**SmartSpend – Personal Expense Tracker**
- Built a responsive expense tracking web app using Flask, SQLite, HTML, CSS and JavaScript.
- Implemented transaction CRUD, category-wise analytics, CSV export and automated spending insights.
- Visualized spending distribution using Chart.js.

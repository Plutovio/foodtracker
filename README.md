# PG Food Tracker

A personal, mobile-first web utility built to help residents of a Paying Guest (PG) accommodation track their daily food consumption, custom expenses (such as laundry or guest meals), payments, and calculate outstanding dues at the end of the month.

It is designed to be extremely lightweight, fast, and easy to use on mobile devices.

---

## Features

- **Tap-to-Toggle Meal Log:** High-contrast capsules to mark Breakfast, Lunch, or Dinner as Consumed/Skipped. Tapping saves instantly via HTMX without refreshing the page.
- **Rate-Locking Mechanism:** Historical meal entries keep the pricing rate active at the time they were logged, even if you update your default meal rates later in settings.
- **Custom Expense Tracker:** Easily log one-off extras like guest meals, special orders, laundry, or maintenance fees.
- **Payment Ledger:** Log all payments made to the PG owner (UPI, Cash, Bank Transfer).
- **Copy-to-Clipboard Summary:** One-click copy-pasteable WhatsApp report to send straight to your PG owner as proof of calculation.
- **Responsive Theme:** A clean, minimal light-mode slate and indigo UI designed specifically for quick mobile logins.

---

## Tech Stack

- **Backend:** Django 4.2+ (Python)
- **Database:** SQLite (local development), PostgreSQL (production/Render)
- **Frontend:** HTML5 + Vanilla CSS (Custom styling system) + HTMX (Server-driven dynamic interactions)
- **Production Server:** Gunicorn

---

## Local Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Plutovio/foodtracker.git
   cd foodtracker
   ```

2. **Set up Virtual Environment:**
   ```bash
   python -m venv .venv
   # Activate on Windows:
   .venv\Scripts\activate
   # Activate on macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Modify `.env` to set your secret key and set `DEBUG=True`.

5. **Run Migrations & Initialize Database:**
   ```bash
   python manage.py migrate
   ```

6. **Create a User Account:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://127.0.0.1:8000/` in your browser.

---

## Deployment Settings

### 1. Render Deployment
- **Build Command:**
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
  ```
- **Start Command:**
  ```bash
  gunicorn config.wsgi:application
  ```
- **Environment Variables:**
  - `SECRET_KEY`: A unique production secret.
  - `DEBUG`: `False`
  - `ALLOWED_HOSTS`: `localhost,127.0.0.1,your-app.onrender.com`
  - *(Optional)* `DATABASE_URL`: Automatically provisioned by Render when linking a PostgreSQL database.

### 2. Vercel Deployment
- Install Vercel CLI (`npm install -g vercel`), log in, and run:
  ```bash
  vercel --prod
  ```
  Vercel reads routing and build rules automatically from the included `vercel.json` file.

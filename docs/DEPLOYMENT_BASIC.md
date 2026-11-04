# Deployment Guide (Basic / University Submission)

> This is the short version of the deployment guide. For a university project, hosting
> it online usually isn't a requirement — a submission typically just needs the code
> plus a working local demo (`python manage.py runserver`). This guide is here **in
> case you want to show it off with a live link anyway** (e.g. in a presentation or
> portfolio). If you need a production-grade deployment with real security and
> reliability, use `DEPLOYMENT_PROFESSIONAL.md` instead.

## Do you need this at all?

If your submission just requires running the project locally and showing it to your
lecturer/grader on your own laptop, you can stop here — `python manage.py runserver` is
all you need, and none of this guide is necessary.

If you'd like a live link to share anyway, the steps below use **Render**, since it has
the simplest free option for a small project like this.

## Quick setup on Render (free tier)

1. **Do the handful of fixes in `BUGS_AND_FIXES_BASIC.md`** — these are quick either
   way and make the demo look correct.

2. **Add two small things to the code:**

   a. A file named `Procfile` in the project root (no file extension) containing:
      ```
      web: gunicorn ecommerce.wsgi:application
      ```

   b. Add this line to `requirements.txt`:
      ```
      gunicorn==23.0.0
      ```

3. **Make `settings.py` flexible enough to run on Render**, by changing these three
   lines near the top of `ecommerce/settings.py`:

   ```python
   import os

   SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-key-not-for-real-use')
   DEBUG = os.environ.get('DEBUG', 'True') == 'True'
   ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
   ```

   > Note: using a fallback secret key and allowing `*` hosts like this is fine for a
   > temporary class-project demo link, but is **not** something to do for a real,
   > ongoing public website — see `DEPLOYMENT_PROFESSIONAL.md` for the proper version
   > of this if the project ever needs to go further than a demo.

4. **Push your changes to GitHub:**
   ```bash
   git add Procfile requirements.txt ecommerce/settings.py
   git commit -m "Prepare project for a demo deployment"
   git push origin main
   ```

5. **Create a Render account** at [render.com](https://render.com) (GitHub sign-in is
   fastest).

6. **Create a Web Service:**
   - Click **New** → **Web Service**, and connect the `E-Commerce-Django` repo.
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py migrate
     ```
   - **Start Command:**
     ```
     gunicorn ecommerce.wsgi:application
     ```
   - Click **Create Web Service** and wait for the first deploy to finish.

7. **Create an admin login** so you can show the admin/vendor dashboards: open the
   **Shell** tab on your Render service and run:
   ```bash
   python manage.py createsuperuser
   ```

8. **Open your link** — Render will give you a URL like
   `https://your-app-name.onrender.com`. That's what you can share or present.

## A couple of things to know about this basic setup

- **The free tier "sleeps"** after a period of no traffic, so the first visit after a
  while may take 30-60 seconds to wake up — totally fine for a demo, just mention it if
  presenting live.
- **Data isn't permanent** — because this basic setup still uses SQLite (not a separate
  database), anything added on the live site (orders, new products) can be lost if the
  service restarts or redeploys. That's expected and fine for a demo; don't rely on it
  for anything you need to keep.
- If you later need the site to behave like a real, reliable product (persistent data,
  proper secrets, HTTPS hardening), that's exactly what `DEPLOYMENT_PROFESSIONAL.md` and
  `BUGS_AND_FIXES_PROFESSIONAL.md` are for.

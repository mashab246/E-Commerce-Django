# Deployment Guide (Professional / Production Setting) — Render & Railway

> **This is the full, professional-grade deployment guide** — written for putting the
> site online for real customers, with real money and real uptime expectations. If this
> is for a university submission where going online is optional or just for a demo, use
> `DEPLOYMENT_BASIC.md` instead — it's a much shorter version covering only what's
> needed to show the project running live.

This guide walks through putting MarketHub online for real, on either **Render** or
**Railway** — both are beginner-friendly hosting platforms well suited to a Django app
like this one.

> **Before you follow this guide:** work through `BUGS_AND_FIXES_PROFESSIONAL.md` first,
> at least everything under "Part 1 — Must fix before launch." Several of those fixes
> (database, static files, environment variables) are things this deployment guide
> assumes are already in place. Deploying before fixing them will result in a broken or
> unsafe site.

## Which one should you pick?

Both are good choices for a beginner. Rough differences:

| | Render | Railway |
|---|---|---|
| Free tier | Yes (web service sleeps after inactivity on free tier) | Usage-based trial credit, then paid |
| Postgres database | Free tier available | Included, usage-based |
| Setup style | Mostly dashboard + a `render.yaml` file (optional) | Mostly dashboard, very fast to click through |
| Good for | First deployment, simplest mental model | If you want everything (app + DB) in one project view |

If you're not sure, start with **Render** — the steps below are written for it first,
with Railway's equivalent steps alongside.

---

## Part A — One-time code changes needed for either platform

These are small additions to the project so it can run on a hosting platform instead of
your own laptop. (Some of these overlap with `BUGS_AND_FIXES.md` — if you already did
them there, skip ahead.)

### 1. Add a `Procfile`

Create a new file named `Procfile` (no extension) in the project root, next to
`manage.py`:

```
web: gunicorn ecommerce.wsgi:application --log-file -
```

This tells the hosting platform how to actually start your app. Railway can also work
without this file using its auto-detection, but it's good practice to include it for
both platforms.

### 2. Add production packages to `requirements.txt`

Make sure these lines are present (add any that are missing):

```
gunicorn==23.0.0
whitenoise==6.8.2
dj-database-url==2.2.0
psycopg2-binary==2.9.9
```

### 3. Confirm your `settings.py` reads configuration from environment variables

This should already be true if you completed `BUGS_AND_FIXES.md` items 1–6. In short,
your `settings.py` should:
- Read `SECRET_KEY` from an environment variable (no default — it should error if missing).
- Read `DEBUG` from an environment variable, defaulting to `False`.
- Read `ALLOWED_HOSTS` from an environment variable.
- Use `dj_database_url.config(...)` for `DATABASES`, so it automatically picks up the
  `DATABASE_URL` variable the platform's Postgres add-on provides.
- Have `STATIC_ROOT` set and WhiteNoise configured for static files.

### 4. Commit and push everything

```bash
git add Procfile requirements.txt ecommerce/settings.py
git commit -m "Prepare project for production deployment"
git push origin main
```

---

## Part B — Deploying on Render

### 1. Create a Render account

Go to [render.com](https://render.com) and sign up (GitHub sign-in is the fastest route
— it also makes connecting your repo a one-click step).

### 2. Create the Postgres database first

1. From the Render dashboard, click **New** → **PostgreSQL**.
2. Give it a name (e.g. `markethub-db`), pick the free plan, and create it.
3. Once it's ready, open it and copy the **Internal Database URL** — you'll paste this
   into the web service's environment variables in a moment.

### 3. Create the web service

1. Click **New** → **Web Service**.
2. Connect your GitHub account and select the `E-Commerce-Django` repository.
3. Fill in:
   - **Name:** `markethub` (or anything you like — this becomes part of your URL,
     e.g. `markethub.onrender.com`)
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:**
     ```
     gunicorn ecommerce.wsgi:application
     ```
4. Under **Environment Variables**, add each of these (click "Add Environment
   Variable" for each one):

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | A new random value — generate one with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `markethub.onrender.com` (use the exact hostname Render shows you) |
   | `CSRF_TRUSTED_ORIGINS` | `https://markethub.onrender.com` |
   | `DATABASE_URL` | Paste the Internal Database URL you copied in step 2 |

5. Click **Create Web Service**. Render will build and deploy automatically — watch the
   logs; this takes a few minutes the first time.

### 4. Create your admin account

Once the first deploy finishes, open the **Shell** tab for your web service (Render
provides this in the dashboard) and run:

```bash
python manage.py createsuperuser
```

Follow the prompts to set up your admin login.

### 5. Visit your site

Your app will be live at `https://markethub.onrender.com` (or whatever name you chose).
Log in to `/admin/` with the superuser account you just created to confirm everything
works, then click around the storefront.

### Redeploying later

Every time you `git push` to the `main` branch, Render automatically rebuilds and
redeploys the site using the same build/start commands above — you don't need to repeat
these steps.

---

## Part C — Deploying on Railway

### 1. Create a Railway account

Go to [railway.app](https://railway.app) and sign up with GitHub.

### 2. Create a new project from your repo

1. Click **New Project** → **Deploy from GitHub repo**.
2. Select the `E-Commerce-Django` repository. Railway will detect it's a Python project
   automatically.

### 3. Add a Postgres database

1. In your new project, click **New** → **Database** → **Add PostgreSQL**.
2. Railway automatically creates a `DATABASE_URL` variable and makes it available to
   your other services in the same project — you can reference it instead of copying it
   manually (see the next step).

### 4. Configure the web service

1. Click on your deployed web service (the one from your GitHub repo), then go to its
   **Variables** tab.
2. Add these variables:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | A new random value (same command as the Render section above) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | Your Railway-provided domain, e.g. `markethub-production.up.railway.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://markethub-production.up.railway.app` |
   | `DATABASE_URL` | Click "Add Reference" and select the Postgres service's `DATABASE_URL`, so it stays in sync automatically |

3. Go to the **Settings** tab for the web service and set:
   - **Build Command:**
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:**
     ```
     gunicorn ecommerce.wsgi:application
     ```
4. Under **Settings → Networking**, click **Generate Domain** if one hasn't been created
   automatically, to get your public URL.
5. Railway redeploys automatically whenever you change variables or settings, or push to
   GitHub. Watch the **Deployments** tab for build progress.

### 5. Create your admin account

Open the web service, go to its command/shell access (Railway's dashboard has a
"Shell" option on the service, or you can use the Railway CLI: `railway run python
manage.py createsuperuser`), and run:

```bash
python manage.py createsuperuser
```

### 6. Visit your site

Open the domain Railway generated for you, confirm the storefront loads, and log into
`/admin/` with the superuser you just created.

---

## Part D — After you're live

A few things worth doing once the site is up and working on either platform:

- **Uploaded images:** if you haven't yet set up external file storage (see
  `BUGS_AND_FIXES.md` item 6), do this soon — otherwise every product image uploaded by
  a vendor will disappear the next time you redeploy.
- **Custom domain:** both Render and Railway let you attach your own domain name (e.g.
  `markethub.com`) for free under their Settings → Custom Domain / Networking sections.
  If you do this, remember to add the new domain to both `ALLOWED_HOSTS` and
  `CSRF_TRUSTED_ORIGINS`.
- **Backups:** both platforms' managed Postgres databases support backups — check your
  plan's backup settings so you don't lose customer/order data if something goes wrong.
- **Monitoring:** keep an eye on each platform's built-in logs page after launch,
  especially in the first few days, to catch any errors real users run into.

---

*If anything in this guide doesn't match what you see in the Render/Railway dashboard
(these platforms update their UI occasionally), the overall steps — database first,
environment variables, build/start commands, create a superuser — stay the same even if
button names shift slightly.*

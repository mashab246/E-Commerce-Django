# Bugs & Fixes Checklist (Professional / Production Setting) — Read Before Going Live

> **This is the full, professional-grade version of this checklist** — written for a
> real, publicly hosted site with real customers and real money. If this is for a
> university submission that won't be exposed to the public, use
> `BUGS_AND_FIXES_BASIC.md` instead, which only covers the fixes that actually matter
> for that context.

This document lists everything found in a full code review of the MarketHub project that
should be fixed **before** this site is deployed for real customers. It's written so that
someone new to Django can follow along — each item explains *what's wrong*, *why it
matters*, and *exactly how to fix it*.

Work through this list top to bottom. The items under **"Must fix before launch"** are
either security holes, data-loss risks, or bugs that will visibly break the site for real
users. The items under **"Should fix soon"** won't necessarily break the site on day one,
but will cause real problems (lost customers, confusing admin errors, race conditions)
once there's real traffic.

Tick each box as you fix it.

---

## Part 1 — Must fix before launch

### 1. The secret key is hardcoded and committed to GitHub

**File:** `ecommerce/settings.py`, line 23

```python
SECRET_KEY = 'django-insecure-g^s7q_3g2pv^ow4w_ex#si-@t#plx4)xs&&a%!67o*a%h3s9jy'
```

**What this is:** Django uses `SECRET_KEY` to cryptographically sign things like login
sessions, CSRF tokens, and password-reset links.

**Why it's a problem:** This value is sitting in plain text in your public GitHub repo.
Anyone who looks at the code can use it to forge a valid admin session cookie or a
password-reset link for any user — essentially an admin backdoor. It must never be
checked into source control, and must be a different, secret value in production.

**How to fix it:**

```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
```

Then, on Render/Railway (see `DEPLOYMENT.md`), set an environment variable called
`SECRET_KEY` to a brand new random value — **do not reuse the one above**, treat it as
already leaked. You can generate a new one locally with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- [ ] Fixed

---

### 2. `DEBUG = True` will leak your entire codebase to visitors

**File:** `ecommerce/settings.py`, line 26

```python
DEBUG = True
```

**What this is:** When `DEBUG` is on, any error on the site shows a detailed yellow error
page with your source code, local variable values, and settings.

**Why it's a problem:** On a live site, this page is shown to *any visitor* who triggers
an error (even by accident) — handing out your source code, internal logic, and
potentially parts of your configuration.

**How to fix it:**

```python
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

Leave the `DEBUG` environment variable unset on Render/Railway (it will default to
`False`). Only turn it on locally on your own machine if you want to see detailed errors
while developing.

- [ ] Fixed

---

### 3. `ALLOWED_HOSTS` is empty — the site will refuse to load once DEBUG is off

**File:** `ecommerce/settings.py`, line 28

```python
ALLOWED_HOSTS = []
```

**What this is:** This setting tells Django which domain names are allowed to serve the
site (a security measure against "Host header" attacks).

**Why it's a problem:** An empty list only "works" by accident while `DEBUG = True`. The
moment you fix bug #2 above, every single request will be rejected with a `400 Bad
Request (DisallowedHost)` error — the site will appear completely broken.

**How to fix it:**

```python
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else []
```

Then set an `ALLOWED_HOSTS` environment variable on Render/Railway to your app's domain,
e.g. `your-app.onrender.com` (comma-separate multiple domains if you add a custom one
later). Never set this to `*` in production — that removes the protection entirely.

- [ ] Fixed

---

### 4. Email sending is silently broken (`MAILERS` isn't a real Django setting)

**File:** `ecommerce/settings.py`, lines 135–139

```python
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
```

**What this is:** This looks like it's trying to configure how Django sends emails
(useful for things like password reset emails, order confirmations, vendor approval
notices).

**Why it's a problem:** Django has no setting called `MAILERS` — this block does
nothing. The correct setting name is `EMAIL_BACKEND`, and it must be a plain string, not
a dictionary. Because of this typo, Django silently falls back to its default SMTP
backend with no server configured, so **any attempt to send an email anywhere in the app
will fail**.

**How to fix it:**

```python
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
```

The "console" backend (the default above) just prints emails to the server log instead
of actually sending them — fine for testing, but for real emails to reach real users
you'll eventually need a real email provider (e.g. Gmail SMTP, SendGrid, Mailgun) and
set `EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` as environment variables.

- [ ] Fixed

---

### 5. The database (SQLite) will lose all data every time you redeploy

**File:** `ecommerce/settings.py`, lines 82–87

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**What this is:** SQLite stores the entire database as one file (`db.sqlite3`) on disk.

**Why it's a problem:** Render and Railway run your app in containers with an
**ephemeral filesystem** — anything written to disk (like this file) is wiped out every
time you redeploy, restart, or scale the app. In practice, this means **every
order, every user account, every product a vendor creates will disappear the next time
you push a change or the service restarts.** This is the single most dangerous issue on
this list for a live store.

**How to fix it:** Use a real, managed Postgres database (both Render and Railway offer
one — see `DEPLOYMENT.md` for exact steps) instead of SQLite in production.

1. Add these to `requirements.txt`:
   ```
   dj-database-url==2.2.0
   psycopg2-binary==2.9.9
   ```
2. Update `settings.py`:
   ```python
   import dj_database_url

   DATABASES = {
       'default': dj_database_url.config(
           default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
           conn_max_age=600,
       )
   }
   ```
   This keeps SQLite for local development (when no `DATABASE_URL` variable exists) but
   automatically switches to Postgres in production, where Render/Railway provide a
   `DATABASE_URL` environment variable automatically when you attach a Postgres database.
3. After deploying, run `python manage.py migrate` against the new database (see
   `DEPLOYMENT.md`) and re-create your admin user with `createsuperuser`.

- [ ] Fixed

---

### 6. Uploaded images (product photos, etc.) will also vanish, and won't even load once DEBUG is off

**Files:** `ecommerce/settings.py` lines 141–142, `ecommerce/urls.py` (the `if
settings.DEBUG:` block near the bottom)

**What this is:** Vendor-uploaded product images are saved to a local `media/` folder on
disk, and are only served to browsers by a special Django helper that is **only active
while `DEBUG = True`**.

**Why it's a problem:** Two separate issues stack here:
1. Same ephemeral-disk problem as the database — any image a vendor uploads disappears
   on the next redeploy.
2. Once you correctly turn `DEBUG` off (bug #2), the code that actually serves `/media/...`
   URLs stops running entirely — so even images that do exist will 404 (image broken
   icon) for every visitor.

**How to fix it:** The proper fix is to store uploaded files somewhere that isn't your
app's own disk — an object storage service like **Cloudinary**, **AWS S3**, or
**Cloudflare R2**, using the `django-storages` package. This is a bit more setup than the
other fixes, so treat it as a dedicated task:

1. Pick a provider. **Cloudinary** has the simplest free tier and is a very common choice
   for small Django projects — it even has a dedicated `django-cloudinary-storage`
   package that needs almost no configuration.
2. Add the package to `requirements.txt` and follow its setup docs to point
   `DEFAULT_FILE_STORAGE` (or `STORAGES["default"]` on Django 6) at it, using environment
   variables for the API credentials (never hardcode them).
3. Once that's done, you can remove the `if settings.DEBUG:` media-serving block from
   `ecommerce/urls.py` entirely, since Django will no longer be responsible for serving
   media files at all.

If you'd like, this can be done as a focused follow-up task once the other items on this
list are fixed — it's the most involved change here.

- [ ] Fixed

---

### 7. Logging in redirects everyone to the same page — vendors and admins never reach their dashboards

**File:** `accounts/views.py`, lines 40–55

```python
class RoleBasedLoginView(LoginView):
    def get_default_redirect_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse("admin_dashboard")
        if user.role == "VENDOR":
            return reverse("vendors:vendor_dashboard")
        return reverse("products:product_list")
```

**What's wrong:** This method name, `get_default_redirect_url`, doesn't exist in
Django's `LoginView` — Django never calls it. The real method Django uses to decide
where to send someone after login is called `get_success_url`. Because of this typo, all
the logic above is dead code that never runs.

**What actually happens:** Every single user — customers, vendors, *and* admins — gets
redirected to the plain product listing page after logging in (controlled by
`LOGIN_REDIRECT_URL` in settings.py). Vendors and admins will think the dashboard
"doesn't work" because they never land on it.

**How to fix it:**

```python
from accounts.models import User

class RoleBasedLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user

        if user.is_superuser:
            return reverse("admin_dashboard")

        if user.role == User.Role.VENDOR:
            return reverse("vendors:vendor_dashboard")

        return super().get_success_url()
```

(Using `super().get_success_url()` as the fallback — instead of hardcoding the product
list — also makes Django's built-in "redirect back to the page you were trying to view
before being asked to log in" (`?next=`) continue to work for ordinary customers.)

- [ ] Fixed

---

### 8. Vendors can set negative or free prices on products

**Files:** `products/models.py` (the `price` field on `Product` and `ProductVariant`),
`products/forms.py`

**What's wrong:** The price field has no server-side minimum. The form only sets a `min`
attribute on the HTML input box, which is purely cosmetic — it only stops someone typing
a negative number *in a normal browser*. Anyone submitting the form directly (a modified
request, a script, or just disabling the browser's own validation) can set a product's
price to `-50` or `0`, and Django will happily save it.

**Why it matters:** Negative/zero prices can break order totals, discounts, and could
plausibly let someone be "paid" to buy something, depending on how totals are computed.

**How to fix it:** Add a server-side validator directly on the model field so the
database itself enforces the rule, not just the browser:

```python
from django.core.validators import MinValueValidator

price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
```

Apply this to both `Product.price` and `ProductVariant.price`. After changing the model,
you'll need to create and run a new migration:

```bash
python manage.py makemigrations products
python manage.py migrate
```

- [ ] Fixed

---

## Part 2 — Should fix soon (won't break day one, but will bite you)

These aren't launch-blockers in the same way as Part 1, but they're real bugs that will
cause confusing failures, lost money, or outages as soon as the site has real usage.
Fix these as soon as you reasonably can after launch, ideally before.

### 9. No HTTPS/security settings for Render's or Railway's proxy setup

Render and Railway both put your app behind a proxy that handles HTTPS for you, and
forward plain HTTP internally with a header that says "this was actually HTTPS." Without
telling Django about this, secure cookies, CSRF protection, and forced-HTTPS redirects
won't work correctly, and **login/checkout form submissions may get rejected** with a
CSRF error once the site is on HTTPS.

**Fix** — add this near the end of `ecommerce/settings.py`:

```python
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []
```

Then set `CSRF_TRUSTED_ORIGINS` to your site's full HTTPS URL, e.g.
`https://your-app.onrender.com`, as an environment variable.

- [ ] Fixed

### 10. Static files (CSS/JS) have no production serving set up

There's no `STATIC_ROOT` and no tool (like WhiteNoise) configured to serve CSS/JS files
in production — meaning the live site will look completely unstyled (no CSS at all).

**Fix:**

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

Add `'whitenoise.middleware.WhiteNoiseMiddleware'` to `MIDDLEWARE`, directly after
`'django.middleware.security.SecurityMiddleware'`. Add `whitenoise` to
`requirements.txt`. The deployment guide (`DEPLOYMENT.md`) includes the build command
that runs `collectstatic` so this takes effect.

- [ ] Fixed

### 11. `requirements.txt` is missing the packages needed to actually run in production

Currently only `asgiref`, `Django`, `pillow`, `sqlparse`, `tzdata` are listed. Add:

```
gunicorn==23.0.0
whitenoise==6.8.2
dj-database-url==2.2.0
psycopg2-binary==2.9.9
```

`gunicorn` is the production web server Render/Railway will actually run (the
`manage.py runserver` command used for local development is not safe or supported for
production).

- [ ] Fixed

### 12. Category admin allows circular parent/child relationships, which can hang the site

**File:** `products/admin.py` (`CategoryAdmin`)

The form used elsewhere (`CategoryForm`) correctly blocks a category from being set as
its own ancestor, but the Django admin page for categories doesn't use that form, so an
admin can accidentally set Category A's parent to B and B's parent to A. The product
listing page walks the category tree in a loop that never ends if there's a cycle,
effectively freezing that request forever.

**Fix:** In `products/admin.py`, tell the admin to use the safe form:

```python
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    ...
```

- [ ] Fixed

### 13. Stock "movements" in the admin don't actually change stock

**File:** `products/models.py` / `products/admin.py`

There's an `InventoryMovement` model meant to log stock added/removed, but creating one
in the admin never updates the product's actual `stock_quantity` — they're two
disconnected numbers. Whoever manages inventory will think they've updated stock when
they haven't.

**Fix:** See the detailed code suggestion from the review (apply the movement to
`ProductVariant.stock_quantity` inside `InventoryMovementAdmin.save_model`, wrapped in a
database transaction). This is a slightly bigger change — happy to implement it as a
follow-up if useful.

- [ ] Fixed

### 14. Checkout logic exists in two different places, and only one is tested

**Files:** `orders/views.py` (`checkout` — this is the one that actually runs) vs.
`orders/services.py` (`checkout_cart` — this is the one with tests, but nothing calls it)

This means the actual code path real customers go through when paying has no automated
tests at all, and the two versions have already started drifting apart (the tested
version is missing a check the live version has). Recommend consolidating down to one
implementation (`services.checkout_cart`, with the view calling it) so there's one
source of truth with test coverage.

- [ ] Fixed

### 15. Adding items to the cart doesn't lock stock rows, which can oversell during traffic spikes

**File:** `carts/views.py` (`add_to_cart`, `update_cart`)

The checkout step itself correctly locks stock rows to prevent two people buying the
last item at once, but adding things *to the cart* doesn't use that same protection —
`carts/services.py` already has the safe version. Point `carts/views.py` at
`carts/services.py`'s functions instead of its own separate logic.

- [ ] Fixed

### 16. Cancelling a vendor's order doesn't safely restore stock or fix the order total

**File:** `orders/views.py` (`cancel_vendor_order`)

Restoring stock after a cancellation reads-then-writes the stock number without locking,
which can lose updates under concurrent activity. It also never recalculates the
parent order's total price after a partial cancellation, so the order can show the
wrong total afterward. See the review notes for the exact fix (`F()` expressions
for the stock update, and recomputing totals from the remaining non-cancelled
suborders).

- [ ] Fixed

### 17. No password-reset flow for forgotten passwords

**File:** `accounts/urls.py`

There's no "forgot password" link or flow at all. Any customer who forgets their
password has no way to recover their account except contacting you directly. Django has
this built in — it mostly needs URLs wired up and a few templates, plus working email
(see item #4 above).

- [ ] Fixed

### 18. No automated tests for login/registration

**File:** `accounts/tests.py` (currently empty)

Since every other app depends on the `accounts` app for who's allowed to do what, it's
worth adding at least a few tests here so a future change doesn't silently break login
again (as happened with bug #7).

- [ ] Fixed

---

## Items reviewed and found OK (no action needed)

For completeness — these were checked carefully and are already done correctly:

- Password hashing (uses Django's built-in secure hashing, no plaintext).
- CSRF protection on login/logout forms.
- Vendors cannot view, edit, or cancel another vendor's products or orders (verified
  directly — this matches the fix mentioned in your recent commit history).
- No SQL injection risk anywhere — the whole codebase uses Django's ORM, no raw SQL.
- No hardcoded API keys, passwords, or secrets found anywhere else in the code.
- Checkout correctly recalculates prices/stock on the server rather than trusting
  anything sent from the browser — the most important anti-fraud check is in place.
- Money values consistently use `Decimal`, not floating-point numbers, avoiding rounding
  bugs.

---

*Once everything in Part 1 is checked off, move on to `DEPLOYMENT.md` to actually put
the site online.*

# Bugs & Fixes Checklist (Basic / University Submission)

> **This is the short version of this checklist**, for a university project that will be
> submitted and demoed, not launched as a real public website with real customers. It
> only includes fixes for things that would actually look wrong or behave wrong in a
> demo or when a grader clicks through the app.
>
> There's a longer, professional-grade version — `BUGS_AND_FIXES_PROFESSIONAL.md` — that
> also covers security hardening and production-infrastructure concerns (hosting
> secrets safely, databases that survive redeploys, HTTPS configuration, etc.). None of
> that is necessary just to submit and demo this project, so it's kept separate.

Work through the list below. Each item explains what's wrong, why it would show up
during a demo or grading, and exactly how to fix it. Tick each box as you go.

---

### 1. Logging in sends everyone to the same page — vendor/admin dashboards are unreachable

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

**Why this matters for your submission:** This is a real bug you'll run into the moment
you demo logging in as a vendor or admin — they'll land on the plain product list
instead of their dashboard, which will look broken in front of a grader.

**What's wrong:** `get_default_redirect_url` isn't a real method Django looks for.
Django's `LoginView` calls a method named `get_success_url` instead, so this code never
runs.

**Fix:**

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

- [ ] Fixed

---

### 2. Email sending is silently broken because of a typo in settings

**File:** `ecommerce/settings.py`, lines 135–139

```python
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
```

**Why this matters for your submission:** If any part of your app sends email (e.g. a
confirmation or notification), this setting does nothing because `MAILERS` isn't a real
Django setting — the correct name is `EMAIL_BACKEND`. If you demo any feature that
sends an email, it will fail.

If your project doesn't currently send any real emails during the demo, you can
deprioritize this one — but it's a one-line fix, so there's little reason not to do it.

**Fix:**

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This makes Django print emails to your terminal/console instead of actually sending
them — perfectly fine for a university project; you don't need a real email provider
for a submission.

- [ ] Fixed

---

### 3. Product prices can be set to negative or zero

**Files:** `products/models.py` (the `price` field on `Product` and `ProductVariant`),
`products/forms.py`

**Why this matters for your submission:** If a grader (or you, testing it) tries
entering a negative or zero price while demoing the vendor "add product" form, it will
be silently accepted, and the cart/checkout totals will look wrong (e.g. a negative
total). This is an easy, visible correctness bug to fix.

**Fix:** Add a minimum-value check directly on the model field:

```python
from django.core.validators import MinValueValidator

price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
```

Do this for both `Product.price` and `ProductVariant.price`. After editing the model,
run:

```bash
python manage.py makemigrations products
python manage.py migrate
```

- [ ] Fixed

---

### 4. An admin can accidentally create a category loop that freezes the product page

**File:** `products/admin.py` (`CategoryAdmin`)

**Why this matters for your submission:** If you're demoing category management in the
Django admin, setting Category A's parent to B and B's parent to A is possible, and it
will make the storefront's product listing page hang indefinitely the next time it's
opened — a bad thing to have happen live in front of a grader.

**Fix:** Tell the admin to reuse the form that already has a safety check built in:

```python
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    ...
```

- [ ] Fixed

---

### 5. Recording a stock "movement" in the admin doesn't change the actual stock number

**File:** `products/models.py` / `products/admin.py`

**Why this matters for your submission:** If your project description or demo includes
an inventory-tracking feature, this is where it would visibly fail — adding a "stock
in"/"stock out" record in the admin doesn't update the product's real stock count, so a
grader testing this feature will notice the number never changes.

If inventory tracking isn't something you plan to demo or isn't a graded requirement,
you can safely skip this one for a basic submission.

**Fix (optional for a basic submission, but here if you want it):** Update the
`stock_quantity` on the related product/variant whenever a movement is created — this
is a slightly bigger change than the others above, so ask if you'd like help wiring it
up.

- [ ] Fixed / Skipped (not required for my submission)

---

## Things you do NOT need to worry about for a university submission

These were found during the review but only matter if the site is actually going to be
hosted publicly for real users — they won't affect how the project looks or behaves
when you run it locally or demo it from a single machine:

- The secret key being hardcoded, `DEBUG` being left on, and `ALLOWED_HOSTS` being
  empty — these are security concerns for a *public* website, not for local
  development or a classroom demo.
- The database (SQLite) and uploaded images disappearing on redeploy — this is only a
  problem on hosting platforms with temporary storage; running locally, your data stays
  exactly where you left it.
- HTTPS/security headers, production static file serving, and the production package
  list — all deployment-specific concerns.
- Race conditions on cart/stock updates under heavy simultaneous traffic — unlikely to
  come up with the handful of users involved in a project demo.

If you later decide to actually host this project online (even just to show it off),
see `DEPLOYMENT_BASIC.md` for a lightweight walkthrough, and come back to
`BUGS_AND_FIXES_PROFESSIONAL.md` for the fixes that become relevant once it's public.

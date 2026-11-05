from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse
import secrets
from django.conf import settings
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


def register(request):
    if request.user.is_authenticated:
        return redirect("products:product_list")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            from django.contrib.auth import login
            login(request, user)
            return redirect("products:product_list")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


class RoleBasedLoginView(LoginView):
    def get_default_redirect_url(self):
        user = self.request.user

        if user.is_superuser:
            return reverse("admin_dashboard")

        if user.role == "VENDOR":
            return reverse("vendors:vendor_dashboard")

        return reverse("products:product_list")
    
@require_http_methods(["GET", "POST"])
def create_production_superuser(request):
    token = request.POST.get("token", "") if request.method == "POST" else ""
    setup_token = getattr(settings, "SUPERUSER_SETUP_TOKEN", "")

    if not setup_token or not secrets.compare_digest(token, setup_token):
        if request.method == "POST":
            return HttpResponseForbidden("Invalid setup token.")

    if User.objects.filter(is_superuser=True).exists():
        return render(
            request,
            "accounts/superuser_setup.html",
            {"message": "A superuser already exists."},
        )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            return render(
                request,
                "accounts/superuser_setup.html",
                {"error": "All fields are required."},
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "accounts/superuser_setup.html",
                {"error": "That username already exists."},
            )

        if User.objects.filter(email=email).exists():
            return render(
                request,
                "accounts/superuser_setup.html",
                {"error": "That email already exists."},
            )

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        return render(
            request,
            "accounts/superuser_setup.html",
            {"message": "Superuser created successfully. Remove this temporary setup page now."},
        )

    return render(request, "accounts/superuser_setup.html")
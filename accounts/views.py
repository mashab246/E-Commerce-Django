from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
import os

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
    

def create_temporary_superuser(request):
    User = get_user_model()

    if User.objects.filter(username="admin").exists():
        return HttpResponse(
            "The admin account already exists."
        )

    if request.method == "POST":
        setup_code = request.POST.get("setup_code", "")
        expected_code = os.environ.get("ADMIN_SETUP_CODE", "")

        if not expected_code or setup_code != expected_code:
            return HttpResponseForbidden("Invalid setup code.")

        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
        )

        return HttpResponse(
            "Superuser created successfully. Remove this temporary setup page now."
        )

    return render(
        request,
        "accounts/temporary_superuser_setup.html"
    )
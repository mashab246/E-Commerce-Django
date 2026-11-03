from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse

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

        # Superusers go to the custom MarketHub admin dashboard
        if user.is_superuser:
            return reverse("admin_dashboard")

        # Vendors go to their vendor dashboard
        if user.role == "VENDOR":
            return reverse("vendors:vendor_dashboard")

        # Customers go to the storefront
        return reverse("products:product_list")
    

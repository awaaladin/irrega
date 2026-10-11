from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=60)
    identifier = forms.CharField(label="Email or phone")
    password = forms.CharField(widget=forms.PasswordInput)
    pilot_code = forms.CharField(required=False, max_length=20)

    def clean_identifier(self):
        v = self.cleaned_data["identifier"].strip()
        if "@" in v:
            if User.objects.filter(email__iexact=v).exists():
                raise ValidationError("That email already has an account. Try signing in.")
        else:
            digits = "".join(c for c in v if c.isdigit() or c == "+")
            if len(digits) < 8:
                raise ValidationError("Enter a valid email or phone number.")
            if User.objects.filter(phone=digits).exists():
                raise ValidationError("That phone number already has an account. Try signing in.")
            v = digits
        return v

    def clean_password(self):
        p = self.cleaned_data["password"]
        password_validation.validate_password(p)
        return p

    def save(self):
        d = self.cleaned_data
        is_email = "@" in d["identifier"]
        user = User(first_name=d["name"], username=d["identifier"])
        if is_email:
            user.email = d["identifier"]
        else:
            user.phone = d["identifier"]
        user.set_password(d["password"])
        user.save()
        return user

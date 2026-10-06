from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class CadastroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

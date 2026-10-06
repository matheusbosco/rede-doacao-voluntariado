from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário da plataforma. O e-mail é obrigatório e único (sem diferenciar maiúsculas)."""

    email = models.EmailField("e-mail", unique=True)
    first_name = models.CharField("nome", max_length=150)

    REQUIRED_FIELDS = ["email", "first_name"]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

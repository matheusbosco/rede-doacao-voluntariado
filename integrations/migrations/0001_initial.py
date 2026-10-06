# Gerada pelo Django 5.2.18 em 2026-10-06 21:06.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CacheCep',
            fields=[
                ('cep', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('logradouro', models.CharField(blank=True, max_length=200)),
                ('bairro', models.CharField(blank=True, max_length=100)),
                ('cidade', models.CharField(max_length=100)),
                ('uf', models.CharField(max_length=2)),
                ('expira_em', models.DateTimeField()),
            ],
        ),
    ]

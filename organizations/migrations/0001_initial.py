# Gerada pelo Django 5.2.18 em 2026-10-06 21:06.

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150, verbose_name='nome')),
                ('descricao', models.TextField(validators=[django.core.validators.MaxLengthValidator(5000)], verbose_name='descrição')),
                ('causa', models.CharField(max_length=80, verbose_name='causa')),
                ('cnpj', models.CharField(blank=True, max_length=14, null=True, unique=True, validators=[django.core.validators.RegexValidator('\\A[0-9]{14}\\Z', 'Informe um CNPJ com 14 dígitos.')], verbose_name='CNPJ')),
                ('email_contato', models.EmailField(max_length=254, verbose_name='e-mail de contato')),
                ('telefone', models.CharField(blank=True, max_length=20, verbose_name='telefone')),
                ('site', models.URLField(blank=True, validators=[django.core.validators.URLValidator(schemes=['http', 'https'])], verbose_name='site')),
                ('cep', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator('\\A[0-9]{8}\\Z', 'Informe um CEP com 8 dígitos.')], verbose_name='CEP')),
                ('logradouro', models.CharField(max_length=200, verbose_name='logradouro')),
                ('numero', models.CharField(max_length=20, verbose_name='número')),
                ('complemento', models.CharField(blank=True, max_length=120, verbose_name='complemento')),
                ('bairro', models.CharField(max_length=100, verbose_name='bairro')),
                ('cidade', models.CharField(max_length=100, verbose_name='cidade')),
                ('uf', models.CharField(choices=[('AC', 'AC'), ('AL', 'AL'), ('AP', 'AP'), ('AM', 'AM'), ('BA', 'BA'), ('CE', 'CE'), ('DF', 'DF'), ('ES', 'ES'), ('GO', 'GO'), ('MA', 'MA'), ('MT', 'MT'), ('MS', 'MS'), ('MG', 'MG'), ('PA', 'PA'), ('PB', 'PB'), ('PR', 'PR'), ('PE', 'PE'), ('PI', 'PI'), ('RJ', 'RJ'), ('RN', 'RN'), ('RS', 'RS'), ('RO', 'RO'), ('RR', 'RR'), ('SC', 'SC'), ('SP', 'SP'), ('SE', 'SE'), ('TO', 'TO')], max_length=2, verbose_name='UF')),
                ('instrucoes_recebimento', models.TextField(validators=[django.core.validators.MaxLengthValidator(2000)], verbose_name='instruções de recebimento')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('aprovada', 'Aprovada'), ('recusada', 'Recusada')], default='pendente', max_length=8)),
                ('analisada_em', models.DateTimeField(blank=True, null=True)),
                ('motivo_analise', models.CharField(blank=True, max_length=500)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('analisada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('responsavel', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='ong', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['uf', 'cidade', 'bairro'], name='ong_localizacao_idx'), models.Index(fields=['status', 'nome'], name='ong_status_nome_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('analisada_em__isnull', True), ('analisada_por__isnull', True), ('status', 'pendente')), models.Q(('analisada_em__isnull', False), ('analisada_por__isnull', False), ('status__in', ['aprovada', 'recusada'])), _connector='OR'), name='ong_analise_coerente'), models.CheckConstraint(condition=models.Q(models.Q(('status', 'recusada'), _negated=True), models.Q(('motivo_analise', ''), _negated=True), _connector='OR'), name='ong_recusa_com_motivo')],
            },
        ),
    ]

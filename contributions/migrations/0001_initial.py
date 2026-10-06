# Gerada pelo Django 5.2.18 em 06/10/2026 às 21:47 UTC.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('campaigns', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contribuicao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('dinheiro', 'Dinheiro'), ('item', 'Item'), ('horas', 'Horas')], max_length=8)),
                ('valor', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='valor (BRL)')),
                ('quantidade', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='quantidade')),
                ('observacao', models.CharField(blank=True, max_length=500, verbose_name='observação')),
                ('status', models.CharField(choices=[('declarada', 'Declarada'), ('aceita', 'Aceita'), ('confirmada', 'Confirmada'), ('recusada', 'Recusada'), ('cancelada', 'Cancelada')], default='declarada', max_length=10)),
                ('avaliada_em', models.DateTimeField(blank=True, null=True)),
                ('motivo_avaliacao', models.CharField(blank=True, max_length=500)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('atualizada_em', models.DateTimeField(auto_now=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contribuicoes', to=settings.AUTH_USER_MODEL)),
                ('avaliada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('campanha', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contribuicoes', to='campaigns.campanha')),
            ],
            options={
                'indexes': [models.Index(fields=['campanha', 'status'], name='contrib_campanha_status_idx'), models.Index(fields=['autor', 'criada_em'], name='contrib_autor_criada_idx'), models.Index(fields=['criada_em'], name='contrib_criada_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('quantidade__isnull', True), ('tipo', 'dinheiro'), ('valor__gt', 0), ('valor__isnull', False)), models.Q(('quantidade__gt', 0), ('quantidade__isnull', False), ('tipo__in', ['item', 'horas']), ('valor__isnull', True)), _connector='OR'), name='contrib_medida_coerente'), models.CheckConstraint(condition=models.Q(('status', 'aceita'), ('tipo', 'dinheiro'), _negated=True), name='contrib_dinheiro_sem_aceite'), models.CheckConstraint(condition=models.Q(models.Q(('avaliada_em__isnull', True), ('avaliada_por__isnull', True), ('status', 'declarada')), models.Q(('avaliada_em__isnull', False), ('avaliada_por__isnull', False), ('status__in', ['aceita', 'confirmada', 'recusada'])), ('status', 'cancelada'), _connector='OR'), name='contrib_avaliacao_coerente'), models.CheckConstraint(condition=models.Q(models.Q(('status', 'recusada'), _negated=True), models.Q(('motivo_avaliacao', ''), _negated=True), _connector='OR'), name='contrib_recusa_com_motivo')],
            },
        ),
    ]

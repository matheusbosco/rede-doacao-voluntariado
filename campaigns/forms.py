from django import forms
from django.utils import timezone

from integrations.ufs import UFS

from .models import Campanha


class CampanhaForm(forms.ModelForm):
    class Meta:
        model = Campanha
        fields = ("titulo", "descricao", "tipo", "unidade", "meta", "data_inicio", "data_fim")
        widgets = {
            "data_inicio": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "data_fim": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def clean_data_fim(self):
        fim = self.cleaned_data["data_fim"]
        if self.instance._state.adding and fim < timezone.localdate():
            raise forms.ValidationError("A data de fim não pode estar no passado.")
        return fim


class BuscaCampanhaForm(forms.Form):
    q = forms.CharField(label="Buscar", max_length=100, required=False)
    cidade = forms.CharField(label="Cidade", max_length=100, required=False)
    bairro = forms.CharField(label="Bairro", max_length=100, required=False)
    uf = forms.ChoiceField(label="UF", choices=[("", "Todas")] + [(uf, uf) for uf in UFS], required=False)
    tipo = forms.ChoiceField(label="Tipo", choices=[("", "Todos")] + Campanha.Tipo.choices, required=False)
    status = forms.ChoiceField(
        label="Status", required=False,
        choices=[("", "Todos")] + [par for par in Campanha.Status.choices if par[0] != "rascunho"],
    )
    disponivel = forms.BooleanField(label="Disponível hoje", required=False)
    ordenacao = forms.ChoiceField(
        label="Ordenação", required=False,
        choices=[("", "Mais recentes"), ("-criada_em", "Mais recentes"), ("data_fim", "Data de fim")],
    )


class FiltroPainelCampanhaForm(forms.Form):
    status = forms.ChoiceField(label="Status", choices=[("", "Todos")] + Campanha.Status.choices, required=False)

from datetime import date

from django import forms

from campaigns.models import Campanha


class RelatorioForm(forms.Form):
    inicio = forms.DateField(label="Início", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    fim = forms.DateField(label="Fim", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    campanha = forms.ModelChoiceField(label="Campanha", queryset=Campanha.objects.none(), required=False)
    tipo = forms.ChoiceField(label="Tipo", choices=[("", "Todos")] + Campanha.Tipo.choices, required=False)

    def __init__(self, *args, ong, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campanha"].queryset = ong.campanhas.order_by("titulo", "pk")

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get("inicio"), dados.get("fim")
        if inicio and fim:
            if inicio > fim:
                self.add_error("fim", "O fim não pode ser anterior ao início.")
            elif (fim - inicio).days + 1 > 366:
                self.add_error("fim", "O intervalo deve ter no máximo 366 dias.")
        return dados

    def clean_fim(self):
        fim = self.cleaned_data["fim"]
        if fim == date.max:
            raise forms.ValidationError("Informe uma data de fim anterior a 31/12/9999.")
        return fim

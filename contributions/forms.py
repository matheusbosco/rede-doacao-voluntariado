from django import forms

from campaigns.models import Campanha

from .models import Contribuicao


class ContribuicaoForm(forms.Form):
    valor = forms.DecimalField(label="Valor declarado (BRL)", max_digits=12, decimal_places=2)
    quantidade = forms.DecimalField(label="Quantidade", max_digits=12, decimal_places=2)
    observacao = forms.CharField(label="Observação", max_length=500, required=False, widget=forms.Textarea)

    def __init__(self, *args, tipo, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("quantidade" if tipo == "dinheiro" else "valor")


class FiltroContribuicaoForm(forms.Form):
    tipo = forms.ChoiceField(label="Tipo", choices=[("", "Todos")] + Campanha.Tipo.choices, required=False)
    status = forms.ChoiceField(label="Status", choices=[("", "Todos")] + Contribuicao.Status.choices, required=False)


class FiltroRecebidasForm(FiltroContribuicaoForm):
    status = forms.ChoiceField(label="Status", choices=[("", "Aguardando análise ou realização"), ("todos", "Todos")] + Contribuicao.Status.choices, required=False)
    campanha = forms.ModelChoiceField(label="Campanha", queryset=Campanha.objects.none(), required=False)

    def __init__(self, *args, ong, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campanha"].queryset = ong.campanhas.order_by("titulo", "pk")

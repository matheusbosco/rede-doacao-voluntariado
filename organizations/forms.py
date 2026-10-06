import re

from django import forms

from integrations.ufs import UFS
from integrations.viacep import CepInvalido, normalizar_cep

from .models import Ong


class OngForm(forms.ModelForm):
    cep = forms.CharField(label="CEP", max_length=9)
    cnpj = forms.CharField(label="CNPJ", required=False)
    uf = forms.CharField(label="UF", widget=forms.Select(choices=[("", "---------")] + [(uf, uf) for uf in UFS]))

    class Meta:
        model = Ong
        fields = (
            "nome", "descricao", "causa", "cnpj", "email_contato", "telefone", "site",
            "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "instrucoes_recebimento",
        )

    def clean_cep(self):
        try:
            return normalizar_cep(self.cleaned_data["cep"])
        except CepInvalido as erro:
            raise forms.ValidationError(str(erro)) from erro

    def clean_cnpj(self):
        valor = self.cleaned_data["cnpj"]
        cnpj = re.sub(r"[^0-9]", "", valor)
        if valor and len(cnpj) != 14:
            raise forms.ValidationError("Informe um CNPJ com 14 dígitos.")
        return cnpj or None

    def clean_uf(self):
        uf = self.cleaned_data["uf"].upper()
        if uf not in UFS:
            raise forms.ValidationError("Selecione uma UF válida.")
        return uf

    def save(self, commit=True):
        ong = super().save(commit=False)
        campos_reanalise = {"nome", "cnpj", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf"}
        if ong.status == Ong.Status.APROVADA and any(
            self.cleaned_data[campo] != self.initial.get(campo) for campo in campos_reanalise
        ):
            ong.status = Ong.Status.PENDENTE
            ong.analisada_por = None
            ong.analisada_em = None
            ong.motivo_analise = ""
        if commit:
            ong.save()
            self.save_m2m()
        return ong


class BuscaOngForm(forms.Form):
    q = forms.CharField(label="Buscar", max_length=100, required=False)
    cidade = forms.CharField(label="Cidade", max_length=100, required=False)
    bairro = forms.CharField(label="Bairro", max_length=100, required=False)
    uf = forms.ChoiceField(label="UF", choices=[("", "Todas")] + [(uf, uf) for uf in UFS], required=False)

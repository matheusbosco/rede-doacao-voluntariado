from decimal import Decimal
from types import SimpleNamespace

from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

from .templatetags.quantidades import medida


@override_settings(LANGUAGE_CODE="pt-br")
class MedidaTests(SimpleTestCase):
    def test_dinheiro_tem_simbolo_e_duas_casas(self):
        self.assertEqual(medida(Decimal("150"), {"tipo": "dinheiro", "unidade": "BRL"}), "R$ 150,00")
        self.assertEqual(medida(Decimal("0"), {"tipo": "dinheiro", "unidade": "BRL"}), "R$ 0,00")

    def test_itens_inteiros_singular_plural_e_zero(self):
        campanha = SimpleNamespace(tipo="item", unidade="cesta")
        for valor, esperado in (("1.00", "1 cesta"), ("3.00", "3 cestas"), ("0.00", "0 cestas")):
            with self.subTest(valor=valor):
                self.assertEqual(medida(Decimal(valor), campanha), esperado)

    def test_unidades_com_terminacoes_comuns(self):
        for unidade, plural in (("kit", "kits"), ("caixa", "caixas"), ("pão", "pães"), ("papel", "papéis"), ("animal", "animais"), ("barril", "barris"), ("lápis", "lápis"), ("cobertor", "cobertores"), ("lençol", "lençóis"), ("cesta básica", "cestas básicas"), ("cesta de alimentos", "cestas de alimentos")):
            with self.subTest(unidade=unidade):
                self.assertEqual(medida(3, {"tipo": "item", "unidade": unidade}), f"3 {plural}")

    def test_horas_sem_zeros_desnecessarios_e_ate_duas_casas(self):
        campanha = SimpleNamespace(tipo="horas", unidade="hora")
        for valor, esperado in (("1", "1 hora"), ("2.50", "2,5 horas"), ("2.25", "2,25 horas"), ("2", "2 horas"), ("0", "0 horas")):
            with self.subTest(valor=valor):
                self.assertEqual(medida(Decimal(valor), campanha), esperado)

    def test_filtro_carregado_em_template_e_escapa_unidade(self):
        template = Template('{% load quantidades %}{{ valor|medida:campanha }}')
        resultado = template.render(Context({"valor": Decimal("1"), "campanha": {"tipo": "item", "unidade": "<script>"}}))
        self.assertEqual(resultado, "1 &lt;script&gt;")

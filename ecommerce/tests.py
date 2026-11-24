from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .forms import ProdutoForm
from .models import Cupom, ItemPedido, Organizacao, Pedido, Perfil, Produto, Vendedor


class BaseTeste(TestCase):
    def setUp(self):
        self.org_a = Organizacao.objects.create(nome="Loja Alpha")
        self.org_b = Organizacao.objects.create(nome="Loja Beta")

        self.admin_a = self.equipe("admin_a", self.org_a, "admin")
        self.oper_a = self.equipe("oper_a", self.org_a, "operador")
        self.admin_b = self.equipe("admin_b", self.org_b, "admin")
        self.cliente = User.objects.create_user(username="cliente", password="123")

        self.vend_a = Vendedor.objects.create(
            organizacao=self.org_a, usuario=User.objects.create_user("vend_a", password="1"), loja_nome="Vend A"
        )
        self.vend_b = Vendedor.objects.create(
            organizacao=self.org_b, usuario=User.objects.create_user("vend_b", password="1"), loja_nome="Vend B"
        )
        self.prod_a = Produto.objects.create(
            organizacao=self.org_a, vendedor=self.vend_a, nome="Hambúrguer", preco=Decimal("30.00"), estoque=10
        )
        self.prod_b = Produto.objects.create(
            organizacao=self.org_b, vendedor=self.vend_b, nome="Pizza", preco=Decimal("50.00"), estoque=10
        )
        self.ped_a = Pedido.objects.create(organizacao=self.org_a, cliente=self.admin_a, status="Pago")
        ItemPedido.objects.create(pedido=self.ped_a, produto=self.prod_a, quantidade=2)
        self.ped_b = Pedido.objects.create(organizacao=self.org_b, cliente=self.admin_b, status="Pago")
        ItemPedido.objects.create(pedido=self.ped_b, produto=self.prod_b, quantidade=1)

    def equipe(self, nome, org, papel):
        u = User.objects.create_user(username=nome, password="123")
        Perfil.objects.create(usuario=u, organizacao=org, papel=papel)
        return u

    def comprar(self, prod, vezes=1):
        for _ in range(vezes):
            self.client.post(reverse("adicionar_ao_carrinho", args=[prod.pk]))


class VitrineETestes(BaseTeste):
    def test_visitante_ve_produtos_de_todas_as_lojas(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        prods = list(r.context["produtos"])
        self.assertIn(self.prod_a, prods)
        self.assertIn(self.prod_b, prods)

    def test_filtro_por_loja_e_busca(self):
        r = self.client.get(reverse("home"), {"loja": self.org_a.id})
        self.assertEqual(list(r.context["produtos"]), [self.prod_a])
        r = self.client.get(reverse("home"), {"q": "piz"})
        self.assertEqual(list(r.context["produtos"]), [self.prod_b])
        self.assertEqual(self.client.get(reverse("home"), {"loja": "abc"}).status_code, 200)

    def test_paginas_publicas_abrem_sem_login(self):
        for nome in ("home", "ver_carrinho", "login", "cadastro"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_cadastro_cria_usuario_comum_logado(self):
        r = self.client.post(reverse("cadastro"), {
            "username": "maria", "password1": "Senh@Forte123", "password2": "Senh@Forte123",
        })
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username="maria")
        self.assertFalse(hasattr(u, "perfil"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), u.pk)


class CarrinhoETestes(BaseTeste):
    def test_visitante_monta_carrinho_com_cupom(self):
        Cupom.objects.create(organizacao=self.org_a, codigo="ALPHA10", desconto_percentual=Decimal("10.00"))
        self.comprar(self.prod_a, 2)
        self.client.post(reverse("aplicar_cupom"), {"codigo_cupom": "alpha10"})
        r = self.client.get(reverse("ver_carrinho"))
        self.assertEqual(r.context["subtotal_geral"], Decimal("60.00"))
        self.assertEqual(r.context["desconto_aplicado"], Decimal("6.00"))
        self.assertEqual(r.context["total_geral"], Decimal("54.00"))

    def test_carrinho_nao_mistura_lojas(self):
        self.comprar(self.prod_a)
        self.comprar(self.prod_b)
        itens = self.client.get(reverse("ver_carrinho")).context["itens"]
        self.assertEqual([i["produto"] for i in itens], [self.prod_a])

    def test_cupom_de_outra_loja_nao_vale(self):
        Cupom.objects.create(organizacao=self.org_b, codigo="BETA20", desconto_percentual=Decimal("20.00"))
        self.comprar(self.prod_a)
        self.client.post(reverse("aplicar_cupom"), {"codigo_cupom": "BETA20"})
        r = self.client.get(reverse("ver_carrinho"))
        self.assertIsNone(r.context["codigo_cupom"])
        self.assertEqual(r.context["desconto_aplicado"], Decimal("0.00"))

    def test_nao_passa_do_estoque_e_remove_itens(self):
        self.comprar(self.prod_a, 15)
        self.assertEqual(self.client.session["carrinho"][str(self.prod_a.pk)], 8)
        self.client.post(reverse("remover_do_carrinho", args=[self.prod_a.pk]))
        self.assertEqual(self.client.session["carrinho"][str(self.prod_a.pk)], 7)
        self.client.post(reverse("esvaziar_carrinho"))
        self.assertEqual(self.client.session["carrinho"], {})

    def test_acoes_do_carrinho_exigem_post(self):
        r = self.client.get(reverse("adicionar_ao_carrinho", args=[self.prod_a.pk]))
        self.assertEqual(r.status_code, 405)

    def test_finalizar_exige_login(self):
        self.comprar(self.prod_a)
        r = self.client.post(reverse("finalizar_pedido"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

    def test_cliente_comum_finaliza_pedido(self):
        Cupom.objects.create(organizacao=self.org_a, codigo="ALPHA10", desconto_percentual=Decimal("10.00"))
        self.client.force_login(self.cliente)
        self.comprar(self.prod_a, 2)
        self.client.post(reverse("aplicar_cupom"), {"codigo_cupom": "ALPHA10"})
        r = self.client.post(reverse("finalizar_pedido"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_geral"], Decimal("54.00"))
        ped = Pedido.objects.get(cliente=self.cliente)
        self.assertEqual(ped.organizacao, self.org_a)
        self.prod_a.refresh_from_db()
        self.assertEqual(self.prod_a.estoque, 6)
        self.assertEqual(self.client.session["carrinho"], {})


class EquipeETestes(BaseTeste):
    def test_cliente_comum_nao_acessa_area_da_equipe(self):
        self.client.force_login(self.cliente)
        for nome in ("novo_produto", "exportar_pedidos_csv"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 403, nome)
        self.assertEqual(self.client.get(reverse("editar_produto", args=[self.prod_a.pk])).status_code, 403)

    def test_visitante_vai_para_login_na_area_da_equipe(self):
        for nome in ("novo_produto", "exportar_pedidos_csv"):
            r = self.client.get(reverse(nome))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("login"), r.url)

    def test_editar_produto_de_outra_org_da_404(self):
        self.client.force_login(self.admin_a)
        r = self.client.get(reverse("editar_produto", args=[self.prod_b.pk]))
        self.assertEqual(r.status_code, 404)

    def test_novo_produto_usa_org_do_usuario(self):
        self.client.force_login(self.admin_a)
        r = self.client.post(reverse("novo_produto"), {
            "nome": "Suco", "descricao": "Natural", "preco": "12.00", "estoque": 5, "vendedor": self.vend_a.pk,
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Produto.objects.get(nome="Suco").organizacao, self.org_a)

    def test_form_filtra_vendedores_e_valida(self):
        form = ProdutoForm(org=self.org_a)
        vends = list(form.fields["vendedor"].queryset)
        self.assertIn(self.vend_a, vends)
        self.assertNotIn(self.vend_b, vends)
        ruim = ProdutoForm(
            data={"nome": "x", "preco": "-5", "estoque": 1, "vendedor": self.vend_a.pk}, org=self.org_a
        )
        self.assertFalse(ruim.is_valid())

    def test_unicidade_de_cupom_por_org(self):
        Cupom.objects.create(organizacao=self.org_a, codigo="P10", desconto_percentual=10)
        Cupom.objects.create(organizacao=self.org_b, codigo="P10", desconto_percentual=15)
        self.assertEqual(Cupom.objects.filter(codigo="P10").count(), 2)


class DashboardETestes(BaseTeste):
    def test_metricas_isoladas_por_org(self):
        self.client.force_login(self.admin_a)
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)
        k = r.context["kpis"]
        self.assertEqual(k["total_pedidos"], 1)
        self.assertEqual(k["receita_total"], Decimal("60.00"))
        self.assertEqual(k["ticket_medio"], Decimal("60.00"))
        self.assertEqual(r.context["ranking_produtos"][0]["pct"], 100)
        self.assertTrue(r.context["mostra_series"])
        self.assertContains(r, "grafMes")

    def test_periodo_futuro_vazio_sem_erro(self):
        self.client.force_login(self.admin_a)
        r = self.client.get(reverse("dashboard"), {"inicio": "2099-01-01", "fim": "2099-12-31"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["kpis"]["total_pedidos"], 0)
        self.assertContains(r, "Sem vendas no período")

    def test_periodo_de_hoje_e_data_invalida(self):
        self.client.force_login(self.admin_a)
        hoje = timezone.localdate().isoformat()
        r = self.client.get(reverse("dashboard"), {"inicio": hoje, "fim": hoje})
        self.assertEqual(r.context["kpis"]["total_pedidos"], 1)
        r = self.client.get(reverse("dashboard"), {"inicio": "abc"})
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse("dashboard"), {"inicio": "2026-05-02", "fim": "2026-05-01"})
        self.assertContains(r, "não pode ser maior")

    def test_operador_sem_series_nem_csv(self):
        self.client.force_login(self.oper_a)
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context["mostra_series"])
        self.assertNotContains(r, "grafMes")
        self.assertEqual(self.client.get(reverse("exportar_pedidos_csv")).status_code, 403)

    def test_csv_do_admin_isolado(self):
        self.client.force_login(self.admin_a)
        r = self.client.get(reverse("exportar_pedidos_csv"))
        self.assertEqual(r.status_code, 200)
        txt = r.content.decode("utf-8")
        self.assertIn("admin_a", txt)
        self.assertNotIn("admin_b", txt)

    def test_dashboard_nao_cresce_em_consultas(self):
        self.client.force_login(self.admin_a)
        for i in range(5):
            p = Pedido.objects.create(organizacao=self.org_a, cliente=self.admin_a)
            ItemPedido.objects.create(pedido=p, produto=self.prod_a, quantidade=1)
        with self.assertNumQueries(9):
            self.client.get(reverse("dashboard"))


class DashboardPublicoTeste(BaseTeste):
    def test_visitante_ve_dashboard_de_uma_loja(self):
        r = self.client.get(reverse("dashboard"), {"loja": self.org_b.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["organizacao"], self.org_b)
        self.assertEqual(r.context["kpis"]["receita_total"], Decimal("50.00"))
        self.assertNotContains(r, "Exportar pedidos")
        self.assertNotContains(r, "Repor estoque")
        self.assertContains(r, "grafMes")

    def test_visitante_sem_loja_cai_na_primeira(self):
        r = self.client.get(reverse("dashboard"), {"loja": "abc"})
        self.assertEqual(r.context["organizacao"], self.org_a)

    def test_cliente_comum_tambem_ve(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_equipe_continua_presa_na_propria_org(self):
        self.client.force_login(self.admin_a)
        r = self.client.get(reverse("dashboard"), {"loja": self.org_b.id})
        self.assertEqual(r.context["organizacao"], self.org_a)

    def test_desligando_o_modo_publico(self):
        with self.settings(DASHBOARD_PUBLICO=False):
            r = self.client.get(reverse("dashboard"))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("login"), r.url)
            self.client.force_login(self.cliente)
            self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)


class ApiTeste(BaseTeste):
    def test_api_exige_equipe(self):
        api = APIClient()
        self.assertIn(api.get("/api/produtos/").status_code, (401, 403))
        api.force_authenticate(user=self.cliente)
        self.assertEqual(api.get("/api/produtos/").status_code, 403)
        self.assertEqual(api.get("/api/dashboard/").status_code, 403)

    def test_api_produtos_isolamento_e_validacao(self):
        api = APIClient()
        api.force_authenticate(user=self.admin_a)
        ids = [i["id"] for i in api.get("/api/produtos/").data]
        self.assertIn(self.prod_a.id, ids)
        self.assertNotIn(self.prod_b.id, ids)
        self.assertEqual(api.get(f"/api/produtos/{self.prod_b.id}/").status_code, 404)
        base = {"nome": "N", "preco": "25.50", "estoque": 8}
        r = api.post("/api/produtos/", {**base, "preco": "-10", "vendedor": self.vend_a.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        r = api.post("/api/produtos/", {**base, "vendedor": self.vend_b.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        r = api.post("/api/produtos/", {**base, "vendedor": self.vend_a.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["organizacao"], self.org_a.id)

    def test_api_dashboard(self):
        api = APIClient()
        api.force_authenticate(user=self.admin_a)
        r = api.get("/api/dashboard/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["kpis"]["total_pedidos"], 1)

from django.contrib.auth import views as auth
from django.urls import path, reverse_lazy

from . import views
from .forms import EntrarForm

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "entrar/",
        auth.LoginView.as_view(
            template_name="ecommerce/conta.html",
            authentication_form=EntrarForm,
            redirect_authenticated_user=True,
            next_page=reverse_lazy("home"),
            extra_context={"modo": "entrar"},
        ),
        name="login",
    ),
    path("sair/", auth.LogoutView.as_view(next_page=reverse_lazy("home")), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("produtos/novo/", views.novo_produto, name="novo_produto"),
    path("produtos/<int:pk>/editar/", views.editar_produto, name="editar_produto"),
    path("carrinho/", views.ver_carrinho, name="ver_carrinho"),
    path("carrinho/adicionar/<int:produto_id>/", views.adicionar_ao_carrinho, name="adicionar_ao_carrinho"),
    path("carrinho/remover/<int:produto_id>/", views.remover_do_carrinho, name="remover_do_carrinho"),
    path("carrinho/esvaziar/", views.esvaziar_carrinho, name="esvaziar_carrinho"),
    path("carrinho/cupom/", views.aplicar_cupom, name="aplicar_cupom"),
    path("finalizar-pedido/", views.finalizar_pedido, name="finalizar_pedido"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/exportar-csv/", views.exportar_pedidos_csv, name="exportar_pedidos_csv"),
]

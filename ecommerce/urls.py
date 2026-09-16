from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'carrinho/adicionar/<int:produto_id>/',
        views.adicionar_ao_carrinho,
        name='adicionar_ao_carrinho',
    ),
    path(
        'carrinho/remover/<int:produto_id>/',
        views.remover_do_carrinho,
        name='remover_do_carrinho',
    ),
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/cupom/', views.aplicar_cupom, name='aplicar_cupom'),
    path('finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido'),
]
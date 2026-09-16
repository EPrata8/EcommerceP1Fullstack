from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'carrinho/adicionar/<int:produto_id>/',
        views.adicionar_ao_carrinho,
        name='adicionar_ao_carrinho',
    ),
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('finalizar-pedido/', views.finalizar_pedido, name='finalizar_pedido'),
]
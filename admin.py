from django.contrib import admin
from .models import Cupom, ItemPedido, Organizacao, Pedido, Produto, Vendedor
from .forms import ProdutoForm

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    readonly_fields = ["preco_unitario"]

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "total", "status", "criado_em"]
    inlines = [ItemPedidoInline]
    readonly_fields = ["total"]

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    form = ProdutoForm

admin.site.register(Organizacao)
admin.site.register(Vendedor)
admin.site.register(Cupom)
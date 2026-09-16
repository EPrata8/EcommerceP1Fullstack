from django.contrib import admin
from .models import Cupom, ItemPedido, Organizacao, Pedido, Produto, Vendedor

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    readonly_fields = ["preco_unitario"]

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "total", "status", "criado_em"]
    inlines = [ItemPedidoInline]
    readonly_fields = ["total"]

admin.site.register(Organizacao)
admin.site.register(Vendedor)
admin.site.register(Produto)
admin.site.register(Cupom)
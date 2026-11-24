from django.contrib import admin
<<<<<<< HEAD
from django.utils.html import format_html
=======
from .models import Cupom, ItemPedido, Organizacao, Pedido, Produto, Vendedor
from .forms import ProdutoForm

>>>>>>> 3a39be6964b3f167629dc8b6025f92803e5a3fe4

from .models import Cupom, ItemPedido, Organizacao, Pedido, Perfil, Produto, Vendedor

admin.site.site_header = "Gestão E-commerce"
admin.site.site_title = "Admin E-commerce"
admin.site.index_title = "Painel de Controle da Loja"


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    extra = 0


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "total_produtos", "total_pedidos", "criada_em")
    search_fields = ("nome",)
    ordering = ("nome",)

    @admin.display(description="Produtos")
    def total_produtos(self, obj):
        return obj.produto_set.count()

    @admin.display(description="Pedidos")
    def total_pedidos(self, obj):
        return obj.pedido_set.count()


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "organizacao", "papel")
    list_filter = ("organizacao", "papel")
    search_fields = ("usuario__username", "usuario__email", "organizacao__nome")
    autocomplete_fields = ("usuario", "organizacao")


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ("loja_nome", "usuario", "organizacao")
    list_filter = ("organizacao",)
    search_fields = ("loja_nome", "usuario__username", "organizacao__nome")
    autocomplete_fields = ("usuario", "organizacao")


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "organizacao", "vendedor", "preco", "estoque", "situacao_estoque")
    list_editable = ("preco", "estoque")
    list_filter = ("organizacao", "vendedor")
    search_fields = ("nome", "descricao", "vendedor__loja_nome")
    autocomplete_fields = ("organizacao", "vendedor")
    list_per_page = 20

    fieldsets = (
        ("Identificação do Produto", {
            "fields": ("organizacao", "vendedor", "nome", "descricao"),
        }),
        ("Preço e Controle de Estoque", {
            "fields": ("preco", "estoque"),
        }),
    )

    @admin.display(description="Situação")
    def situacao_estoque(self, obj):
        if obj.estoque == 0:
            cor, texto = "#dc3545", "Esgotado"
        elif obj.estoque <= 5:
            cor, texto = "#ffc107", "Estoque baixo"
        else:
            cor, texto = "#198754", "Disponível"
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:12px; font-size:12px; font-weight:600;">{}</span>',
            cor,
            texto,
        )


@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ("codigo", "desconto_percentual", "ativo", "organizacao")
    list_editable = ("desconto_percentual", "ativo")
    list_filter = ("organizacao", "ativo")
    search_fields = ("codigo", "organizacao__nome")
    autocomplete_fields = ("organizacao",)


class ItemInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("preco_unitario", "subtotal_item")
    autocomplete_fields = ("produto",)

    @admin.display(description="Subtotal")
    def subtotal_item(self, obj):
        if obj.pk:
            return f"R$ {obj.preco_unitario * obj.quantidade:.2f}"
        return "-"


@admin.action(description="Marcar pedidos selecionados como Pago")
def marcar_como_pago(modeladmin, request, queryset):
    queryset.update(status="Pago")


@admin.action(description="Marcar pedidos selecionados como Cancelado")
def marcar_como_cancelado(modeladmin, request, queryset):
    queryset.update(status="Cancelado")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "organizacao", "status", "total", "criado_em")
    list_editable = ("status",)
    list_filter = ("organizacao", "status", "criado_em")
    search_fields = ("id", "cliente__username", "organizacao__nome")
    date_hierarchy = "criado_em"
    readonly_fields = ("total", "criado_em")
    autocomplete_fields = ("organizacao", "cliente", "cupom")
    inlines = [ItemInline]
    actions = [marcar_como_pago, marcar_como_cancelado]

<<<<<<< HEAD
    fieldsets = (
        ("Dados do Pedido", {
            "fields": ("organizacao", "cliente", "status", "criado_em"),
        }),
        ("Valores e Desconto", {
            "fields": ("cupom", "total"),
        }),
    )
=======
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    form = ProdutoForm

admin.site.register(Organizacao)
admin.site.register(Vendedor)
admin.site.register(Cupom)
>>>>>>> 3a39be6964b3f167629dc8b6025f92803e5a3fe4

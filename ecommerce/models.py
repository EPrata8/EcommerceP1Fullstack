from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Organizacao(models.Model):
    nome = models.CharField(max_length=120)
    criada_em = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.nome


class DaOrganizacao(models.Model):
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class Perfil(models.Model):
    PAPEIS = [("admin", "Administrador"), ("operador", "Operador")]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    organizacao = models.ForeignKey(Organizacao, on_delete=models.PROTECT)
    papel = models.CharField(max_length=20, choices=PAPEIS, default="operador")

    @property
    def eh_admin(self):
        return self.papel == "admin"

    def __str__(self):
        return f"{self.usuario.username} - {self.organizacao.nome}"


class Vendedor(DaOrganizacao):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    loja_nome = models.CharField(max_length=100)

    def __str__(self):
        return self.loja_nome


class Produto(DaOrganizacao):
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    estoque = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco} (Estoque: {self.estoque})"


class Cupom(DaOrganizacao):
    codigo = models.CharField(max_length=50)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organizacao", "codigo"], name="cupom_codigo_unico_por_org"
            )
        ]

    def __str__(self):
        return f"{self.codigo} ({self.desconto_percentual}%)"


class Pedido(DaOrganizacao):
    STATUS = [("Pendente", "Pendente"), ("Pago", "Pago"), ("Cancelado", "Cancelado")]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    cupom = models.ForeignKey(Cupom, on_delete=models.SET_NULL, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pendente", choices=STATUS)

    class Meta:
        indexes = [models.Index(fields=["organizacao", "criado_em"])]

    def calcular_total(self):
        bruto = sum(i.preco_unitario * i.quantidade for i in self.itens.all())
        if self.cupom and self.cupom.ativo:
            bruto -= bruto * (self.cupom.desconto_percentual / 100)
        self.total = bruto
        self.save(update_fields=["total"])
        return self.total

    def __str__(self):
        return f"Pedido #{self.id} - Cliente: {self.cliente.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="itens", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if not self.pk and self.quantidade > self.produto.estoque:
            raise ValidationError(
                f"Estoque insuficiente para '{self.produto.nome}'. "
                f"Disponível: {self.produto.estoque}."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            self.preco_unitario = self.produto.preco
            self.produto.estoque -= self.quantidade
            self.produto.save()
        super().save(*args, **kwargs)
        self.pedido.calcular_total()

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

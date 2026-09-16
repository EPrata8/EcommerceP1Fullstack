from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

class Organizacao(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Vendedor(models.Model):
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    loja_nome = models.CharField(max_length=100)

    def __str__(self):
        return self.loja_nome

class Produto(models.Model):
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nome} - R$ {self.preco} (Estoque: {self.estoque})"

class Cupom(models.Model):
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50, unique=True)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo} ({self.desconto_percentual}%)"

class Pedido(models.Model):
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE)
    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="pedidos"
    )
    cupom = models.ForeignKey(
        Cupom, on_delete=models.SET_NULL, blank=True, null=True
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default="Pendente",
        choices=[
           ("Pendente", "Pendente"),
           ("Pago", "Pago"),
           ("Cancelado", "Cancelado"),
        ],
    )

    def calcular_total(self):
        total_itens = sum(
            item.preco_unitario * item.quantidade for item in self.itens.all()
        )
        if self.cupom and self.cupom.ativo:
            desconto = total_itens * (self.cupom.desconto_percentual / 100)
            total_itens -= desconto
        self.total = total_itens
        self.save(update_fields=["total"])
        return self.total

    def __str__(self):
        return f"Pedido #{self.id} - Cliente: {self.cliente.username}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, related_name="itens", on_delete=models.CASCADE
    )
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if not self.pk and self.quantidade > self.produto.estoque:
            raise ValidationError(
                f"Estoque insuficiente para '{self.produto.nome}'. Disponível:"
                f" {self.produto.estoque}."
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
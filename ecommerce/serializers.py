from rest_framework import serializers
from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ["id", "nome", "descricao", "preco", "estoque", "vendedor", "organizacao"]
        read_only_fields = ["organizacao"]

    # preço/estoque: validação herdada do model (sem duplicar a regra).

    def validate_vendedor(self, vendedor):
        org = self.context["request"].user.perfil.organizacao
        if vendedor.organizacao_id != org.id:
            raise serializers.ValidationError("Vendedor inválido para esta organização.")
        return vendedor

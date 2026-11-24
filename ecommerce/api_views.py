from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .acesso import DaEquipe, org_atual
from .dashboard import obter_metricas_dashboard
from .models import Produto
from .serializers import ProdutoSerializer


class ProdutosDaOrg:
    serializer_class = ProdutoSerializer
    permission_classes = [DaEquipe]

    def get_queryset(self):
        return Produto.objects.filter(organizacao=org_atual(self.request)).select_related(
            "organizacao", "vendedor"
        )


class ProdutoListCreateAPIView(ProdutosDaOrg, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(organizacao=org_atual(self.request))


class ProdutoDetailAPIView(ProdutosDaOrg, generics.RetrieveUpdateDestroyAPIView):
    pass


class DashboardApiView(APIView):
    permission_classes = [DaEquipe]

    def get(self, request):
        m = obter_metricas_dashboard(request, org_atual(request))
        m["estoque_baixo"] = [
            {"id": p.id, "nome": p.nome, "estoque": p.estoque} for p in m["estoque_baixo"]
        ]
        return Response(m)

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .forms import filtrar_periodo
from .models import ItemPedido, Pedido, Produto

VALIDOS = ~Q(status="Cancelado")


def atalhos():
    hoje = timezone.localdate()
    return [
        {"rotulo": rot, "inicio": hoje - timedelta(days=d), "fim": hoje}
        for rot, d in (("7 dias", 7), ("30 dias", 30), ("90 dias", 90))
    ]


def obter_metricas_dashboard(request, org):
    peds = filtrar_periodo(request, Pedido.objects.filter(organizacao=org))

    kpis = peds.aggregate(
        total_pedidos=Count("id"),
        receita_total=Sum("total", filter=VALIDOS),
        ticket_medio=Avg("total", filter=VALIDOS),
        clientes_unicos=Count("cliente", distinct=True),
        pedidos_pendentes=Count("id", filter=Q(status="Pendente")),
    )

    ranking = list(
        ItemPedido.objects.filter(pedido__in=peds)
        .exclude(pedido__status="Cancelado")
        .values("produto__nome")
        .annotate(quantidade_vendida=Sum("quantidade"))
        .order_by("-quantidade_vendida", "produto__nome")[:5]
    )
    topo = ranking[0]["quantidade_vendida"] if ranking else 1
    for r in ranking:
        r["pct"] = round(r["quantidade_vendida"] * 100 / topo)

    meses = (
        peds.annotate(mes=TruncMonth("criado_em"))
        .values("mes")
        .annotate(qtd=Count("id"), receita=Sum("total", filter=VALIDOS))
        .order_by("mes")
    )
    por_mes = [
        {"mes": r["mes"].strftime("%m/%Y"), "total": r["qtd"], "receita": float(r["receita"] or 0)}
        for r in meses
    ]

    por_status = list(peds.values("status").annotate(total=Count("id")).order_by("status"))

    estoque_baixo = list(
        Produto.objects.filter(organizacao=org, estoque__lte=5)
        .select_related("vendedor")
        .order_by("estoque", "nome")[:10]
    )

    return {
        "kpis": kpis,
        "ranking_produtos": ranking,
        "por_mes": por_mes,
        "por_status": por_status,
        "estoque_baixo": estoque_baixo,
    }

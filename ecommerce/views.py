import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .acesso import org_atual, papel_requerido
from .dashboard import atalhos, obter_metricas_dashboard
from .forms import CadastroForm, PeriodoForm, ProdutoForm, filtrar_periodo
from .models import Cupom, ItemPedido, Organizacao, Pedido, Produto


def _inteiro(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def home(request):
    q = request.GET.get("q", "").strip()
    loja = _inteiro(request.GET.get("loja"))
    prods = Produto.objects.filter(estoque__gt=0).select_related("organizacao")
    if loja:
        prods = prods.filter(organizacao_id=loja)
    if q:
        prods = prods.filter(nome__icontains=q)
    lojas = (
        Organizacao.objects.annotate(n=Count("produto", filter=Q(produto__estoque__gt=0)))
        .filter(n__gt=0)
        .order_by("nome")
    )
    org = org_atual(request)
    return render(request, "ecommerce/index.html", {
        "produtos": prods.order_by("organizacao__nome", "nome"),
        "lojas": lojas,
        "loja_id": loja,
        "q": q,
        "minha_org": org.id if org else None,
    })


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = CadastroForm(request.POST or None)
    prox = request.GET.get("next", "")
    if form.is_valid():
        login(request, form.save())
        ok = url_has_allowed_host_and_scheme(prox, {request.get_host()})
        return redirect(prox if ok else "home")
    return render(request, "ecommerce/conta.html", {"form": form, "modo": "cadastro", "next": prox})


@papel_requerido("admin", "operador")
def novo_produto(request):
    org = org_atual(request)
    form = ProdutoForm(request.POST or None, org=org)
    if form.is_valid():
        prod = form.save(commit=False)
        prod.organizacao = org
        prod.save()
        messages.success(request, "Produto cadastrado.")
        return redirect("home")
    return render(request, "ecommerce/produto_form.html", {"form": form, "titulo": "Novo produto"})


@papel_requerido("admin", "operador")
def editar_produto(request, pk):
    org = org_atual(request)
    prod = get_object_or_404(Produto, pk=pk, organizacao=org)
    form = ProdutoForm(request.POST or None, instance=prod, org=org)
    if form.is_valid():
        form.save()
        messages.success(request, "Produto atualizado.")
        return redirect("home")
    return render(request, "ecommerce/produto_form.html", {"form": form, "titulo": "Editar produto"})


def _itens(request):
    car = request.session.get("carrinho", {})
    prods = Produto.objects.filter(pk__in=list(car)).select_related("organizacao").order_by("nome")
    itens = []
    for p in prods:
        q = min(car[str(p.pk)], p.estoque)
        if q > 0:
            itens.append({"produto": p, "quantidade": q, "subtotal": p.preco * q})
    return itens


def _loja(itens):
    return itens[0]["produto"].organizacao if itens else None


def _cupom(request, org):
    cod = request.session.get("cupom_codigo")
    if not cod or org is None:
        return None
    cupom = Cupom.objects.filter(organizacao=org, codigo__iexact=cod, ativo=True).first()
    if cupom is None:
        request.session.pop("cupom_codigo", None)
    return cupom


def _totais(itens, cupom):
    sub = sum((i["subtotal"] for i in itens), Decimal("0.00"))
    desc = (sub * cupom.desconto_percentual / 100) if cupom else Decimal("0.00")
    return sub, desc, max(sub - desc, Decimal("0.00"))


def ver_carrinho(request):
    itens = _itens(request)
    loja = _loja(itens)
    cupom = _cupom(request, loja)
    sub, desc, total = _totais(itens, cupom)
    return render(request, "ecommerce/carrinho.html", {
        "itens": itens,
        "loja": loja,
        "subtotal_geral": sub,
        "desconto_aplicado": desc,
        "total_geral": total,
        "codigo_cupom": cupom.codigo if cupom else None,
    })


@require_POST
def adicionar_ao_carrinho(request, produto_id):
    prod = get_object_or_404(Produto, pk=produto_id, estoque__gt=0)
    loja = _loja(_itens(request))
    if loja and loja.id != prod.organizacao_id:
        messages.warning(request, f"Seu carrinho é da loja {loja.nome}. Esvazie-o para comprar de outra loja.")
        return redirect("ver_carrinho")
    car = request.session.setdefault("carrinho", {})
    k = str(prod.pk)
    if car.get(k, 0) < prod.estoque:
        car[k] = car.get(k, 0) + 1
        request.session.modified = True
    else:
        messages.info(request, "Você já adicionou todo o estoque disponível deste produto.")
    return redirect("ver_carrinho")


@require_POST
def remover_do_carrinho(request, produto_id):
    car = request.session.get("carrinho", {})
    k = str(produto_id)
    if k in car:
        car[k] -= 1
        if car[k] <= 0:
            del car[k]
        request.session.modified = True
    return redirect("ver_carrinho")


@require_POST
def esvaziar_carrinho(request):
    request.session["carrinho"] = {}
    request.session.pop("cupom_codigo", None)
    return redirect("ver_carrinho")


@require_POST
def aplicar_cupom(request):
    loja = _loja(_itens(request))
    cod = request.POST.get("codigo_cupom", "").strip()
    cupom = None
    if loja and cod:
        cupom = Cupom.objects.filter(organizacao=loja, codigo__iexact=cod, ativo=True).first()
    if cupom:
        request.session["cupom_codigo"] = cupom.codigo
        messages.success(request, f"Cupom {cupom.codigo} aplicado.")
    else:
        request.session.pop("cupom_codigo", None)
        messages.warning(request, "Cupom inválido para esta loja.")
    return redirect("ver_carrinho")


@login_required(login_url="login")
@require_POST
def finalizar_pedido(request):
    itens = _itens(request)
    if not itens:
        return redirect("home")
    loja = _loja(itens)
    cupom = _cupom(request, loja)
    try:
        with transaction.atomic():
            trava = Produto.objects.select_for_update().in_bulk([i["produto"].pk for i in itens])
            ped = Pedido.objects.create(organizacao=loja, cliente=request.user, cupom=cupom)
            for i in itens:
                ItemPedido.objects.create(
                    pedido=ped, produto=trava[i["produto"].pk], quantidade=i["quantidade"]
                )
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
        return redirect("ver_carrinho")
    request.session["carrinho"] = {}
    request.session.pop("cupom_codigo", None)
    return render(request, "ecommerce/sucesso.html", {"pedido": ped, "total_geral": ped.total, "loja": loja})


def _resolver_org_dashboard(request):
    perfil = getattr(request.user, "perfil", None)
    lojas = None
    if perfil:
        org = perfil.organizacao
    elif getattr(settings, "DASHBOARD_PUBLICO", True):
        lojas = Organizacao.objects.order_by("nome")
        org = lojas.filter(pk=_inteiro(request.GET.get("loja"))).first() or lojas.first()
        if org is None:
            raise Http404
    elif request.user.is_authenticated:
        raise PermissionDenied
    else:
        return None, None, None, redirect_to_login(request.get_full_path(), "login")
    return perfil, org, lojas, None


def dashboard_view(request):
    perfil, org, lojas, resp_login = _resolver_org_dashboard(request)
    if resp_login:
        return resp_login

    if request.method == "POST":
        if not perfil:
            raise PermissionDenied
        prod_id = _inteiro(request.POST.get("repor_produto_id"))
        qtd_repor = _inteiro(request.POST.get("qtd_repor")) or 10
        if prod_id and qtd_repor > 0:
            prod = get_object_or_404(Produto, pk=prod_id, organizacao=org)
            Produto.objects.filter(pk=prod.pk).update(estoque=F("estoque") + qtd_repor)
            messages.success(request, f"+{qtd_repor} un. adicionadas ao estoque de '{prod.nome}'.")
        qs_str = request.META.get("QUERY_STRING", "")
        destino = f"{request.path}?{qs_str}" if qs_str else request.path
        return redirect(destino)

    form = PeriodoForm(request.GET)
    form.is_valid()
    m = obter_metricas_dashboard(request, org)
    return render(request, "ecommerce/dashboard.html", {
        "organizacao": org,
        "lojas": lojas,
        "form_periodo": form,
        "atalhos": atalhos(),
        "equipe": bool(perfil),
        "mostra_series": perfil.eh_admin if perfil else True,
        "pode_exportar": bool(perfil and perfil.eh_admin),
        "dados_js": {"mes": m["por_mes"], "status": m["por_status"]},
        **m,
    })


def _celula(valor):
    t = str(valor)
    return "'" + t if t[:1] in ("=", "+", "-", "@") else t


@papel_requerido("admin")
def exportar_pedidos_csv(request):
    qs = filtrar_periodo(
        request,
        Pedido.objects.filter(organizacao=org_atual(request)).select_related("cliente", "cupom"),
    )
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="pedidos.csv"'
    resp.write("\ufeff")
    w = csv.writer(resp)
    w.writerow(["ID", "Cliente", "Status", "Cupom", "Total", "Criado em"])
    for p in qs.order_by("-criado_em"):
        w.writerow([
            p.id,
            _celula(p.cliente.username),
            p.status,
            p.cupom.codigo if p.cupom else "",
            p.total,
            p.criado_em.strftime("%d/%m/%Y %H:%M"),
        ])
    return resp
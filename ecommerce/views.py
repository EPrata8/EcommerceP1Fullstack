from django.shortcuts import get_object_or_404, redirect, render
from .models import ItemPedido, Organizacao, Pedido, Produto

def lista_produtos(request):
    produtos = Produto.objects.filter(estoque__gt=0)
    return render(request, "loja/lista_produtos.html", {"produtos": produtos})

def adicionar_ao_carrinho(request, produto_id):
    prod = get_object_or_404(Produto, id=produto_id)
    carrinho = request.session.get("carrinho", {})

    produto_id_str = str(produto_id)
    if produto_id_str in carrinho:
        carrinho[produto_id_str]["quantidade"] += 1
    else:
        carrinho[produto_id_str] = {
            "nome": prod.nome,
            "preco": float(prod.preco),
            "quantidade": 1,
        }

    request.session["carrinho"] = carrinho
    return redirect("ver_carrinho")

def ver_carrinho(request):
    carrinho = request.session.get("carrinho", {})
    total_geral = sum(
        item["preco"] * item["quantidade"] for item in carrinho.values()
    )
    return render(
        request,
        "loja/carrinho.html",
        {"carrinho": carrinho, "total_geral": total_geral},
    )

def finalizar_pedido(request):
    carrinho = request.session.get("carrinho", {})
    if not carrinho:
        return redirect("lista_produtos")

    if not request.user.is_authenticated:
        return redirect("/admin/login/?next=/carrinho/")

    org = Organizacao.objects.first()
    ped = Pedido.objects.create(organizacao=org, cliente=request.user)

    for prod_id, dados in carrinho.items():
        prod = get_object_or_404(Produto, id=int(prod_id))
        ItemPedido.objects.create(
            pedido=ped, produto=prod, quantidade=dados["quantidade"]
        )

    request.session["carrinho"] = {}
    return render(request, "loja/sucesso.html", {"pedido": ped})
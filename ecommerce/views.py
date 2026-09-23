from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Produto, Organizacao, Pedido, ItemPedido, Cupom

def home(produtos_view):
    query = produtos_view.GET.get('q', '')
    organizacao_id = produtos_view.GET.get('organizacao', '')
    
    produtos = Produto.objects.all()
    
    if query:
        produtos = produtos.filter(nome__icontains=query)
        
    if organizacao_id:
        produtos = produtos.filter(organizacao_id=organizacao_id)
        
    organizacoes = Organizacao.objects.all()
    
    context = {
        'produtos': produtos,
        'organizacoes': organizacoes,
    }
    return render(produtos_view, 'ecommerce/index.html', context)

def adicionar_ao_carrinho(produtos_view, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho = produtos_view.session.get('carrinho', {})
    
    if str(produto_id) in carrinho:
        carrinho[str(produto_id)] += 1
    else:
        carrinho[str(produto_id)] = 1
        
    produtos_view.session['carrinho'] = carrinho
    return redirect('home')

def ver_carrinho(produtos_view):
    carrinho = produtos_view.session.get('carrinho', {})
    itens = []
    total = 0
    
    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=produto_id)
        subtotal = produto.preco * quantidade
        total += subtotal
        itens.append({
            'produto': produto,
            'quantidade': quantidade,
            'subtotal': subtotal
        })
        
    context = {
        'itens': itens,
        'total': total,
    }
    return render(produtos_view, 'ecommerce/carrinho.html', context)

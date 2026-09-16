from django.shortcuts import get_object_or_404, redirect, render
from .models import ItemPedido, Pedido, Produto


def home(request):
  # Filtra produtos com estoque maior que zero
  produtos = Produto.objects.filter(estoque__gt=0)
  return render(request, 'ecommerce/index.html', {'produtos': produtos})


def adicionar_ao_carrinho(request, produto_id):
  produto = get_object_or_404(Produto, id=produto_id)

  if 'carrinho' not in request.session:
    request.session['carrinho'] = {}

  carrinho = request.session['carrinho']
  str_id = str(produto_id)

  if str_id in carrinho:
    carrinho[str_id]['quantidade'] += 1
  else:
    carrinho[str_id] = {
        'nome': produto.nome,
        'preco': float(produto.preco),
        'quantidade': 1,
    }

  request.session.modified = True
  return redirect('ver_carrinho')


def ver_carrinho(request):
  carrinho = request.session.get('carrinho', {})
  produtos_no_carrinho = []
  total_geral = 0

  for produto_id, item in carrinho.items():
    subtotal = item['preco'] * item['quantidade']
    total_geral += subtotal
    produtos_no_carrinho.append({
        'id': produto_id,
        'nome': item['nome'],
        'preco': item['preco'],
        'quantidade': item['quantidade'],
        'subtotal': subtotal,
    })

  context = {
      'itens': produtos_no_carrinho,
      'total_geral': total_geral,
  }
  return render(request, 'ecommerce/carrinho.html', context)


def finalizar_pedido(request):
  carrinho = request.session.get('carrinho', {})
  if not carrinho:
    return redirect('home')

  total_geral = sum(
      item['preco'] * item['quantidade'] for item in carrinho.values()
  )

  # Limpa o carrinho após finalizar a compra
  request.session['carrinho'] = {}
  request.session.modified = True

  return render(
      request, 'ecommerce/sucesso.html', {'total_geral': total_geral}
  )
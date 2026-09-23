from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from .models import Cupom, Organizacao, Produto


def home(request):
  termo_busca = request.GET.get('q', '')
  organizacao_id = request.GET.get('organizacao', '')

  produtos = Produto.objects.filter(estoque__gt=0)

  if termo_busca:
    produtos = produtos.filter(nome__icontains=termo_busca)

  if organizacao_id:
    produtos = produtos.filter(organizacao_id=organizacao_id)

  organizacoes = Organizacao.objects.all()

  context = {
      'produtos': produtos,
      'organizacoes': organizacoes,
      'termo_busca': termo_busca,
      'organizacao_selecionada': organizacao_id,
  }
  return render(request, 'ecommerce/index.html', context)


def adicionar_ao_carrinho(request, produto_id):
  produto = get_object_or_404(Produto, id=produto_id)

  if 'carrinho' not in request.session:
    request.session['carrinho'] = {}

  carrinho = request.session['carrinho']
  str_id = str(produto_id)

  if str_id in carrinho:
    if carrinho[str_id]['quantidade'] < produto.estoque:
      carrinho[str_id]['quantidade'] += 1
  else:
    if produto.estoque > 0:
      carrinho[str_id] = {
          'nome': produto.nome,
          'preco': float(produto.preco),
          'quantidade': 1,
          'organizacao_id': produto.organizacao.id,  # Salva a organização para o cupom correto
      }

  request.session.modified = True
  return redirect('ver_carrinho')


def remover_do_carrinho(request, produto_id):
  carrinho = request.session.get('carrinho', {})
  str_id = str(produto_id)

  if str_id in carrinho:
    if carrinho[str_id]['quantidade'] > 1:
      carrinho[str_id]['quantidade'] -= 1
    else:
      del carrinho[str_id]

  request.session.modified = True
  return redirect('ver_carrinho')


def ver_carrinho(request):
  carrinho = request.session.get('carrinho', {})
  produtos_no_carrinho = []
  subtotal_geral = Decimal('0.00')

  for produto_id, item in carrinho.items():
    sub_total = Decimal(str(item['preco'])) * item['quantidade']
    subtotal_geral += sub_total
    produtos_no_carrinho.append({
        'id': produto_id,
        'nome': item['nome'],
        'preco': item['preco'],
        'quantidade': item['quantidade'],
        'organizacao_id': item.get('organizacao_id'),
        'subtotal': float(sub_total),
    })

  desconto_aplicado = Decimal('0.00')
  codigo_cupom = request.session.get('cupom_codigo')

  if codigo_cupom:
    try:
      cupom = Cupom.objects.get(codigo__iexact=codigo_cupom, ativo=True)

      base_calculo_desconto = Decimal('0.00')
      for item in produtos_no_carrinho:
        if (
            item.get('organizacao_id')
            and item['organizacao_id'] == cupom.organizacao.id
        ):
          base_calculo_desconto += (
              Decimal(str(item['preco'])) * item['quantidade']
          )

      desconto_aplicado = (
          base_calculo_desconto * cupom.desconto_percentual
      ) / Decimal('100')

    except Cupom.DoesNotExist:
      del request.session['cupom_codigo']
      request.session.modified = True

  total_geral = max(Decimal('0.00'), subtotal_geral - desconto_aplicado)

  context = {
      'itens': produtos_no_carrinho,
      'subtotal_geral': float(subtotal_geral),
      'desconto_aplicado': float(desconto_aplicado),
      'total_geral': float(total_geral),
      'codigo_cupom': codigo_cupom,
  }
  return render(request, 'ecommerce/carrinho.html', context)


def aplicar_cupom(request):
  if request.method == 'POST':
    codigo = request.POST.get('codigo_cupom', '').strip()
    try:
      cupom = Cupom.objects.get(codigo__iexact=codigo, ativo=True)
      request.session['cupom_codigo'] = cupom.codigo
    except Cupom.DoesNotExist:
      if 'cupom_codigo' in request.session:
        del request.session['cupom_codigo']

    request.session.modified = True
  return redirect('ver_carrinho')


def finalizar_pedido(request):
  carrinho = request.session.get('carrinho', {})
  if not carrinho:
    return redirect('home')

  request.session['carrinho'] = {}
  if 'cupom_codigo' in request.session:
    del request.session['cupom_codigo']
  request.session.modified = True

  return render(request, 'ecommerce/sucesso.html')
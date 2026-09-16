#Mini E-commerce - P1

Aplicação Django de e-commerce multi-organização, com catálogo de produtos, carrinho de compras baseado em sessão, cupons de desconto e finalização de pedido.

#Funcionalidades

- Catálogo de produtos com controle de estoque
- Carrinho de compras (armazenado na sessão do usuário)
- Cálculo automático do total do pedido, com aplicação de cupom de desconto
- Finalização de pedido com limpeza do carrinho
- Painel administrativo do Django para gerenciar organizações, vendedores, produtos, cupons e pedidos

#Modelo de dados

- Organizacao - cada loja do sistema
- Vendedor - usuário vinculado a uma organização, dono de uma loja
- Produto - nome, descrição, preço e estoque, vinculado a uma organização e um vendedor
- Cupom - código com desconto
- Pedido - pedido de um cliente, com cupom opcional e total calculado automaticamente
- ItemPedido - item de um pedido; ao ser salvo, debita o estoque do produto e recalcula o total do pedido

#Stack

- Python + Django 4.2
- PostgreSQL 
- Bootstrap 5 
- Variáveis de ambiente via `python-dotenv`

#Estrutura do projeto

```
P1Fullstack/
├── configs/ # settings, urls, wsgi/asgi do projeto
├── ecommerce/ # app principal (models, views, urls, admin, templates)
│ └── templates/
│ ├── ecommerce/ # base, index, carrinho, sucesso
│ └── loja/ # lista_produtos (template auxiliar)
├── manage.py
├── requirements.txt
└── .env.example
```

## Como rodar

1. **Pré-requisitos**: Python 3.10+ e um servidor PostgreSQL rodando localmente

2. Crie a Venv
 ```bash
 python -m venv venv
 venv\Scripts\activate
 ```

3. Instale o requirements
 ```bash
 pip install -r requirements.txt
 ```

4. Configure o `.env`

 Copie `.env.example` para `.env` e preencha com os dados do seu banco:
 ```
 SECRET_KEY=
 DB_NAME=bancoecommerce
 DB_USER=postgres
 DB_PASSWORD=
 DB_HOST=localhost
 DB_PORT=5432
 ```

5. Rode as migrações
 ```bash
 python manage.py migrate
 ```

6. Crie um superusuário
 ```bash
 python manage.py createsuperuser
 ```

7. Inicie o servidor
 ```bash
 python manage.py runserver
 ```

 Acesse `http://127.0.0.1:8000/` para a loja e `http://127.0.0.1:8000/admin/` para o painel administrativo.

#Rotas principais

| Rota | Descrição |
|---|---|
| `/` | Página inicial com produtos em estoque |
| `/carrinho/adicionar/<produto_id>/` | Adiciona um produto ao carrinho |
| `/carrinho/` | Exibe o carrinho e o total geral |
| `/finalizar-pedido/` | Finaliza o pedido e limpa o carrinho |
| `/admin/` | Painel administrativo do Django |

#Observações

- O carrinho é armazenado na sessão do navegador - ele não persiste entre dispositivos e é limpo ao finalizar o pedido.
- O modelo `ItemPedido` debita o estoque automaticamente ao ser criado e recalcula o total do `Pedido` correspondente, aplicando o desconto do cupom quando houver um ativo.
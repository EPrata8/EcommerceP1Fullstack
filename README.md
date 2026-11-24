#Mini E-commerce - P2

Aplicação Django de e-commerce multi-organização, com catálogo de produtos, carrinho de compras baseado em sessão, cupons de desconto, finalização de pedido, perfis de acesso, dashboard de vendas e API REST.

#Funcionalidades

- Catálogo de produtos com controle de estoque, busca por nome e filtro por loja
- Carrinho de compras (armazenado na sessão do usuário), sempre de uma loja só
- Cálculo automático do total do pedido, com aplicação de cupom de desconto da loja
- Finalização de pedido com limpeza do carrinho e baixa de estoque
- Cadastro e login de clientes (usuário comum, sem perfil de equipe)
- Multi-organização: cada loja enxerga somente os próprios dados
- Perfis de acesso: administrador e operador, com permissões diferentes
- Dashboard com receita, pedidos, ticket médio, ranking de produtos, série por mês, pedidos por situação e estoque em alerta
- Filtro por período validado e exportação de pedidos em CSV
- API REST (DRF) de produtos e do dashboard, com validação e permissões
- Painel administrativo do Django para gerenciar organizações, perfis, vendedores, produtos, cupons e pedidos

#Modelo de dados

- Organizacao - cada loja do sistema
- Perfil - liga um usuário a uma organização e define o papel (administrador ou operador)
- Vendedor - usuário vinculado a uma organização, dono de uma loja
- Produto - nome, descrição, preço e estoque, vinculado a uma organização e um vendedor
- Cupom - código com desconto, único por organização
- Pedido - pedido de um cliente, com cupom opcional, status e total calculado automaticamente
- ItemPedido - item de um pedido; ao ser salvo, debita o estoque do produto e recalcula o total do pedido

Todo model de negócio herda de `DaOrganizacao`, uma base abstrata com a ForeignKey para a organização.

#Stack

- Python + Django 4.2
- Django REST Framework
- PostgreSQL 
- Bootstrap 5 
- Chart.js (arquivo local em `static`)
- Variáveis de ambiente via `python-dotenv`

#Estrutura do projeto

```
P1Fullstack/
├── configs/ # settings, urls, wsgi/asgi do projeto
├── ecommerce/ # app principal
│ ├── acesso.py # org_atual, papel_requerido e permissão da API
│ ├── dashboard.py # métricas calculadas pelo ORM
│ ├── api_views.py # views da API (DRF)
│ ├── api_urls.py # rotas da API
│ ├── serializers.py # serializers da API
│ ├── forms.py # formulários, período e login/cadastro
│ ├── views.py, urls.py, models.py, admin.py, tests.py
│ ├── static/ecommerce/
│ │ ├── css/ # tema.css
│ │ └── js/ # chart.umd.js, dashboard.js
│ └── templates/
│ ├── 403.html # acesso restrito
│ └── ecommerce/ # base, index, carrinho, sucesso, dashboard, conta, produto_form
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

 O `requirements.txt` precisa incluir o `djangorestframework`. Se faltar, rode `pip install djangorestframework` e `pip freeze > requirements.txt`.

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

8. Cadastre os dados iniciais pelo Django Admin

 Crie as organizações, os usuários, os perfis (organização e papel), os vendedores, os produtos e os cupons. Quem tem Perfil acessa as telas da equipe da loja.

#Rotas principais

| Rota | Quem acessa | Descrição |
|---|---|---|
| `/` | Todos | Página inicial com produtos em estoque (`?q=` busca, `?loja=` filtra) |
| `/entrar/`, `/cadastro/` | Todos | Login e criação de conta de cliente |
| `/carrinho/` | Todos | Exibe o carrinho e o total geral |
| `/carrinho/adicionar/<produto_id>/` | Todos (POST) | Adiciona um produto ao carrinho |
| `/carrinho/remover/<produto_id>/` | Todos (POST) | Remove uma unidade do carrinho |
| `/carrinho/cupom/` | Todos (POST) | Aplica um cupom da loja do carrinho |
| `/finalizar-pedido/` | Cliente logado (POST) | Finaliza o pedido e limpa o carrinho |
| `/dashboard/` | Todos (`?loja=` escolhe a loja) | Dashboard de vendas e estoque |
| `/dashboard/exportar-csv/` | Administrador | Exporta os pedidos em CSV |
| `/produtos/novo/` | Equipe | Cadastra um produto na própria organização |
| `/produtos/<id>/editar/` | Equipe | Edita um produto da própria organização |
| `/api/produtos/`, `/api/produtos/<id>/` | Equipe | CRUD de produtos em JSON |
| `/api/dashboard/` | Equipe | Métricas do dashboard em JSON |
| `/admin/` | Superusuário | Painel administrativo do Django |

#Perfis e permissões

| Recurso | Visitante | Cliente | Operador | Administrador |
|---|---|---|---|---|
| Loja, carrinho e cupom | Sim | Sim | Sim | Sim |
| Finalizar pedido | Não | Sim | Sim | Sim |
| Dashboard | Sim | Sim | Sim | Sim |
| Gráfico por mês | Sim | Sim | Não | Sim |
| Cadastrar e editar produtos | Não | Não | Sim | Sim |
| Exportar CSV | Não | Não | Não | Sim |
| API | Não | Não | Sim | Sim |

#Dashboard

As métricas seguem o que foi visto na Aula 17: `aggregate` para os totais, `values` + `annotate` + `order_by` para o ranking, `TruncMonth` para a série e contagem por status para a distribuição. Toda métrica parte do queryset filtrado pela organização e pelo período.

- Receita (sem pedidos cancelados), pedidos, ticket médio e clientes
- Produtos mais vendidos
- Pedidos por situação
- Receita e pedidos por mês
- Estoque em alerta (até 5 unidades)

#Testes

```bash
python manage.py test ecommerce
```

Roteiro de isolamento entre organizações, coberto por testes automatizados:

| Cenário | Resultado esperado | Resultado |
|---|---|---|
| Equipe da loja A abre a lista de produtos da API | Vê só os produtos da loja A | Passou |
| Equipe da loja A abre `/produtos/<id da B>/editar/` | 404 | Passou |
| Equipe da loja A cria um produto | Gravado com a organização A | Passou |
| Formulário de produto da loja A | Select de vendedor mostra só a loja A | Passou |
| Cupom com o mesmo código em duas lojas | Permitido (unicidade por organização) | Passou |
| Cupom da loja B no carrinho da loja A | Recusado | Passou |
| Dashboard e CSV da loja A | Só dados da loja A | Passou |

#Observações

- O carrinho é armazenado na sessão do navegador - ele não persiste entre dispositivos e é limpo ao finalizar o pedido. A sessão guarda só o id e a quantidade; os preços são lidos do banco.
- O carrinho aceita produtos de uma loja só por vez, e o cupom só vale para a loja do carrinho.
- O modelo `ItemPedido` debita o estoque automaticamente ao ser criado e recalcula o total do `Pedido` correspondente, aplicando o desconto do cupom quando houver um ativo. A finalização trava as linhas dos produtos para não vender estoque duas vezes.
- O dashboard está aberto ao público para apresentação, com seletor de loja. Para exigir login da equipe, coloque `DASHBOARD_PUBLICO = False` no `settings.py`.
- A equipe da loja sempre enxerga só a própria organização, mesmo que tente trocar a loja pela URL.
- O Chart.js fica em `ecommerce/static/ecommerce/js`, então o dashboard funciona sem CDN.

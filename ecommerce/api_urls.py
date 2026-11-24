from django.urls import path
from .api_views import DashboardApiView, ProdutoDetailAPIView, ProdutoListCreateAPIView

urlpatterns = [
    path("produtos/", ProdutoListCreateAPIView.as_view(), name="api-produto-list-create"),
    path("produtos/<int:pk>/", ProdutoDetailAPIView.as_view(), name="api-produto-detail"),
    path("dashboard/", DashboardApiView.as_view(), name="api-dashboard"),
]

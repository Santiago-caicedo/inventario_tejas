from django.urls import path

from . import views

urlpatterns = [
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/', views.cliente_detalle, name='cliente_detalle'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('pedidos/', views.pedidos_lista, name='pedidos_lista'),
    path('pedidos/nuevo/', views.pedido_crear, name='pedido_crear'),
    path('pedidos/<int:pk>/', views.pedido_detalle, name='pedido_detalle'),
    path('pedidos/<int:pk>/editar/', views.pedido_editar, name='pedido_editar'),
    path('pedidos/<int:pk>/estado/<str:estado>/', views.pedido_cambiar_estado, name='pedido_cambiar_estado'),
]

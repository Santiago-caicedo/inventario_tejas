from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('productos/', views.productos_lista, name='productos_lista'),
    path('productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/', views.producto_detalle, name='producto_detalle'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('categorias/nueva/', views.categoria_crear, name='categoria_crear'),
    path('movimientos/', views.movimientos_lista, name='movimientos_lista'),
    path('movimientos/nuevo/', views.movimiento_crear, name='movimiento_crear'),
]

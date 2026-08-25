from django.contrib import admin

from .models import Categoria, Movimiento, Producto

admin.site.site_header = 'Terracogua Arcillas'
admin.site.site_title = 'Terracogua'
admin.site.index_title = 'Administración'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['sku', 'nombre', 'categoria', 'unidad', 'precio', 'stock', 'stock_minimo', 'activo']
    list_filter = ['categoria', 'activo', 'unidad']
    search_fields = ['sku', 'nombre']


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'tipo', 'producto', 'cantidad', 'pedido', 'usuario', 'nota']
    list_filter = ['tipo']
    search_fields = ['producto__nombre', 'producto__sku', 'nota']
    date_hierarchy = 'fecha'

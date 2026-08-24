from django.contrib import admin

from .models import Cliente, ItemPedido, Pedido


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'telefono', 'ciudad']
    search_fields = ['nombre', 'nit']


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'estado', 'fecha_entrega', 'creado']
    list_filter = ['estado']
    search_fields = ['numero', 'cliente__nombre']
    inlines = [ItemPedidoInline]

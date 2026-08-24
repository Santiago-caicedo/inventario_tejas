"""Reglas de negocio del inventario: todo cambio de stock pasa por aquí."""

from django.db import transaction
from django.db.models import F

from .models import Movimiento, Producto


class StockInsuficiente(Exception):
    def __init__(self, producto, solicitado):
        self.producto = producto
        self.solicitado = solicitado
        super().__init__(
            f'Stock insuficiente de {producto.nombre}: hay {producto.stock}, se pidieron {solicitado}.'
        )


@transaction.atomic
def registrar_movimiento(*, producto, tipo, cantidad, usuario, nota='', pedido=None):
    """Crea un movimiento y actualiza el stock del producto de forma atómica.

    Para ENTRADA y SALIDA `cantidad` es positiva; para AJUSTE puede ser
    negativa (corrección hacia abajo) o positiva (hacia arriba).
    """
    producto = Producto.objects.select_for_update().get(pk=producto.pk)

    if tipo == Movimiento.Tipo.SALIDA:
        if cantidad > producto.stock:
            raise StockInsuficiente(producto, cantidad)
        delta = -cantidad
    elif tipo == Movimiento.Tipo.ENTRADA:
        delta = cantidad
    else:  # AJUSTE
        if producto.stock + cantidad < 0:
            raise StockInsuficiente(producto, abs(cantidad))
        delta = cantidad

    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=tipo,
        cantidad=cantidad,
        nota=nota,
        pedido=pedido,
        usuario=usuario,
    )
    Producto.objects.filter(pk=producto.pk).update(stock=F('stock') + delta)
    return movimiento

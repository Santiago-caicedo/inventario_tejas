"""Transiciones de estado de un pedido y su efecto sobre el inventario."""

from django.db import transaction

from inventario.models import Movimiento
from inventario.services import StockInsuficiente, registrar_movimiento

from .models import Pedido


class TransicionInvalida(Exception):
    pass


@transaction.atomic
def cambiar_estado(pedido, nuevo_estado, usuario):
    """Aplica una transición del flujo del pedido.

    - Al CONFIRMAR se descuenta el stock (una salida por ítem).
    - Al CANCELAR un pedido que ya había descontado stock, se devuelve.
    Lanza StockInsuficiente si no alcanza el inventario al confirmar.
    """
    if not pedido.puede_pasar_a(nuevo_estado):
        raise TransicionInvalida(
            f'Un pedido {pedido.get_estado_display().lower()} no puede pasar a ese estado.'
        )

    descontado = pedido.estado in (Pedido.Estado.CONFIRMADO, Pedido.Estado.DESPACHADO)

    if nuevo_estado == Pedido.Estado.CONFIRMADO:
        for item in pedido.items.select_related('producto'):
            registrar_movimiento(
                producto=item.producto,
                tipo=Movimiento.Tipo.SALIDA,
                cantidad=item.cantidad,
                usuario=usuario,
                nota=f'Pedido {pedido.numero}',
                pedido=pedido,
            )
    elif nuevo_estado == Pedido.Estado.CANCELADO and descontado:
        for item in pedido.items.select_related('producto'):
            registrar_movimiento(
                producto=item.producto,
                tipo=Movimiento.Tipo.ENTRADA,
                cantidad=item.cantidad,
                usuario=usuario,
                nota=f'Devolución por cancelación de {pedido.numero}',
                pedido=pedido,
            )

    pedido.estado = nuevo_estado
    pedido.save(update_fields=['estado', 'actualizado'])
    return pedido

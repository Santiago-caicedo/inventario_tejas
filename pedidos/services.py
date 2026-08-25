"""Transiciones de estado de un pedido y su efecto sobre el inventario."""

from django.db import transaction

from inventario.models import Movimiento
from inventario.services import StockInsuficiente, registrar_movimiento

from .models import Pedido


class TransicionInvalida(Exception):
    pass


def stock_descontado(pedido):
    """¿El pedido ya tiene salidas registradas contra el inventario?

    Se consulta el rastro de movimientos en vez del estado. Con la regla
    anterior el descuento ocurría al confirmar, así que un pedido viejo puede
    estar CONFIRMADO y con el stock ya descontado; mirando los movimientos no
    se descuenta ni se devuelve dos veces.
    """
    return pedido.movimientos.filter(tipo=Movimiento.Tipo.SALIDA).exists()


@transaction.atomic
def cambiar_estado(pedido, nuevo_estado, usuario):
    """Aplica una transición del flujo del pedido.

    - Al DESPACHAR se descuenta el stock (una salida por ítem): la mercancía
      sale del patio cuando sale el camión, no al confirmar.
    - Al CANCELAR un pedido que ya había descontado stock, se devuelve.
    Lanza StockInsuficiente si no alcanza el inventario al despachar.
    """
    if not pedido.puede_pasar_a(nuevo_estado):
        raise TransicionInvalida(
            f'Un pedido {pedido.get_estado_display().lower()} no puede pasar a ese estado.'
        )

    descontado = stock_descontado(pedido)

    if nuevo_estado == Pedido.Estado.DESPACHADO and not descontado:
        for item in pedido.items.select_related('producto'):
            registrar_movimiento(
                producto=item.producto,
                tipo=Movimiento.Tipo.SALIDA,
                cantidad=item.cantidad,
                usuario=usuario,
                nota=f'Despacho del pedido {pedido.numero}',
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

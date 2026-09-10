"""Roles de acceso: quién puede entrar a cada parte del sistema.

El sistema tiene dos áreas de trabajo y un rol por área:

- **Inventario**: productos, categorías y movimientos de stock.
- **Pedidos**: clientes y pedidos, con su flujo de estados.

Cada área se abre con un permiso propio (`gestionar_inventario`,
`gestionar_pedidos`) y no con los permisos de modelo. La razón: quien monta
pedidos necesita *ver* los productos para armar el pedido, pero eso no debe
abrirle la sección de inventario. Con un permiso por área las dos cosas no se
confunden.

Los roles son grupos de Django. Se definen aquí y se sincronizan solos en cada
`migrate` (ver `cuentas/apps.py`), así que **el código manda**: editar los
permisos del grupo a mano en Administración se pierde en el siguiente despliegue.
Para darle algo extra a una sola persona, usar sus permisos de usuario.

Un superusuario pasa todos los controles sin pertenecer a ningún grupo.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

GESTIONAR_INVENTARIO = 'inventario.gestionar_inventario'
GESTIONAR_PEDIDOS = 'pedidos.gestionar_pedidos'

INVENTARIO = 'Inventario'
PEDIDOS = 'Pedidos'

# Permisos de cada rol, en formato `app.codename`.
#
# Nadie puede borrar: un producto o un cliente con historia se desactiva o se
# deja quieto, no se elimina. Los movimientos además no se editan — son el
# rastro contable del stock y tienen que poder leerse igual dentro de un año.
ROLES = {
    INVENTARIO: (
        GESTIONAR_INVENTARIO,
        'inventario.view_categoria',
        'inventario.add_categoria',
        'inventario.change_categoria',
        'inventario.view_producto',
        'inventario.add_producto',
        'inventario.change_producto',
        'inventario.view_movimiento',
        'inventario.add_movimiento',
    ),
    PEDIDOS: (
        GESTIONAR_PEDIDOS,
        'pedidos.view_cliente',
        'pedidos.add_cliente',
        'pedidos.change_cliente',
        'pedidos.view_pedido',
        'pedidos.add_pedido',
        'pedidos.change_pedido',
        'pedidos.view_itempedido',
        'pedidos.add_itempedido',
        'pedidos.change_itempedido',
        'pedidos.delete_itempedido',
        # Para elegir el producto y su precio al armar el pedido. No abre la
        # sección de inventario: eso lo controla `gestionar_inventario`.
        'inventario.view_producto',
    ),
}

SIN_PERMISO = 'Tu usuario no tiene acceso a esa sección.'


def sincronizar_roles():
    """Crea los grupos y les deja exactamente los permisos declarados arriba.

    Es idempotente: se puede correr las veces que haga falta. Devuelve la lista
    de permisos que no existen en la base (señal de que falta una migración).
    """
    from django.contrib.auth.models import Group, Permission

    faltantes = []
    for nombre, codigos in ROLES.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        permisos = []
        for codigo in codigos:
            app_label, codename = codigo.split('.', 1)
            permiso = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            if permiso is None:
                faltantes.append(codigo)
            else:
                permisos.append(permiso)
        grupo.permissions.set(permisos)
    return faltantes


def requiere(permiso):
    """Decorador de vista: exige un permiso y, si falta, vuelve al tablero.

    A un anónimo lo manda al login (por `login_required`); a alguien con sesión
    pero sin el permiso se le explica por qué no entró, en vez de darle un 403
    que en esta aplicación no significa nada para el usuario.
    """

    def decorador(vista):
        @login_required
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.has_perm(permiso):
                messages.error(request, SIN_PERMISO)
                return redirect('dashboard')
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


requiere_inventario = requiere(GESTIONAR_INVENTARIO)
requiere_pedidos = requiere(GESTIONAR_PEDIDOS)

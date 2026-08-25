from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from inventario.models import Producto
from inventario.services import StockInsuficiente

from .forms import ClienteForm, ItemPedidoFormSet, PedidoForm
from .models import Cliente, Pedido
from .services import TransicionInvalida, cambiar_estado, stock_descontado


# ----- Clientes -----

@login_required
def clientes_lista(request):
    clientes = Cliente.objects.all()
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) | Q(nit__icontains=busqueda) | Q(ciudad__icontains=busqueda)
        )
    pagina = Paginator(clientes, 15).get_page(request.GET.get('pagina'))
    return render(request, 'pedidos/clientes_lista.html', {
        'seccion': 'clientes', 'pagina': pagina, 'busqueda': busqueda,
    })


@login_required
def cliente_crear(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save()
        messages.success(request, f'Cliente {cliente.nombre} creado.')
        return redirect('cliente_detalle', pk=cliente.pk)
    return render(request, 'pedidos/cliente_form.html', {
        'seccion': 'clientes', 'form': form, 'titulo': 'Nuevo cliente',
    })


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Cliente {cliente.nombre} actualizado.')
        return redirect('cliente_detalle', pk=cliente.pk)
    return render(request, 'pedidos/cliente_form.html', {
        'seccion': 'clientes', 'form': form, 'titulo': f'Editar cliente', 'cliente': cliente,
    })


@login_required
def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    pedidos = cliente.pedidos.prefetch_related('items')[:20]
    return render(request, 'pedidos/cliente_detalle.html', {
        'seccion': 'clientes', 'cliente': cliente, 'pedidos': pedidos,
    })


# ----- Pedidos -----

@login_required
def pedidos_lista(request):
    pedidos = Pedido.objects.select_related('cliente').prefetch_related('items')
    estado = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '').strip()
    if estado in Pedido.Estado.values:
        pedidos = pedidos.filter(estado=estado)
    if busqueda:
        pedidos = pedidos.filter(
            Q(numero__icontains=busqueda) | Q(cliente__nombre__icontains=busqueda)
        )
    pagina = Paginator(pedidos, 15).get_page(request.GET.get('pagina'))
    return render(request, 'pedidos/pedidos_lista.html', {
        'seccion': 'pedidos', 'pagina': pagina, 'estado': estado,
        'busqueda': busqueda, 'estados': Pedido.Estado.choices,
    })


def _precios_productos():
    """Mapa id → precio para autocompletar el precio al elegir producto."""
    return {
        str(p.pk): {'precio': str(p.precio), 'stock': p.stock}
        for p in Producto.objects.filter(activo=True)
    }


@login_required
def pedido_crear(request):
    pedido = Pedido(usuario=request.user)
    form = PedidoForm(request.POST or None, instance=pedido)
    formset = ItemPedidoFormSet(request.POST or None, instance=pedido)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, f'Pedido {pedido.numero} creado. El stock se descuenta cuando lo despaches.')
        return redirect('pedido_detalle', pk=pedido.pk)
    return render(request, 'pedidos/pedido_form.html', {
        'seccion': 'pedidos', 'form': form, 'formset': formset,
        'titulo': 'Nuevo pedido', 'precios': _precios_productos(),
    })


@login_required
def pedido_editar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if not pedido.editable:
        messages.error(request, 'Solo se pueden editar pedidos pendientes.')
        return redirect('pedido_detalle', pk=pedido.pk)
    form = PedidoForm(request.POST or None, instance=pedido)
    formset = ItemPedidoFormSet(request.POST or None, instance=pedido)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, f'Pedido {pedido.numero} actualizado.')
        return redirect('pedido_detalle', pk=pedido.pk)
    return render(request, 'pedidos/pedido_form.html', {
        'seccion': 'pedidos', 'form': form, 'formset': formset,
        'titulo': f'Editar {pedido.numero}', 'pedido': pedido,
        'precios': _precios_productos(),
    })


@login_required
def pedido_detalle(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente', 'usuario').prefetch_related('items__producto'),
        pk=pk,
    )
    descontado = stock_descontado(pedido)
    acciones = {
        Pedido.Estado.CONFIRMADO: (
            'Confirmar pedido',
            'Aparta el pedido. El stock se descuenta al despacharlo.',
        ),
        Pedido.Estado.DESPACHADO: (
            'Marcar despachado',
            '' if descontado else 'Descuenta el stock del patio.',
        ),
        Pedido.Estado.ENTREGADO: ('Marcar entregado', ''),
        Pedido.Estado.CANCELADO: (
            'Cancelar pedido',
            'El stock vuelve al patio.' if descontado else 'Todavía no se ha movido stock.',
        ),
    }
    disponibles = [
        (estado, acciones[estado][0], acciones[estado][1])
        for estado in pedido.FLUJO[pedido.estado]
    ]
    return render(request, 'pedidos/pedido_detalle.html', {
        'seccion': 'pedidos', 'pedido': pedido, 'acciones': disponibles,
        'descontado': descontado,
    })


@login_required
@require_POST
def pedido_cambiar_estado(request, pk, estado):
    pedido = get_object_or_404(Pedido, pk=pk)
    if estado not in Pedido.Estado.values:
        messages.error(request, 'Estado no válido.')
        return redirect('pedido_detalle', pk=pedido.pk)
    try:
        cambiar_estado(pedido, estado, request.user)
    except StockInsuficiente as error:
        messages.error(request, str(error))
    except TransicionInvalida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f'{pedido.numero} ahora está {pedido.get_estado_display().lower()}.')
    return redirect('pedido_detalle', pk=pedido.pk)

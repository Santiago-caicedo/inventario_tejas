from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from pedidos.models import Pedido

from .forms import CategoriaForm, MovimientoForm, ProductoForm
from .models import Categoria, Movimiento, Producto
from .services import StockInsuficiente, registrar_movimiento


@login_required
def dashboard(request):
    productos = Producto.objects.filter(activo=True)
    valor_total = productos.aggregate(v=Sum(F('precio') * F('stock')))['v'] or 0
    stock_bajo = productos.filter(stock__lte=F('stock_minimo')).order_by(
        F('stock') - F('stock_minimo')
    )
    pendientes = Pedido.objects.filter(estado=Pedido.Estado.PENDIENTE).count()
    en_proceso = Pedido.objects.filter(
        estado__in=[Pedido.Estado.CONFIRMADO, Pedido.Estado.DESPACHADO]
    ).count()

    contexto = {
        'seccion': 'dashboard',
        'total_productos': productos.count(),
        'valor_total': valor_total,
        'unidades_totales': productos.aggregate(u=Sum('stock'))['u'] or 0,
        'stock_bajo': stock_bajo[:6],
        'stock_bajo_total': stock_bajo.count(),
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'movimientos': Movimiento.objects.select_related('producto', 'usuario')[:8],
        'ultimos_pedidos': Pedido.objects.select_related('cliente').prefetch_related('items')[:6],
    }
    return render(request, 'dashboard.html', contexto)


@login_required
def productos_lista(request):
    productos = Producto.objects.select_related('categoria')
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    filtro = request.GET.get('filtro', '')

    if busqueda:
        productos = productos.filter(Q(nombre__icontains=busqueda) | Q(sku__icontains=busqueda))
    if categoria_id.isdigit():
        productos = productos.filter(categoria_id=categoria_id)
    if filtro == 'bajo':
        productos = productos.filter(stock__lte=F('stock_minimo'), activo=True)
    elif filtro == 'inactivos':
        productos = productos.filter(activo=False)
    else:
        productos = productos.filter(activo=True)

    pagina = Paginator(productos, 15).get_page(request.GET.get('pagina'))
    return render(request, 'inventario/productos_lista.html', {
        'seccion': 'productos',
        'pagina': pagina,
        'categorias': Categoria.objects.all(),
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'filtro': filtro,
    })


@login_required
def producto_crear(request):
    form = ProductoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        messages.success(request, f'Producto {producto.nombre} creado. Registra una entrada para darle stock.')
        return redirect('producto_detalle', pk=producto.pk)
    return render(request, 'inventario/producto_form.html', {
        'seccion': 'productos', 'form': form, 'titulo': 'Nuevo producto',
    })


@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Producto {producto.nombre} actualizado.')
        return redirect('producto_detalle', pk=producto.pk)
    return render(request, 'inventario/producto_form.html', {
        'seccion': 'productos', 'form': form, 'titulo': f'Editar {producto.sku}', 'producto': producto,
    })


@login_required
def producto_detalle(request, pk):
    producto = get_object_or_404(Producto.objects.select_related('categoria'), pk=pk)
    movimientos = producto.movimientos.select_related('usuario', 'pedido')[:20]
    return render(request, 'inventario/producto_detalle.html', {
        'seccion': 'productos', 'producto': producto, 'movimientos': movimientos,
    })


@login_required
def categoria_crear(request):
    form = CategoriaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoría creada.')
        return redirect('productos_lista')
    return render(request, 'inventario/categoria_form.html', {
        'seccion': 'productos', 'form': form,
    })


@login_required
def movimientos_lista(request):
    movimientos = Movimiento.objects.select_related('producto', 'usuario', 'pedido')
    tipo = request.GET.get('tipo', '')
    if tipo in Movimiento.Tipo.values:
        movimientos = movimientos.filter(tipo=tipo)
    pagina = Paginator(movimientos, 20).get_page(request.GET.get('pagina'))
    return render(request, 'inventario/movimientos_lista.html', {
        'seccion': 'movimientos', 'pagina': pagina, 'tipo': tipo,
        'tipos': Movimiento.Tipo.choices,
    })


@login_required
def movimiento_crear(request):
    inicial = {}
    producto_id = request.GET.get('producto')
    if producto_id and producto_id.isdigit():
        inicial['producto'] = producto_id
    if request.GET.get('tipo') in Movimiento.Tipo.values:
        inicial['tipo'] = request.GET['tipo']

    form = MovimientoForm(request.POST or None, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        datos = form.cleaned_data
        try:
            registrar_movimiento(
                producto=datos['producto'],
                tipo=datos['tipo'],
                cantidad=datos['cantidad'],
                nota=datos['nota'],
                usuario=request.user,
            )
        except StockInsuficiente as error:
            form.add_error('cantidad', str(error))
        else:
            messages.success(request, 'Movimiento registrado y stock actualizado.')
            return redirect('movimientos_lista')
    return render(request, 'inventario/movimiento_form.html', {
        'seccion': 'movimientos', 'form': form,
    })

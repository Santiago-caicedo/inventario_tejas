from django.conf import settings
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField('nombre', max_length=80, unique=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    class Unidad(models.TextChoices):
        UNIDAD = 'UN', 'Unidad'
        MILLAR = 'MI', 'Millar'
        PALETA = 'PA', 'Estiba'
        M2 = 'M2', 'Metro cuadrado'

    sku = models.CharField('referencia', max_length=20, unique=True)
    nombre = models.CharField('nombre', max_length=120)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos', verbose_name='categoría'
    )
    descripcion = models.TextField('descripción', blank=True)
    unidad = models.CharField('unidad de venta', max_length=2, choices=Unidad.choices, default=Unidad.UNIDAD)
    precio = models.DecimalField('precio unitario (COP)', max_digits=12, decimal_places=0, default=0)
    stock = models.IntegerField('stock actual', default=0)
    stock_minimo = models.PositiveIntegerField('stock mínimo', default=0)
    activo = models.BooleanField('activo', default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.sku} · {self.nombre}'

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        return self.precio * self.stock


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = 'ENT', 'Entrada'
        SALIDA = 'SAL', 'Salida'
        AJUSTE = 'AJU', 'Ajuste'

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    # Para entradas y salidas siempre es positiva; en ajustes puede ser negativa.
    cantidad = models.IntegerField('cantidad')
    nota = models.CharField('nota', max_length=200, blank=True)
    pedido = models.ForeignKey(
        'pedidos.Pedido', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos'
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} {self.cantidad} — {self.producto.sku}'

    @property
    def efecto(self):
        """Cambio neto que este movimiento aplicó sobre el stock."""
        if self.tipo == self.Tipo.SALIDA:
            return -self.cantidad
        return self.cantidad

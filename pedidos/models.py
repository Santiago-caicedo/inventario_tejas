from django.conf import settings
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField('nombre o razón social', max_length=120)
    nit = models.CharField('NIT / cédula', max_length=30, blank=True)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    email = models.EmailField('correo', blank=True)
    ciudad = models.CharField('ciudad', max_length=60, blank=True)
    direccion = models.CharField('dirección', max_length=160, blank=True)
    notas = models.TextField('notas', blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PEN', 'Pendiente'
        CONFIRMADO = 'CON', 'Confirmado'
        DESPACHADO = 'DES', 'Despachado'
        ENTREGADO = 'ENT', 'Entregado'
        CANCELADO = 'CAN', 'Cancelado'

    numero = models.CharField('número', max_length=12, unique=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_entrega = models.DateField('fecha de entrega', null=True, blank=True)
    direccion_entrega = models.CharField('dirección de entrega', max_length=160, blank=True)
    notas = models.TextField('notas', blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.numero:
            self.numero = f'PED-{self.pk:04d}'
            super().save(update_fields=['numero'])

    def __str__(self):
        return f'{self.numero} — {self.cliente}'

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), 0)

    @property
    def unidades(self):
        return sum((item.cantidad for item in self.items.all()), 0)

    # Transiciones permitidas desde cada estado.
    FLUJO = {
        Estado.PENDIENTE: [Estado.CONFIRMADO, Estado.CANCELADO],
        Estado.CONFIRMADO: [Estado.DESPACHADO, Estado.CANCELADO],
        Estado.DESPACHADO: [Estado.ENTREGADO, Estado.CANCELADO],
        Estado.ENTREGADO: [],
        Estado.CANCELADO: [],
    }

    def puede_pasar_a(self, estado):
        return estado in self.FLUJO[self.estado]

    @property
    def editable(self):
        return self.estado == self.Estado.PENDIENTE


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField('cantidad')
    precio = models.DecimalField('precio unitario', max_digits=12, decimal_places=0)

    class Meta:
        verbose_name = 'ítem'
        verbose_name_plural = 'ítems'

    def __str__(self):
        return f'{self.cantidad} × {self.producto.nombre}'

    @property
    def subtotal(self):
        return self.precio * self.cantidad

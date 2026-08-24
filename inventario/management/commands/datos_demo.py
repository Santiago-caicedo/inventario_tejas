"""Carga datos de ejemplo: categorías, productos, clientes y stock inicial.

Uso:  python manage.py datos_demo
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from inventario.models import Categoria, Movimiento, Producto
from inventario.services import registrar_movimiento
from pedidos.models import Cliente


PRODUCTOS = [
    # (sku, nombre, categoría, unidad, precio, stock inicial, stock mínimo)
    ('TEJ-COL-04', 'Teja colonial No. 4', 'Tejas', 'UN', 2800, 4200, 800),
    ('TEJ-COL-06', 'Teja colonial No. 6', 'Tejas', 'UN', 3400, 2650, 800),
    ('TEJ-ESP-08', 'Teja española No. 8', 'Tejas', 'UN', 4100, 1900, 600),
    ('TEJ-CUM-01', 'Caballete cumbrera', 'Tejas', 'UN', 5200, 640, 200),
    ('LAD-H10-01', 'Ladrillo estructural H-10', 'Ladrillos', 'UN', 1450, 18500, 5000),
    ('LAD-H15-01', 'Ladrillo estructural H-15', 'Ladrillos', 'UN', 1980, 9200, 3000),
    ('LAD-TOL-01', 'Ladrillo tolete común', 'Ladrillos', 'UN', 780, 26400, 8000),
    ('LAD-LIM-01', 'Ladrillo limpio a la vista', 'Ladrillos', 'UN', 1150, 3100, 4000),
    ('BLO-N4-01', 'Bloque No. 4', 'Bloques', 'UN', 1650, 7800, 2500),
    ('BLO-N5-01', 'Bloque No. 5', 'Bloques', 'UN', 1890, 5600, 2000),
    ('ADO-PAT-01', 'Adoquín de patio 20×10', 'Pisos', 'M2', 42000, 380, 120),
    ('ENC-CAS-01', 'Enchape castaño 24×6', 'Pisos', 'M2', 56000, 95, 100),
]

CLIENTES = [
    ('Ferretería El Constructor', '890.234.117-2', '317 442 8890', 'Bucaramanga', 'Cra 15 # 34-20'),
    ('Depósito San Rafael', '901.882.340-1', '315 660 1234', 'Girón', 'Km 4 vía Girón'),
    ('Constructora Altos del Cacique', '900.451.226-8', '607 685 2210', 'Bucaramanga', 'Cll 48 # 27-14 of. 502'),
    ('Obras y Acabados J.M.', '13.872.440-6', '300 218 7745', 'Floridablanca', 'Cra 8 # 12-33'),
    ('Depósito de Materiales La 45', '804.117.552-9', '318 904 5512', 'Piedecuesta', 'Cll 45 # 9-60'),
]


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para probar el sistema.'

    def handle(self, *args, **opciones):
        if Producto.objects.exists():
            self.stdout.write(self.style.WARNING('Ya hay productos; no se cargó nada.'))
            return

        usuario = User.objects.filter(is_superuser=True).first()

        for sku, nombre, cat, unidad, precio, stock, minimo in PRODUCTOS:
            categoria, _ = Categoria.objects.get_or_create(nombre=cat)
            producto = Producto.objects.create(
                sku=sku, nombre=nombre, categoria=categoria, unidad=unidad,
                precio=precio, stock_minimo=minimo,
            )
            registrar_movimiento(
                producto=producto, tipo=Movimiento.Tipo.ENTRADA, cantidad=stock,
                usuario=usuario, nota='Inventario inicial',
            )

        for nombre, nit, telefono, ciudad, direccion in CLIENTES:
            Cliente.objects.create(
                nombre=nombre, nit=nit, telefono=telefono, ciudad=ciudad, direccion=direccion,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {len(PRODUCTOS)} productos y {len(CLIENTES)} clientes de ejemplo.'
        ))

# Tejas Santa Ana S.A.S — Inventario y pedidos

Sistema web de gestión de inventario y pedidos para la planta, construido con Django.

## Qué hace

- **Tablero**: indicadores de la operación — valor del inventario, unidades en patio,
  pedidos pendientes y referencias con stock bajo.
- **Productos**: catálogo con referencia (SKU), categoría, unidad de venta, precio y
  stock mínimo. El stock nunca se edita a mano: siempre cambia con un movimiento,
  para dejar rastro de cada unidad.
- **Movimientos**: entradas (producción), salidas manuales y ajustes de conteo,
  con nota, usuario y fecha.
- **Clientes**: ferreterías, depósitos y constructoras con sus datos de contacto.
- **Pedidos**: flujo Pendiente → Confirmado → Despachado → Entregado (o Cancelado).
  Al **confirmar** se descuenta el stock automáticamente; al **cancelar** un pedido
  confirmado, el stock se devuelve. Si no hay inventario suficiente, el sistema
  no deja confirmar.

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abrir <http://127.0.0.1:8000> e iniciar sesión.

**Usuario inicial**: `admin` / `tejas2026` — cámbiala en Administración → Usuarios.

## Datos de ejemplo

El proyecto viene con productos y clientes de muestra. Para recargarlos en una
base vacía:

```bash
python manage.py datos_demo
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `config/` | Configuración del proyecto |
| `inventario/` | Productos, categorías y movimientos de stock |
| `pedidos/` | Clientes, pedidos y su flujo de estados |
| `templates/` | Plantillas HTML |
| `static/` | Estilos, logo e interacciones |

La regla de negocio central vive en `inventario/services.py`
(`registrar_movimiento`, único punto que toca el stock) y en
`pedidos/services.py` (`cambiar_estado`, transiciones del pedido).

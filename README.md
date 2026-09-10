# Terracogua Arcillas — Inventario y pedidos

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
  Confirmar solo aparta el pedido: el stock **se descuenta al despachar**, que es
  cuando la mercancía sale del patio. Al **cancelar** un pedido ya despachado el
  stock se devuelve; si se cancela antes, no hay nada que devolver. Si no hay
  inventario suficiente, el sistema no deja despachar.
  Cada pedido tiene una vista de remisión imprimible desde **Ver recibo**.

## Roles y accesos

Hay dos roles, uno por área de trabajo. Se crean solos al correr `migrate` y
están definidos en `cuentas/roles.py`:

| Rol | Entra a | No entra a |
|---|---|---|
| **Inventario** | Productos, categorías y movimientos | Clientes y pedidos |
| **Pedidos** | Clientes y pedidos, con su flujo de estados | Productos, categorías y movimientos |

Quien monta pedidos sí ve los productos y sus precios **dentro del formulario
del pedido** — los necesita para armarlo —, pero no puede abrir la sección de
inventario ni tocar el catálogo. Ninguno de los dos roles borra nada, y los
movimientos no se editan: son el rastro contable del stock.

El tablero lo ve todo el mundo, pero cada quien solo ve sus propios indicadores;
en el menú lateral no aparece lo que no se puede abrir. Un **superusuario** entra
a todo sin pertenecer a ningún rol.

Para asignarlos: Administración → Usuarios → *Grupos*, o desde la línea de
comandos:

```bash
python manage.py roles                              # ver el estado
python manage.py roles --asignar juan --rol inventario
python manage.py roles --quitar juan --rol pedidos
```

Los permisos de cada grupo se rehacen en cada `migrate` a partir del código, así
que editarlos a mano en Administración no sobrevive a un despliegue. Para darle
algo puntual a una sola persona, usar sus permisos de usuario.

## Cómo ejecutarlo

El proyecto usa **PostgreSQL** y lee su configuración de un archivo `.env`
que no se versiona.

1. Crear la base de datos en PostgreSQL (por ejemplo `db_inventario`).
2. Copiar la plantilla de variables y completarla con los datos reales:

   ```bash
   cp .env.example .env
   ```

3. Instalar dependencias y arrancar:

   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

Abrir <http://127.0.0.1:8000> e iniciar sesión.

### Variables del `.env`

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Clave criptográfica de Django |
| `DEBUG` | `True` en desarrollo, `False` en producción |
| `ALLOWED_HOSTS` | Dominios permitidos, separados por comas |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Credenciales de PostgreSQL |
| `DB_HOST`, `DB_PORT` | Dónde escucha PostgreSQL (`localhost`, `5432`) |

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
| `cuentas/` | Roles de acceso y quién entra a cada sección |
| `templates/` | Plantillas HTML |
| `static/` | Estilos, logo e interacciones |

Quién puede entrar a cada sección se decide en `cuentas/roles.py`.
La regla de negocio central vive en `inventario/services.py`
(`registrar_movimiento`, único punto que toca el stock) y en
`pedidos/services.py` (`cambiar_estado`, transiciones del pedido).

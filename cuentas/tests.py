"""Cada rol entra a lo suyo y solo a lo suyo."""

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from cuentas.roles import INVENTARIO, PEDIDOS, ROLES, sincronizar_roles
from inventario.models import Categoria, Producto
from pedidos.models import Cliente, Pedido

# Vistas de cada área, con el método con el que se piden.
VISTAS_INVENTARIO = [
    ('productos_lista', {}),
    ('producto_crear', {}),
    ('categorias_lista', {}),
    ('categoria_crear', {}),
    ('movimientos_lista', {}),
    ('movimiento_crear', {}),
]
VISTAS_PEDIDOS = [
    ('clientes_lista', {}),
    ('cliente_crear', {}),
    ('pedidos_lista', {}),
    ('pedido_crear', {}),
]


class RolesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sincronizar_roles()
        cls.categoria = Categoria.objects.create(nombre='Tejas')
        cls.producto = Producto.objects.create(
            sku='TEJ-01', nombre='Teja colonial', categoria=cls.categoria,
            precio=3000, stock=100,
        )
        cls.cliente = Cliente.objects.create(nombre='Ferretería El Constructor')
        cls.pedido = Pedido.objects.create(cliente=cls.cliente)

        cls.bodeguero = User.objects.create_user('bodeguero', password='clave-de-prueba')
        cls.bodeguero.groups.add(Group.objects.get(name=INVENTARIO))
        cls.vendedor = User.objects.create_user('vendedor', password='clave-de-prueba')
        cls.vendedor.groups.add(Group.objects.get(name=PEDIDOS))
        cls.sin_rol = User.objects.create_user('nuevo', password='clave-de-prueba')
        cls.jefe = User.objects.create_superuser('jefe', password='clave-de-prueba')

    def entrar(self, usuario):
        self.client.force_login(usuario)

    # --- los grupos ---

    def test_sincronizar_es_idempotente(self):
        sincronizar_roles()
        faltantes = sincronizar_roles()
        self.assertEqual(faltantes, [])
        for nombre, codigos in ROLES.items():
            self.assertEqual(Group.objects.get(name=nombre).permissions.count(), len(codigos))

    def test_sincronizar_devuelve_los_permisos_del_codigo(self):
        """Editar el grupo a mano no sobrevive: manda lo declarado en roles.py."""
        grupo = Group.objects.get(name=INVENTARIO)
        grupo.permissions.clear()
        sincronizar_roles()
        self.assertTrue(self.bodeguero.has_perm('inventario.gestionar_inventario'))

    def test_ningun_rol_puede_borrar(self):
        for nombre in ROLES:
            codenames = Group.objects.get(name=nombre).permissions.values_list('codename', flat=True)
            borrados = [c for c in codenames if c.startswith('delete_') and c != 'delete_itempedido']
            self.assertEqual(borrados, [], f'{nombre} puede borrar: {borrados}')

    def test_los_movimientos_no_se_editan(self):
        """El rastro del stock es contable: se agrega, no se corrige."""
        self.assertTrue(self.bodeguero.has_perm('inventario.add_movimiento'))
        self.assertFalse(self.bodeguero.has_perm('inventario.change_movimiento'))

    # --- inventario ---

    def test_inventario_entra_a_su_seccion(self):
        self.entrar(self.bodeguero)
        for nombre, kwargs in VISTAS_INVENTARIO:
            with self.subTest(vista=nombre):
                self.assertEqual(self.client.get(reverse(nombre, kwargs=kwargs)).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('producto_detalle', kwargs={'pk': self.producto.pk})).status_code, 200
        )

    def test_inventario_no_entra_a_pedidos(self):
        self.entrar(self.bodeguero)
        for nombre, kwargs in VISTAS_PEDIDOS:
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, kwargs=kwargs))
                self.assertRedirects(respuesta, reverse('dashboard'))

    def test_inventario_no_mueve_el_estado_de_un_pedido(self):
        """El permiso se revisa antes que nada: ni siquiera llega a buscar el pedido."""
        self.entrar(self.bodeguero)
        url = reverse('pedido_cambiar_estado', kwargs={'pk': self.pedido.pk, 'estado': 'CON'})
        self.assertRedirects(self.client.post(url), reverse('dashboard'))
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.PENDIENTE)

    # --- pedidos ---

    def test_pedidos_entra_a_su_seccion(self):
        self.entrar(self.vendedor)
        for nombre, kwargs in VISTAS_PEDIDOS:
            with self.subTest(vista=nombre):
                self.assertEqual(self.client.get(reverse(nombre, kwargs=kwargs)).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('pedido_detalle', kwargs={'pk': self.pedido.pk})).status_code, 200
        )

    def test_pedidos_no_entra_a_inventario(self):
        self.entrar(self.vendedor)
        for nombre, kwargs in VISTAS_INVENTARIO:
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre, kwargs=kwargs))
                self.assertRedirects(respuesta, reverse('dashboard'))
        self.assertRedirects(
            self.client.get(reverse('producto_detalle', kwargs={'pk': self.producto.pk})),
            reverse('dashboard'),
        )

    def test_pedidos_ve_los_productos_al_armar_el_pedido(self):
        """Ver productos dentro del formulario no es entrar a inventario."""
        self.entrar(self.vendedor)
        respuesta = self.client.get(reverse('pedido_crear'))
        self.assertContains(respuesta, self.producto.nombre)

    def test_pedidos_despacha_y_descuenta_stock(self):
        """El rol comercial mueve el flujo completo, incluido el stock."""
        self.pedido.items.create(producto=self.producto, cantidad=10, precio=3000)
        self.entrar(self.vendedor)
        for estado in (Pedido.Estado.CONFIRMADO, Pedido.Estado.DESPACHADO):
            self.client.post(
                reverse('pedido_cambiar_estado', kwargs={'pk': self.pedido.pk, 'estado': estado})
            )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 90)

    # --- tablero y menú ---

    def test_el_tablero_es_de_todos_pero_muestra_lo_de_cada_uno(self):
        self.entrar(self.bodeguero)
        tablero = self.client.get(reverse('dashboard'))
        self.assertContains(tablero, 'Últimos movimientos')
        self.assertNotContains(tablero, 'Pedidos recientes')

        self.entrar(self.vendedor)
        tablero = self.client.get(reverse('dashboard'))
        self.assertContains(tablero, 'Pedidos recientes')
        self.assertNotContains(tablero, 'Últimos movimientos')

    def test_el_administrador_lo_ve_todo(self):
        self.entrar(self.jefe)
        tablero = self.client.get(reverse('dashboard'))
        self.assertContains(tablero, 'Últimos movimientos')
        self.assertContains(tablero, 'Pedidos recientes')
        # Con los cuatro indicadores la fila va completa, sin la clase reducida.
        self.assertNotContains(tablero, 'kpis-parcial')

    def test_con_un_solo_rol_los_indicadores_no_se_estiran(self):
        self.entrar(self.vendedor)
        self.assertContains(self.client.get(reverse('dashboard')), 'kpis-parcial')

    def test_el_menu_no_ofrece_lo_que_no_se_puede_abrir(self):
        self.entrar(self.vendedor)
        menu = self.client.get(reverse('dashboard'))
        self.assertNotContains(menu, reverse('productos_lista'))
        self.assertContains(menu, reverse('pedidos_lista'))

    def test_usuario_sin_rol_no_ve_nada_y_se_le_explica(self):
        self.entrar(self.sin_rol)
        tablero = self.client.get(reverse('dashboard'))
        self.assertEqual(tablero.status_code, 200)
        self.assertContains(tablero, 'Sin rol asignado')

    # --- anónimos ---

    def test_sin_sesion_se_va_al_login(self):
        """A quien no ha entrado se le pide la clave, no se le manda al tablero."""
        for nombre, kwargs in VISTAS_INVENTARIO + VISTAS_PEDIDOS:
            with self.subTest(vista=nombre):
                url = reverse(nombre, kwargs=kwargs)
                self.assertRedirects(
                    self.client.get(url), f'{reverse("login")}?next={url}'
                )


class UsuariosDesdeElFrontTest(TestCase):
    """El superadministrador crea y edita las cuentas sin entrar a /admin/."""

    CLAVE = 'planta-2026-teja'

    @classmethod
    def setUpTestData(cls):
        sincronizar_roles()
        cls.jefe = User.objects.create_superuser('jefe', password=cls.CLAVE)
        cls.bodeguero = User.objects.create_user('bodeguero', password=cls.CLAVE)
        cls.bodeguero.groups.add(Group.objects.get(name=INVENTARIO))

    def datos(self, **cambios):
        base = {
            'username': 'jperez',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@ejemplo.com',
            'rol': 'pedidos',
            'contrasena': self.CLAVE,
            'contrasena2': self.CLAVE,
        }
        base.update(cambios)
        return base

    # --- quién entra a la pantalla ---

    def test_solo_el_administrador_abre_usuarios(self):
        self.client.force_login(self.bodeguero)
        for nombre in ('usuarios_lista', 'usuario_crear'):
            with self.subTest(vista=nombre):
                self.assertRedirects(self.client.get(reverse(nombre)), reverse('dashboard'))

        self.client.force_login(self.jefe)
        self.assertEqual(self.client.get(reverse('usuarios_lista')).status_code, 200)

    def test_un_operario_no_crea_usuarios_ni_por_POST(self):
        self.client.force_login(self.bodeguero)
        self.assertRedirects(
            self.client.post(reverse('usuario_crear'), self.datos()), reverse('dashboard')
        )
        self.assertFalse(User.objects.filter(username='jperez').exists())

    def test_el_menu_ofrece_usuarios_solo_al_administrador(self):
        self.client.force_login(self.jefe)
        self.assertContains(self.client.get(reverse('dashboard')), reverse('usuarios_lista'))
        self.client.force_login(self.bodeguero)
        self.assertNotContains(self.client.get(reverse('dashboard')), reverse('usuarios_lista'))

    # --- crear ---

    def test_crear_usuario_con_rol_y_que_pueda_entrar(self):
        self.client.force_login(self.jefe)
        respuesta = self.client.post(reverse('usuario_crear'), self.datos())
        self.assertRedirects(respuesta, reverse('usuarios_lista'))

        nuevo = User.objects.get(username='jperez')
        self.assertEqual(list(nuevo.groups.values_list('name', flat=True)), [PEDIDOS])
        self.assertTrue(nuevo.has_perm('pedidos.gestionar_pedidos'))
        self.assertFalse(nuevo.has_perm('inventario.gestionar_inventario'))
        self.assertFalse(nuevo.is_staff)
        self.assertTrue(self.client.login(username='jperez', password=self.CLAVE))

    def test_crear_administrador(self):
        self.client.force_login(self.jefe)
        self.client.post(reverse('usuario_crear'), self.datos(username='otro', rol='admin'))
        otro = User.objects.get(username='otro')
        self.assertTrue(otro.is_superuser)
        self.assertTrue(otro.is_staff)
        self.assertEqual(otro.groups.count(), 0)

    def test_crear_con_los_dos_roles(self):
        self.client.force_login(self.jefe)
        self.client.post(reverse('usuario_crear'), self.datos(username='todero', rol='ambos'))
        todero = User.objects.get(username='todero')
        self.assertTrue(todero.has_perm('inventario.gestionar_inventario'))
        self.assertTrue(todero.has_perm('pedidos.gestionar_pedidos'))

    def test_las_contrasenas_tienen_que_coincidir(self):
        self.client.force_login(self.jefe)
        respuesta = self.client.post(
            reverse('usuario_crear'), self.datos(contrasena2='otra-cosa-distinta')
        )
        self.assertContains(respuesta, 'no coinciden')
        self.assertFalse(User.objects.filter(username='jperez').exists())

    def test_una_contrasena_floja_se_rechaza(self):
        self.client.force_login(self.jefe)
        respuesta = self.client.post(
            reverse('usuario_crear'), self.datos(contrasena='12345', contrasena2='12345')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username='jperez').exists())

    # --- editar ---

    def test_cambiar_de_rol_no_deja_restos_del_anterior(self):
        self.client.force_login(self.jefe)
        url = reverse('usuario_editar', kwargs={'pk': self.bodeguero.pk})
        self.client.post(url, self.datos(
            username='bodeguero', rol='pedidos', contrasena='', contrasena2='', is_active='on',
        ))
        self.bodeguero.refresh_from_db()
        self.assertEqual(list(self.bodeguero.groups.values_list('name', flat=True)), [PEDIDOS])

    def test_editar_sin_contrasena_conserva_la_que_tenia(self):
        self.client.force_login(self.jefe)
        url = reverse('usuario_editar', kwargs={'pk': self.bodeguero.pk})
        self.client.post(url, self.datos(
            username='bodeguero', first_name='Ana', rol='inventario',
            contrasena='', contrasena2='', is_active='on',
        ))
        self.bodeguero.refresh_from_db()
        self.assertEqual(self.bodeguero.first_name, 'Ana')
        self.assertTrue(self.client.login(username='bodeguero', password=self.CLAVE))

    def test_desactivar_a_alguien_le_cierra_la_entrada(self):
        self.client.force_login(self.jefe)
        url = reverse('usuario_editar', kwargs={'pk': self.bodeguero.pk})
        self.client.post(url, self.datos(username='bodeguero', rol='inventario',
                                         contrasena='', contrasena2=''))
        self.bodeguero.refresh_from_db()
        self.assertFalse(self.bodeguero.is_active)
        self.assertFalse(self.client.login(username='bodeguero', password=self.CLAVE))

    # --- no cerrarse la puerta a uno mismo ---

    def test_no_puede_quitarse_su_propio_rol_de_administrador(self):
        self.client.force_login(self.jefe)
        url = reverse('usuario_editar', kwargs={'pk': self.jefe.pk})
        respuesta = self.client.post(url, self.datos(
            username='jefe', rol='pedidos', contrasena='', contrasena2='', is_active='on',
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.jefe.refresh_from_db()
        self.assertTrue(self.jefe.is_superuser)

    def test_no_puede_desactivarse_a_si_mismo(self):
        self.client.force_login(self.jefe)
        url = reverse('usuario_editar', kwargs={'pk': self.jefe.pk})
        respuesta = self.client.post(url, self.datos(
            username='jefe', rol='admin', contrasena='', contrasena2='',
        ))
        self.assertContains(respuesta, 'No puedes desactivar tu propio usuario')
        self.jefe.refresh_from_db()
        self.assertTrue(self.jefe.is_active)

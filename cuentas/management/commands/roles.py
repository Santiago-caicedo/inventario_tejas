"""Ver los roles del sistema y asignárselos a una persona.

    python manage.py roles                          # estado actual
    python manage.py roles --asignar juan --rol inventario
    python manage.py roles --quitar juan --rol pedidos

Lo mismo se puede hacer desde Administración → Usuarios → Grupos; este comando
existe para el servidor, donde entrar por el navegador es más lento.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from cuentas.roles import INVENTARIO, PEDIDOS, ROLES, sincronizar_roles

# Cómo se escribe cada rol en la línea de comandos.
ALIAS = {'inventario': INVENTARIO, 'pedidos': PEDIDOS}


class Command(BaseCommand):
    help = 'Sincroniza los roles del sistema y los asigna a los usuarios.'

    def add_arguments(self, parser):
        parser.add_argument('--asignar', metavar='USUARIO', help='Usuario al que se le da el rol.')
        parser.add_argument('--quitar', metavar='USUARIO', help='Usuario al que se le quita el rol.')
        parser.add_argument('--rol', choices=sorted(ALIAS), help='inventario o pedidos.')

    def handle(self, *args, **opciones):
        faltantes = sincronizar_roles()
        if faltantes:
            raise CommandError(
                'Faltan permisos en la base: {}. Corre primero «manage.py migrate».'
                .format(', '.join(faltantes))
            )

        usuario_asignar = opciones['asignar']
        usuario_quitar = opciones['quitar']
        rol = opciones['rol']

        if (usuario_asignar or usuario_quitar) and not rol:
            raise CommandError('Indica también el rol: --rol inventario | --rol pedidos')

        if usuario_asignar:
            self._mover(usuario_asignar, rol, agregar=True)
        if usuario_quitar:
            self._mover(usuario_quitar, rol, agregar=False)

        self._mostrar_estado()

    def _mover(self, username, alias, *, agregar):
        Usuario = get_user_model()
        try:
            usuario = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            raise CommandError(f'No existe el usuario «{username}».')

        grupo = Group.objects.get(name=ALIAS[alias])
        if agregar:
            usuario.groups.add(grupo)
            verbo = 'ahora tiene'
        else:
            usuario.groups.remove(grupo)
            verbo = 'ya no tiene'
        self.stdout.write(self.style.SUCCESS(f'{username} {verbo} el rol {grupo.name}.'))

        if usuario.is_superuser:
            self.stdout.write(self.style.WARNING(
                f'Ojo: {username} es superusuario, así que entra a todo sin importar el rol.'
            ))

    def _mostrar_estado(self):
        self.stdout.write('')
        for nombre in ROLES:
            grupo = Group.objects.get(name=nombre)
            personas = list(grupo.user_set.values_list('username', flat=True))
            self.stdout.write(self.style.MIGRATE_HEADING(f'{nombre}'))
            self.stdout.write(f'  permisos: {grupo.permissions.count()}')
            self.stdout.write(f'  usuarios: {", ".join(personas) if personas else "(ninguno)"}')

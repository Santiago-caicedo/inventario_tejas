from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_migrate


def _sincronizar(sender, **kwargs):
    from .roles import sincronizar_roles

    sincronizar_roles()


class CuentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuentas'
    verbose_name = 'Cuentas y roles'

    def ready(self):
        # Los grupos se rehacen en cada `migrate`, para que un despliegue no
        # dependa de que alguien se acuerde de correr un comando aparte.
        # `cuentas` va de última en INSTALLED_APPS: así, cuando llega esta
        # señal, django.contrib.auth ya creó los permisos de inventario y
        # pedidos y hay algo que asignarle a los grupos.
        post_migrate.connect(_sincronizar, sender=self)

        # Marca a qué hora entró cada quien, para el tope de duración.
        from .sesiones import marcar_inicio

        user_logged_in.connect(marcar_inicio, dispatch_uid='cuentas.marcar_inicio')

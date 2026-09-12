"""Cierre automático de la sesión: por inactividad y por tiempo máximo.

Django sabe caducar la cookie de sesión, pero no distingue «lleva media hora
sin tocar nada» de «lleva doce horas adentro». En la planta importan las dos:
el computador del patio queda encendido y a la vista de cualquiera, y una
sesión abierta desde ayer no debería seguir sirviendo hoy.

Los dos plazos se configuran en el `.env` (ver `config/settings.py`) y
cualquiera de los dos se apaga poniéndolo en 0.
"""

import time

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

# Marcas de tiempo que se guardan en la sesión.
INICIO = 'sesion_inicio'
VISTO = 'sesion_visto'

# Por qué se cerró, para poder explicárselo en la pantalla de ingreso.
POR_INACTIVIDAD = 'inactividad'
POR_LIMITE = 'limite'


def marcar_inicio(sender, request, user, **kwargs):
    """Arranca el reloj del tiempo máximo al iniciar sesión.

    Va enganchado a `user_logged_in` (ver `cuentas/apps.py`) y no al middleware
    porque `login()` conserva los datos de la sesión anterior: si el inicio se
    dedujera de lo que ya había, una sesión vieja le heredaría el reloj a la
    nueva.
    """
    ahora = time.time()
    request.session[INICIO] = ahora
    request.session[VISTO] = ahora


class CierreDeSesion:
    """Cierra la sesión vencida antes de que la petición llegue a la vista."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        if usuario is not None and usuario.is_authenticated:
            motivo = self.vencida(request.session)
            if motivo:
                logout(request)
                return redirect(f'{reverse("login")}?cerrada={motivo}')
            request.session[VISTO] = time.time()
        return self.get_response(request)

    @staticmethod
    def vencida(sesion):
        """Motivo por el que la sesión ya no vale, o None si sigue viva."""
        ahora = time.time()
        # Las sesiones abiertas antes de que esto existiera no traen marcas: se
        # les pone el reloj en hora en vez de echar a todo el mundo en el primer
        # despliegue.
        inicio = sesion.setdefault(INICIO, ahora)
        visto = sesion.setdefault(VISTO, ahora)

        if settings.SESION_INACTIVIDAD and ahora - visto > settings.SESION_INACTIVIDAD:
            return POR_INACTIVIDAD
        if settings.SESION_MAXIMA and ahora - inicio > settings.SESION_MAXIMA:
            return POR_LIMITE
        return None

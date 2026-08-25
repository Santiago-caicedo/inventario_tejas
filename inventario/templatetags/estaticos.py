"""Estáticos con marca de versión, para que el navegador no sirva copias viejas.

`app.css` y `app.js` conservan siempre el mismo nombre, así que un navegador
que los tenga en caché sigue usando la versión anterior aunque el HTML ya venga
con clases nuevas: la página se ve sin formato. Añadir la fecha del archivo a la
URL obliga a volver a pedirlo cada vez que cambia.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def estatico(ruta):
    url = static(ruta)
    archivo = finders.find(ruta)
    if not archivo:
        return url
    try:
        version = int(os.path.getmtime(archivo))
    except OSError:
        return url
    separador = '&' if '?' in url else '?'
    return f'{url}{separador}v={version}'

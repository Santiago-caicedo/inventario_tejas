from django import template

register = template.Library()


@register.filter
def cop(valor):
    """Formatea un número como pesos colombianos: 1234500 → $ 1.234.500"""
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return valor
    signo = '-' if entero < 0 else ''
    cifra = f'{abs(entero):,}'.replace(',', '.')
    return f'{signo}$ {cifra}'


@register.filter
def miles(valor):
    """Separador de miles sin símbolo: 1234500 → 1.234.500"""
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return valor
    signo = '-' if entero < 0 else ''
    return signo + f'{abs(entero):,}'.replace(',', '.')


# --- Total en letras, como lo exige un documento comercial -------------------

_UNIDADES = (
    '', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE',
    'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS',
    'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE', 'VEINTE',
)
_VEINTIS = (
    '', 'VEINTIÚN', 'VEINTIDÓS', 'VEINTITRÉS', 'VEINTICUATRO', 'VEINTICINCO',
    'VEINTISÉIS', 'VEINTISIETE', 'VEINTIOCHO', 'VEINTINUEVE',
)
_DECENAS = (
    '', '', '', 'TREINTA', 'CUARENTA', 'CINCUENTA',
    'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA',
)
_CENTENAS = (
    '', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
    'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS',
)


def _menor_a_mil(n):
    if n == 100:
        return 'CIEN'
    partes = []
    centena, resto = divmod(n, 100)
    if centena:
        partes.append(_CENTENAS[centena])
    if resto:
        if resto <= 20:
            partes.append(_UNIDADES[resto])
        elif resto < 30:
            partes.append(_VEINTIS[resto - 20])
        else:
            decena, unidad = divmod(resto, 10)
            partes.append(_DECENAS[decena] if not unidad
                          else f'{_DECENAS[decena]} Y {_UNIDADES[unidad]}')
    return ' '.join(partes)


def _a_letras(n):
    if n == 0:
        return 'CERO'
    bloques = []
    millones, resto = divmod(n, 1_000_000)
    if millones:
        bloques.append('UN MILLÓN' if millones == 1
                       else f'{_a_letras(millones)} MILLONES')
    miles_, resto = divmod(resto, 1000)
    if miles_:
        bloques.append('MIL' if miles_ == 1 else f'{_menor_a_mil(miles_)} MIL')
    if resto:
        bloques.append(_menor_a_mil(resto))
    return ' '.join(bloques)


@register.filter
def en_letras(valor):
    """Monto en palabras para la remisión: 2038800 → DOS MILLONES TREINTA Y OCHO MIL OCHOCIENTOS PESOS M/CTE"""
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return ''
    signo = 'MENOS ' if entero < 0 else ''
    n = abs(entero)
    if n == 1:
        peso = 'PESO'
    elif n >= 1_000_000 and n % 1_000_000 == 0:
        # "DOS MILLONES DE PESOS", pero "DOS MILLONES TREINTA MIL PESOS"
        peso = 'DE PESOS'
    else:
        peso = 'PESOS'
    return f'{signo}{_a_letras(n)} {peso} M/CTE'

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

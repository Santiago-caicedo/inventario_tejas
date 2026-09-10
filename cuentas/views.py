from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UsuarioForm
from .roles import AYUDA_ROL, COMBINACIONES, etiqueta_rol, rol_de, solo_administrador


def _ayudas():
    """Qué hace cada rol, para explicarlo al lado del selector."""
    return [(etiqueta, AYUDA_ROL[clave]) for clave, (etiqueta, _) in COMBINACIONES.items()]


@solo_administrador
def usuarios_lista(request):
    usuarios = User.objects.prefetch_related('groups')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
        )
    # Primero los administradores, después el resto por nombre de usuario.
    usuarios = usuarios.order_by('-is_superuser', 'username')
    pagina = Paginator(usuarios, 15).get_page(request.GET.get('pagina'))

    # El rol no es un campo: se deduce de los grupos, así que se resuelve aquí
    # y la plantilla solo pinta.
    filas = []
    for usuario in pagina:
        clave = rol_de(usuario)
        filas.append({'usuario': usuario, 'rol': clave, 'etiqueta': etiqueta_rol(clave)})

    return render(request, 'cuentas/usuarios_lista.html', {
        'seccion': 'usuarios', 'pagina': pagina, 'filas': filas, 'busqueda': busqueda,
    })


@solo_administrador
def usuario_crear(request):
    form = UsuarioForm(request.POST or None, editor=request.user)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(
            request,
            f'Usuario {usuario.username} creado con el rol '
            f'{etiqueta_rol(rol_de(usuario)).lower()}. Ya puede entrar con su contraseña.',
        )
        return redirect('usuarios_lista')
    return render(request, 'cuentas/usuario_form.html', {
        'seccion': 'usuarios', 'form': form, 'titulo': 'Nuevo usuario', 'ayudas': _ayudas(),
    })


@solo_administrador
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario, editor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Usuario {usuario.username} actualizado.')
        return redirect('usuarios_lista')
    return render(request, 'cuentas/usuario_form.html', {
        'seccion': 'usuarios', 'form': form, 'titulo': f'Editar {usuario.username}',
        'usuario_editado': usuario, 'ayudas': _ayudas(),
    })

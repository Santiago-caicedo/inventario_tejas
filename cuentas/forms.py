from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from inventario.forms import FormBase

from .roles import ADMINISTRADOR, aplicar_rol, opciones_de_rol, rol_de


class UsuarioForm(FormBase):
    """Alta y edición de una persona del equipo, con su rol.

    Sirve para las dos cosas porque el único campo que cambia de exigencia es
    la contraseña: al crear es obligatoria, al editar se deja en blanco para
    conservar la que ya tiene.
    """

    rol = forms.ChoiceField(
        label='rol',
        choices=opciones_de_rol,
        help_text='Define a qué secciones entra. Se puede cambiar después.',
    )
    contrasena = forms.CharField(
        label='contraseña',
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
    )
    contrasena2 = forms.CharField(
        label='repetir contraseña',
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {
            'username': 'usuario',
            'first_name': 'nombres',
            'last_name': 'apellidos',
            'email': 'correo',
            'is_active': 'puede entrar al sistema',
        }
        help_texts = {
            'username': 'Con esto inicia sesión. Sin espacios ni tildes.',
            'is_active': 'Al desactivarlo deja de poder entrar, pero su historial '
                         'de movimientos y pedidos queda intacto.',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'jperez', 'autocomplete': 'off'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Juan'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Pérez'}),
        }

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Quién está editando: hace falta para no dejar que se cierre la puerta
        # a sí mismo.
        self.editor = editor
        self.creando = self.instance.pk is None

        if self.creando:
            self.fields['contrasena'].help_text = 'Mínimo 8 caracteres. Entrégasela a la persona y que la cambie.'
            # Al crear, «activo» sobra: nadie da de alta a alguien apagado.
            del self.fields['is_active']
        else:
            self.fields['rol'].initial = rol_de(self.instance)
            self.fields['contrasena'].label = 'contraseña nueva'
            self.fields['contrasena'].help_text = 'Déjala en blanco para no cambiarla.'

    @property
    def se_edita_a_si_mismo(self):
        return not self.creando and self.editor is not None and self.editor.pk == self.instance.pk

    def clean_rol(self):
        rol = self.cleaned_data['rol']
        if self.se_edita_a_si_mismo and rol != ADMINISTRADOR:
            raise forms.ValidationError(
                'No puedes quitarte a ti mismo el rol de administrador: te quedarías '
                'sin poder entrar a esta pantalla. Pídeselo a otro administrador.'
            )
        return rol

    def clean_is_active(self):
        activo = self.cleaned_data['is_active']
        if not activo and self.se_edita_a_si_mismo:
            raise forms.ValidationError('No puedes desactivar tu propio usuario.')
        return activo

    def clean(self):
        datos = super().clean()
        clave, repetida = datos.get('contrasena'), datos.get('contrasena2')

        if self.creando and not clave:
            self.add_error('contrasena', 'Ponle una contraseña para que pueda entrar.')
        elif clave or repetida:
            if clave != repetida:
                self.add_error('contrasena2', 'Las dos contraseñas no coinciden.')
            else:
                try:
                    validate_password(clave, self.instance)
                except forms.ValidationError as error:
                    self.add_error('contrasena', error)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        clave = self.cleaned_data.get('contrasena')
        if clave:
            usuario.set_password(clave)
        usuario.save()
        # El rol se aplica después de guardar: cambia `is_superuser`, `is_staff`
        # y los grupos de una sola vez.
        aplicar_rol(usuario, self.cleaned_data['rol'])
        return usuario

from django import forms
from django.forms import inlineformset_factory

from inventario.forms import FormBase
from inventario.models import Producto

from .models import Cliente, ItemPedido, Pedido


class ClienteForm(FormBase):
    class Meta:
        model = Cliente
        fields = ['nombre', 'nit', 'telefono', 'email', 'ciudad', 'direccion', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ferretería El Constructor'}),
            'nit': forms.TextInput(attrs={'placeholder': '900.123.456-7'}),
        }


class PedidoForm(FormBase):
    class Meta:
        model = Pedido
        fields = ['cliente', 'fecha_entrega', 'direccion_entrega', 'notas']
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].empty_label = 'Elige el cliente…'


class ItemPedidoForm(FormBase):
    class Meta:
        model = ItemPedido
        fields = ['producto', 'cantidad', 'precio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        self.fields['producto'].empty_label = 'Elige el producto…'
        self.fields['cantidad'].widget.attrs['min'] = 1
        self.fields['precio'].widget.attrs['min'] = 0


ItemPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemPedido,
    form=ItemPedidoForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class EstadoPedidoForm(forms.Form):
    """Cambio de estado desde la pantalla de edición.

    A propósito no es un ModelForm: el estado nunca se guarda directo sobre el
    pedido, se aplica con `pedidos.services.cambiar_estado` para que el stock
    se mueva y se respete el flujo. El selector solo ofrece las transiciones
    válidas desde el estado actual.
    """

    estado = forms.ChoiceField(
        label='Cambiar estado',
        required=False,
        widget=forms.Select(attrs={'class': 'campo campo-select'}),
    )

    def __init__(self, *args, pedido, **kwargs):
        super().__init__(*args, **kwargs)
        self.pedido = pedido
        nombres = dict(Pedido.Estado.choices)
        self.fields['estado'].choices = (
            [('', f'Dejarlo en «{nombres[pedido.estado]}»')]
            + [(e, nombres[e]) for e in pedido.FLUJO[pedido.estado]]
        )

    def clean_estado(self):
        estado = self.cleaned_data['estado']
        if estado and not self.pedido.puede_pasar_a(estado):
            raise forms.ValidationError('Ese cambio de estado no está permitido.')
        return estado

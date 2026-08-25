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

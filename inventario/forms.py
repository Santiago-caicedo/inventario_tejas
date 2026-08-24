from django import forms

from .models import Categoria, Movimiento, Producto


class FormBase(forms.ModelForm):
    """Aplica las clases de estilo del sistema a todos los campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault('class', 'campo campo-select')
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'campo-check')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'campo campo-area')
                widget.attrs['rows'] = 3
            else:
                widget.attrs.setdefault('class', 'campo')


class ProductoForm(FormBase):
    class Meta:
        model = Producto
        fields = [
            'sku', 'nombre', 'categoria', 'unidad', 'precio',
            'stock_minimo', 'descripcion', 'activo',
        ]
        widgets = {
            'sku': forms.TextInput(attrs={'placeholder': 'TEJ-COL-01'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Teja colonial No. 4'}),
        }


class CategoriaForm(FormBase):
    class Meta:
        model = Categoria
        fields = ['nombre']


class MovimientoForm(FormBase):
    class Meta:
        model = Movimiento
        fields = ['producto', 'tipo', 'cantidad', 'nota']
        widgets = {
            'nota': forms.TextInput(attrs={'placeholder': 'Ej.: producción del horno 2, rotura en patio…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        self.fields['producto'].empty_label = 'Elige el producto…'

    def clean(self):
        datos = super().clean()
        tipo = datos.get('tipo')
        cantidad = datos.get('cantidad')
        if cantidad is not None:
            if cantidad == 0:
                self.add_error('cantidad', 'La cantidad no puede ser cero.')
            elif tipo in (Movimiento.Tipo.ENTRADA, Movimiento.Tipo.SALIDA) and cantidad < 0:
                self.add_error('cantidad', 'Para entradas y salidas usa una cantidad positiva.')
        return datos

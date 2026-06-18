from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_venta', 'stock_actual', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'precio_venta': 'Precio de venta ($)',
            'stock_actual': 'Stock actual',
            'imagen': 'Imagen del producto',
            'activo': 'Producto activo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Kit de limpieza premium'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el producto...'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'placeholder': '0',
                'min': '0'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
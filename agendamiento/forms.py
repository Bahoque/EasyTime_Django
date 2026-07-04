from django import forms
from .models import Cita, Servicio, Operario
from django.utils import timezone
from django.core.exceptions import ValidationError

class CitaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        self.fields['servicio'].queryset = Servicio.objects.filter(activo=True)
        self.fields['servicio'].label_from_instance = lambda obj: f"{obj.nombre} - ${obj.precio:,.0f} ({obj.duracion_estimada})"
        self.fields['operario'].queryset = Operario.objects.filter(activo=True)
        self.fields['operario'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido}"
        self.fields['fecha_hora'].widget.attrs['min'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Cita
        fields = ['servicio', 'operario', 'fecha_hora', 'placa_vehiculo', 'notas']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                }
            ),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'operario': forms.Select(attrs={'class': 'form-select'}),
            'placa_vehiculo': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'placeholder': 'Ej: ABC-123',
                    'style': 'text-transform: uppercase;'
                }
            ),
            'notas': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles adicionales...'}
            ),
        }
        labels = {
            'fecha_hora': 'Fecha y Hora de la Cita',
            'placa_vehiculo': 'Placa del Vehículo',
            'servicio': 'Tipo de Servicio',
            'operario': 'Operario',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_hora = cleaned_data.get('fecha_hora')
        servicio = cleaned_data.get('servicio')
        operario = cleaned_data.get('operario')

        if fecha_hora and fecha_hora < timezone.now():
            raise ValidationError("No puedes agendar una cita en una fecha u hora que ya pasó.")

        if fecha_hora and servicio and operario:
            if not operario.esta_disponible(fecha_hora, servicio.duracion_estimada):
                fecha_fin = fecha_hora + servicio.duracion_estimada
                raise ValidationError(
                    f"{operario.nombre} {operario.apellido} no está disponible entre "
                    f"{fecha_hora.strftime('%H:%M')} y {fecha_fin.strftime('%H:%M')}. "
                    f"Por favor elige otro operario u otro horario."
                )

        return cleaned_data

    def clean_placa_vehiculo(self):
        placa = self.cleaned_data.get('placa_vehiculo')
        return placa.upper() if placa else placa


class ServicioForm(forms.ModelForm):
    duracion_estimada = forms.DurationField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '00:45:00 (HH:MM:SS)'
        }),
        label='Duración estimada',
        help_text='Ingresa el tiempo estimado en formato Horas:Minutos:Segundos.'
    )

    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio', 'duracion_estimada', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre del servicio',
            'descripcion': 'Descripción del servicio',
            'precio': 'Precio ($)',
            'imagen': 'Imagen descriptiva',
            'activo': 'Servicio activo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. Lavado General de Auto/Moto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Detalla qué incluye este paquete...'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class OperarioForm(forms.ModelForm):
    class Meta:
        model = Operario
        fields = ['nombre', 'apellido', 'telefono', 'especialidad', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'telefono': 'Teléfono',
            'especialidad': 'Especialidad',
            'imagen': 'Foto del operario',
            'activo': 'Operario activo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del operario'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 3001234567'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Lavado exterior'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductoFacturaForm(forms.Form):
    """Formulario para agregar productos a la factura durante el agendamiento"""
    producto = forms.ModelChoiceField(
        queryset=None,
        label='Producto',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        required=False,
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )

    def __init__(self, *args, **kwargs):
        from inventario.models import Producto
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True, stock_actual__gt=0)
        self.fields['producto'].label_from_instance = lambda obj: f"{obj.nombre} - ${obj.precio_venta:,.0f}"
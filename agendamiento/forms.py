from django import forms
from .models import Cita, Servicio
from django.utils import timezone
from django.core.exceptions import ValidationError

class CitaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        self.fields['servicio'].queryset = Servicio.objects.filter(activo=True)
        self.fields['servicio'].label_from_instance = lambda obj: f"{obj.nombre}"
        self.fields['fecha_hora'].widget.attrs['min'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Cita
        fields = ['servicio', 'fecha_hora', 'placa_vehiculo', 'notas']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                }
            ),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
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
        }

    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        if fecha_hora and fecha_hora < timezone.now():
            raise ValidationError("No puedes agendar una cita en una fecha o hora que ya pasó.")
        return fecha_hora

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
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Operario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    imagen = CloudinaryField('imagen', null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def esta_disponible(self, fecha_hora, duracion, excluir_cita_id=None):
        """Verifica si el operario está disponible en el rango de tiempo dado"""
        from django.utils import timezone
        fecha_fin = fecha_hora + duracion
        citas = Cita.objects.filter(
            operario=self,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        )
        if excluir_cita_id:
            citas = citas.exclude(id=excluir_cita_id)
        for cita in citas:
            cita_fin = cita.fecha_hora + cita.servicio.duracion_estimada
            if fecha_hora < cita_fin and fecha_fin > cita.fecha_hora:
                return False
        return True

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada = models.DurationField(help_text="Formato: HH:MM:SS")
    imagen = CloudinaryField('imagen', null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class Cita(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='citas'
    )
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    operario = models.ForeignKey(
        Operario,
        on_delete=models.PROTECT,
        related_name='citas',
        null=True,
        blank=True
    )
    fecha_hora = models.DateTimeField()
    placa_vehiculo = models.CharField(max_length=10)
    notas = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    creado_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Agendamiento"
        verbose_name_plural = "Agendamientos"

    def __str__(self):
        return f"Cita {self.id}: {self.usuario.username} - {self.fecha_hora}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, null=True, blank=True) 
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return self.mensaje
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imagen = CloudinaryField('imagen', null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio_venta})"

class EntradaInventario(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

class DetalleEntrada(models.Model):
    entrada = models.ForeignKey(EntradaInventario, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_recibida = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.producto.stock_actual += self.cantidad_recibida
        self.producto.save()
        super().save(*args, **kwargs)

class Venta(models.Model):
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)

    @property
    def obtener_total_carrito(self):
        return sum(item.obtener_subtotal for item in self.items_venta.all())

    def __str__(self):
        estado = "Pagado" if self.pagado else "Carrito Activo"
        return f"Venta {self.id} - {self.cliente} ({estado})"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='items_venta', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def obtener_subtotal(self):
        return self.precio_unitario * self.cantidad

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
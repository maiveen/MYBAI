from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Marca(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    especificaciones = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    oferta = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.nombre

class Carrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carritos')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario',)  # ⭐ SOLUCIÓN: Solo 1 carrito por usuario

    def __str__(self):
        return f"Carrito {self.id} - {self.usuario.username}"

    def total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal()
        return total

    def total_items(self):
        return sum(item.cantidad for item in self.items.all())

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def subtotal(self):
        return self.producto.precio * self.cantidad

class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('en_camino', 'En camino'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    carrito = models.OneToOneField(Carrito, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    direccion_envio = models.CharField(max_length=255, blank=True, null=True)
    codigo_rastreo = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"

    def total(self):
        return self.carrito.total()

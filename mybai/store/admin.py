from django.contrib import admin
from .models import Producto, Carrito, CarritoItem, Pedido

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'categoria', 'precio', 'stock', 'oferta')
    list_editable = ('oferta', 'stock')
    list_filter = ('marca', 'categoria', 'oferta')
    search_fields = ('nombre', 'descripcion', 'especificaciones')

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'creado', 'total')

@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'producto', 'cantidad', 'subtotal')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'estado', 'fecha_creacion', 'codigo_rastreo')
    list_filter = ('estado',)
    search_fields = ('usuario__username', 'codigo_rastreo')

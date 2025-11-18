from django.urls import path
from . import views

urlpatterns = [
    # Página principal (única ruta raíz en la app)
    path('', views.inicio, name='inicio'),

    # Autenticación (mantener signin/register intactos)
    path('signin/', views.signin, name='signin'),
    path('register/', views.register, name='register'),
    path('logout/', views.signout, name='signout'),

    # Catálogo y detalle
    path('catalogo/', views.catalogo, name='catalogo'),
    path('detalle_producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),

    # Soporte (mapear a la vista existente de catálogo si no hay una específica)
    path('soporte/', views.soporte, name='soporte'),

    # Carrito
    path('carrito/', views.ver_carrito, name='carrito'),
    path('agregar_al_carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_item, name='eliminar_item'),
    path('carrito/disminuir/<int:item_id>/', views.disminuir_item, name='disminuir_item'),

    # Checkout / Pedidos
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/', views.ver_pedidos, name='ver_pedidos'),
    path('pedido/<int:pedido_id>/', views.estado_pedido, name='estado_pedido'),
]

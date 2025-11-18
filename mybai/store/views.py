from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Categoria, Marca, Carrito, CarritoItem, Pedido
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model

UserModel = get_user_model()

def signin(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = None
        try:
            user = authenticate(request, username=email, password=password)
            if user is None:
                try:
                    u = UserModel.objects.get(email__iexact=email)
                    user = authenticate(request, username=u.username, password=password)
                except UserModel.DoesNotExist:
                    user = None
        except Exception:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}.")
            return redirect('inicio')
        else:
            messages.error(request, "Correo o contraseña incorrectos.")
            return redirect('signin')

    return render(request, 'store/signin.html')

def register(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('register')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Ya existe una cuenta con este correo.")
            return redirect('register')

        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        # ⭐ CREAR CARRITO AUTOMÁTICAMENTE
        Carrito.objects.get_or_create(usuario=user)

        messages.success(request, "Cuenta creada correctamente. Inicia sesión.")
        return redirect('signin')

    return render(request, 'store/register.html')

@login_required
def signout(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('inicio')

def inicio(request):
    productos_destacados = Producto.objects.filter(oferta=True)[:4]
    return render(request, 'store/inicio.html', {'productos_destacados': productos_destacados})

def catalogo(request):
    productos = Producto.objects.all()
    categorias = {c.id: c.nombre for c in Categoria.objects.all()}
    marcas = {m.id: m.nombre for m in Marca.objects.all()}
    selected_categoria = request.GET.get('categoria')
    selected_marca = request.GET.get('marca')
    selected_orden = request.GET.get('orden')

    if selected_categoria:
        try:
            selected_categoria = int(selected_categoria)
            productos = productos.filter(categoria_id=selected_categoria)
        except ValueError:
            pass

    if selected_marca:
        try:
            selected_marca = int(selected_marca)
            productos = productos.filter(marca_id=selected_marca)
        except ValueError:
            pass

    if selected_orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif selected_orden == 'precio_desc':
        productos = productos.order_by('-precio')

    productos = productos.order_by('id')

    paginator = Paginator(productos, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'productos': page_obj.object_list,
        'categorias': categorias,
        'marcas': marcas,
        'selected_categoria': selected_categoria,
        'selected_marca': selected_marca,
        'selected_orden': selected_orden,
        'page_obj': page_obj,
    }
    return render(request, 'store/catalogo.html', context)


def soporte(request):
    """Página de soporte técnico"""
    return render(request, 'store/soporte.html')

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'store/detalle_producto.html', {'producto': producto})

@login_required(login_url='signin')
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method != 'POST':
        # fallback: si es AJAX devuelve error, si no redirige al catálogo
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
        return redirect('catalogo')

    try:
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except (ValueError, TypeError):
            cantidad = 1
        if cantidad < 1:
            cantidad = 1

        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

        if producto.stock < 1:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Sin stock.'}, status=400)
            messages.error(request, 'Producto sin stock.')
            return redirect(request.META.get('HTTP_REFERER', 'catalogo'))

        item, creado_item = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)
        if not creado_item:
            item.cantidad = min(item.cantidad + cantidad, producto.stock)
        else:
            item.cantidad = min(cantidad, producto.stock)
        item.save()

        # Respuesta AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'✓ {producto.nombre} añadido al carrito',
                'total_items': carrito.total_items(),
                'carrito_total': str(carrito.total()),
            })

        # Fallback no-JS: mensaje y redirección al referer o catálogo
        messages.success(request, f"Se añadió {producto.nombre} al carrito.")
        return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', 'catalogo'))

    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error al añadir producto.'}, status=500)
        messages.error(request, 'No se pudo añadir el producto al carrito.')
        return redirect(request.META.get('HTTP_REFERER', 'catalogo'))

@login_required
def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, 'store/carrito.html', {'carrito': carrito})

@login_required
def disminuir_item(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()
    return redirect('carrito')

@login_required
def eliminar_item(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    item.delete()
    return redirect('carrito')

@login_required
def checkout(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        # Obtener dirección del formulario
        direccion = request.POST.get('direccion', '').strip()
        apartamento = request.POST.get('apartamento', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        
        # Combinar dirección completa
        if apartamento:
            direccion_completa = f"{direccion}, {apartamento}, {ciudad}"
        else:
            direccion_completa = f"{direccion}, {ciudad}"
        
        if not direccion:
            messages.error(request, 'Por favor ingresa una dirección de envío.')
            return redirect('checkout')

        try:
            with transaction.atomic():
                if not carrito.items.exists():
                    messages.error(request, 'Tu carrito está vacío.')
                    return redirect('carrito')

                # Crear pedido
                pedido = Pedido.objects.create(
                    usuario=request.user,
                    carrito=carrito,
                    direccion_envio=direccion_completa
                )
                pedido.codigo_rastreo = f"MYB-{pedido.id:06d}"
                pedido.save()

                # Actualizar stock
                for item in carrito.items.select_related('producto'):
                    prod = item.producto
                    if prod.stock >= item.cantidad:
                        prod.stock = max(0, prod.stock - item.cantidad)
                        prod.save()
                    else:
                        raise IntegrityError(f"Stock insuficiente para {prod.nombre}")

                # Crear nuevo carrito
                # Vaciar el carrito actual en lugar de crear uno nuevo
                # Crear un nuevo Carrito para el usuario fallaría si existe una restricción
                # de unicidad; por tanto eliminamos los items para dejar el carrito vacío.
                carrito.items.all().delete()

            messages.success(request, f'✓ Pedido #{pedido.id} creado correctamente. Código de rastreo: {pedido.codigo_rastreo}')
            return redirect('ver_pedidos')
        
        except IntegrityError as ie:
            messages.error(request, str(ie))
            return redirect('carrito')
        except Exception as e:
            messages.error(request, 'Ocurrió un error al procesar el pago. Inténtalo más tarde.')
            return redirect('carrito')

    return render(request, 'store/finalizar_compra.html', {'carrito': carrito})

@login_required
def crear_pedido(request):
    try:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        if not carrito.items.exists():
            messages.error(request, 'No hay items en el carrito para crear un pedido.')
            return redirect('carrito')
        pedido = Pedido.objects.create(usuario=request.user, carrito=carrito)
        pedido.codigo_rastreo = f"MYB-{pedido.id:06d}"
        pedido.save()
        # Vaciar el carrito (no crear uno nuevo para evitar violar restricciones únicas)
        carrito.items.all().delete()
        messages.success(request, 'Pedido creado.')
    except Exception as e:
        messages.error(request, 'No se pudo crear el pedido.')
    return redirect('ver_pedidos')

@login_required
def ver_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'store/ver_pedidos.html', {'pedidos': pedidos})

@login_required
def estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'store/ver_estado_pedido.html', {'pedido': pedido})

function initAddToCart() {
  const forms = document.querySelectorAll('.add-to-cart-form');
  console.debug('[carrito-ajax] initAddToCart, found forms:', forms.length);

  forms.forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      console.debug('[carrito-ajax] submit intercepted for', this.dataset.productId || this.action);

      const productId = this.dataset.productId;
      const productName = this.dataset.productName;
      // intentar leer la cantidad desde el input visible en el mismo contenedor
      let cantidad = 1;
      try {
        const visibleContainer = this.closest('.product-container') || document;
        const visibleQty = visibleContainer.querySelector('#qty');
        if (visibleQty) {
          cantidad = visibleQty.value || 1;
          // actualizar hidden input si existe
          const hidden = this.querySelector('input[name="cantidad"]');
          if (hidden) hidden.value = cantidad;
        } else {
          const cantidadInput = this.querySelector('input[name="cantidad"]');
          cantidad = cantidadInput ? cantidadInput.value : 1;
        }
      } catch (e) {
        console.warn('[carrito-ajax] error leyendo cantidad visible', e);
        const cantidadInput = this.querySelector('input[name="cantidad"]');
        cantidad = cantidadInput ? cantidadInput.value : 1;
      }
      const csrfTokenInput = this.querySelector('[name="csrfmiddlewaretoken"]');
      if (!csrfTokenInput) {
        console.error('CSRF token missing in form.');
        return;
      }

      const formData = new FormData();
      formData.append('cantidad', cantidad);
      formData.append('csrfmiddlewaretoken', csrfTokenInput.value);

      try {
        const res = await fetch(this.action || `/agregar_al_carrito/${productId}/`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          },
          credentials: 'same-origin',
          body: formData
        });

        const contentType = res.headers.get('content-type') || '';
        console.debug('[carrito-ajax] response status', res.status, 'content-type', contentType);

        if (!res.ok && contentType.includes('text/html')) {
          // probable redirect (no autenticado) -> forzar login
          Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'warning',
            title: 'Inicia sesión para añadir al carrito',
            showConfirmButton: true,
            confirmButtonText: 'Ir a iniciar sesión'
          }).then(() => {
            // usar ruta fija (coincide con urlpatterns: 'signin/' en [store/urls.py](store/urls.py))
            window.location.href = '/signin/';
          });
          return;
        }

        let data = null;
        if (contentType.includes('application/json')) {
          data = await res.json();
        } else {
          const text = await res.text();
          console.error('Respuesta inesperada (no JSON):', text);
          // Mostrar mensaje amigable y depuración
          try {
            Swal.fire({
              toast: true,
              position: 'top-end',
              icon: 'error',
              title: 'Error de servidor: respuesta inesperada',
              text: text ? (text.substring(0,120) + '...') : '',
              showConfirmButton: false,
              timer: 3500
            });
          } catch(e) {
            alert('Error al añadir al carrito.');
          }
          return;
        }

        if (data.success) {
          Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: data.message || `✓ ${productName} añadido`,
            showConfirmButton: false,
            timer: 2200,
            timerProgressBar: true
          });
          updateCartCount(data.total_items);
        } else {
          Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: data.message || 'No se pudo añadir al carrito',
            showConfirmButton: false,
            timer: 3000
          });
        }
      } catch (err) {
        console.error(err);
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'error',
          title: 'Error de red',
          showConfirmButton: false,
          timer: 2500
        });
      }
    });
  });
}

// Ensures initialization whether the script is loaded before or after DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAddToCart);
} else {
  initAddToCart();
}

// Delegated handlers for quantity +/- buttons (works even if buttons are outside the form)
function initQtyDelegation() {
  document.addEventListener('click', function(e) {
    const inc = e.target.closest('.qty-increment-btn');
    const dec = e.target.closest('.qty-decrement-btn');
    if (!inc && !dec) return;
    e.preventDefault();
    // buscar el input #qty más cercano dentro de .product-container
    const container = (inc || dec).closest('.product-container') || document;
    const qtyInput = container.querySelector('#qty');
    if (!qtyInput) return;
    let val = parseInt(qtyInput.value || '1');
    const max = parseInt(qtyInput.max || '99999');
    if (inc) {
      if (val < max) val = val + 1;
    } else if (dec) {
      if (val > 1) val = val - 1;
    }
    qtyInput.value = val;
    // si existe un hidden dentro del formulario cercano, sincronizarlo
    const form = container.querySelector('.add-to-cart-form');
    if (form) {
      const hidden = form.querySelector('input[name="cantidad"]');
      if (hidden) hidden.value = val;
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initQtyDelegation);
} else {
  initQtyDelegation();
}

// Función para actualizar el contador de carrito en el header
function updateCartCount(count) {
  let badge = document.querySelector('.cart-badge');
  if (!badge) {
    // si no existe, intentar crear uno junto al icono de carrito
    const cartLink = document.querySelector('a[href$="/carrito/"], a[href$="carrito/"], .cart-link');
    if (cartLink) {
      badge = document.createElement('span');
      badge.className = 'cart-badge';
      badge.style.marginLeft = '6px';
      cartLink.appendChild(badge);
    }
  }
  if (badge) {
    badge.textContent = count;
  }
}
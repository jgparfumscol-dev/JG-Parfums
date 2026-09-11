// Carrito persistido en localStorage. No hay carrito en el backend: el
// checkout recibe la lista de items directo en POST /orders.
const CART_KEY = 'jg_cart';

function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (_err) {
    return [];
  }
}

function saveCart(items) {
  localStorage.setItem(CART_KEY, JSON.stringify(items));
  updateCartBadge();
}

// Cada línea del carrito se identifica por producto + presentación, no solo
// por producto: así un cliente puede llevar el frasco completo y un decant
// del mismo perfume como dos líneas separadas.
function cartLineKey(productId, variantId) {
  return `${productId}:${variantId || 'full'}`;
}

// variant, si viene, es {id, size_ml, price, stock} — un decant de 5ml/10ml.
// Sin variant se agrega el frasco completo, tal como funcionaba antes.
function addToCart(product, quantity = 1, variant = null) {
  const items = getCart();
  const lineKey = cartLineKey(product.id, variant ? variant.id : null);
  const stock = variant ? variant.stock : product.stock;
  const existing = items.find((item) => item.line_key === lineKey);
  if (existing) {
    existing.quantity = Math.min(existing.quantity + quantity, stock);
  } else {
    items.push({
      line_key: lineKey,
      product_id: product.id,
      variant_id: variant ? variant.id : null,
      name: product.name,
      slug: product.slug,
      price: variant ? variant.price : product.price,
      size_label: variant ? `${variant.size_ml} ml (decant)` : `${product.size_ml} ml`,
      stock,
      image: product.images && product.images[0] ? product.images[0].url : null,
      quantity: Math.min(quantity, stock),
    });
  }
  saveCart(items);
}

function updateCartItemQuantity(lineKey, quantity) {
  const items = getCart()
    .map((item) => (item.line_key === lineKey ? { ...item, quantity } : item))
    .filter((item) => item.quantity > 0);
  saveCart(items);
}

function removeFromCart(lineKey) {
  saveCart(getCart().filter((item) => item.line_key !== lineKey));
}

function clearCart() {
  saveCart([]);
}

function getCartCount() {
  return getCart().reduce((total, item) => total + item.quantity, 0);
}

function getCartTotal() {
  return getCart().reduce((total, item) => total + item.price * item.quantity, 0);
}

function updateCartBadge() {
  document.querySelectorAll('[data-cart-count]').forEach((el) => {
    const count = getCartCount();
    el.textContent = count;
    el.hidden = count === 0;
  });
}

document.addEventListener('DOMContentLoaded', updateCartBadge);

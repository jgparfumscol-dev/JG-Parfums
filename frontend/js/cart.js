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

function addToCart(product, quantity = 1) {
  const items = getCart();
  const existing = items.find((item) => item.product_id === product.id);
  if (existing) {
    existing.quantity = Math.min(existing.quantity + quantity, product.stock);
  } else {
    items.push({
      product_id: product.id,
      name: product.name,
      slug: product.slug,
      price: product.price,
      size_ml: product.size_ml,
      stock: product.stock,
      image: product.images && product.images[0] ? product.images[0].url : null,
      quantity: Math.min(quantity, product.stock),
    });
  }
  saveCart(items);
}

function updateCartItemQuantity(productId, quantity) {
  const items = getCart()
    .map((item) => (item.product_id === productId ? { ...item, quantity } : item))
    .filter((item) => item.quantity > 0);
  saveCart(items);
}

function removeFromCart(productId) {
  saveCart(getCart().filter((item) => item.product_id !== productId));
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

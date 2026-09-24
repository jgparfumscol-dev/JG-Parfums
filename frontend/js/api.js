// Helpers de red y sesión, compartidos por todas las páginas.
// Ajusta API_URL al dominio real del backend antes de desplegar a producción.
const API_URL = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
  ? 'http://localhost:8080'
  : 'https://jg-parfums-production.up.railway.app';

const TOKEN_KEY = 'jg_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// El widget de chat (ver sections.js, getChatSessionId/getChatHistory) guarda
// su session_id y el historial visible en sessionStorage bajo estas claves.
// Se borran acá, en el único lugar por donde pasa todo login/logout, para
// que la memoria de una cuenta (tanto la del navegador como la de n8n, que
// usa el session_id como llave de su propia memoria de conversación) nunca
// se filtre a otra cuenta en el mismo navegador.
function resetChatSession() {
  try {
    sessionStorage.removeItem('jg_chat_session');
    sessionStorage.removeItem('jg_chat_history');
  } catch (_err) {
    // sessionStorage inaccesible (ej. modo privado estricto) — no hay nada
    // que limpiar entonces, seguir sin romper el login/logout por esto.
  }
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  resetChatSession();
}

function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
  resetChatSession();
}

function isLoggedIn() {
  return Boolean(getToken());
}

// Wrapper único: agrega Authorization si hay token, y solo fuerza redirect a
// login en un 401 cuando efectivamente había un token adjunto (un 401 sin
// token, ej. credenciales incorrectas en el login, no debe redirigir).
async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });

  if (response.status === 401 && token) {
    removeToken();
    window.location.href = '/login.html';
    throw new Error('Sesión expirada');
  }

  if (!response.ok) {
    let detail = 'Ocurrió un error inesperado';
    try {
      const body = await response.json();
      // FastAPI manda `detail` como texto en los errores que arma la ruta a
      // mano, pero como lista de {loc, msg, type} en cualquier 422 de
      // validación automática (incluida la nuestra) — sin este chequeo,
      // ese caso se mostraba como "[object Object]" en vez del mensaje.
      if (Array.isArray(body.detail)) {
        detail = body.detail.map((e) => e.msg || JSON.stringify(e)).join(' · ') || detail;
      } else if (body.detail) {
        detail = body.detail;
      }
    } catch (_err) {
      // respuesta sin cuerpo JSON, se usa el mensaje genérico
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
}

function formatCOP(amount) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(amount);
}

// Precio con descuento: el original tachado, el final y la etiqueta "-X%".
// Sin descuento devuelve solo el precio, igual que antes.
function priceHtml(originalPrice, finalPrice, discountPercent) {
  if (!discountPercent) return formatCOP(finalPrice);
  return `${formatCOP(finalPrice)} <s class="price-original">${formatCOP(originalPrice)}</s> <span class="discount-tag">-${discountPercent}%</span>`;
}

// Precio más bajo con el que se puede comprar el producto (frasco o decant
// activo), ya con el descuento aplicado, para ordenar y mostrar "Desde".
function lowestFinalPrice(product) {
  const activeVariants = (product.variants || []).filter((v) => v.is_active);
  return Math.min(product.final_price, ...activeVariants.map((v) => v.final_price));
}

// Precio de la tarjeta de producto: "Desde" cuando hay decants activos.
function productCardPriceHtml(product) {
  const activeVariants = (product.variants || []).filter((v) => v.is_active);
  const prefix = activeVariants.length ? 'Desde ' : '';
  const originalLowest = Math.min(product.price, ...activeVariants.map((v) => v.price));
  return prefix + priceHtml(originalLowest, lowestFinalPrice(product), product.discount_percent);
}

// Estadísticas propias del sitio: sin cookies, sin IP ni user-agent guardados,
// solo qué página se vio. No cuenta el panel admin (es tráfico del dueño de
// la tienda, no de clientes) ni falla nunca de forma visible al usuario.
if (!location.pathname.startsWith('/admin')) {
  fetch(`${API_URL}/stats/track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: location.pathname, referrer: document.referrer || null }),
  }).catch(() => {});
}

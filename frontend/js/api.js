// Helpers de red y sesión, compartidos por todas las páginas.
// Ajusta API_URL al dominio real del backend antes de desplegar a producción.
const API_URL = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
  ? 'http://localhost:8080'
  : 'https://jg-parfums-production.up.railway.app';

const TOKEN_KEY = 'jg_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
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
      detail = body.detail || detail;
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

/* Aplica la identidad de tienda configurada en el panel admin (nombre,
   color de marca, tipografía, contacto) a cada página pública. No se carga
   en admin.html: el panel se queda con la marca fija a propósito, para no
   interferir con su propia UI mientras se edita el resto del sitio.

   El color de marca no se retiñe cambiando solo --accent: varias reglas del
   sitio (el filete de .section-title, ::selection, :focus-visible, el
   brillo de la pirámide olfativa) usan directamente algún punto de la
   escala --gold-*. Por eso se regenera la escala completa a partir del
   color elegido y se aplica inline sobre <html> — inline gana sobre
   cualquier hoja de estilos, así que todo lo que use la escala se retiñe
   solo, sin tocar components.css ni tokens.css. */

const FONT_PAIRINGS = {
  classic: {
    display: "'Newsreader', Georgia, serif",
    body: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif",
    url: null, // ya la carga tokens.css
  },
  warm: {
    display: "'Newsreader', Georgia, serif",
    body: "'Hanken Grotesk', system-ui, sans-serif",
    url: 'https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Hanken+Grotesk:wght@400;500;600&display=swap',
  },
  elegant: {
    display: "'Cormorant Garamond', Georgia, serif",
    body: "'Manrope', system-ui, sans-serif",
    url: 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Manrope:wght@400;500;600&display=swap',
  },
  minimal: {
    display: "'Libre Baskerville', Georgia, serif",
    body: "'Karla', system-ui, sans-serif",
    url: 'https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Karla:wght@400;500;600&display=swap',
  },
  editorial: {
    display: "'Prata', Georgia, serif",
    body: "'Outfit', system-ui, sans-serif",
    url: 'https://fonts.googleapis.com/css2?family=Prata&family=Outfit:wght@400;500;600&display=swap',
  },
};

let _siteSettingsCache = null;

async function getSiteSettings() {
  if (_siteSettingsCache) return _siteSettingsCache;
  try {
    _siteSettingsCache = await apiFetch('/settings');
  } catch (_err) {
    _siteSettingsCache = {};
  }
  return _siteSettingsCache;
}

function hexToHsl(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      default: h = (r - g) / d + 4;
    }
    h /= 6;
  }
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h, s, l) {
  const sNorm = s / 100;
  const lNorm = l / 100;
  const k = (n) => (n + h / 30) % 12;
  const a = sNorm * Math.min(lNorm, 1 - lNorm);
  const f = (n) => lNorm - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  const toHex = (x) => Math.round(255 * x).toString(16).padStart(2, '0');
  return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`;
}

// Mismos pasos de luminosidad que ya tiene la escala real de marca: tintes
// claros para fondos suaves, tonos oscuros para texto legible sobre claro.
const GOLD_SCALE_LIGHTNESS = { 50: 92, 100: 85, 200: 75, 400: 63, 500: 58, 600: 45, 700: 35, 800: 25 };

function applyAccentColor(hex) {
  if (!/^#[0-9A-Fa-f]{6}$/.test(hex || '')) return;
  const [h, s] = hexToHsl(hex);
  const root = document.documentElement.style;
  Object.entries(GOLD_SCALE_LIGHTNESS).forEach(([step, l]) => {
    root.setProperty(`--gold-${step}`, hslToHex(h, s, l));
  });
  root.setProperty('--jg-gold', hslToHex(h, s, GOLD_SCALE_LIGHTNESS[400]));
}

function applyFontPairing(key) {
  const pairing = FONT_PAIRINGS[key] || FONT_PAIRINGS.classic;
  if (pairing.url) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = pairing.url;
    document.head.appendChild(link);
  }
  document.documentElement.style.setProperty('--font-display', pairing.display);
  document.documentElement.style.setProperty('--font-body', pairing.body);
}

// Íconos genéricos (no los logotipos oficiales) — currentColor para heredar
// el blanco del footer; el círculo que los envuelve viene de .footer-social-icon.
const SOCIAL_ICONS = {
  whatsapp: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3a9 9 0 0 0-7.75 13.5L3 21l4.5-1.25A9 9 0 1 0 12 3z"/><path d="M8.5 9.5c.3 2.5 2.5 4.7 5 5" stroke-linecap="round"/></svg>',
  instagram: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>',
  tiktok: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M15 4v9.5a3.5 3.5 0 1 1-3.5-3.5c.35 0 .68.04 1 .12" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 4c.6 2 2.2 3.4 4 3.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

// Fila de íconos redondos en el footer — usa exactamente los mismos links
// de Ajustes > Contacto y redes que ya alimentan applyStoreExtras, así que
// solo aparece el ícono de la red que el admin haya configurado.
function applyFooterSocial(s) {
  const el = document.getElementById('footerSocial');
  if (!el) return;

  const links = [];
  if (s.whatsapp_number) links.push({ href: `https://wa.me/${encodeURIComponent(s.whatsapp_number)}`, key: 'whatsapp', label: 'WhatsApp' });
  if (s.instagram_url) links.push({ href: s.instagram_url, key: 'instagram', label: 'Instagram' });
  if (s.tiktok_url) links.push({ href: s.tiktok_url, key: 'tiktok', label: 'TikTok' });

  if (links.length === 0) return;
  el.innerHTML = links
    .map((l) => `<a class="footer-social-icon" href="${l.href}" target="_blank" rel="noopener" aria-label="${l.label}">${SOCIAL_ICONS[l.key]}</a>`)
    .join('');
  el.hidden = false;
}

function applyStoreExtras(s) {
  const extras = document.getElementById('storeExtras');
  const list = document.getElementById('storeExtrasList');
  if (!extras || !list) return;

  const links = [];
  if (s.whatsapp_number) links.push(`<li><a class="text-muted" href="https://wa.me/${encodeURIComponent(s.whatsapp_number)}" target="_blank" rel="noopener">WhatsApp</a></li>`);
  if (s.instagram_url) links.push(`<li><a class="text-muted" href="${s.instagram_url}" target="_blank" rel="noopener">Instagram</a></li>`);
  if (s.tiktok_url) links.push(`<li><a class="text-muted" href="${s.tiktok_url}" target="_blank" rel="noopener">TikTok</a></li>`);
  if (s.contact_email) links.push(`<li><a class="text-muted" href="mailto:${s.contact_email}">${s.contact_email}</a></li>`);
  if (s.contact_phone) links.push(`<li><a class="text-muted" href="tel:${s.contact_phone}">${s.contact_phone}</a></li>`);

  if (links.length === 0) return;
  list.innerHTML = links.join('');
  extras.hidden = false;
}

async function applySiteBranding() {
  const s = await getSiteSettings();
  if (!s || Object.keys(s).length === 0) return;
  if (s.accent_color) applyAccentColor(s.accent_color);
  if (s.font_pairing) applyFontPairing(s.font_pairing);
  if (s.store_name) document.title = document.title.replace('JG Parfums', s.store_name);
  applyStoreExtras(s);
  applyFooterSocial(s);
}

applySiteBranding();

/* ---- header: menú móvil, clases (categorías) y buscador ----
   Compartido por todas las páginas de la tienda que traen el header
   (ver nav-top/nav-bottom en components.css); páginas sin ese markup
   simplemente no tienen los elementos y cada init sale sin hacer nada. */

function initMobileNavToggle() {
  const toggle = document.getElementById('navToggle');
  const panel = document.getElementById('navMobilePanel');
  if (!toggle || !panel) return;
  toggle.addEventListener('click', () => {
    const isOpen = panel.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
}

// El header arranca sólido y pasa a vidrio esmerilado (ver .nav.is-scrolled
// en components.css) apenas se hace scroll, en vez de quedarse como una
// franja plana pegada arriba todo el tiempo.
function initNavScrollState() {
  const nav = document.querySelector('header.nav');
  if (!nav) return;
  const THRESHOLD = 24;
  let ticking = false;
  function update() {
    nav.classList.toggle('is-scrolled', window.scrollY > THRESHOLD);
    ticking = false;
  }
  update();
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    },
    { passive: true }
  );
}

// Las "clases" del header son las categorías ya creadas en el panel admin
// (Mujer, Hombre, Ocasiones...) — mismo listado que alimenta el filtro del
// catálogo, solo que acá cada una linkea directo con el filtro aplicado.
async function initNavClasses() {
  const desktopList = document.getElementById('navClasses');
  const mobileList = document.getElementById('navClassesMobile');
  if (!desktopList && !mobileList) return;
  try {
    const categories = await apiFetch('/categories');
    if (categories.length === 0) return;
    const items = categories
      .map((c) => `<li><a href="/catalogo.html?category_id=${c.id}">${c.name}</a></li>`)
      .join('');
    if (desktopList) desktopList.innerHTML = items;
    if (mobileList) mobileList.innerHTML = items;
  } catch (_err) {
    // sin categorías todavía, o falló la carga: el header se queda sin esa lista
  }
}

// Menú de clases en escritorio (ver .nav-classes-menu en components.css):
// botón con icono de menú + "Clases" que despliega un panel flotante,
// distinto del panel de menú móvil de abajo. Se cierra al hacer clic
// afuera, con Escape, o al elegir una clase.
function initNavClassesToggle() {
  const toggle = document.getElementById('navClassesToggle');
  const dropdown = document.getElementById('navClasses');
  if (!toggle || !dropdown) return;

  function close() {
    dropdown.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  function open() {
    dropdown.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  toggle.addEventListener('click', (event) => {
    event.stopPropagation();
    if (dropdown.classList.contains('is-open')) close();
    else open();
  });
  dropdown.addEventListener('click', (event) => {
    if (event.target.closest('a')) close();
  });
  document.addEventListener('click', (event) => {
    if (!dropdown.classList.contains('is-open')) return;
    if (dropdown.contains(event.target) || toggle.contains(event.target)) return;
    close();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') close();
  });
}

// Fricción básica contra copiar/descargar fotos: sin menú de clic derecho
// ("Guardar imagen como", "Copiar imagen") sobre ninguna <img> de la
// tienda pública. Este archivo no lo carga admin.html, así que el panel
// nunca queda afectado. No es protección real -- cualquiera puede tomar
// una captura de pantalla igual -- solo desalienta al visitante casual.
function initImageProtection() {
  document.addEventListener('contextmenu', (event) => {
    if (event.target.tagName === 'IMG') event.preventDefault();
  });
}

function initNavSearch() {
  document.querySelectorAll('.nav-search').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const query = new FormData(form).get('q');
      const params = query ? `?search=${encodeURIComponent(query)}` : '';
      window.location.href = `/catalogo.html${params}`;
    });
  });
}

// Header que se esconde al bajar y vuelve a aparecer apenas se sube (ver
// .nav.nav-hidden en components.css), en todas las páginas menos home:
// home tiene su propio header flotante/transparente sobre el hero (ver
// body.home-transparent-nav) y no participa de esto. Compara contra el
// último scroll conocido en vez de un umbral fijo desde arriba, así que
// "subir un poco" lo trae de vuelta sin necesidad de volver al tope de la
// página; DELTA descarta el micro-scroll (rebote táctil en iOS, etc.) para
// que no parpadee.
function initNavHideOnScroll() {
  if (document.body.classList.contains('home-transparent-nav')) return;
  const nav = document.querySelector('header.nav');
  if (!nav) return;
  const mobilePanel = document.getElementById('navMobilePanel');
  const classesDropdown = document.getElementById('navClasses');
  const DELTA = 8;
  let lastY = window.scrollY;
  let ticking = false;
  function update() {
    // no esconder el header con el menú móvil o el desplegable de clases
    // abierto: viven dentro de header.nav, así que se irían con él.
    if (mobilePanel?.classList.contains('is-open') || classesDropdown?.classList.contains('is-open')) {
      ticking = false;
      return;
    }
    const y = Math.max(window.scrollY, 0);
    const diff = y - lastY;
    if (Math.abs(diff) > DELTA) {
      if (diff > 0 && y > nav.offsetHeight) nav.classList.add('nav-hidden');
      else nav.classList.remove('nav-hidden');
      lastY = y;
    }
    ticking = false;
  }
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    },
    { passive: true }
  );
}

// Los breadcrumbs "← Volver a…" (producto.html, checkout.html) linkeaban
// siempre al mismo destino fijo (catálogo / carrito), así que entrar a un
// producto desde el inicio y darle "atrás" mandaba al catálogo en vez de al
// inicio, que era de donde el visitante venía. Si el referrer es de la
// misma tienda y hay historial de navegación, el breadcrumb usa
// history.back() (vuelve a la página real anterior); si no —enlace externo,
// pestaña nueva, o llegó por marcador— cae al href fijo de siempre.
function initSmartBackLinks() {
  const sameOriginReferrer = document.referrer && new URL(document.referrer, window.location.href).origin === window.location.origin;
  if (!sameOriginReferrer || window.history.length <= 1) return;
  document.querySelectorAll('[data-smart-back]').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      window.history.back();
    });
  });
}

initMobileNavToggle();
initNavClasses();
initNavClassesToggle();
initNavSearch();
initNavScrollState();
initNavHideOnScroll();
initSmartBackLinks();
initImageProtection();

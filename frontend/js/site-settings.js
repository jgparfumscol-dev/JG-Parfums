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
    display: "'Bodoni Moda', 'Didot', Georgia, serif",
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
}

applySiteBranding();

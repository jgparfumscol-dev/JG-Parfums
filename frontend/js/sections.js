/* Renderiza las secciones de contenido administrables (anuncios, banners,
   encabezados, grillas de producto, texto, categorías, imágenes, footer,
   testimonios, contadores, HTML/CSS libre) que el panel admin agrega a cada
   página. Un solo script para todas las páginas: agregar/quitar/reordenar
   secciones no requiere tocar el HTML de cada página, solo el contenido en
   la base de datos. */

/* --- Barra de anuncios (announcement_bar) ---
   El backend ya filtró `content.messages` a solo los vigentes (activos y
   dentro de fecha, ver _message_is_live en routes/page_sections.py) — acá
   solo queda decidir cómo mostrarlos: con un mensaje no hay rotación ni
   controles; con varios, rota con pausa/reproducir (o flechas manuales si
   el usuario prefiere menos movimiento) y se puede cerrar si el admin lo
   marcó como cerrable.

   El texto se arma con textContent en initAnnouncementBar, nunca
   interpolado en el string de HTML: es contenido que escribió el admin,
   no confiamos en que nunca traiga un `<` suelto. */
function renderAnnouncementBar(section) {
  const c = section.content || {};
  const messages = c.messages || [];
  if (messages.length === 0) return '';

  const variant = ['onyx', 'paper', 'gold-soft'].includes(c.variant) ? c.variant : 'onyx';
  const transition = c.transition === 'slide' ? 'slide' : 'fade';
  const interval = Math.min(10, Math.max(3, Number(c.rotation_interval) || 5));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const canRotate = messages.length > 1;

  const slides = messages
    .map((_, i) => `<div class="announcement-bar-slide" data-slide data-index="${i}"${i === 0 ? '' : ' hidden'}></div>`)
    .join('');

  const controls = [];
  if (canRotate && !reduceMotion) {
    controls.push(
      `<button type="button" class="announcement-bar-btn" data-pause aria-label="Pausar anuncios" aria-pressed="false">${ICON_PAUSE}</button>`
    );
  } else if (canRotate && reduceMotion) {
    controls.push(
      `<button type="button" class="announcement-bar-btn" data-prev aria-label="Anuncio anterior">${ICON_PREV}</button>`,
      `<button type="button" class="announcement-bar-btn" data-next aria-label="Siguiente anuncio">${ICON_NEXT}</button>`
    );
  }
  if (c.closable) {
    controls.push(`<button type="button" class="announcement-bar-btn" data-close aria-label="Cerrar anuncios">${ICON_CLOSE}</button>`);
  }

  return `
    <aside class="announcement-bar announcement-bar--${variant}" aria-label="Anuncios" data-section-id="${section.id}" data-transition="${transition}" data-interval="${interval}" data-can-rotate="${canRotate && !reduceMotion}">
      <div class="announcement-bar-inner">
        <div class="announcement-bar-viewport" data-viewport aria-live="off">${slides}</div>
        ${controls.length ? `<div class="announcement-bar-controls">${controls.join('')}</div>` : ''}
      </div>
    </aside>
  `;
}

const ICON_PAUSE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14"/><rect x="14" y="5" width="4" height="14"/></svg>';
const ICON_PLAY = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4l13 8-13 8z"/></svg>';
const ICON_PREV = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="15 6 9 12 15 18"/></svg>';
const ICON_NEXT = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="9 6 15 12 9 18"/></svg>';
const ICON_CLOSE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="5" y1="5" x2="19" y2="19"/><line x1="19" y1="5" x2="5" y2="19"/></svg>';

// Hash simple (no criptográfico, no hace falta) del contenido — la clave de
// localStorage lo incluye para que si el admin cambia los mensajes, la
// barra que el visitante ya había cerrado vuelva a aparecer.
function announcementContentHash(content) {
  const raw = JSON.stringify(content || {});
  let hash = 0;
  for (let i = 0; i < raw.length; i += 1) {
    hash = (Math.imul(31, hash) + raw.charCodeAt(i)) | 0;
  }
  return (hash >>> 0).toString(36);
}

// Arma "[destacado en negrita] texto", siempre con textContent — nunca se
// concatena contenido del admin dentro de un string de HTML.
function buildAnnouncementMessageNode(message) {
  const wrap = message.link_url ? document.createElement('a') : document.createElement('span');
  if (message.link_url) {
    wrap.href = message.link_url;
    if (/^https?:\/\//i.test(message.link_url)) {
      wrap.target = '_blank';
      wrap.rel = 'noopener';
    }
  }
  if (message.highlight) {
    const strong = document.createElement('strong');
    strong.textContent = message.highlight;
    wrap.appendChild(strong);
    wrap.appendChild(document.createTextNode(' '));
  }
  wrap.appendChild(document.createTextNode(message.text || ''));
  return wrap;
}

function initAnnouncementBar(el, section) {
  if (!el) return;
  const messages = (section.content && section.content.messages) || [];
  if (messages.length === 0) return;

  // Cerrar se recuerda en localStorage; el acceso va en try/catch porque
  // puede fallar (modo privado, storage bloqueado) sin que eso rompa la
  // barra — simplemente no persiste el cierre entre visitas.
  const storageKey = `jg_announcement_closed_${section.id}_${announcementContentHash(section.content)}`;
  try {
    if (localStorage.getItem(storageKey) === '1') {
      el.hidden = true;
      return;
    }
  } catch (_err) {
    // sin storage disponible: la barra igual funciona, solo no recuerda el cierre
  }

  // Reserva la altura animando desde 0 en vez de aparecer de golpe (evita
  // que se sienta como un salto de layout aunque el contenido llegue
  // después del primer render — ver reveal.js para el mismo criterio).
  el.style.overflow = 'hidden';
  el.style.maxHeight = '0px';
  el.style.transition = 'max-height 260ms ease';

  el.querySelectorAll('[data-slide]').forEach((slide, i) => {
    if (messages[i]) slide.appendChild(buildAnnouncementMessageNode(messages[i]));
  });

  requestAnimationFrame(() => {
    el.style.maxHeight = `${el.scrollHeight}px`;
  });
  el.addEventListener(
    'transitionend',
    () => {
      el.style.maxHeight = '';
      el.style.overflow = '';
    },
    { once: true }
  );

  const closeBtn = el.querySelector('[data-close]');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      el.hidden = true;
      try {
        localStorage.setItem(storageKey, '1');
      } catch (_err) {
        // sin storage: el cierre solo dura esta visita
      }
    });
  }

  if (messages.length <= 1) return;

  const viewport = el.querySelector('[data-viewport]');
  const slides = Array.from(el.querySelectorAll('[data-slide]'));
  const transition = el.dataset.transition;
  let current = 0;

  function show(index, { announce = false } = {}) {
    const next = (index + slides.length) % slides.length;
    if (next === current) return;
    slides[current].classList.remove('is-leaving');
    slides[current].hidden = true;
    current = next;
    slides[current].hidden = false;
    slides[current].classList.add(transition === 'slide' ? 'is-entering-slide' : 'is-entering-fade');
    viewport.setAttribute('aria-live', announce ? 'polite' : 'off');
  }

  const prevBtn = el.querySelector('[data-prev]');
  const nextBtn = el.querySelector('[data-next]');
  if (prevBtn) prevBtn.addEventListener('click', () => show(current - 1, { announce: true }));
  if (nextBtn) nextBtn.addEventListener('click', () => show(current + 1, { announce: true }));

  if (el.dataset.canRotate !== 'true') return; // reduced motion: solo flechas, sin autoplay

  const intervalMs = Number(el.dataset.interval) * 1000;
  let timer = null;
  let userPaused = false;

  function tick() {
    show(current + 1);
  }
  function start() {
    stop();
    if (userPaused || document.hidden) return;
    timer = setInterval(tick, intervalMs);
  }
  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  start();
  el.addEventListener('mouseenter', stop);
  el.addEventListener('mouseleave', start);
  el.addEventListener('focusin', stop);
  el.addEventListener('focusout', start);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else start();
  });

  const pauseBtn = el.querySelector('[data-pause]');
  if (pauseBtn) {
    pauseBtn.addEventListener('click', () => {
      userPaused = !userPaused;
      pauseBtn.setAttribute('aria-pressed', String(userPaused));
      pauseBtn.setAttribute('aria-label', userPaused ? 'Reanudar anuncios' : 'Pausar anuncios');
      pauseBtn.innerHTML = userPaused ? ICON_PLAY : ICON_PAUSE;
      if (userPaused) stop();
      else start();
    });
  }
}

// Color de texto legible sobre el color de botón que elija el admin —
// mismo criterio de luminancia relativa que usa applyAccentColor en
// site-settings.js para no depender de que el admin acierte el contraste.
function contrastTextColor(hex) {
  const h = /^#[0-9A-Fa-f]{6}$/.test(hex || '') ? hex.slice(1) : null;
  if (!h) return '#FFFFFF';
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? '#201E1F' : '#FFFFFF';
}

function renderBanner(section) {
  const c = section.content || {};
  const bgStyle = c.image_url ? ` style="background-image:url('${c.image_url}')"` : '';
  const ctaStyle = c.cta_color
    ? ` style="background-color:${c.cta_color}; border-color:${c.cta_color}; color:${contrastTextColor(c.cta_color)};"`
    : '';
  return `
    <section class="section pgs-banner"${bgStyle}>
      <div class="container pgs-banner-inner">
        ${c.title ? `<h2 class="h2 pgs-banner-title">${c.title}</h2>` : ''}
        ${c.subtitle ? `<p class="pgs-banner-subtitle">${c.subtitle}</p>` : ''}
        ${c.link_url ? `<a class="btn btn-onDark"${ctaStyle} href="${c.link_url}">${c.cta_label || 'Ver más'}</a>` : ''}
      </div>
    </section>
  `;
}

function renderHeader(section) {
  const c = section.content || {};
  if (!c.title) return '';
  return `
    <section class="section">
      <div class="container" style="text-align:center;">
        <h2 class="h2 section-title">${c.title}</h2>
        ${c.subtitle ? `<p class="text-muted" style="max-width:520px; margin-inline:auto;">${c.subtitle}</p>` : ''}
      </div>
    </section>
  `;
}

async function renderProducts(section) {
  const c = section.content || {};
  const params = new URLSearchParams({ page_size: String(c.limit || 8) });
  if (c.category_id) params.set('category_id', c.category_id);
  try {
    const data = await apiFetch(`/products?${params.toString()}`);
    if (data.items.length === 0) return '';
    return `
      <section class="section">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          <div class="product-grid">
            ${data.items.map((p) => `
              <a class="product-card" href="/producto.html?slug=${encodeURIComponent(p.slug)}">
                <div class="product-card-media">
                  ${p.images[0] ? `<img src="${p.images[0].url}" alt="${p.images[0].alt_text}" loading="lazy">` : ''}
                </div>
                <div class="product-card-body">
                  <p class="product-card-name">${p.name}</p>
                  <p class="product-card-meta">${p.house ? `${p.house} · ` : ''}${p.size_ml} ml</p>
                  <p class="product-card-price">${formatCOP(p.price)}</p>
                </div>
              </a>
            `).join('')}
          </div>
        </div>
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

function renderText(section) {
  const c = section.content || {};
  if (!c.body) return '';
  const paragraphs = c.body.split('\n').filter((p) => p.trim()).map((p) => `<p class="text-muted" style="max-width:68ch;">${p}</p>`).join('');
  return `
    <section class="section">
      <div class="container">
        ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
        ${paragraphs}
      </div>
    </section>
  `;
}

async function renderCategories(section) {
  const c = section.content || {};
  try {
    const categories = await apiFetch('/categories');
    if (categories.length === 0) return '';
    return `
      <section class="section">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          <div class="pgs-categories">
            ${categories.map((cat) => `<a class="pgs-category-chip" href="/catalogo.html">${cat.name}</a>`).join('')}
          </div>
        </div>
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

function renderImage(section) {
  const c = section.content || {};
  if (!c.image_url) return '';
  const img = `<img src="${c.image_url}" alt="${c.alt_text || ''}" loading="lazy" style="width:100%; display:block;">`;
  return `
    <section class="section">
      <div class="container">
        ${c.link_url ? `<a href="${c.link_url}">${img}</a>` : img}
        ${c.caption ? `<p class="text-muted text-small" style="margin-top:var(--space-2);">${c.caption}</p>` : ''}
      </div>
    </section>
  `;
}

function renderTestimonials(section) {
  const items = (section.content && section.content.items) || [];
  if (items.length === 0) return '';
  return `
    <section class="section">
      <div class="container">
        <div class="pgs-testimonials">
          ${items.map((t) => `
            <div class="pgs-testimonial-card">
              <p class="pgs-testimonial-text">&ldquo;${t.text || ''}&rdquo;</p>
              <div class="pgs-testimonial-author">
                ${t.photo_url ? `<img src="${t.photo_url}" alt="">` : ''}
                <div>
                  <p class="pgs-testimonial-name">${t.author_name || ''}</p>
                  ${t.author_detail ? `<p class="pgs-testimonial-detail">${t.author_detail}</p>` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </section>
  `;
}

function renderCounters(section) {
  const items = (section.content && section.content.items) || [];
  if (items.length === 0) return '';
  return `
    <section class="section">
      <div class="container pgs-counters">
        ${items.map((i) => `
          <div class="pgs-counter">
            <p class="pgs-counter-value">${i.value || ''}</p>
            <p class="pgs-counter-label">${i.label || ''}</p>
          </div>
        `).join('')}
      </div>
    </section>
  `;
}

function renderFooterBlock(section) {
  const c = section.content || {};
  if (!c.heading) return '';
  return `
    <section class="section" style="background:var(--jg-onyx); color:#FFFFFF; text-align:center;">
      <div class="container">
        <h2 class="h2" style="color:#FFFFFF;">${c.heading}</h2>
        ${c.text ? `<p style="color:#B9B4B0; max-width:520px; margin-inline:auto;">${c.text}</p>` : ''}
        ${c.cta_link ? `<a class="btn btn-onDark" href="${c.cta_link}" style="margin-top:var(--space-6); display:inline-flex;">${c.cta_label || 'Ver más'}</a>` : ''}
      </div>
    </section>
  `;
}

function renderCustomHtml(section) {
  const c = section.content || {};
  return `${c.css ? `<style>${c.css}</style>` : ''}${c.html || ''}`;
}

/* --- Secciones "fijas" de la página, convertidas en editables ---
   A diferencia de las de arriba, no se agregan libremente: cada una tiene
   una `key` fija y un `<div id="pgs-{key}">` ya puesto en el HTML de la
   página, en el lugar exacto donde vivía el contenido hardcodeado que
   reemplaza. Si la sección está inactiva o fue borrada, ese div
   simplemente queda vacío — no hay contenido de respaldo hardcodeado. */

function renderSectionHeading(section) {
  const c = section.content || {};
  if (!c.heading) return '';
  if (section.key === 'catalogo_header') return `<h1 class="h1">${c.heading}</h1>`;
  return `<h2 class="h2 section-title">${c.heading}</h2>`;
}

function renderDecantCallout(section) {
  const c = section.content || {};
  if (!c.heading) return '';
  const rows = (c.rows || [])
    .map((r) => `<div class="spec-row"><dt>${r.label || ''}</dt><dd>${r.value || ''}</dd></div>`)
    .join('');
  return `
    <div>
      <h2 class="h2 section-title">${c.heading}</h2>
      ${c.body ? `<p class="text-muted" style="max-width:46ch; margin-bottom: var(--space-4);">${c.body}</p>` : ''}
      ${c.cta_link ? `<a class="link" href="${c.cta_link}">${c.cta_label || 'Ver más'}</a>` : ''}
    </div>
    <dl class="spec-list">${rows}</dl>
  `;
}

function renderManifesto(section) {
  const items = (section.content && section.content.items) || [];
  if (items.length === 0) return '';
  return items
    .map(
      (item, i) => `
        <div class="manifesto-item">
          <span class="manifesto-mark">${String(i + 1).padStart(2, '0')}</span>
          <p class="manifesto-heading">${item.heading || ''}</p>
          <p class="text-muted text-small">${item.text || ''}</p>
        </div>
      `
    )
    .join('');
}

const SECTION_RENDERERS = {
  announcement_bar: renderAnnouncementBar,
  banner: renderBanner,
  header: renderHeader,
  products: renderProducts,
  text: renderText,
  categories: renderCategories,
  image: renderImage,
  testimonials: renderTestimonials,
  counters: renderCounters,
  footer: renderFooterBlock,
  custom_html: renderCustomHtml,
  section_heading: renderSectionHeading,
  decant_callout: renderDecantCallout,
  manifesto: renderManifesto,
};

async function renderPageSections(pageKey, mountId = 'dynamicSections') {
  const mount = document.getElementById(mountId);
  const topBarMount = document.getElementById('pgs-announcement-bar');
  try {
    const sections = await apiFetch(`/page-sections?page=${encodeURIComponent(pageKey)}`);
    const freeform = [];
    // "top": una sola por página, se monta antes del header (ver
    // #pgs-announcement-bar en cada <body>) en vez de en el flujo normal de
    // secciones — el backend ya garantiza que como mucho una esté activa.
    let topBar = null;
    for (const section of sections) {
      if (!section.key) {
        if (section.type === 'announcement_bar' && (section.content || {}).position === 'top') {
          topBar = topBar || section;
        } else {
          freeform.push(section);
        }
        continue;
      }
      // Sección fija: se monta en su propio lugar, no en el mount genérico.
      const target = document.getElementById(`pgs-${section.key}`);
      if (!target) continue;
      const renderer = SECTION_RENDERERS[section.type];
      target.innerHTML = renderer ? await renderer(section) : '';
    }
    if (topBarMount) {
      topBarMount.innerHTML = topBar ? renderAnnouncementBar(topBar) : '';
      if (topBar) initAnnouncementBar(topBarMount.querySelector('.announcement-bar'), topBar);
    }
    if (mount) {
      const rendered = await Promise.all(
        freeform.map((s) => (SECTION_RENDERERS[s.type] ? SECTION_RENDERERS[s.type](s) : ''))
      );
      mount.innerHTML = rendered.join('');
      mount.querySelectorAll('.announcement-bar[data-section-id]').forEach((el) => {
        const section = freeform.find((s) => String(s.id) === el.dataset.sectionId);
        if (section) initAnnouncementBar(el, section);
      });
    }
  } catch (_err) {
    // Si falla, la página sigue funcionando igual sin las secciones extra.
  }
}

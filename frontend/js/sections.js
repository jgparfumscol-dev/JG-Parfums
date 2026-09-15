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
   controles; con varios, rota sola (fundido o deslizamiento horizontal) y
   se puede cerrar si el admin lo marcó como cerrable.

   Sin botón de pausa a propósito — se pausa igual, solo que sin un ícono
   visible: al pasar el mouse, al enfocar por teclado y cuando la pestaña
   no está visible (ver initAnnouncementBar). Con prefers-reduced-motion no
   hay autoplay en absoluto y aparecen flechas manuales en su lugar, así
   que la rotación siempre queda controlable de alguna forma.

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
  if (canRotate && reduceMotion) {
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

  // dir 1 = entra desde la derecha (avanzando), -1 = entra desde la
  // izquierda (retrocediendo) — solo importa para el deslizamiento
  // horizontal, el fundido lo ignora.
  function show(index, { announce = false, dir = 1 } = {}) {
    const next = (index + slides.length) % slides.length;
    if (next === current) return;
    slides[current].hidden = true;
    current = next;
    const entering = slides[current];
    entering.hidden = false;
    if (transition === 'slide') {
      entering.style.setProperty('--slide-dir', String(dir));
      entering.classList.add('is-entering-slide');
      entering.addEventListener('animationend', () => entering.classList.remove('is-entering-slide'), { once: true });
    } else {
      entering.classList.add('is-entering-fade');
      entering.addEventListener('animationend', () => entering.classList.remove('is-entering-fade'), { once: true });
    }
    viewport.setAttribute('aria-live', announce ? 'polite' : 'off');
  }

  const prevBtn = el.querySelector('[data-prev]');
  const nextBtn = el.querySelector('[data-next]');
  if (prevBtn) prevBtn.addEventListener('click', () => show(current - 1, { announce: true, dir: -1 }));
  if (nextBtn) nextBtn.addEventListener('click', () => show(current + 1, { announce: true, dir: 1 }));

  if (el.dataset.canRotate !== 'true') return; // reduced motion: solo flechas, sin autoplay

  const intervalMs = Number(el.dataset.interval) * 1000;
  let timer = null;

  function tick() {
    show(current + 1, { dir: 1 });
  }
  function start() {
    stop();
    if (document.hidden) return;
    timer = setInterval(tick, intervalMs);
  }
  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  // Sin botón de pausa visible: se pausa solo al interactuar (mouse,
  // teclado) o cuando la pestaña no está visible — cumple con "pausar,
  // detener u ocultar" sin un ícono permanente en la barra.
  start();
  el.addEventListener('mouseenter', stop);
  el.addEventListener('mouseleave', start);
  el.addEventListener('focusin', stop);
  el.addEventListener('focusout', start);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else start();
  });
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

// Imagen de fondo por tamaño: el CSS decide cuál usar según el ancho de
// pantalla (ver --pgs-banner-bg-mobile/-desktop en components.css) — si el
// admin solo carga una, esa se usa en los dos tamaños.
function renderBanner(section) {
  const c = section.content || {};
  const bgVars = [];
  if (c.image_url_mobile) bgVars.push(`--pgs-banner-bg-mobile:url('${c.image_url_mobile}')`);
  if (c.image_url) bgVars.push(`--pgs-banner-bg-desktop:url('${c.image_url}')`);
  const bgStyle = bgVars.length ? ` style="${bgVars.join('; ')}"` : '';
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
   No se agregan libremente desde "+ Añadir sección" — vienen sembradas por
   migración con una `key` fija — pero se editan, ocultan y ahora también
   se reordenan igual que cualquier sección libre (ver renderPageSections).

   catalogo_header y producto_related_heading siguen ancladas a un
   `<div id="pgs-{key}">` puesto a propósito en medio de otro elemento de
   la página (la barra de filtros, la grilla de relacionados) — moverlas
   no tendría sentido, así que se quedan bare (sin su propio <section>) y
   con mount fijo. home_decant_callout y home_manifesto, en cambio, ya no
   tienen mount fijo en el HTML: se arman su propio <section> acá mismo y
   entran al flujo general de secciones, junto con banner/testimonios/etc. */

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
    <section class="section" style="background: var(--jg-white);">
      <div class="container decant-callout">
        <div>
          <h2 class="h2 section-title">${c.heading}</h2>
          ${c.body ? `<p class="text-muted" style="max-width:46ch; margin-bottom: var(--space-4);">${c.body}</p>` : ''}
          ${c.cta_link ? `<a class="link" href="${c.cta_link}">${c.cta_label || 'Ver más'}</a>` : ''}
        </div>
        <dl class="spec-list">${rows}</dl>
      </div>
    </section>
  `;
}

function renderManifesto(section) {
  const items = (section.content && section.content.items) || [];
  if (items.length === 0) return '';
  const cols = items
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
  return `
    <section class="section" style="background: var(--jg-white);">
      <div class="container manifesto-strip">${cols}</div>
    </section>
  `;
}

// Ficha del perfume destacado (hero de inicio): el texto acá es el
// respaldo — home.html pisa heroHouse/heroName/heroDesc/heroCta/heroTiers
// con datos del producto real apenas cargan (ver loadFeatured() en
// index.html), pero antes de que eso pase, o si no hay ningún producto
// todavía, se queda con lo que el admin haya puesto acá. Nombre distinto
// de renderHeroProduct(product) de index.html a propósito — son funciones
// distintas que conviven en el mismo scope global.
function renderHeroProductSection(section) {
  const c = section.content || {};
  return `
    <section class="section section-dark">
      <div class="container hero-spec-layout">
        <div class="hero-spec-copy">
          <p class="hero-spec-house text-small" id="heroHouse">${c.eyebrow || ''}</p>
          <h1 class="display" id="heroName">${c.heading || ''}</h1>
          <p class="hero-spec-desc" id="heroDesc">${c.description || ''}</p>
          <a class="btn btn-onDark" id="heroCta" href="${c.cta_link || '/catalogo.html'}">${c.cta_label || 'Ver catálogo'}</a>
        </div>
        <div class="scent-diagram">
          <p class="scent-diagram-heading">${c.diagram_heading || ''}</p>
          <div id="heroTiers"></div>
        </div>
      </div>
    </section>
  `;
}

const SECTION_RENDERERS = {
  hero_product: renderHeroProductSection,
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
      // Sección fija con mount propio en el HTML (catalogo_header,
      // producto_related_heading): se monta ahí, no en el flujo general.
      // Si no hay mount para su key en esta página (ej. home_decant_callout
      // / home_manifesto, que ya arman su propio <section>), se trata como
      // cualquier sección libre y entra al orden general por posición.
      const target = document.getElementById(`pgs-${section.key}`);
      if (target) {
        const renderer = SECTION_RENDERERS[section.type];
        target.innerHTML = renderer ? await renderer(section) : '';
      } else {
        freeform.push(section);
      }
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

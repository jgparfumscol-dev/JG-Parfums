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
  const slideDirection = c.slide_direction === 'left' ? 'left' : 'right';
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
    <aside class="announcement-bar announcement-bar--${variant}" aria-label="Anuncios" data-section-id="${section.id}" data-transition="${transition}" data-slide-direction="${slideDirection}" data-interval="${interval}" data-can-rotate="${canRotate && !reduceMotion}">
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

// Hash simple (no criptográfico, no hace falta) del contenido de una
// sección — usado en la clave de storage de cualquier widget que recuerde
// haber sido cerrado (barra de anuncios, popup de promo), para que si el
// admin cambia el contenido, lo que el visitante ya había cerrado vuelva a
// aparecer.
function contentHash(content) {
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
  const storageKey = `jg_announcement_closed_${section.id}_${contentHash(section.content)}`;
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
  const n = slides.length;
  const transition = el.dataset.transition;
  // 'right' = el mensaje siguiente entra desde la derecha (empuja el actual
  // hacia la izquierda); 'left' = al revés. Ver el mismo cálculo de "camino
  // más corto" que usa el banner (renderBanner/initBanner) para que la
  // vuelta del último mensaje al primero también entre por el lado que
  // corresponde, sin arrastrarse por los del medio.
  const baseDir = el.dataset.slideDirection === 'left' ? -1 : 1;
  let current = 0;

  // Todas las diapositivas quedan apiladas (position:absolute) — hace
  // falta un alto fijo en el viewport para que no colapse a 0 (algunos
  // mensajes ocupan 1 línea, otros 2). Se mide una sola vez con el
  // contenido ya armado, y de nuevo si la ventana cambia de tamaño (el
  // quiebre a 2 líneas depende del ancho disponible).
  function syncHeight() {
    let max = 0;
    slides.forEach((slide) => {
      slide.hidden = false;
      max = Math.max(max, slide.scrollHeight);
    });
    slides.forEach((slide, i) => { slide.hidden = i !== current; });
    viewport.style.height = `${max}px`;
  }

  function layout(instant) {
    slides.forEach((slide, i) => {
      slide.hidden = false;
      let rel = i - current;
      if (rel > n / 2) rel -= n;
      if (rel < -n / 2) rel += n;
      const isCurrent = i === current;
      if (instant) slide.style.transition = 'none';
      if (transition === 'slide') {
        slide.style.transform = `translateX(${rel * baseDir * 100}%)`;
      } else {
        slide.style.opacity = isCurrent ? '1' : '0';
      }
      if (instant) {
        void slide.offsetWidth; // fuerza reflow: el próximo cambio sí anima
        slide.style.transition = '';
      }
      slide.setAttribute('aria-hidden', isCurrent ? 'false' : 'true');
      const link = slide.querySelector('a');
      if (link) link.tabIndex = isCurrent ? 0 : -1;
    });
  }

  syncHeight();
  layout(true);
  window.addEventListener('resize', syncHeight);

  function show(index, { announce = false } = {}) {
    const next = ((index % n) + n) % n;
    if (next === current) return;
    current = next;
    layout(false);
    viewport.setAttribute('aria-live', announce ? 'polite' : 'off');
  }

  const prevBtn = el.querySelector('[data-prev]');
  const nextBtn = el.querySelector('[data-next]');
  if (prevBtn) prevBtn.addEventListener('click', () => show(current - 1, { announce: true }));
  if (nextBtn) nextBtn.addEventListener('click', () => show(current + 1, { announce: true }));

  if (el.dataset.canRotate !== 'true') return; // reduced motion: solo flechas, sin autoplay

  const intervalMs = Number(el.dataset.interval) * 1000;
  let timer = null;

  function tick() {
    show(current + 1);
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

// Banner con una o varias fotos ("slides"). Compatible con el shape viejo
// (un solo objeto plano con image_url/title/etc, sin `slides`): se trata
// como un array de un solo elemento, así que ningún banner ya guardado se
// rompe — el admin lo "actualiza" al nuevo shape la próxima vez que lo
// edite y guarde desde el panel.
function renderBannerSlide(slide, index, isFirst) {
  const s = slide || {};
  const mainImg = s.image_url || s.image_url_mobile;
  const blur = Math.max(0, Math.min(20, Number(s.blur) || 0));
  const imgStyle = blur > 0 ? ` style="filter: blur(${blur}px); transform: scale(1.1);"` : '';
  const pictureHtml = mainImg
    ? `
      <picture>
        ${s.image_url_mobile ? `<source media="(max-width: 767px)" srcset="${s.image_url_mobile}">` : ''}
        <img class="pgs-banner-media" src="${mainImg}" alt="${s.title || ''}"${imgStyle}>
      </picture>
    `
    : '';
  const ctaStyle = s.cta_color
    ? ` style="background-color:${s.cta_color}; border-color:${s.cta_color}; color:${contrastTextColor(s.cta_color)};"`
    : '';
  // overlay_opacity: 0-100 (%), oscurece la foto para que el texto resalte —
  // ajustable por el admin en vez del alpha fijo que había antes.
  const overlayOpacity = Math.max(0, Math.min(100, s.overlay_opacity == null ? 45 : Number(s.overlay_opacity))) / 100;
  const position = ['left', 'center', 'right'].includes(s.text_position) ? s.text_position : 'left';
  const justify = { left: 'flex-start', center: 'center', right: 'flex-end' }[position];
  return `
    <div class="pgs-banner-slide" data-slide data-index="${index}" aria-hidden="${isFirst ? 'false' : 'true'}">
      ${pictureHtml}
      <div class="pgs-banner-scrim" style="background-color: rgba(32, 30, 31, ${overlayOpacity});"></div>
      <div class="pgs-banner-inner" style="justify-content: ${justify};">
        <div class="pgs-banner-copy" style="text-align: ${position};">
          ${s.title ? `<h2 class="h2 pgs-banner-title">${s.title}</h2>` : ''}
          ${s.subtitle ? `<p class="pgs-banner-subtitle">${s.subtitle}</p>` : ''}
          ${s.link_url ? `<a class="btn btn-onDark"${ctaStyle} href="${s.link_url}">${s.cta_label || 'Ver más'}</a>` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderBanner(section) {
  const c = section.content || {};
  const slides = (c.slides && c.slides.length ? c.slides : [c]).filter(
    (s) => s && (s.image_url || s.image_url_mobile || s.title || s.subtitle)
  );
  if (slides.length === 0) return '';
  const interval = Math.max(2, Number(c.rotation_interval) || 5);
  const slidesHtml = slides.map((s, i) => renderBannerSlide(s, i, i === 0)).join('');
  const dotsHtml =
    slides.length > 1
      ? `<div class="pgs-banner-dots">${slides
          .map((_, i) => `<button type="button" class="pgs-banner-dot${i === 0 ? ' is-active' : ''}" data-dot="${i}" aria-label="Ir a la foto ${i + 1}"></button>`)
          .join('')}</div>`
      : '';
  const arrowsHtml =
    slides.length > 1
      ? `
        <button type="button" class="pgs-banner-arrow pgs-banner-arrow-prev" data-prev aria-label="Foto anterior">${ICON_PREV}</button>
        <button type="button" class="pgs-banner-arrow pgs-banner-arrow-next" data-next aria-label="Foto siguiente">${ICON_NEXT}</button>
      `
      : '';
  return `
    <section class="section pgs-banner" data-section-id="${section.id}" data-interval="${interval}">
      ${slidesHtml}
      ${arrowsHtml}
      ${dotsHtml}
    </section>
  `;
}

// Misma lógica de rotación que la barra de anuncios (ver
// initAnnouncementBar): pausa al pasar el mouse/enfocar/pestaña oculta, sin
// botón de pausa visible, y sin autoplay si se prefiere menos movimiento
// (ahí los puntos siguen sirviendo para navegar a mano).
function initBanner(el) {
  const slides = Array.from(el.querySelectorAll('[data-slide]'));
  const n = slides.length;
  if (n <= 1) return;
  let current = 0;

  // Todas las fotos están apiladas (position:absolute) y se reposicionan
  // con transform en vez de aparecer de golpe. Siempre toma el camino más
  // corto del círculo (pos > n/2 se reposiciona al otro lado) para que la
  // vuelta de la última foto a la primera también entre suave y por el
  // lado que corresponde, sin arrastrarse por todas las de en medio.
  function layout(instant) {
    slides.forEach((slide, i) => {
      let pos = i - current;
      if (pos > n / 2) pos -= n;
      if (pos < -n / 2) pos += n;
      if (instant) slide.style.transition = 'none';
      slide.style.transform = `translateX(${pos * 100}%)`;
      if (instant) {
        void slide.offsetWidth; // fuerza reflow: el próximo cambio sí anima
        slide.style.transition = '';
      }
      slide.setAttribute('aria-hidden', i === current ? 'false' : 'true');
    });
  }
  layout(true);

  function show(index) {
    const next = ((index % n) + n) % n;
    if (next === current) return;
    current = next;
    layout(false);
    el.querySelectorAll('[data-dot]').forEach((dot, i) => dot.classList.toggle('is-active', i === current));
  }

  el.querySelectorAll('[data-dot]').forEach((dot) => {
    dot.addEventListener('click', () => show(Number(dot.dataset.dot)));
  });

  const prevBtn = el.querySelector('[data-prev]');
  const nextBtn = el.querySelector('[data-next]');
  if (prevBtn) prevBtn.addEventListener('click', () => show(current - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => show(current + 1));

  // --- arrastre con el dedo o con el mouse (Pointer Events cubre ambos) ---
  // Sigue el dedo/cursor en vivo (misma pista transform que layout(), con un
  // offset en px encima) y al soltar decide si cambia de foto o vuelve a su
  // lugar, según qué tan lejos se arrastró. Empieza solo si el gesto no
  // arrancó sobre un botón/enlace (flechas, puntos, CTA), para no robarles
  // el clic.
  let dragging = false;
  let dragStartX = 0;
  let dragDeltaX = 0;
  let dragWidth = el.clientWidth || 1;

  function dragLayout(offsetPx) {
    slides.forEach((slide, i) => {
      let pos = i - current;
      if (pos > n / 2) pos -= n;
      if (pos < -n / 2) pos += n;
      slide.style.transition = 'none';
      slide.style.transform = `translateX(calc(${pos * 100}% + ${offsetPx}px))`;
    });
  }

  function onPointerDown(event) {
    if (event.target.closest('a, button')) return;
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    dragging = true;
    dragStartX = event.clientX;
    dragDeltaX = 0;
    dragWidth = el.clientWidth || 1;
    el.setPointerCapture(event.pointerId);
  }
  function onPointerMove(event) {
    if (!dragging) return;
    dragDeltaX = event.clientX - dragStartX;
    dragLayout(dragDeltaX);
  }
  function onPointerUp() {
    if (!dragging) return;
    dragging = false;
    slides.forEach((slide) => { slide.style.transition = ''; });
    const threshold = dragWidth * 0.15;
    if (dragDeltaX <= -threshold) show(current + 1);
    else if (dragDeltaX >= threshold) show(current - 1);
    else layout(false);
  }

  el.addEventListener('pointerdown', onPointerDown);
  el.addEventListener('pointermove', onPointerMove);
  el.addEventListener('pointerup', onPointerUp);
  el.addEventListener('pointercancel', onPointerUp);

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const intervalMs = Number(el.dataset.interval) * 1000;
  let timer = null;

  function tick() {
    show(current + 1);
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

// Sección "products" administrable (+ Añadir sección): además de la
// grilla de siempre, ahora soporta lista compacta en fila o carrusel
// horizontal con flechas — mismo vocabulario que "También te puede
// interesar" de la ficha de producto (ver loadRelated en producto.html),
// ahora reusable en cualquier página. "Productos por fila en móvil" (1-4)
// aplica tanto a grilla (columnas reales, ver [data-cols-mobile] en
// components.css, mismo mecanismo que el catálogo) como a carrusel
// (cuántas tarjetas entran por pantalla, ver --pgs-cards-mobile) — en
// lista no aplica, cada producto ocupa una fila entera.
// Filtros que el enlace del botón de la sección aplicaría en el catálogo
// (?category_id= / ?has_decant=true). La sección los usa para mostrar los
// mismos productos a los que lleva el botón — "solo decants" muestra solo
// perfumes con decant, no todo el catálogo con un botón que filtra aparte.
// Solo cuenta un enlace interno al catálogo: cualquier otra URL no filtra.
function catalogFiltersFromLink(link) {
  if (!link) return {};
  try {
    const url = new URL(link, window.location.origin);
    if (url.origin !== window.location.origin || url.pathname !== '/catalogo.html') return {};
    const filters = {};
    const categoryId = url.searchParams.get('category_id');
    if (/^\d+$/.test(categoryId || '')) filters.category_id = categoryId;
    if (url.searchParams.get('has_decant') === 'true') filters.has_decant = 'true';
    return filters;
  } catch (_err) {
    return {};
  }
}

async function renderProducts(section) {
  const c = section.content || {};
  // Cantidad de productos por separado para móvil/tablet y PC — se decide
  // una sola vez al cargar la página (no reactivo al resize, mismo
  // criterio que el resto de las secciones administrables: la cantidad de
  // tarjetas visibles de un carrusel tampoco cambia en vivo si se
  // redimensiona la ventana). `limit` es el campo viejo, de antes de que
  // esto se separara — sigue de fallback para secciones ya guardadas que
  // todavía no tengan limit_mobile/limit_desktop.
  const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
  const limit = isDesktop ? (c.limit_desktop || c.limit || 8) : (c.limit_mobile || c.limit || 6);
  const params = new URLSearchParams({ page_size: String(limit) });
  if (c.category_id) params.set('category_id', c.category_id);
  // El enlace del botón manda sobre la categoría propia de la sección: si
  // apunta a una clase o a "solo decants", los productos se filtran igual.
  Object.entries(catalogFiltersFromLink(c.cta_link)).forEach(([key, value]) => params.set(key, value));
  try {
    const data = await apiFetch(`/products?${params.toString()}`);
    if (data.items.length === 0) return '';

    const displayMode = ['grid', 'list', 'carousel'].includes(c.display_mode) ? c.display_mode : 'grid';
    const mobileCols = Math.min(4, Math.max(1, Number(c.mobile_columns) || 2));
    const cardsHtml = data.items.map((p) => `
      <a class="product-card" href="/producto.html?slug=${encodeURIComponent(p.slug)}">
        <div class="product-card-media">
          ${p.images[0] ? `<img src="${p.images[0].url}" alt="${p.images[0].alt_text}" loading="lazy">` : ''}
        </div>
        <div class="product-card-body">
          <p class="product-card-name">${p.name}</p>
          <p class="product-card-meta">${p.house ? `${p.house} · ` : ''}${p.size_ml} ml</p>
          <p class="product-card-price">${priceHtml(p.price, p.final_price, p.discount_percent)}</p>
        </div>
      </a>
    `).join('');

    let itemsHtml;
    if (displayMode === 'carousel') {
      itemsHtml = `
        <div class="pgs-products-carousel" data-section-id="${section.id}">
          <div class="pgs-carousel-wrap" style="--pgs-cards-mobile:${mobileCols};">
            <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-prev" data-prev aria-label="Anterior">${ICON_PREV}</button>
            <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-next" data-next aria-label="Siguiente">${ICON_NEXT}</button>
            <div class="pgs-carousel-track" data-track>${cardsHtml}</div>
          </div>
        </div>
      `;
    } else if (displayMode === 'list') {
      itemsHtml = `<div class="product-list">${cardsHtml}</div>`;
    } else {
      itemsHtml = `<div class="product-grid" data-cols-mobile="${mobileCols}" style="--product-grid-cols-mobile:${mobileCols};">${cardsHtml}</div>`;
    }

    return `
      <section class="section">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          ${itemsHtml}
          ${c.cta_link ? `<p class="pgs-products-cta"><a class="btn btn-secondary" href="${c.cta_link}">${c.cta_label || 'Ver todos'}</a></p>` : ''}
        </div>
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

// "Cookies y almacenamiento" → "cookies-y-almacenamiento": ancla para
// enlazar directo a una sección de texto (ej. el aviso de cookies apunta a
// /politicas.html#cookies-y-almacenamiento-en-tu-navegador).
function headingAnchor(text) {
  return String(text || '')
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function renderText(section) {
  const c = section.content || {};
  if (!c.body) return '';
  const paragraphs = c.body.split('\n').filter((p) => p.trim()).map((p) => `<p class="text-muted" style="max-width:68ch;">${p}</p>`).join('');
  const anchor = headingAnchor(c.heading);
  return `
    <section class="section"${anchor ? ` id="${anchor}"` : ''}>
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

/* --- Galería de fotos (gallery) ---
   Una o varias imágenes. Con una sola foto siempre se muestra igual (a
   todo el ancho) sin importar qué modo haya elegido el admin — carrusel o
   comparar no tienen sentido con un solo elemento. El carrusel navega
   manual, con flechas y guiones — sin autoplay no hace falta botón de
   pausa (misma lección que la barra de anuncios: un control que nadie
   pidió ensucia el diseño). El texto/botón opcional se ve superpuesto
   sobre las fotos, con pointer-events recortado para no tapar los
   controles del carrusel que quedan debajo. */

// Una foto de la galería, con su texto/botón opcional encima (distinto del
// overlay de toda la sección, de arriba) — mismos controles que el banner:
// posición del texto, oscurecido y desenfoque por foto. Si hay botón (link
// + cta_label) no se envuelve la foto entera en <a> para no anidar
// enlaces; si hay link_url pero no botón, se mantiene el comportamiento
// de siempre (toda la foto es clicable).
function renderGalleryImageMedia(img) {
  const g = img || {};
  const blur = Math.max(0, Math.min(20, Number(g.blur) || 0));
  // --pgs-gallery-base-scale (no transform directo): así el zoom en hover
  // (que multiplica ese mismo custom property, ver CSS) sigue funcionando
  // encima sin que el estilo inline lo pise — mismo criterio que las
  // tarjetas del carrusel de clases.
  const imgStyle = blur > 0 ? ` style="filter: blur(${blur}px); --pgs-gallery-base-scale: 1.1;"` : '';
  const imgTagHtml = `<img src="${g.url}" alt="${g.alt || ''}" loading="lazy"${imgStyle}>`;

  const hasCta = Boolean(g.link_url && g.cta_label);
  const hasOverlayText = Boolean(g.title || g.subtitle || hasCta);
  const overlayOpacity = Math.max(0, Math.min(100, Number(g.overlay_opacity) || 0)) / 100;
  const position = ['left', 'center', 'right'].includes(g.text_position) ? g.text_position : 'left';
  const justify = { left: 'flex-start', center: 'center', right: 'flex-end' }[position];
  const vPosition = ['top', 'center', 'bottom'].includes(g.text_position_vertical) ? g.text_position_vertical : 'bottom';
  const alignItems = { top: 'flex-start', center: 'center', bottom: 'flex-end' }[vPosition];
  const ctaStyle = g.cta_color
    ? ` style="background-color:${g.cta_color}; border-color:${g.cta_color}; color:${contrastTextColor(g.cta_color)};"`
    : '';
  const overlayHtml = hasOverlayText
    ? `
      <div class="pgs-gallery-img-scrim" style="background-color: rgba(32, 30, 31, ${overlayOpacity});"></div>
      <div class="pgs-gallery-img-inner" style="justify-content: ${justify}; align-items: ${alignItems};">
        <div class="pgs-gallery-img-copy" style="text-align: ${position};">
          ${g.title ? `<h3 class="h3 pgs-gallery-img-title">${g.title}</h3>` : ''}
          ${g.subtitle ? `<p class="pgs-gallery-img-subtitle">${g.subtitle}</p>` : ''}
          ${hasCta ? `<a class="btn btn-onDark"${ctaStyle} href="${g.link_url}">${g.cta_label}</a>` : ''}
        </div>
      </div>
    `
    : '';

  const body = imgTagHtml + overlayHtml;
  const wrapInLink = g.link_url && !hasCta;
  return `<div class="pgs-gallery-img-wrap">${wrapInLink ? `<a href="${g.link_url}">${body}</a>` : body}</div>`;
}

function renderGallery(section) {
  const c = section.content || {};
  const images = (c.images || []).filter((img) => img && img.url);
  if (images.length === 0) return '';

  const layout = images.length === 1 ? 'single' : (['carousel', 'compare'].includes(c.layout) ? c.layout : 'grid');
  const hasOverlay = Boolean(c.heading || c.subtitle || (c.cta_link && c.cta_label));

  let mediaHtml;
  if (layout === 'single') {
    mediaHtml = `<div class="pgs-gallery-single">${renderGalleryImageMedia(images[0])}</div>`;
  } else if (layout === 'carousel') {
    const slides = images
      .map((img, i) => `<div class="pgs-gallery-slide" data-slide data-index="${i}"${i === 0 ? '' : ' hidden'}>${renderGalleryImageMedia(img)}</div>`)
      .join('');
    const dots = images
      .map((_, i) => `<button type="button" class="pgs-gallery-dot${i === 0 ? ' is-active' : ''}" data-dot="${i}" aria-label="Ir a la foto ${i + 1}"></button>`)
      .join('');
    mediaHtml = `
      <div class="pgs-gallery-carousel" data-carousel>
        <div class="pgs-gallery-viewport" data-viewport>${slides}</div>
        <button type="button" class="pgs-gallery-arrow pgs-gallery-arrow-prev" data-prev aria-label="Foto anterior">${ICON_PREV}</button>
        <button type="button" class="pgs-gallery-arrow pgs-gallery-arrow-next" data-next aria-label="Foto siguiente">${ICON_NEXT}</button>
        <div class="pgs-gallery-dots">${dots}</div>
      </div>
    `;
  } else if (layout === 'compare') {
    mediaHtml = `<div class="pgs-gallery-compare">${images
      .map((img) => `<div class="pgs-gallery-compare-item">${renderGalleryImageMedia(img)}${img.caption ? `<p class="pgs-gallery-caption">${img.caption}</p>` : ''}</div>`)
      .join('')}</div>`;
  } else {
    mediaHtml = `<div class="pgs-gallery-grid">${images
      .map((img) => `<div class="pgs-gallery-grid-item">${renderGalleryImageMedia(img)}${img.caption ? `<p class="pgs-gallery-caption">${img.caption}</p>` : ''}</div>`)
      .join('')}</div>`;
  }

  const overlayHtml = hasOverlay
    ? `
      <div class="pgs-gallery-overlay">
        <div class="pgs-gallery-overlay-inner">
          ${c.heading ? `<h2 class="h2 pgs-gallery-heading">${c.heading}</h2>` : ''}
          ${c.subtitle ? `<p class="pgs-gallery-subtitle">${c.subtitle}</p>` : ''}
          ${c.cta_link && c.cta_label ? `<a class="btn btn-onDark" href="${c.cta_link}">${c.cta_label}</a>` : ''}
        </div>
      </div>
    `
    : '';

  // spacing: mismo criterio que el carrusel de clases — normal (de
  // siempre), compact o flush. Proporción de foto opcional: si el admin
  // pone ancho y alto, pisa el recorte por defecto de cada layout (ver
  // --pgs-gallery-img-ratio en components.css); sin eso, cada layout se
  // queda con el suyo de siempre.
  const spacingClass = c.spacing && c.spacing !== 'normal' ? ` section--${c.spacing}` : '';
  const ratioStyle = c.image_ratio_w && c.image_ratio_h ? ` style="--pgs-gallery-img-ratio: ${c.image_ratio_w} / ${c.image_ratio_h};"` : '';
  // width: ancho del bloque — mismo criterio que "layout" en el carrusel de
  // clases (contenido/ancho completo), pero acá el default depende del modo
  // de visualización para no cambiarle el aspecto a nada ya guardado antes
  // de que existiera esta opción: grid ya venía siempre contenida, el resto
  // (carrusel/comparar/una sola foto) siempre a todo el ancho.
  const width = c.width === 'contained' || c.width === 'full' ? c.width : (layout === 'grid' ? 'contained' : 'full');
  const containedClass = width === 'contained' ? ' pgs-gallery--contained' : '';

  return `
    <section class="section${spacingClass} pgs-gallery pgs-gallery--${layout}${containedClass}" data-section-id="${section.id}">
      <div class="pgs-gallery-media"${ratioStyle}>${mediaHtml}</div>
      ${overlayHtml}
    </section>
  `;
}

function initGallery(el) {
  const carousel = el.querySelector('[data-carousel]');
  if (!carousel) return;
  const slides = Array.from(carousel.querySelectorAll('[data-slide]'));
  if (slides.length <= 1) return;
  let current = 0;

  function show(index) {
    const next = (index + slides.length) % slides.length;
    if (next === current) return;
    slides[current].hidden = true;
    current = next;
    slides[current].hidden = false;
    carousel.querySelectorAll('[data-dot]').forEach((dot, i) => dot.classList.toggle('is-active', i === current));
  }

  const prevBtn = carousel.querySelector('[data-prev]');
  const nextBtn = carousel.querySelector('[data-next]');
  if (prevBtn) prevBtn.addEventListener('click', () => show(current - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => show(current + 1));
  carousel.querySelectorAll('[data-dot]').forEach((dot) => {
    dot.addEventListener('click', () => show(Number(dot.dataset.dot)));
  });
}

/* --- Carrusel de clases (classes_carousel) y de marcas (brands_carousel) ---
   Módulo compartido: `initSnapCarousel` maneja el deslizamiento (pista
   `scroll-snap-type:x mandatory`, nativa al dedo en móvil) y las flechas de
   ambos carruseles — nada de librería externa. El contenido de las
   tarjetas/logos no se guarda en la sección: se lee en vivo de /categories
   y /brands al renderizar, la sección solo guarda cómo mostrarlo. */

// Avanza/retrocede la pista una tarjeta por clic (con scroll suave nativo),
// deshabilita las flechas en los extremos o, si `loop` está activo (solo el
// autoplay de clases lo usa), da la vuelta al otro extremo en vez de
// quedarse quieta. Mismo criterio de pausa en hover/foco/pestaña oculta que
// el banner (ver initBanner) cuando hay autoplay.
function initSnapCarousel(wrap, { loop = false, autoplayInterval = 0 } = {}) {
  const track = wrap.querySelector('[data-track]');
  if (!track) return;
  const items = Array.from(track.children);
  if (items.length === 0) return;

  const prevBtn = wrap.querySelector('[data-prev]');
  const nextBtn = wrap.querySelector('[data-next]');

  function cardStep() {
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    return items[0].getBoundingClientRect().width + gap;
  }
  function atStart() { return track.scrollLeft <= 1; }
  function atEnd() { return track.scrollLeft >= track.scrollWidth - track.clientWidth - 1; }

  function updateArrows() {
    if (prevBtn) prevBtn.disabled = !loop && atStart();
    if (nextBtn) nextBtn.disabled = !loop && atEnd();
  }

  function goNext() {
    if (atEnd()) {
      if (loop) track.scrollTo({ left: 0, behavior: 'smooth' });
      return;
    }
    track.scrollBy({ left: cardStep(), behavior: 'smooth' });
  }
  function goPrev() {
    if (atStart()) {
      if (loop) track.scrollTo({ left: track.scrollWidth, behavior: 'smooth' });
      return;
    }
    track.scrollBy({ left: -cardStep(), behavior: 'smooth' });
  }

  if (prevBtn) prevBtn.addEventListener('click', goPrev);
  if (nextBtn) nextBtn.addEventListener('click', goNext);
  track.addEventListener('scroll', updateArrows, { passive: true });
  window.addEventListener('resize', updateArrows);
  updateArrows();

  if (autoplayInterval > 0 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let timer = null;
    function start() { stop(); timer = setInterval(goNext, autoplayInterval * 1000); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    start();
    wrap.addEventListener('mouseenter', stop);
    wrap.addEventListener('mouseleave', start);
    wrap.addEventListener('focusin', stop);
    wrap.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stop();
      else start();
    });
  }
}

function renderClassCard(cat) {
  const overlay = Math.max(0, Math.min(100, cat.overlay_darkness == null ? 40 : Number(cat.overlay_darkness))) / 100;
  const position = ['left', 'center', 'right'].includes(cat.text_position) ? cat.text_position : 'left';
  const justify = { left: 'flex-start', center: 'center', right: 'flex-end' }[position];
  const name = cat.display_name || cat.name;
  // El desenfoque va con --pgs-class-base-scale en vez de transform directo:
  // así el hover (que multiplica ese mismo custom property, ver CSS) sigue
  // funcionando encima sin que el estilo inline lo pise.
  const blur = Math.max(0, Math.min(20, Number(cat.blur) || 0));
  const imgStyle = blur > 0 ? ` style="filter: blur(${blur}px); --pgs-class-base-scale: 1.1;"` : '';
  return `
    <a class="pgs-class-card" href="/catalogo.html?category_id=${cat.id}">
      <div class="pgs-class-card-media">
        ${cat.image_url ? `<img src="${cat.image_url}" alt="${name}" loading="lazy"${imgStyle}>` : ''}
        <div class="pgs-class-card-scrim" style="background: rgba(32, 30, 31, ${overlay});"></div>
        <div class="pgs-class-card-copy" style="align-items: ${justify}; text-align: ${position};">
          ${cat.eyebrow ? `<p class="pgs-class-card-eyebrow">${cat.eyebrow}</p>` : ''}
          <p class="pgs-class-card-name">${name}</p>
        </div>
        <span class="pgs-class-card-arrow" aria-hidden="true">${ICON_NEXT}</span>
      </div>
    </a>
  `;
}

async function renderClassesCarousel(section) {
  const c = section.content || {};
  try {
    const categories = await apiFetch('/categories');
    let items = categories.filter((cat) => cat.is_active);
    if (c.mode === 'manual' && (c.category_ids || []).length) {
      const byId = new Map(items.map((cat) => [cat.id, cat]));
      items = c.category_ids.map((id) => byId.get(id)).filter(Boolean);
    }
    if (items.length === 0) return '';

    // Modo continuo: mismo criterio que renderBrandsCarousel — pista
    // duplicada que se desliza sola (ver initContinuousCarousel, por JS con
    // requestAnimationFrame en vez de @keyframes, para poder arrastrarla),
    // sin parar nunca y con pausa en hover/foco. Con prefers-reduced-motion
    // cae al carrusel de flechas de siempre, sin duplicar la pista.
    const continuous = c.carousel_mode === 'continuous' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const reverse = c.carousel_direction === 'right';
    const showArrows = c.show_arrows !== false && !continuous;
    const arrowsHtml = showArrows
      ? `
        <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-prev" data-prev aria-label="Clase anterior">${ICON_PREV}</button>
        <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-next" data-next aria-label="Siguiente clase">${ICON_NEXT}</button>
      `
      : '';
    const cardsHtml = items.map(renderClassCard).join('');
    // La pista duplicada se desliza hasta la mitad de su ancho real
    // (scrollWidth/2, ver initContinuousCarousel): ahí queda exactamente
    // donde empezó la copia, así el "salto" de vuelta es invisible.
    const trackHtml = continuous ? cardsHtml + cardsHtml : cardsHtml;
    const trackClass = continuous ? ' pgs-class-track--continuous' : '';
    const carouselHtml = `
      <div class="pgs-carousel-wrap${continuous ? ' pgs-carousel-wrap--continuous' : ''}"${continuous ? ` data-direction="${reverse ? 'right' : 'left'}" data-speed="${c.carousel_speed || 'normal'}"` : ''}>
        <div class="pgs-carousel-track${trackClass}" data-track>${trackHtml}</div>
        ${arrowsHtml}
      </div>
    `;
    // "full": el bloque rompe el container y ocupa todo el ancho de la
    // pantalla (el título se queda alineado con el resto del sitio,
    // adentro del container) — "contained" es el ancho angosto de siempre.
    const isFull = c.layout === 'full';
    // spacing: cuánto aire arriba/abajo de la sección — normal (de
    // siempre), compact o flush (pegada a lo de arriba/abajo).
    const spacingClass = c.spacing && c.spacing !== 'normal' ? ` section--${c.spacing}` : '';
    const cardRatioW = Number(c.card_ratio_w) || 3;
    const cardRatioH = Number(c.card_ratio_h) || 4;
    return `
      <section class="section${spacingClass} pgs-classes-carousel${isFull ? ' pgs-classes-carousel--full' : ''}" data-section-id="${section.id}" data-carousel-mode="${continuous ? 'continuous' : 'arrows'}" data-autoplay-interval="${!continuous && c.autoplay ? (c.autoplay_interval || 5) : ''}"
        style="--pgs-cards-mobile:${c.cards_mobile || 1.3}; --pgs-cards-tablet:${c.cards_tablet || 3}; --pgs-cards-desktop:${c.cards_desktop || 4}; --pgs-card-ratio: ${cardRatioW} / ${cardRatioH};">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          ${isFull ? '' : carouselHtml}
        </div>
        ${isFull ? carouselHtml : ''}
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

// px/seg por velocidad — fijo independiente de cuántas tarjetas/logos haya
// (a diferencia de la duración por @keyframes de antes), así se siente
// igual sea un carrusel de tarjetas grandes o de logos chicos. Configurable
// desde el admin (carousel_speed, ver ClassesCarouselContent/
// BrandsCarouselContent en el backend).
const PGS_CAROUSEL_SPEED_PX = { slow: 25, normal: 45, fast: 70 };

// Carrusel continuo (clases y marcas): la pista avanza sola con
// requestAnimationFrame en vez de @keyframes — así JS controla la posición
// exacta en todo momento y el visitante puede arrastrarla con el dedo o el
// cursor, se haya congelado por hover/foco o no. Al soltar sigue
// deslizándose sola desde donde quedó, en la misma dirección de siempre.
function initContinuousCarousel(wrap) {
  const track = wrap.querySelector('[data-track]');
  if (!track) return;
  const direction = wrap.dataset.direction === 'right' ? 1 : -1;
  const speed = PGS_CAROUSEL_SPEED_PX[wrap.dataset.speed] || PGS_CAROUSEL_SPEED_PX.normal;

  // scrollWidth/2 es el ancho real de una copia (la pista está duplicada,
  // ver renderClassesCarousel/renderBrandsCarousel): moverse exactamente
  // esa distancia deja la copia en el lugar donde empezó el original, así
  // que envolver ahí (en vez de dejar crecer translateX sin límite) es
  // invisible para quien mira.
  let half = track.scrollWidth / 2;
  window.addEventListener('resize', () => { half = track.scrollWidth / 2; });

  let position = 0;
  let paused = false;
  let dragging = false;
  let dragStartX = 0;
  let dragStartPosition = 0;
  let dragMoved = false;
  let lastTime = null;

  function normalize(p) {
    if (!half) return 0;
    p %= half;
    if (p > 0) p -= half;
    return p;
  }

  function render() {
    track.style.transform = `translateX(${position}px)`;
  }

  function tick(now) {
    if (lastTime == null) lastTime = now;
    const dt = now - lastTime;
    lastTime = now;
    if (!paused && !dragging) {
      position = normalize(position + direction * speed * (dt / 1000));
      render();
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // Mismo criterio de pausa que el resto de carruseles con autoavance (ver
  // initSnapCarousel): hover, foco o pestaña oculta la congelan. El
  // arrastre (abajo) es independiente de esto — se puede arrastrar tanto
  // congelada como en movimiento.
  wrap.addEventListener('mouseenter', () => { paused = true; });
  wrap.addEventListener('mouseleave', () => { paused = false; });
  wrap.addEventListener('focusin', () => { paused = true; });
  wrap.addEventListener('focusout', () => { paused = false; });
  document.addEventListener('visibilitychange', () => {
    paused = document.hidden || wrap.matches(':hover') || wrap.matches(':focus-within');
  });

  function onPointerDown(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    dragging = true;
    dragMoved = false;
    dragStartX = e.clientX;
    dragStartPosition = position;
    track.classList.add('is-dragging');
    track.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e) {
    if (!dragging) return;
    const dx = e.clientX - dragStartX;
    if (Math.abs(dx) > 4) dragMoved = true;
    position = normalize(dragStartPosition + dx);
    render();
  }
  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
    track.classList.remove('is-dragging');
    try { track.releasePointerCapture(e.pointerId); } catch (_err) { /* ya liberado */ }
  }
  track.addEventListener('pointerdown', onPointerDown);
  track.addEventListener('pointermove', onPointerMove);
  track.addEventListener('pointerup', onPointerUp);
  track.addEventListener('pointercancel', onPointerUp);
  // Si de verdad arrastró (no fue un simple clic), que no navegue el link
  // de la tarjeta/logo que quedó debajo del dedo o el cursor al soltar.
  track.addEventListener('click', (e) => {
    if (dragMoved) { e.preventDefault(); e.stopPropagation(); }
  }, true);
}

function initClassesCarousel(el) {
  const wrap = el.querySelector('.pgs-carousel-wrap');
  if (!wrap) return;
  if (el.dataset.carouselMode === 'continuous') { initContinuousCarousel(wrap); return; }
  const interval = Number(el.dataset.autoplayInterval) || 0;
  // Siempre en bucle: seguir dando a la misma flecha vuelve al principio
  // (o al final, desde la primera) en vez de quedarse deshabilitada en la
  // punta — independiente de si el autoavance está prendido o no.
  initSnapCarousel(wrap, { loop: true, autoplayInterval: interval });
}

function renderBrandLogo(brand, grayscale) {
  const img = `<img src="${brand.logo_url}" alt="${brand.name}" loading="lazy" class="pgs-brand-logo${grayscale ? ' pgs-brand-logo--grayscale' : ''}">`;
  return `<div class="pgs-brand-item">${brand.link_url ? `<a class="pgs-brand-logo-link" href="${brand.link_url}">${img}</a>` : img}</div>`;
}

async function renderBrandsCarousel(section) {
  const c = section.content || {};
  try {
    const brands = await apiFetch('/brands');
    let items = brands;
    if (c.mode === 'manual' && (c.brand_ids || []).length) {
      const byId = new Map(items.map((b) => [b.id, b]));
      items = c.brand_ids.map((id) => byId.get(id)).filter(Boolean);
    }
    if (items.length === 0) return '';

    const grayscale = c.logo_color !== 'original';
    // El modo continuo se resuelve acá, no en initBrandsCarousel: con
    // prefers-reduced-motion la pista NO se duplica (si no, el manual de
    // respaldo mostraría cada logo dos veces) y queda como carrusel de
    // flechas normal.
    const continuous = c.carousel_mode === 'continuous' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const logosHtml = items.map((b) => renderBrandLogo(b, grayscale)).join('');
    const trackHtml = continuous ? logosHtml + logosHtml : logosHtml;
    const arrowsHtml = `
      <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-prev" data-prev aria-label="Marca anterior">${ICON_PREV}</button>
      <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-next" data-next aria-label="Siguiente marca">${ICON_NEXT}</button>
    `;
    const carouselHtml = `
      <div class="pgs-carousel-wrap${continuous ? ' pgs-carousel-wrap--continuous' : ''}"${continuous ? ` data-speed="${c.carousel_speed || 'normal'}"` : ''}>
        <div class="pgs-carousel-track pgs-brand-track${continuous ? ' pgs-brand-track--continuous' : ''}" data-track>${trackHtml}</div>
        ${arrowsHtml}
      </div>
    `;
    // Mismo criterio que el carrusel de clases (ver renderClassesCarousel):
    // "full" rompe el container y ocupa todo el ancho de la pantalla (el
    // título se queda adentro, como cualquier título de sección);
    // "contained" es el ancho angosto de siempre. spacing: aire arriba/abajo
    // de la sección — normal, compact o flush.
    const isFull = c.layout === 'full';
    const spacingClass = c.spacing && c.spacing !== 'normal' ? ` section--${c.spacing}` : '';
    return `
      <section class="section${spacingClass} pgs-brands-carousel${isFull ? ' pgs-brands-carousel--full' : ''}" data-section-id="${section.id}" data-carousel-mode="${continuous ? 'continuous' : 'arrows'}"
        style="--pgs-logos-mobile:${c.logos_mobile || 3}; --pgs-logos-tablet:${c.logos_tablet || 5}; --pgs-logos-desktop:${c.logos_desktop || 7};">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          ${isFull ? '' : carouselHtml}
        </div>
        ${isFull ? carouselHtml : ''}
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

function initBrandsCarousel(el) {
  const wrap = el.querySelector('.pgs-carousel-wrap');
  if (!wrap) return;
  // Modo continuo: mismo motor por JS que el carrusel de clases, ver
  // initContinuousCarousel. Las flechas quedan en el DOM pero ocultas por
  // CSS, salvo que el usuario prefiera menos movimiento (ver
  // renderBrandsCarousel), caso en el que ya no se marca como "continuous"
  // y cae acá igual, en modo manual normal.
  if (el.dataset.carouselMode === 'continuous') { initContinuousCarousel(wrap); return; }
  initSnapCarousel(wrap, { loop: true });
}

// Sección administrable "Chat" (+ Añadir sección, cualquier página):
// burbuja fija en una esquina que despliega un panel de chat conectado al
// webhook de n8n (ver POST /chat/message en el backend — nunca se llama a
// n8n directo desde acá, así el token del usuario nunca sale del backend).
// Posición (lado + distancia del borde inferior), tamaño (compacto/amplio,
// a propósito chicos: es un widget, no un chat de pantalla completa) y
// color quedan en content, con fallback a los valores de marca de siempre
// si el admin no los toca.
function renderChatWidget(section) {
  const c = section.content || {};
  const position = c.position === 'left' ? 'left' : 'right';
  const size = c.size === 'medium' ? 'medium' : 'small';
  const offset = Number(c.offset) || 24;
  const color = (c.color || '').trim();
  const title = c.title || 'Habla con nosotros';
  const greeting = (c.greeting || '').replace(/"/g, '&quot;');
  // Bienvenida distinta con sesión iniciada (el cliente puede preguntar por
  // sus pedidos) — si el admin no la personalizó, cae a un default propio en
  // vez del genérico de arriba, ver initChatWidget().
  const greetingLoggedIn = (c.greeting_logged_in || '').replace(/"/g, '&quot;');
  return `
    <div class="pgs-chat-widget pgs-chat-widget--${position} pgs-chat-widget--${size}" data-section-id="${section.id}" data-greeting="${greeting}" data-greeting-logged-in="${greetingLoggedIn}"
      style="--pgs-chat-offset:${offset}px;${color ? ` --pgs-chat-color:${color};` : ''}">
      <button type="button" class="pgs-chat-bubble" aria-label="Abrir chat" aria-expanded="false" aria-controls="pgsChatPanel${section.id}">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
      </button>
      <div class="pgs-chat-panel" id="pgsChatPanel${section.id}" hidden>
        <div class="pgs-chat-header">
          <span>${title}</span>
          <button type="button" class="pgs-chat-close" aria-label="Cerrar chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="6" y1="6" x2="18" y2="18"/><line x1="6" y1="18" x2="18" y2="6"/></svg>
          </button>
        </div>
        <div class="pgs-chat-messages" aria-live="polite"></div>
        <form class="pgs-chat-form">
          <input type="text" name="message" placeholder="Escribe tu mensaje…" aria-label="Mensaje" required autocomplete="off">
          <button type="submit" aria-label="Enviar">${ICON_NEXT}</button>
        </form>
      </div>
    </div>
  `;
}

// session_id e historial visible del chat viven en sessionStorage (no
// localStorage): así se pierden solos al cerrar la pestaña, y sobre todo se
// pueden borrar a mano al iniciar/cerrar sesión (ver resetChatSession en
// api.js) sin dejar memoria de una cuenta filtrándose a otra en el mismo
// navegador — tanto la del propio widget (estos mensajes) como la de n8n
// (que usa este mismo session_id como llave para su memoria de conversación
// del lado del workflow).
const CHAT_SESSION_KEY = 'jg_chat_session';
const CHAT_HISTORY_KEY = 'jg_chat_history';

function getChatSessionId() {
  let id = sessionStorage.getItem(CHAT_SESSION_KEY);
  if (!id) {
    id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(CHAT_SESSION_KEY, id);
  }
  return id;
}

function getChatHistory() {
  try {
    return JSON.parse(sessionStorage.getItem(CHAT_HISTORY_KEY) || '[]');
  } catch (_err) {
    return [];
  }
}

function pushChatHistory(role, text) {
  const history = getChatHistory();
  history.push({ role, text });
  sessionStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
}

// Un puñado de rutas propias que el bot puede mencionar en texto plano (ej.
// "inicia sesión en /login") y que sí tiene sentido volver clicables —
// nunca HTML del lado de n8n/el LLM, solo estos paths reconocidos o URLs
// completas, ver renderMessageText().
const CHAT_LINK_TARGETS = { '/login': '/login.html', '/registro': '/registro.html', '/mi-cuenta': '/mi-cuenta.html' };
const CHAT_LINK_PATTERN = /(https?:\/\/[^\s]+|\/(?:login|registro|mi-cuenta)(?:\.html)?)/g;

function renderMessageText(container, text) {
  let lastIndex = 0;
  let match;
  CHAT_LINK_PATTERN.lastIndex = 0;
  while ((match = CHAT_LINK_PATTERN.exec(text))) {
    if (match.index > lastIndex) container.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
    const a = document.createElement('a');
    a.href = CHAT_LINK_TARGETS[match[0]] || match[0];
    a.textContent = match[0];
    if (match[0].startsWith('http')) { a.target = '_blank'; a.rel = 'noopener'; }
    container.appendChild(a);
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) container.appendChild(document.createTextNode(text.slice(lastIndex)));
}

function initChatWidget(el) {
  const bubble = el.querySelector('.pgs-chat-bubble');
  const panel = el.querySelector('.pgs-chat-panel');
  const closeBtn = el.querySelector('.pgs-chat-close');
  const messagesEl = el.querySelector('.pgs-chat-messages');
  const form = el.querySelector('.pgs-chat-form');
  const input = form.querySelector('input');
  const loggedIn = typeof isLoggedIn === 'function' && isLoggedIn();
  const greeting = loggedIn
    ? (el.dataset.greetingLoggedIn || 'Puedo ayudarte con tus pedidos y lo que necesites.')
    : (el.dataset.greeting || '');
  let greeted = getChatHistory().length > 0;

  // role 'bot'/'user' igual que antes; persist=false solo al repintar
  // historial ya guardado, para no duplicarlo en sessionStorage.
  function appendMessage(role, text, { persist = true } = {}) {
    const div = document.createElement('div');
    div.className = `pgs-chat-msg pgs-chat-msg--${role}`;
    // Nodos de texto armados a mano (renderMessageText), nunca innerHTML: el
    // texto del usuario y la respuesta de n8n/el LLM no son contenido de
    // confianza del admin como el resto de esta sección — no se interpreta
    // como HTML, solo se reconocen unos pocos links propios en texto plano.
    renderMessageText(div, text);
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    if (persist) pushChatHistory(role, text);
    return div;
  }

  // Repinta lo que ya había en sessionStorage (ej. el visitante navegó a
  // otra página con el mismo widget) antes de decidir si hace falta saludo.
  getChatHistory().forEach((msg) => appendMessage(msg.role, msg.text, { persist: false }));

  // En iOS Safari el layout viewport (y el "vh" de components.css) NO se
  // achica cuando aparece el teclado — solo el visualViewport sí. Sin esto,
  // el panel fixed queda mal ubicado o tapado por el teclado. Mientras el
  // teclado esté activo (heurística: el visual viewport se achicó bastante
  // más de lo que explicaría solo la barra de direcciones) se reancla el
  // panel a esa altura real; al cerrarse el teclado vuelve al hoja-fija
  // normal de components.css.
  const isMobileQuery = window.matchMedia('(max-width: 480px)');
  function adjustPanelForKeyboard() {
    if (panel.hidden || !isMobileQuery.matches || !window.visualViewport) return;
    const vv = window.visualViewport;
    const keyboardOpen = window.innerHeight - vv.height > 120;
    if (keyboardOpen) {
      const margin = 12;
      panel.style.top = `${vv.offsetTop + margin}px`;
      panel.style.bottom = 'auto';
      panel.style.height = `${vv.height - margin * 2}px`;
    } else {
      panel.style.top = '';
      panel.style.bottom = '';
      panel.style.height = '';
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', adjustPanelForKeyboard);
    window.visualViewport.addEventListener('scroll', adjustPanelForKeyboard);
  }

  function open() {
    panel.hidden = false;
    bubble.setAttribute('aria-expanded', 'true');
    if (!greeted && greeting) {
      appendMessage('bot', greeting);
      greeted = true;
    }
    // Sin foco automático acá: en móvil eso dispara el teclado apenas se
    // abre el panel sin que el visitante haya tocado nada — que lo abra el
    // propio input cuando lo toquen, como cualquier campo de texto normal.
    adjustPanelForKeyboard();
  }
  function close() {
    panel.hidden = true;
    bubble.setAttribute('aria-expanded', 'false');
    panel.style.top = '';
    panel.style.bottom = '';
    panel.style.height = '';
  }
  bubble.addEventListener('click', () => (panel.hidden ? open() : close()));
  closeBtn.addEventListener('click', close);

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    appendMessage('user', text);
    const pending = appendMessage('bot', 'Escribiendo…', { persist: false });
    pending.classList.add('pgs-chat-msg--pending');
    try {
      // apiFetch adjunta el token si hay sesión (Authorization: Bearer) — el
      // backend arma el customer_context (pedidos recientes, ya en texto
      // listo para el prompt) del lado del servidor a partir de ese token,
      // nunca se manda el token en sí hacia n8n (ver POST /chat/message).
      const result = await apiFetch('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ message: text, session_id: getChatSessionId() }),
      });
      pending.textContent = '';
      renderMessageText(pending, result.reply);
      pushChatHistory('bot', result.reply);
    } catch (_err) {
      pending.textContent = 'No pudimos conectar con el asistente. Intenta de nuevo en un momento.';
    } finally {
      pending.classList.remove('pgs-chat-msg--pending');
    }
  });
}

// Sección administrable "Barra inferior" (bottom_bar) (+ Añadir sección,
// cualquier página): tira fija abajo de la pantalla, a diferencia de
// announcement_bar (que va arriba o en línea), y con un comportamiento
// propio a propósito distinto de esa: solo aparece mientras el visitante
// se desliza hacia abajo, y se esconde apenas se desliza hacia arriba —
// como el visitante ya vio el resto de la página al bajar, no compite por
// espacio con el contenido, y no queda pegada tapando algo cuando el
// visitante vuelve a subir a revisar algo.
function renderBottomBar(section) {
  const c = section.content || {};
  if (!c.text) return '';
  const variant = ['onyx', 'paper', 'gold-soft'].includes(c.variant) ? c.variant : 'onyx';
  const hasButton = Boolean(c.button_label && c.button_link);
  return `
    <aside class="pgs-bottom-bar pgs-bottom-bar--${variant}" aria-label="Aviso" data-section-id="${section.id}">
      <div class="pgs-bottom-bar-inner">
        <p class="pgs-bottom-bar-text">${c.text}</p>
        ${hasButton ? `<a class="pgs-bottom-bar-btn" href="${c.button_link}">${c.button_label}</a>` : ''}
      </div>
    </aside>
  `;
}

function initBottomBar(el) {
  if (!el) return;
  let lastY = window.scrollY;
  let ticking = false;

  function onScroll() {
    const y = window.scrollY;
    // Umbral chico para ignorar el jitter de rebote de iOS/Android y no
    // parpadear con cada pixel; y > 40 para no mostrarla apenas se entra a
    // la página con un scroll mínimo cerca del borde superior.
    if (Math.abs(y - lastY) > 4) {
      el.classList.toggle('is-visible', y > lastY && y > 40);
      lastY = y;
    }
    ticking = false;
  }

  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        window.requestAnimationFrame(onScroll);
        ticking = true;
      }
    },
    { passive: true }
  );
}

// Sección administrable "Promoción emergente" (promo_popup) (+ Añadir
// sección, cualquier página): cuadro centrado con foto/título/texto/botón
// que aparece al cargar la página donde se agregue — a diferencia del
// banner o el bloque de footer, este flota sobre el contenido con fondo
// oscurecido detrás, y se puede rechazar (X o clic afuera). El cierre se
// recuerda por pestaña (sessionStorage, no localStorage): no vuelve a
// aparecer si el visitante navega a otra página con la misma promo en la
// misma sesión, pero sí en una visita nueva.
function renderPromoPopup(section) {
  const c = section.content || {};
  if (!c.heading && !c.text && !c.image_url) return '';
  const size = ['small', 'medium', 'large'].includes(c.size) ? c.size : 'medium';
  const hasButton = Boolean(c.button_label && c.button_link);
  return `
    <div class="pgs-promo-popup pgs-promo-popup--${size}" data-section-id="${section.id}" hidden>
      <div class="pgs-promo-popup-backdrop" data-promo-backdrop></div>
      <div class="pgs-promo-popup-card" role="dialog" aria-modal="true" aria-label="${c.heading || 'Promoción'}">
        <button type="button" class="pgs-promo-popup-close" data-promo-close aria-label="Cerrar">${ICON_CLOSE}</button>
        ${c.image_url ? `<img class="pgs-promo-popup-image" src="${c.image_url}" alt="">` : ''}
        <div class="pgs-promo-popup-body">
          ${c.heading ? `<h3 class="pgs-promo-popup-heading">${c.heading}</h3>` : ''}
          ${c.text ? `<p class="pgs-promo-popup-text">${c.text}</p>` : ''}
          ${hasButton ? `<a class="btn btn-primary pgs-promo-popup-btn" href="${c.button_link}">${c.button_label}</a>` : ''}
        </div>
      </div>
    </div>
  `;
}

function initPromoPopup(el, section) {
  if (!el) return;
  const storageKey = `jg_promo_dismissed_${section.id}_${contentHash(section.content)}`;
  try {
    if (sessionStorage.getItem(storageKey) === '1') return;
  } catch (_err) {
    // sin storage disponible: el popup igual funciona, solo no recuerda el cierre
  }

  function dismiss() {
    el.hidden = true;
    try {
      sessionStorage.setItem(storageKey, '1');
    } catch (_err) {
      // sin storage: el cierre solo dura mientras la página siga abierta
    }
  }

  el.querySelector('[data-promo-close]').addEventListener('click', dismiss);
  el.querySelector('[data-promo-backdrop]').addEventListener('click', dismiss);
  el.hidden = false;
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
  if (section.key === 'catalogo_header') {
    // Cuántas tarjetas de producto entran por fila en móvil (2 a 4) — ver
    // el campo "Columnas en móvil" del editor, solo visible para esta
    // sección. Se aplica acá porque #productGrid vive fuera del mount de
    // esta sección (ver comentario sobre catalogo_header/mount fijo más
    // arriba) pero está en la misma página.
    const grid = document.getElementById('productGrid');
    if (grid) {
      const cols = String(c.mobile_columns || 2);
      grid.style.setProperty('--product-grid-cols-mobile', cols);
      // data-attribute (no la CSS var) porque el CSS necesita "seleccionar
      // por valor" para achicar tarjeta/gap solo en 3-4 columnas — ver
      // components.css, .product-grid[data-cols-mobile].
      grid.dataset.colsMobile = cols;
    }
    return c.heading ? `<h1 class="h1">${c.heading}</h1>` : '';
  }
  if (!c.heading) return '';
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
  gallery: renderGallery,
  classes_carousel: renderClassesCarousel,
  brands_carousel: renderBrandsCarousel,
  chat_widget: renderChatWidget,
  bottom_bar: renderBottomBar,
  promo_popup: renderPromoPopup,
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
      mount.querySelectorAll('.pgs-gallery[data-section-id]').forEach((el) => initGallery(el));
      mount.querySelectorAll('.pgs-banner[data-section-id]').forEach((el) => initBanner(el));
      mount.querySelectorAll('.pgs-classes-carousel[data-section-id]').forEach((el) => initClassesCarousel(el));
      mount.querySelectorAll('.pgs-brands-carousel[data-section-id]').forEach((el) => initBrandsCarousel(el));
      mount.querySelectorAll('.pgs-products-carousel[data-section-id]').forEach((el) => initSnapCarousel(el.querySelector('.pgs-carousel-wrap')));
      mount.querySelectorAll('.pgs-chat-widget[data-section-id]').forEach((el) => initChatWidget(el));
      mount.querySelectorAll('.pgs-bottom-bar[data-section-id]').forEach((el) => initBottomBar(el));
      mount.querySelectorAll('.pgs-promo-popup[data-section-id]').forEach((el) => {
        const section = freeform.find((s) => String(s.id) === el.dataset.sectionId);
        if (section) initPromoPopup(el, section);
      });
    }
  } catch (_err) {
    // Si falla, la página sigue funcionando igual sin las secciones extra.
  } finally {
    // Revela el footer (ver .site-footer en components.css) haya salido
    // bien o mal el fetch — nunca se queda escondido para siempre.
    document.body.classList.add('pgs-ready');
    // Las secciones llegan después de la carga (fetch), así que el salto
    // nativo a #ancla ya pasó sin encontrar nada — se repite acá.
    if (window.location.hash.length > 1) {
      const target = document.getElementById(decodeURIComponent(window.location.hash.slice(1)));
      if (target) requestAnimationFrame(() => target.scrollIntoView());
    }
  }
}

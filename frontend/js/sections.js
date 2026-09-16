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
  return `
    <section class="section pgs-banner" data-section-id="${section.id}" data-interval="${interval}">
      ${slidesHtml}
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
  const imgStyle = blur > 0 ? ` style="filter: blur(${blur}px); transform: scale(1.1);"` : '';
  const imgTagHtml = `<img src="${g.url}" alt="${g.alt || ''}" loading="lazy"${imgStyle}>`;

  const hasCta = Boolean(g.link_url && g.cta_label);
  const hasOverlayText = Boolean(g.title || g.subtitle || hasCta);
  const overlayOpacity = Math.max(0, Math.min(100, Number(g.overlay_opacity) || 0)) / 100;
  const position = ['left', 'center', 'right'].includes(g.text_position) ? g.text_position : 'left';
  const justify = { left: 'flex-start', center: 'center', right: 'flex-end' }[position];
  const ctaStyle = g.cta_color
    ? ` style="background-color:${g.cta_color}; border-color:${g.cta_color}; color:${contrastTextColor(g.cta_color)};"`
    : '';
  const overlayHtml = hasOverlayText
    ? `
      <div class="pgs-gallery-img-scrim" style="background-color: rgba(32, 30, 31, ${overlayOpacity});"></div>
      <div class="pgs-gallery-img-inner" style="justify-content: ${justify};">
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

  return `
    <section class="section pgs-gallery pgs-gallery--${layout}" data-section-id="${section.id}">
      <div class="pgs-gallery-media">${mediaHtml}</div>
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
  return `
    <a class="pgs-class-card" href="/catalogo.html?category_id=${cat.id}">
      <div class="pgs-class-card-media">
        ${cat.image_url ? `<img src="${cat.image_url}" alt="${name}" loading="lazy">` : ''}
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

    const showArrows = c.show_arrows !== false;
    const arrowsHtml = showArrows
      ? `
        <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-prev" data-prev aria-label="Clase anterior">${ICON_PREV}</button>
        <button type="button" class="pgs-carousel-arrow pgs-carousel-arrow-next" data-next aria-label="Siguiente clase">${ICON_NEXT}</button>
      `
      : '';
    return `
      <section class="section pgs-classes-carousel" data-section-id="${section.id}" data-autoplay-interval="${c.autoplay ? (c.autoplay_interval || 5) : ''}"
        style="--pgs-cards-mobile:${c.cards_mobile || 1.3}; --pgs-cards-tablet:${c.cards_tablet || 3}; --pgs-cards-desktop:${c.cards_desktop || 4};">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          <div class="pgs-carousel-wrap">
            <div class="pgs-carousel-track" data-track>${items.map(renderClassCard).join('')}</div>
            ${arrowsHtml}
          </div>
        </div>
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

function initClassesCarousel(el) {
  const wrap = el.querySelector('.pgs-carousel-wrap');
  if (!wrap) return;
  const interval = Number(el.dataset.autoplayInterval) || 0;
  initSnapCarousel(wrap, { loop: interval > 0, autoplayInterval: interval });
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
    return `
      <section class="section pgs-brands-carousel" data-section-id="${section.id}" data-carousel-mode="${continuous ? 'continuous' : 'arrows'}"
        style="--pgs-logos-mobile:${c.logos_mobile || 3}; --pgs-logos-tablet:${c.logos_tablet || 5}; --pgs-logos-desktop:${c.logos_desktop || 7};">
        <div class="container">
          ${c.heading ? `<h2 class="h2 section-title">${c.heading}</h2>` : ''}
          <div class="pgs-carousel-wrap${continuous ? ' pgs-carousel-wrap--continuous' : ''}">
            <div class="pgs-carousel-track pgs-brand-track${continuous ? ' pgs-brand-track--continuous' : ''}" data-track>${trackHtml}</div>
            ${arrowsHtml}
          </div>
        </div>
      </section>
    `;
  } catch (_err) {
    return '';
  }
}

function initBrandsCarousel(el) {
  const wrap = el.querySelector('.pgs-carousel-wrap');
  if (!wrap) return;
  // Modo continuo: la animación es puro CSS (pista duplicada + @keyframes,
  // pausa en :hover/:focus-within) — no necesita JS. Las flechas quedan en
  // el DOM pero ocultas por CSS, salvo que el usuario prefiera menos
  // movimiento (ver renderBrandsCarousel), caso en el que ya no se marca
  // como "continuous" y cae acá igual, en modo manual normal.
  if (el.dataset.carouselMode === 'continuous') return;
  initSnapCarousel(wrap, {});
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
  gallery: renderGallery,
  classes_carousel: renderClassesCarousel,
  brands_carousel: renderBrandsCarousel,
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
    }
  } catch (_err) {
    // Si falla, la página sigue funcionando igual sin las secciones extra.
  }
}

/* Renderiza las secciones de contenido administrables (anuncios, banners,
   encabezados, grillas de producto, texto, categorías, imágenes, footer,
   testimonios, contadores, HTML/CSS libre) que el panel admin agrega a cada
   página. Un solo script para todas las páginas: agregar/quitar/reordenar
   secciones no requiere tocar el HTML de cada página, solo el contenido en
   la base de datos. */

function renderAnnouncement(section) {
  const c = section.content || {};
  if (!c.text) return '';
  return `
    <div class="pgs-announcement">
      ${c.link_url ? `<a href="${c.link_url}">${c.text}</a>` : `<span>${c.text}</span>`}
    </div>
  `;
}

function renderBanner(section) {
  const c = section.content || {};
  const bgStyle = c.image_url ? ` style="background-image:url('${c.image_url}')"` : '';
  return `
    <section class="section pgs-banner"${bgStyle}>
      <div class="container pgs-banner-inner">
        ${c.title ? `<h2 class="h2 pgs-banner-title">${c.title}</h2>` : ''}
        ${c.subtitle ? `<p class="pgs-banner-subtitle">${c.subtitle}</p>` : ''}
        ${c.link_url ? `<a class="btn btn-onDark" href="${c.link_url}">${c.cta_label || 'Ver más'}</a>` : ''}
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

const SECTION_RENDERERS = {
  announcement: renderAnnouncement,
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
};

async function renderPageSections(pageKey, mountId = 'dynamicSections') {
  const mount = document.getElementById(mountId);
  if (!mount) return;
  try {
    const sections = await apiFetch(`/page-sections?page=${encodeURIComponent(pageKey)}`);
    const rendered = await Promise.all(sections.map((s) => (SECTION_RENDERERS[s.type] ? SECTION_RENDERERS[s.type](s) : '')));
    mount.innerHTML = rendered.join('');
  } catch (_err) {
    // Si falla, la página sigue funcionando igual sin las secciones extra.
  }
}

/* Renderiza las secciones de contenido administrables (banners, testimonios,
   contadores, HTML/CSS libre) que el panel admin agrega a cada página. Un
   solo script para todas las páginas: agregar/quitar/reordenar secciones no
   requiere tocar el HTML de cada página, solo el contenido en la base de datos. */

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

function renderCustomHtml(section) {
  const c = section.content || {};
  return `${c.css ? `<style>${c.css}</style>` : ''}${c.html || ''}`;
}

const SECTION_RENDERERS = {
  banner: renderBanner,
  testimonials: renderTestimonials,
  counters: renderCounters,
  custom_html: renderCustomHtml,
};

async function renderPageSections(pageKey, mountId = 'dynamicSections') {
  const mount = document.getElementById(mountId);
  if (!mount) return;
  try {
    const sections = await apiFetch(`/page-sections?page=${encodeURIComponent(pageKey)}`);
    mount.innerHTML = sections.map((s) => (SECTION_RENDERERS[s.type] ? SECTION_RENDERERS[s.type](s) : '')).join('');
  } catch (_err) {
    // Si falla, la página sigue funcionando igual sin las secciones extra.
  }
}

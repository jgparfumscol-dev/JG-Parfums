/* Aparición progresiva al hacer scroll: cada sección y tarjeta entra con un
   fade + leve desplazamiento hacia arriba en vez de aparecer de golpe con
   el resto de la página. Un solo script para todo el sitio — se aplica
   automáticamente tanto al contenido que ya está en el HTML al cargar como
   al que cada página agrega después por JS (productos, secciones del
   editor, etc.), así que no hay que tocar cada página para sumarla.

   Progressive enhancement: la clase que oculta el elemento (`reveal`) la
   agrega este script, no el HTML — si JS falla o está desactivado, el
   contenido nunca queda invisible. */

(function () {
  const REVEAL_SELECTOR = [
    'main > .section',
    '.product-card',
    '.pgs-testimonial-card',
    '.pgs-counter',
    '.manifesto-item',
  ].join(', ');

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const supported = 'IntersectionObserver' in window;

  // rootMargin positivo: dispara ANTES de que el elemento entre a la
  // pantalla (con -10% pasaba lo contrario — había que scrollear bastante
  // más allá de que "debería" verse para que apareciera, y una sección
  // entera se sentía como si faltara mientras tanto). Con esto ya está
  // visible o terminando de animar para cuando el usuario llega a verla.
  let observer = null;
  if (supported && !reduceMotion) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0, rootMargin: '0px 0px 200px 0px' }
    );
  }

  // Pequeño desfase entre hermanos (tarjetas de una misma grilla, por
  // ejemplo) para que entren en cascada en vez de todas a la vez.
  const siblingIndex = new WeakMap();
  function delayFor(el) {
    const parent = el.parentElement;
    if (!parent) return 0;
    let i = siblingIndex.get(parent) || 0;
    siblingIndex.set(parent, i + 1);
    return Math.min(i, 5) * 70;
  }

  function applyTo(el) {
    if (el.classList.contains('reveal') || el.classList.contains('is-visible')) return;
    if (!observer) {
      el.classList.add('is-visible');
      return;
    }
    el.classList.add('reveal');
    el.style.transitionDelay = `${delayFor(el)}ms`;
    observer.observe(el);
  }

  function scan(root) {
    if (root.nodeType !== 1) return;
    if (root.matches(REVEAL_SELECTOR)) applyTo(root);
    root.querySelectorAll(REVEAL_SELECTOR).forEach(applyTo);
  }

  scan(document.body);

  // El resto del contenido de cada página llega después (fetch a la API):
  // grillas de producto, banners y demás secciones del editor. Se observa
  // el body para agarrarlo apenas se agrega al DOM.
  new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => scan(node));
    });
  }).observe(document.body, { childList: true, subtree: true });
})();

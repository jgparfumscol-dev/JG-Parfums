# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Consumidores finales colombianos (B2C) que compran perfumes de nicho para uso personal, atraídos por la autenticidad del producto (originales, no decants ni inspirados) y que quieren conocer las notas olfativas reales antes de decidir. Compra mayoritariamente desde móvil, con escritorio como segunda composición igual de resuelta (BRAND.md §1).

## Product Purpose

Tienda online que vende perfumes originales de nicho al mercado colombiano, con checkout propio (no solo captación por WhatsApp): catálogo, carrito, checkout con envío, cuentas de usuario o compra como invitado, y pago con Wompi o Mercado Pago. Éxito significa pedidos pagados y entregados, no solo tráfico o consultas.

## Positioning

Perfumes de nicho 100% originales a un precio más accesible que las boutiques tradicionales — autenticidad de producto más acceso, no descuento vía imitación (réplicas/inspirados) ni ser la tienda más barata del mercado. El catálogo también ofrece decants: el mismo frasco original fraccionado en presentaciones de 5ml y 10ml, para quien quiere probar antes de comprar el frasco completo — sigue siendo el producto 100% original, solo en otro tamaño.

## Operating Context

- Checkout con dos pasarelas colombianas (Wompi, Mercado Pago) y checkout invitado además de cuenta registrada.
- Correos transaccionales centralizados vía Resend (bienvenida, recuperación de clave, confirmación de pedido).
- Panel administrativo propio (SPA con tabs) para gestión de productos y pedidos — sin depender de un CMS externo.
- Backend FastAPI/PostgreSQL desplegado en Railway; frontend estático (HTML/CSS/JS vanilla, sin build step) desplegado en Cloudflare Pages.
- Ley 1581 de 2012 (Colombia) exige política de tratamiento de datos personales — todavía no publicada.

## Capabilities and Constraints

- Frontend es HTML/CSS/JS vanilla sin framework ni paso de build: cualquier trabajo visual debe seguir funcionando sin bundler.
- Backend: FastAPI + SQLAlchemy 2.x síncrono + PostgreSQL + Alembic; JWT (python-jose) + bcrypt para auth; rate limiting por IP en login/registro/checkout; sin enumeración de cuentas.
- 29 tests automatizados (pytest contra SQLite en memoria) cubren auth, productos, decants, pedidos y pagos; no tocan `DATABASE_URL` real ni servicios externos.
- Catálogo hoy tiene solo productos de prueba sin fotografía real — el contenido real del cliente todavía no existe.
- Decants: presentaciones de 5ml/10ml por producto, con precio y stock propios (tabla `product_variants`), gestionadas desde el panel admin y seleccionables en la ficha de producto.
- Credenciales de producción de Wompi y Mercado Pago ya configuradas — flujo de pago completo probado de punta a punta con ambas pasarelas.
- **Decisión abierta:** costo y política de envío — el checkout hoy solo cobra el subtotal, sin cargo de envío definido.
- **Decisión abierta:** dominio propio — el sitio corre en `*.pages.dev` / `*.up.railway.app` mientras no se confirme un dominio.
- **Decisión abierta:** verificación de dominio propio en Resend — hoy los correos salen desde `onboarding@resend.dev`, que solo entrega a la cuenta dueña de la API key, no a clientes reales.
- Antes de lanzar: eliminar la cuenta admin y los productos de prueba.

## Brand Commitments

- Manual de marca completo en `BRAND.md` (fuente de verdad de color, tipografía, logo, voz — no se reemplaza aquí; PRODUCT.md registra solo la verdad de producto).
- Tratamiento de voz: **"tú"**, confirmado y ya implementado en la copy existente.
- Voz: directa, sin adjetivos de relleno, con conocimiento técnico real de producto (notas, familia olfativa, duración, estela, ocasión); nunca frases genéricas de perfumería ("experiencia sensorial única").
- Logotipo confirmado y vectorizado (`Logos/`); paleta Ónix/Oro/Marfil y tipografía Bodoni Moda + Jost ya definidas en BRAND.md.

## Evidence on Hand

- README.md documenta el pipeline técnico probado de punta a punta (backend, frontend, base de datos, correos) y el estado real de despliegue.
- BRAND.md es un manual de marca completo (color, tipografía, componentes, accesibilidad, voz) ya aplicado al frontend construido.
- Assets de marca reales en `Logos/` (SVG del logotipo en variantes, favicons, manual de marca en PDF).
- Catálogo real (nombre, casa, notas, precio, stock, fotografía) del cliente **no existe todavía** — no fabricar productos, precios ni fotografía de ejemplo como si fueran reales.
- No hay testimonios, casos de estudio ni prensa — no inventar ninguno.

## Product Principles

1. Autenticidad de producto es la posición central: nunca diseñar ni escribir copy que sugiera réplicas, imitaciones o "inspirado en". El decant es una excepción explícita a esta cautela, no una contradicción: es el mismo frasco original fraccionado, nunca un producto de otro origen — la copy debe dejarlo así de claro (ej. "el mismo perfume, en tamaño de prueba", nunca lenguaje que lo acerque a una imitación).
2. El checkout propio es el objetivo del sitio, no una alternativa a WhatsApp — el flujo de compra completo importa más que la captación de leads.
3. Catálogo y checkout van sobre fondo claro por decisión ya tomada (BRAND.md §3.6): las secciones oscuras son para momentos de marca, no para tareas transaccionales.
4. El sitio es mobile-first por evidencia real de venta, con escritorio como segunda composición completa, nunca un recorte de la versión móvil.
5. Nada se publica como contenido real de cliente (productos, fotos, testimonios) hasta que el cliente lo entregue.

## Accessibility & Inclusion

Mínimos no negociables ya definidos en BRAND.md §10: contraste 4.5:1 en texto normal / 3:1 en texto grande (≥24px), el dorado de marca (`#D3AE6A`) prohibido como texto sobre blanco, el color nunca como único indicador de estado, `prefers-reduced-motion` respetado, y `alt` real (nombre del perfume) en toda imagen de producto.

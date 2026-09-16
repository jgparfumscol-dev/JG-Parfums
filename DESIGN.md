---
name: JG Parfums
description: Tienda de perfumes de nicho 100% originales en Colombia — ónix, oro y marfil, hecha para leerse como una ficha técnica de perfumista.
colors:
  onyx: "#201E1F"
  gold-jg: "#D3AE6A"
  paper: "#F7F5F1"
  white: "#FFFFFF"
  smoke: "#6E6A67"
  gold-50: "#F8F2E7"
  gold-100: "#EFE1C8"
  gold-200: "#E3CCA1"
  gold-500: "#CB9F4E"
  gold-600: "#B18534"
  gold-700: "#8E6B2A"
  gold-800: "#6A501F"
  ink-800: "#2C2A2B"
  ink-600: "#6E6A67"
  ink-300: "#C9C4BF"
  ink-100: "#EDE9E3"
  dark-border: "#3A3739"
  dark-text-muted: "#B9B4B0"
  success: "#4E7A52"
  warning: "#B5772A"
  danger: "#9E3B34"
  info: "#3F5D73"
typography:
  display:
    fontFamily: "'Newsreader', Georgia, serif"
    fontSize: "clamp(2.5rem, 6vw, 4rem)"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  h1:
    fontFamily: "'Newsreader', Georgia, serif"
    fontSize: "clamp(2rem, 5vw, 3rem)"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  h2:
    fontFamily: "'Newsreader', Georgia, serif"
    fontSize: "clamp(1.75rem, 3vw, 2.125rem)"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  h3:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "clamp(1.25rem, 2vw, 1.375rem)"
    fontWeight: 500
    lineHeight: 1.3
  body:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0.005em"
  label:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.03em"
  small:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.01em"
  meta:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
  price:
    fontFamily: "'Newsreader', Georgia, serif"
    fontSize: "clamp(22px, 2vw, 26px)"
    fontWeight: 600
    lineHeight: 1
  price-card:
    fontFamily: "'Jost', 'Futura', 'Century Gothic', system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1
  note-italic:
    fontFamily: "'Newsreader', Georgia, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: "2px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  6: "24px"
  8: "32px"
  12: "48px"
  16: "64px"
  24: "96px"
  32: "128px"
components:
  button-primary:
    backgroundColor: "{colors.onyx}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "0 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.ink-800}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.onyx}"
    rounded: "{rounded.sm}"
    padding: "0 24px"
    height: "48px"
  button-onDark:
    backgroundColor: "transparent"
    textColor: "{colors.gold-jg}"
    rounded: "{rounded.sm}"
    padding: "0 24px"
    height: "48px"
  card:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.sm}"
    padding: "24px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.onyx}"
    rounded: "{rounded.sm}"
    height: "48px"
    padding: "0 16px"
---

# Design System: JG Parfums

## Overview

**Creative North Star: "El cuaderno del perfumista"**

JG Parfums no se viste como una tienda de perfumería genérica de negro-y-dorado: se lee como el cuaderno técnico de alguien que conoce el producto. El sistema ya está construido y en producción — esta es su fotografía, no una propuesta. Cada componente distintivo (`.spec-row`, `.scent-diagram`, `.ledger-row`) reemplaza el ícono decorativo de e-commerce por notación real: filas de ficha técnica con regla fina en vez de tarjetas con ícono, una pirámide olfativa con barras que se llenan en vez de un adorno, un recibo con tipografía tabular en vez de una lista genérica. El dorado (`#D3AE6A`) es tinta, nunca pintura: aparece como filete, borde o texto sobre fondo oscuro, nunca como relleno de un área grande ni como degradado. Las superficies claras (Marfil `#F7F5F1`, nunca blanco puro salvo en frascos y fotografía) cargan el peso de catálogo y checkout; el Ónix casi negro se reserva para momentos de marca — hero, footer, franjas de manifiesto — nunca para tareas transaccionales.

Rechazos confirmados (BRAND.md §11): fondo negro en todo el sitio, la pareja Playfair Display + Inter, un tercer color de acento, dorado como relleno de botón, esquinas redondeadas de 8–12px. Nada de "experiencia sensorial única" ni lenguaje sensacionalista: la voz vende con hechos de producto (notas, familia olfativa, duración), nunca con adjetivos.

**Key Characteristics:**
- Notación de perfumista en vez de iconografía de e-commerce: filas de ficha técnica, pirámide olfativa animada, recibos tabulares.
- Dorado al 10% máximo de superficie, siempre como tinta (borde, filete, texto sobre oscuro), nunca como pintura de área grande.
- Radio de 2px en todo lo interactivo, 0 en imagen de producto — geometría dura, nada de vocabulario de app SaaS.
- Ónix reservado a momentos de marca; Marfil y Blanco cargan catálogo y checkout.
- Sin sombras salvo una única flotante y discreta para menús/modales; las tarjetas se separan con borde de 1px, no con sombra.

## Colors

Paleta de 5 colores de marca más una escala de dorado y neutros derivados — deliberadamente corta para que el frasco fotografiado sea lo único saturado en pantalla.

### Primary
- **Oro JG** (`#D3AE6A`): único acento de marca. Filetes bajo títulos de sección (40px de ancho, 1px de alto), bordes e íconos, texto solo sobre Ónix. Prohibido como texto sobre fondo claro (contraste 2.09:1) — sobre claro se usa `gold-700` (`#8E6B2A`, 4.90:1, AA). **La Regla del 10%**: el dorado nunca supera el 10% de la superficie de una pantalla; pasar ese umbral es el momento en que la marca se ve a bisutería.

### Neutral
- **Ónix** (`#201E1F`): negro cálido, no `#000000`. Texto principal sobre claro; fondo de secciones de marca (hero, footer).
- **Marfil** (`#F7F5F1`): fondo por defecto del sitio. No blanco puro — quema menos en móvil. Catálogo y checkout viven aquí, nunca sobre Ónix.
- **Blanco** (`#FFFFFF`): superficie de tarjeta y fondo de fotografía de producto.
- **Humo** (`#6E6A67`): texto secundario y metadatos sobre claro. Sobre Ónix se reemplaza por `#B9B4B0` (8.07:1) — `Humo` sobre negro cae a 2.5:1 y es ilegible.
- Escala de dorado completa (`gold-50` a `gold-800`) y de tinta (`ink-100` a `ink-800`) documentada en `frontend/css/tokens.css`.

### Named Rules
**La Regla del Dorado como Tinta.** El dorado nunca es fondo de botón ni relleno de área grande; nunca degradado, nunca metalizado, nunca `text-shadow`. Va como borde, filete, ícono o texto sobre oscuro — es lo que separa esta marca del cliché número uno de la perfumería.

## Typography

**Display Font:** Newsreader (con Georgia, serif de respaldo)
**Body Font:** Jost (con Futura, Century Gothic, system-ui de respaldo)

**Character:** Un serif editorial de contraste moderado (evoca el cuaderno técnico, sin la fragilidad de un didone) contra una geométrica neutral (puente con el "JG" macizo del logo). Dos familias, nunca más — la letra del logotipo vive solo en el logo.

> Cambio de fuente (post-lanzamiento): el display original era Bodoni Moda, un didone de contraste muy alto. En pruebas reales, sus trazos finos se volvían casi invisibles contra fondos claros en monitores de escritorio de densidad estándar — no solo por debajo de cierto tamaño, el problema persistía incluso en tamaños grandes de título. Se reemplazó por Newsreader (mismo serif ya usado en la combinación "Cálido"), que mantiene el tono editorial/elegante pero con un contraste de trazo mucho más moderado y un eje óptico pensado para lectura en pantalla.

### Hierarchy
- **Display** (500, clamp 40–64px, 1.05): hero, una vez por página.
- **H1** (500, clamp 32–48px, 1.15): título de página.
- **H2** (500, clamp 28–34px, 1.2): título de sección, siempre con el filete dorado de 40px debajo.
- **H3** (500, 20–22px, 1.3, Jost): nombre de producto en tarjeta.
- **Body** (400, 16px, 1.6): texto general, máximo 68 caracteres de ancho de línea.
- **Small** (400, 14px, 1.5): texto secundario, campos de formulario, líneas de metadatos (`.text-small`).
- **Meta** (400, 13px, 1.4): segunda línea bajo el nombre en tarjeta de producto (casa · tamaño) — un paso por debajo de Small a propósito, para no competir con el nombre.
- **Label** (500, 12px, 1.4, tracking 0.03em): etiquetas de stock, tamaños en ml — nunca mayúsculas sostenidas salvo "PARFUMS" dentro del logo.
- **Price** (600, 22–26px, Newsreader, 1): precio en ficha de producto.
- **Price card** (600, 17px, Jost, 1): precio en tarjeta de catálogo y total de recibo (`.ledger-row-total`) — Jost, no Newsreader, para que no se vuelva ruido repetido en grilla.
- **Nota itálica** (400, 15px, Newsreader): valor de fila técnica (`.spec-row dd`) y nombre de nota en la escalera olfativa (`.notes-step-name`) — la única cursiva permitida, reservada a información real, nunca decorativa.

### Named Rules
**Piso de 28px para títulos.** El display font (Newsreader) se mantiene legible en tamaños más chicos que un didone clásico gracias a su eje óptico, pero los títulos (Display/H1/H2) no bajan de 28px de todas formas — es el tamaño donde cualquier serif con algo de contraste de trazo se lee con comodidad sin esfuerzo, en cualquier densidad de pantalla. Por debajo de eso (nombre de producto en tarjeta, etiquetas), se usa Jost.

## Layout

Mobile-first real: se resuelve primero a 375–430px y desde ahí se expande a una segunda composición completa en escritorio (nunca un recorte). Contenedor máximo 1200px, 24px de margen lateral en móvil / 48px en escritorio. Retícula de 12 columnas en escritorio, 4 en móvil; catálogo en 2 columnas en móvil, 3 en tablet, 4 en escritorio (breakpoints 640px / 1024px). Escala de espaciado estrictamente de 4px (4, 8, 12, 16, 24, 32, 48, 64, 96, 128 — nada fuera de esta escala). Aire vertical entre secciones: 64px en móvil, 96px en escritorio — la sensación de lujo es espacio en blanco, no dorado.

## Elevation & Depth

Sistema plano por decisión: las tarjetas de producto se separan con borde de 1px (`ink-100`), nunca con sombra. Una única sombra existe en todo el sistema, reservada a elementos flotantes (menú, modal).

### Shadow Vocabulary
- **float** (`box-shadow: 0 8px 24px rgba(32, 30, 31, .12)`): único uso permitido, menús y modales.

### Named Rules
**La Regla del Borde, no la Sombra.** Toda separación de tarjeta o superficie en reposo se resuelve con un borde de 1px; la sombra flotante se reserva a lo que literalmente se superpone al contenido.

## Shapes

Radio de 2px en botones, campos y tarjetas — geometría casi dura, deliberadamente lejos del vocabulario redondeado (8–12px) de una app SaaS. Radio 0 en toda imagen de producto: el frasco de perfume es geometría dura, no se suaviza. Bordes de 1px como separador primario (`ink-100` sobre claro, `#3A3739` sobre Ónix).

## Components

### Buttons
- **Shape:** radio 2px, alto 48px, padding horizontal 24px.
- **Primary:** fondo Ónix, texto blanco, borde 1px Ónix. Hover: fondo `ink-800` (`#2C2A2B`). Focus: outline 2px `gold-400` con 2px de offset.
- **Secondary:** fondo transparente, texto Ónix, borde 1px `ink-300`. Hover: borde `gold-600`.
- **onDark:** fondo transparente, texto y borde `gold-400`. Hover: fondo `gold-400`, texto Ónix — el único momento en que el dorado llena un área, y solo porque el estado hover es transitorio, no la superficie en reposo.
- Todo botón deshabilitado baja a 50% de opacidad y `cursor: not-allowed`.

### Cards / Containers
- **Corner Style:** 2px.
- **Background:** Blanco sobre fondo Marfil.
- **Border:** 1px `ink-100` en reposo; `gold-200` en hover (150ms, sin movimiento — nunca `transform` en hover de tarjeta de producto).
- **Excepción acotada — tarjeta de clase y logo de marca:** en el carrusel de clases y el de marcas (home), la imagen/logo sí escala levemente en hover/focus-visible (`transform: scale()`, ver Carrusel de clases / Carrusel de marcas más abajo) — la tarjeta en sí no se mueve ni gana sombra, solo el contenido interno. Es la única excepción a "nunca transform en hover" de esta sección, y no se extiende a la tarjeta de producto.
- **Shadow Strategy:** ninguna — ver Elevation & Depth.

### Inputs / Fields
- **Style:** fondo blanco, borde 1px `ink-300`, radio 2px, alto 48px, label de 14px en `text-muted` encima del campo.
- **Focus:** outline 2px `gold-600` con 1px de offset + borde `gold-600`.
- **Error:** texto de 13px en `danger` (`#9E3B34`) bajo el campo — el color nunca es el único indicador.

### Navigation
- Barra fija (`sticky top:0`), fondo Marfil, borde inferior 1px `ink-100`, alto 64px. Sólida arriba del todo; apenas se hace scroll pasa a vidrio esmerilado (semitransparente + blur), sin quedarse como franja plana pegada arriba. Este es el comportamiento por defecto en toda página que no tenga una sección oscura pegada debajo del header.
- **Excepción — home:** el header flota transparente sobre el banner en vez de quedar sólido (evita la franja sólida entre la barra de anuncios y el banner). Se saca del flujo normal (`position:absolute`, con el alto real de la barra de anuncios como offset) para que el banner suba y quede detrás; un degradado oscuro sutil (~160px, sin caja visible) hace de "sombrita" para que el logo e íconos —en blanco acá— se lean sobre cualquier foto. Apenas se hace scroll pasa a `position:fixed` y recupera el header sólido/vidrio de siempre, con el logo e íconos oscuros otra vez. Es la única excepción a la regla de arriba porque es la única página con una sección oscura pegada debajo del header — no se replica en el resto del sitio (catálogo, carrito, etc. arrancan con fondo claro, un logo blanco ahí se perdería).
- Escritorio (≥1024px): una sola fila compacta en grid de 3 columnas — clases del catálogo (Mujer/Hombre/Ocasiones...) a la izquierda, logo centrado, buscador + cuenta + carrito a la derecha. Links de texto sin mayúsculas, sin subrayado permanente (solo al hover, en dorado).
- Móvil: logo centrado con menú hamburguesa a la izquierda y el ícono de carrito a la derecha (visible siempre, para no perderlo de vista); buscador, clases y cuenta se recogen en el panel del menú.
- Ícono de carrito con contador circular en `gold-800`.

### Spec Row (firma de la marca)
Fila de ficha técnica: `dt` de 12px en `text-muted` a la izquierda (columna fija de 88px), `dd` en Newsreader itálica de 15px a la derecha, separadas por borde inferior de 1px. Reemplaza cualquier patrón de "ícono + etiqueta" para mostrar notas, concentración, tamaño. Reutilizable en cualquier superficie que necesite comunicar un hecho de producto en vez de un adorno.

### Scent Diagram (firma de la marca)
Pirámide olfativa como notación, no como ilustración: tres filas (Salida / Corazón / Fondo) con una barra de progreso de 1px de alto que se llena en dorado con `cubic-bezier(0.16, 1, 0.3, 1)` al cargar la página, respetando `prefers-reduced-motion`. Vive sobre fondo Ónix.

### Ledger Row (firma de la marca)
Fila de recibo con `justify-content: space-between` y números tabulares (`font-variant-numeric: tabular-nums`), borde inferior 1px, la fila de total con borde superior más grueso y peso 600. Usada en resumen de carrito, checkout y detalle de pedido — nunca se reinventa una tabla de precios distinta en otra página.

### Foto con texto superpuesto (banner / galería)
Vocabulario compartido entre el banner del home y la sección de galería — cualquier foto administrable puede llevar título, subtítulo y botón encima, con tres controles por foto: **posición del texto** (izquierda/centro/derecha, mueve el bloque de texto entero), **oscurecido** (0–100%, una capa `rgba(32,30,31,·)` entre la foto y el texto — reemplaza el alpha fijo que había al principio) y **desenfoque** (0–20px, `filter:blur()` sobre la imagen con un `scale(1.1)` para que el blur no deje un borde claro en el límite de la foto). El banner además tiene proporción fija (`aspect-ratio`, 8/3 escritorio · 4/5 móvil) con `object-fit:cover`: nunca se genera marco, se recorta la imagen si hace falta — decisión explícita del cliente sobre priorizar "sin marco" por encima de "sin recorte". Transición entre fotos del banner y entre mensajes de la barra de anuncios (cuando se elige "Deslizamiento"): empuje suave con `transform`, no un cambio brusco — la que sale se desliza hacia un lado mientras la que entra viene del otro, tomando siempre el camino más corto del círculo al volver de la última a la primera.

### Bloque centrado (páginas de texto)
Contacto, Quiénes somos y Envíos y políticas usan una columna de 760px centrada (en vez del `container` de 1200px a todo lo ancho) para que el título, el texto y cualquier formulario se lean como un solo bloque compacto en el centro de la pantalla, no estirados de borde a borde. Mismo criterio en cualquier página nueva que sea mayormente texto/lectura, no catálogo ni grilla.

### Carrusel de clases
Sección administrable (`classes_carousel`) que muestra las clases (categorías) del catálogo como tarjetas de foto — todas las activas o una selección manual ordenable, leídas en vivo de la pestaña Clases del panel, sin duplicar datos en la sección. Tarjeta con proporción fija (`aspect-ratio: 3/4`) y `object-fit:cover`, radio 0 en la imagen y 2px en la tarjeta; texto superpuesto (eyebrow en Jost 14px/500 y nombre en Newsreader ≥28px/500, sin mayúsculas sostenidas) sobre una capa `rgba(32,30,31,·)` graduable por clase (`overlay_darkness`, mismo vocabulario que banner/galería) más el mismo control de posición del texto. Indicador circular con borde 1px `gold-400` y flecha, que se llena de `gold-400` con flecha Ónix en hover — mismo criterio transitorio que `button-onDark`. En hover/focus-visible la imagen (no la tarjeta) escala a ~1.06 con `cubic-bezier(0.16,1,0.3,1)` en 500ms; sin animación bajo `prefers-reduced-motion`. Toda la tarjeta es un único `<a>` al catálogo filtrado por esa clase (`/catalogo.html?category_id=`), sin enlaces anidados. Pista con `scroll-snap-type:x mandatory` (deslizamiento nativo al dedo en móvil) y flechas que avanzan una tarjeta por clic, deshabilitadas en los extremos o con vuelta si el autoavance está activo — cantidad de tarjetas visibles configurable por pantalla (móvil/tablet/escritorio), por defecto 1.3/3/4 (el .3 asoma la siguiente tarjeta a propósito, para invitar al deslizamiento).

### Carrusel de marcas
Sección administrable (`brands_carousel`), pensada para ir justo debajo del carrusel de clases: logos de marca (tabla `brands` nueva, sin relación con `Product.house`) sobre fondo Marfil, altura uniforme (48px móvil / 56px escritorio) y ancho automático, centrados. Escala de grises por defecto (`filter:grayscale(1)`, opacidad ~0.6 — misma franja de logos de pago que ya usa BRAND.md), con opción de color original. Dos modos: **flechas** (mismo carrusel de scroll-snap que el de clases) o **continuo** (pista duplicada + `@keyframes` de deslizamiento lento, se pausa en hover/foco; bajo `prefers-reduced-motion` no hay animación y el carrusel queda en modo flechas). En hover/focus-visible el logo escala a ~1.08 y, si está en escala de grises, pasa a color; sin escala bajo `prefers-reduced-motion`, solo el cambio de color. El catálogo no filtra por marca hoy (`Product.house` es texto libre, sin parámetro de filtro estructurado) — el enlace de cada logo es `link_url` libre que pone el admin, no un filtro automático.

## Do's and Don'ts

### Do:
- **Do** usar `.spec-row`, `.scent-diagram` y `.ledger-row` como el vocabulario compartido para cualquier pantalla nueva que muestre hechos de producto o dinero — son la firma visual de la marca, no un componente de una sola página.
- **Do** usar los mismos tres controles (posición del texto, oscurecido, desenfoque) para cualquier foto administrable nueva que lleve texto encima — no inventar un cuarto patrón de overlay distinto al de banner/galería.
- **Do** mantener el dorado por debajo del 10% de superficie visible en cualquier pantalla nueva.
- **Do** usar Marfil o Blanco como fondo de cualquier pantalla transaccional (catálogo, carrito, checkout, cuenta); Ónix solo en momentos de marca.
- **Do** escribir copy con hechos de producto (notas, familia, duración, estela) en vez de adjetivos de relleno.

### Don't:
- **Don't** usar dorado como fondo de botón o relleno de área grande, ni degradados o efectos metalizados sobre él.
- **Don't** redondear nada a más de 2px, ni usar sombra para separar una tarjeta en reposo.
- **Don't** escribir frases genéricas de perfumería ("experiencia sensorial única", "despierta tus sentidos") ni usar mayúsculas sostenidas fuera de "PARFUMS" en el logo.
- **Don't** inventar contenido de cliente (productos, precios, fotografía, testimonios) que el cliente no haya entregado todavía.

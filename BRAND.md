# JG Parfums — Manual de marca

`docs/BRAND.md` · v0.3 (borrador) · 2026-09-07 · fuente de verdad para color, tipografía, logo y voz.
Todo lo marcado con **[POR CONFIRMAR]** son decisiones del cliente que aún bloquean o pueden cambiar el diseño.

---

## 1. Contexto y supuestos

Lo único confirmado hoy es el logotipo. Todo lo demás en este documento parte de estos supuestos; si alguno es falso, cambia la dirección visual, no solo los detalles.

| # | Supuesto | Impacto si es falso |
|---|---|---|
| S1 | **Confirmado.** Tienda de perfumes que vende al consumidor final (B2C) en Colombia. | — |
| S2 | Catálogo de decants / perfumes árabes o inspirados, precio medio. | Si son originales de nicho de alta gama, sube el minimalismo y baja la densidad de promociones. |
| S3 | Objetivo principal del sitio: **vender** (o captar pedido por WhatsApp), no informar. | Si es solo presencia de marca, la home cambia completa. |
| S4 | Español de Colombia, tratamiento de "tú". | Cambia toda la copy. |
| S5 | **Confirmado.** Ventas mayoritariamente desde móvil, pero el sitio debe quedar igual de resuelto en escritorio. | — |

Confirmado S1 y S5. El diseño se hace **mobile-first**: se resuelve primero a 375–430 px y desde ahí se expande. Escritorio no es un descarte, es una segunda composición real: a partir de 1024 px el catálogo pasa a 4 columnas, la ficha de producto se parte en dos (galería fija a la izquierda, información con scroll a la derecha) y el hero gana aire vertical. Ningún elemento se esconde en escritorio por comodidad de implementación.

**[POR CONFIRMAR] antes de la etapa de diseño visual:** qué vende exactamente, rango de precios, si hay checkout o WhatsApp, si hay tienda física, competencia directa que le gusta al cliente y competencia con la que no quiere parecerse.

---

## 2. Lectura crítica del logo

Antes de construir sobre él, conviene saber qué aguanta y qué no.

**Lo que funciona**
- Contraste de pesos alto: "JG" macizo contra "PARFUMS" fino y muy espaciado. Eso ya es una jerarquía de marca y la puedo replicar en la tipografía del sitio.
- La estrella dorada es el único punto de color: es el elemento con más potencial de convertirse en el activo reutilizable (favicon, viñetas, separadores, marca de agua).

**Problemas reales que hay que resolver**
1. ~~Solo hay PNG de 700×588.~~ **Resuelto.** El logo está vectorizado a SVG; el original en PNG queda solo como referencia histórica y no se usa en el sitio.
2. ~~La versión "blanco" no es utilizable sobre fondo oscuro.~~ **Resuelto.** El núcleo de la estrella era negro `#201E1F` y dejaba un hueco sobre fondo oscuro; en la versión corregida el núcleo va en blanco.
3. **La estrella se solapa con la G y con el descanso de la J.** A menos de ~120 px de ancho la estrella se convierte en ruido y el conjunto se lee sucio. De ahí el tamaño mínimo de la sección 6.
4. **Tensión tipográfica sin resolver.** "JG" es un grotesco geométrico pesado; "PARFUMS" es un romano clásico de proporciones anchas. Es una mezcla de dos épocas. La resuelvo en el sitio eligiendo tipografías que hagan de puente en vez de reforzar el choque.
5. **Negro + dorado es el cliché número uno de la perfumería.** No lo voy a evitar (es lo que dicta el logo), pero sí voy a evitar la versión barata de ese cliché: nada de degradados dorados, nada de dorado metalizado falso, nada de dorado como relleno de áreas grandes. El dorado se usa como **tinta**, no como pintura.

---

## 3. Color

### 3.1 Extracción del logo

Valores medidos pixel a pixel sobre los PNG entregados:

| Elemento | Hex medido | Notas |
|---|---|---|
| Letras JG / PARFUMS | `#201E1F` | Negro cálido, ligeramente desaturado. No es `#000000`. |
| Estrella (contorno) | `#D3AE6A` (mediana `#D0AE6D`) | Dorado champán, HSL 39° 55% 63%. No es dorado saturado. |
| Núcleo de la estrella | `#201E1F` | Mismo negro. |
| Fondo | `#FFFFFF` | Blanco puro. |

### 3.2 Paleta base (5 colores)

```
Ónix        #201E1F   base oscura, texto sobre claro, fondo de secciones de producto
Oro JG      #D3AE6A   acento único de marca: filetes, íconos, estados activos
Marfil      #F7F5F1   fondo claro por defecto (no blanco puro: quema menos en móvil)
Blanco      #FFFFFF   superficies de tarjeta, fondo de foto de producto
Humo        #6E6A67   texto secundario, metadatos, placeholders
```

Solo 5. Un sexto color decorativo es lo que convierte una marca de perfumería en una marca genérica.

### 3.3 Escala de dorado

El dorado del logo (`#D3AE6A`) **no sirve para texto sobre fondo claro**: contraste 2.09:1, muy por debajo de 4.5:1. Por eso la escala baja hacia versiones oscuras para texto y sube hacia versiones claras para fondos.

| Token | Hex | Contraste vs blanco | Contraste vs Ónix | Uso permitido |
|---|---|---|---|---|
| `gold-50` | `#F8F2E7` | 1.11 | 14.88 | Fondos de sección muy suaves |
| `gold-100` | `#EFE1C8` | 1.29 | 12.85 | Bordes sobre claro, hover de fondo |
| `gold-200` | `#E3CCA1` | 1.57 | 10.59 | Filetes decorativos |
| **`gold-400`** | **`#D3AE6A`** | 2.09 | **7.92** | **Color de marca.** Texto e íconos **solo sobre Ónix**. Nunca texto sobre claro. |
| `gold-500` | `#CB9F4E` | 2.44 | 6.79 | Hover del dorado sobre oscuro |
| `gold-600` | `#B18534` | 3.35 | 4.95 | Bordes e íconos grandes sobre claro (no texto pequeño) |
| `gold-700` | `#8E6B2A` | 4.90 | 3.38 | **Texto dorado sobre fondo claro** (cumple AA) |
| `gold-800` | `#6A501F` | 7.55 | 2.19 | Texto dorado sobre claro con más contraste, enlaces visitados |

### 3.4 Neutros

| Token | Hex | Uso |
|---|---|---|
| `ink-900` | `#201E1F` | Texto principal sobre claro, fondos oscuros |
| `ink-800` | `#2C2A2B` | Superficie elevada sobre fondo Ónix (tarjeta en modo oscuro) |
| `ink-600` | `#6E6A67` | Texto secundario |
| `ink-300` | `#C9C4BF` | Bordes sobre claro |
| `ink-100` | `#EDE9E3` | Divisores, fondo alterno |
| `paper` | `#F7F5F1` | Fondo por defecto |
| `white` | `#FFFFFF` | Tarjetas, fondo de producto |

Texto sobre Ónix: blanco 16.58:1, `ink-100` 13.71:1, y para texto secundario en oscuro usar `#B9B4B0` (8.07:1) en vez de `ink-600` (que sobre negro queda en 2.5:1 y es ilegible).

### 3.5 Semánticos

Derivados, no inventados: mismo nivel de saturación baja que el dorado para que no desentonen.

```
success  #4E7A52   confirmación de pedido, stock disponible
warning  #B5772A   últimas unidades, envío demorado
danger   #9E3B34   error de formulario, agotado
info     #3F5D73   avisos neutros
```

### 3.6 Reglas de uso del color

- **Proporción 60 / 30 / 10:** 60% neutro claro u oscuro, 30% fotografía de producto, **máximo 10% dorado**. Si el dorado pasa del 10% de la superficie, la página se ve a bisutería.
- El dorado nunca es fondo de un botón grande. Va como borde, filete, ícono, subrayado o texto sobre oscuro.
- Prohibidos: degradados dorados, sombras doradas, `text-shadow`, efectos metalizados, dorado sobre dorado.
- Las secciones oscuras (`ink-900`) se usan para momentos de marca (hero, historia, banner de campaña). El catálogo y el checkout van sobre claro: leer precios y llenar formularios sobre negro cansa y baja conversión.
- Las fotos de producto aportan el color real de la página. La paleta es deliberadamente neutra para que el frasco sea lo único saturado en pantalla.

### 3.7 Tokens (CSS)

```css
:root {
  /* marca */
  --jg-onyx: #201E1F;
  --jg-gold: #D3AE6A;
  --jg-paper: #F7F5F1;
  --jg-white: #FFFFFF;
  --jg-smoke: #6E6A67;

  /* escala dorado */
  --gold-50:  #F8F2E7;
  --gold-100: #EFE1C8;
  --gold-200: #E3CCA1;
  --gold-400: #D3AE6A;
  --gold-500: #CB9F4E;
  --gold-600: #B18534;
  --gold-700: #8E6B2A;
  --gold-800: #6A501F;

  /* neutros */
  --ink-900: #201E1F;
  --ink-800: #2C2A2B;
  --ink-600: #6E6A67;
  --ink-300: #C9C4BF;
  --ink-100: #EDE9E3;

  /* semánticos */
  --success: #4E7A52;
  --warning: #B5772A;
  --danger:  #9E3B34;
  --info:    #3F5D73;

  /* roles (lo que se usa en los componentes) */
  --bg: var(--jg-paper);
  --surface: var(--jg-white);
  --text: var(--ink-900);
  --text-muted: var(--ink-600);
  --border: var(--ink-300);
  --accent: var(--gold-400);
  --accent-text: var(--gold-700); /* dorado legible sobre claro */
}

[data-theme="dark"] {
  --bg: var(--ink-900);
  --surface: var(--ink-800);
  --text: #FFFFFF;
  --text-muted: #B9B4B0;
  --border: #3A3739;
  --accent: var(--gold-400);
  --accent-text: var(--gold-400);
}
```

Usa siempre los **roles** (`--text`, `--accent`) en los componentes, nunca `--gold-400` directo. Así el día que el cliente pida cambiar el dorado, tocas una línea.

Equivalente en Tailwind v4 (`app/globals.css`):

```css
@theme {
  --color-onyx: #201E1F;
  --color-gold-50:  #F8F2E7;
  --color-gold-100: #EFE1C8;
  --color-gold-200: #E3CCA1;
  --color-gold-400: #D3AE6A;
  --color-gold-500: #CB9F4E;
  --color-gold-600: #B18534;
  --color-gold-700: #8E6B2A;
  --color-gold-800: #6A501F;
  --color-paper: #F7F5F1;
  --color-ink-100: #EDE9E3;
  --color-ink-300: #C9C4BF;
  --color-ink-600: #6E6A67;
  --color-ink-800: #2C2A2B;
}
```

---

## 4. Tipografía

### 4.1 Familias

| Rol | Familia | Por qué |
|---|---|---|
| Títulos y precios grandes | **Bodoni Moda** (Google Fonts, variable) | El didone es el idioma nativo de la perfumería: alto contraste de trazo, serifas finas. Hace de puente con el "PARFUMS" clásico del logo. Variable, así que solo pesa un archivo. |
| Interfaz, cuerpo, botones, formularios | **Jost** (Google Fonts, variable) | Geométrica, emparenta directo con el "JG" del logo. Neutral en formularios y legible en móvil. |

Dos familias, no más. La letra del logotipo **no se usa en la interfaz**: vive solo en el logo.

Fallbacks: `Bodoni Moda, "Didot", Georgia, serif` · `Jost, "Futura", "Century Gothic", system-ui, sans-serif`

**Reglas duras**
- Bodoni Moda solo desde 28 px hacia arriba. Por debajo, sus serifas finas desaparecen en pantallas de baja densidad y en móvil se ve rota.
- Nada de mayúsculas sostenidas para etiquetas de interfaz. Si algo necesita destacar, se destaca con tamaño o color, no con `text-transform: uppercase`. Excepción única: la palabra "PARFUMS" cuando aparece dentro del logo.
- Sin cursivas decorativas. La cursiva se reserva para nombres de notas olfativas (*bergamota, oud, ámbar*) y ahí sí es información, no adorno.
- Ancho de línea máximo 68 caracteres en textos largos.

### 4.2 Escala

Escala modular 1.25 (cuarta mayor reducida), base 16 px. Móvil primero; los tamaños de escritorio van entre paréntesis.

| Token | Tamaño | Familia | Peso | Interlínea | Tracking | Uso |
|---|---|---|---|---|---|---|
| `display` | 40 (64) | Bodoni Moda | 500 | 1.05 | -0.02em | Hero, una vez por página |
| `h1` | 32 (48) | Bodoni Moda | 500 | 1.15 | -0.01em | Título de página |
| `h2` | 26 (34) | Bodoni Moda | 500 | 1.2 | -0.01em | Título de sección |
| `h3` | 20 (22) | Jost | 500 | 1.3 | 0 | Nombre de producto en tarjeta |
| `body` | 16 | Jost | 400 | 1.6 | 0.005em | Texto general |
| `small` | 14 | Jost | 400 | 1.5 | 0.01em | Metadatos, notas de envío |
| `caption` | 12 | Jost | 500 | 1.4 | 0.03em | Etiquetas de stock, tallas de ml |
| `price` | 22 (26) | Bodoni Moda | 600 | 1 | 0 | Precio en ficha de producto |
| `price-card` | 17 | Jost | 600 | 1 | 0 | Precio en tarjeta de catálogo |

El precio de la ficha va en Bodoni y el de la tarjeta en Jost a propósito: en cuadrícula, el didone en tamaño pequeño y repetido 20 veces se vuelve ruido.

---

## 5. Espaciado, retícula y forma

- **Escala de 4 px:** 4, 8, 12, 16, 24, 32, 48, 64, 96, 128. Nada fuera de la escala.
- **Contenedor:** 1200 px máximo, 24 px de margen lateral en móvil, 48 px en escritorio.
- **Retícula:** 12 columnas en escritorio, 4 en móvil. Catálogo: 2 columnas en móvil, 3 en tablet, 4 en escritorio.
- **Aire vertical entre secciones:** 64 px móvil / 96 px escritorio. La sensación de lujo en web es principalmente espacio en blanco, no dorado.
- **Radio de esquina:** `2px` en botones, campos y tarjetas; `0` en imágenes de producto. Nada redondeado: el frasco de perfume es geometría dura.
- **Sombras:** una sola, y muy discreta, solo para elementos flotantes (menú, modal): `0 8px 24px rgba(32,30,31,.12)`. Las tarjetas de producto se separan con borde `1px solid var(--border)`, no con sombra.
- **Filete de marca:** línea de 1 px en `--gold-400` bajo los títulos de sección, con 40 px de ancho. Es el único adorno permitido y se usa con moderación.

---

## 6. Uso del logotipo

### 6.1 Versiones disponibles

Todas vectorizadas a partir del PNG original, con los colores exactos de la sección 3.1.

| Archivo | Contenido | Uso |
|---|---|---|
| `jg-parfums-onyx.svg` | Vertical, letras en Ónix, estrella dorada con núcleo Ónix | Fondos claros |
| `jg-parfums-blanco.svg` | Vertical, letras en blanco, estrella dorada **con núcleo blanco** | Fondos oscuros y foto con capa oscura |
| `jg-parfums-horizontal.svg` | JG y estrella a la izquierda, "PARFUMS" a la derecha, proporción 3.1:1 | Barra de navegación, encabezado de correo, firma |
| `jg-parfums-horizontal-blanco.svg` | Igual, en blanco | Barra de navegación sobre Ónix |
| `jg-star.svg` | Estrella suelta, núcleo Ónix | Viñetas, separadores, marca de agua sobre claro |
| `jg-star-blanco.svg` | Estrella suelta, núcleo blanco | Lo mismo sobre oscuro |
| `jg-star-solida.svg` | Estrella maciza dorada, sin núcleo | Favicon, avatar en redes, tamaños menores a 32 px |
| `favicon/favicon.ico`, `favicon-32.png`, `favicon-180.png`, `favicon-512.png` | Estrella maciza dorada sobre Ónix | Pestaña del navegador, ícono en iOS, manifiesto |

Notas de la vectorización:
- El SVG del logotipo completo pesa 29 KB, cerca de 9 KB servido con compresión. La estrella suelta pesa 7 KB y la maciza 4 KB: para íconos y viñetas se usa siempre la estrella, nunca el logo completo.
- Los colores están escritos como `fill` en cada trazo. Si algún día se necesita el logo en un solo color heredado del contexto, se reemplaza el `fill` por `currentColor`.
- La versión horizontal no es un simple reordenamiento: "PARFUMS" está escalado 1.75× respecto al original para que su altura quede en torno al 21% de la altura del monograma. A tamaño de barra de navegación, la proporción original se volvía ilegible.
- Los archivos vienen con `<title>` y `<desc>`, así que sirven directo como imagen accesible.

### 6.2 Reglas

- **Área de protección:** el alto de la letra "G" por los cuatro lados. Nada entra ahí, ni texto ni bordes ni foto.
- **Tamaño mínimo:** 120 px de ancho en pantalla y 30 mm impreso. Por debajo se usa solo la estrella.
- **Fondos válidos:** Marfil, blanco, Ónix. Sobre foto solo si hay una capa oscura al 55% mínimo por debajo, y ahí va la versión blanca.
- **Prohibido:** recolorear, poner el logo dorado completo, aplicar sombra o contorno, rotarlo, deformarlo, encerrarlo en una caja, animar la estrella con brillos, cambiar el espaciado de "PARFUMS".
- **Favicon:** estrella maciza dorada sobre Ónix, en 32×32 y 180×180 (apple-touch). El logo completo es ilegible a ese tamaño.

---

## 7. Fotografía e imagen

- Fondo neutro (Marfil u Ónix) o superficie de textura mate: piedra, lino, madera oscura. Nada de mármol blanco con vetas doradas ni pétalos de rosa esparcidos.
- Una sola fuente de luz, sombra larga y definida. La sombra es parte de la composición.
- Frasco siempre completo, sin recortes creativos, y a un tamaño consistente entre productos para que la cuadrícula del catálogo no baile.
- Formato de tarjeta: 4:5 vertical. Ficha de producto: 1:1.
- Todas las fotos del catálogo con el **mismo fondo y la misma luz**. Un catálogo de fotos mezcladas destruye más la percepción de marca que cualquier error tipográfico.
- Nada de imágenes de stock genéricas de "mujer oliendo su muñeca". Si no hay presupuesto de foto de estilo de vida, mejor solo producto sobre fondo limpio.
- Entrega: WebP con AVIF de respaldo, `srcset` de 400/800/1200, `loading="lazy"` salvo la del hero.

---

## 8. Voz y tono

**Cómo suena JG Parfums:** directo, sin adjetivos de más, con conocimiento real de producto. Un vendedor que sabe de notas olfativas y no exagera.

- Tratamiento: "tú" **[POR CONFIRMAR]**.
- Frases cortas. Verbos en voz activa. Sin signos de exclamación.
- Se nombra la información concreta: notas, familia olfativa, duración, estela, ocasión. Eso es lo que decide una compra de perfume.
- Prohibidas: "experiencia sensorial única", "despierta tus sentidos", "atrévete a ser tú". No dicen nada y las usa toda la competencia.
- Botones que dicen lo que hacen: `Agregar al carrito`, `Comprar por WhatsApp`, `Ver notas`. Nunca `Enviar` ni `Descubrir más`.
- Errores en formularios: qué pasó y cómo se arregla. "Falta el número de celular para coordinar la entrega", no "Campo inválido".
- Estado vacío del carrito: una invitación, no una disculpa. "Todavía no has agregado nada. Mira los más vendidos."

Ejemplo de descripción de producto, como plantilla:

> Amaderado oriental, para la noche. Abre con bergamota y azafrán, y se asienta en oud y ámbar. Dura entre 8 y 10 horas y deja estela. 100 ml.

---

## 9. Componentes base

```
Botón primario     fondo Ónix, texto blanco, borde 1px Ónix, radio 2px, 48px de alto
                   hover: fondo #2C2A2B    focus: outline 2px gold-400 con 2px de offset
Botón secundario   fondo transparente, texto Ónix, borde 1px ink-300
                   hover: borde gold-600
Botón sobre oscuro fondo transparente, texto y borde gold-400
                   hover: fondo gold-400 con texto Ónix
Enlace             texto Ónix con subrayado a 1px en gold-600, offset 3px
Campo de texto     fondo blanco, borde 1px ink-300, radio 2px, 48px de alto
                   focus: borde gold-600 + outline visible
Tarjeta producto   fondo blanco, borde 1px ink-100, sin sombra
                   hover: borde gold-200 (cambio de 150 ms, sin movimiento)
Badge stock bajo   texto 12px, color warning, sin fondo
```

Altura mínima de cualquier objeto tocable: 44 px. Foco de teclado siempre visible; nunca `outline: none` sin reemplazo.

---

## 10. Accesibilidad (mínimos no negociables)

- Texto normal 4.5:1, texto grande (≥24 px) 3:1. La tabla de la sección 3.3 ya trae los ratios medidos: úsala en vez de improvisar.
- El dorado `#D3AE6A` sobre blanco **está prohibido para texto**. Sobre claro se usa `gold-700`.
- El color nunca es el único indicador: "agotado" lleva texto, no solo un punto rojo.
- `prefers-reduced-motion` respetado en cualquier animación.
- Todas las imágenes de producto con `alt` con el nombre real del perfume.

---

## 11. Qué descarté y por qué

Para que quede el rastro de la decisión y no lo volvamos a discutir en tres semanas:

- **Fondo negro en todo el sitio.** Se ve espectacular en el hero y hunde la conversión en catálogo y checkout. Oscuro solo por secciones.
- **Playfair Display + Inter.** Es la pareja por defecto de cualquier plantilla de e-commerce; no dice nada de esta marca en particular.
- **Un tercer color de acento (vino, verde esmeralda).** El logo entrega dos colores. Un tercero diluye una identidad que ya es reconocible.
- **Dorado como relleno de botones.** Baja el contraste, obliga a texto oscuro sobre dorado y es el atajo visual más común de las tiendas de imitación.
- **Esquinas redondeadas de 8–12 px.** Vocabulario de aplicación SaaS, no de perfumería.

---

## 12. Pendientes

**Bloqueantes**
1. Confirmar S2, S3 y S4 de la sección 1: qué vende exactamente el catálogo, si el objetivo del sitio es vender o solo mostrar, y si el trato es de "tú" o de "usted". S1 y S5 ya están confirmados.

**Medios de pago: confirmados Wompi y Mercado Pago**

Los dos ofrecen las dos modalidades, así que la marca no queda amarrada a una sola forma de cobrar.

| | Wompi (Bancolombia) | Mercado Pago |
|---|---|---|
| Botón / cobro sin desarrollo | Sí. Link de pago generado desde el panel, con foto del producto, y botón de pago que se pega como etiqueta HTML. | Sí. Link de pago desde la app o el panel, y botón para pegar en el sitio con un `<script>` y el id de preferencia. |
| Pago sin salir del sitio | Sí, widget en ventana emergente sobre la propia página. | Parcial: el botón redirige al entorno de Mercado Pago; para pago embebido hay que usar sus módulos de checkout. |
| Pasarela con redirección | Sí, Web Checkout. | Sí, Checkout Pro. |
| Medios que cubre en Colombia | Tarjetas, PSE, Nequi, botón Bancolombia, QR, Daviplata, efectivo en corresponsales. | Tarjetas, PSE, efectivo, QR y saldo en Mercado Pago; cuotas con bancos asociados. |
| Comisión de referencia (2026, sujeta a plan) | Tarifa plana cercana a 2,65% + $700 + IVA para todos los medios; el PSE queda por debajo del mercado. | Alrededor de 3,29% + $800 + IVA con abono inmediato, ~2,79% + $800 esperando 14 días; PSE cerca de 2,99% + $900. |

Cifras referenciales tomadas de comparativas de 2026: hay que confirmarlas con cada proveedor antes de prometerle números al cliente, porque cambian por plan y volumen.

Lo que esto define para la marca:

- **El pago no se puede vestir de JG Parfums.** Ni Wompi ni Mercado Pago permiten rediseñar su interfaz de cobro. La identidad se corta en el momento más delicado de la compra, así que el paso previo (resumen del pedido, confirmación) y el posterior (página de "pedido confirmado") tienen que estar impecables y muy marcados: son lo único que sostiene la continuidad.
- **Los logos de terceros entran a la paleta sin permiso.** Wompi, Mercado Pago, Nequi, PSE y Visa traen sus propios colores. Van agrupados en una sola franja de confianza, en escala de grises al 60% de opacidad sobre fondo Marfil, tamaño uniforme y siempre por debajo del botón de compra. Nunca a color en medio de una página de producto: rompen la regla del 10% de dorado y ensucian todo.
- **Convivencia de dos pasarelas.** Mostrar las dos como opciones separadas obliga al cliente a elegir marca antes que medio de pago, y eso agrega fricción. Mejor un solo botón "Pagar" y que la elección sea por medio (tarjeta, PSE, Nequi), no por proveedor.
- **[POR CONFIRMAR]** si el pago es dentro del sitio (widget) o por link enviado por WhatsApp. Cambia la copy de los botones y la existencia misma de un carrito: si se cobra por link, el sitio deja de ser tienda y pasa a ser catálogo con pedido.

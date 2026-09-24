# Creación de productos — JG Parfums

Cómo se arma la ficha de un perfume para el catálogo. Este documento existe para que
cualquier conversación futura produzca fichas idénticas en criterio, formato y color,
sin volver a discutir las decisiones ya tomadas.

Fuentes de verdad relacionadas: `BRAND.md` (color, tipografía, voz), `DESIGN.md`
(sistema de diseño), `PRODUCT.md` (verdad de producto y principios).

---

## 1. Reparto de responsabilidades

| Lo aporta el cliente / desarrollador | Lo genera la ficha |
|---|---|
| Precio del frasco completo | Nombre exacto |
| Precio y stock de decants (5 ml / 10 ml) | Casa |
| Stock | Categoría |
| Tamaño real del frasco | Concentración |
| Fotografía | Descripción |
| Confirmación de concentración cuando no es visible | Notas olfativas + color por nota |

**Nunca se inventa** precio, stock, fotografía ni testimonios. Nunca se inventan notas
olfativas. Si una nota no se puede verificar, no entra.

---

## 2. Campos de la ficha

```
Nombre:         nombre completo, incluida la edición o el flanker
Casa:           la marca que aparece en el frasco
Categoría:      Hombre / Mujer / Unisex
Concentración:  EDT / EDP / Extrait / Parfum — tamaño en ml
Descripción:    párrafo corrido, 4–6 frases
Notas:          hasta 7, cada una con nombre y color hex, la más fuerte abajo
```

Se entrega en texto plano, sin bloque de código y sin sangría, porque el texto se copia
y se pega directo en el panel administrativo.

---

## 3. Proceso

1. **Identificar el producto exacto** a partir de la foto: marca, nombre completo,
   edición, concentración y tamaño si el frasco o la caja los muestran.
2. **Verificar la pirámide olfativa** contra varias fuentes antes de escribir. El sitio
   oficial de la casa tiene prioridad; Fragrantica sirve de contraste.
3. **Si las fuentes no coinciden**, escribir usando únicamente las notas en las que
   coinciden, y decirlo explícitamente en la entrega. Nunca elegir una pirámide al azar.
4. **Si la pirámide es genérica** ("notas especiadas", "acorde goloso", "notas
   amaderadas"), advertirlo y ofrecer una escalera más corta con solo las notas reales.
   Seis barras honestas valen más que siete con dos vacías.
5. **Verificar el rendimiento** contra reseñas de usuarios, no contra la copy de las
   tiendas que lo revenden.
6. **Señalar lo que haya que confirmar** contra el frasco físico: tamaño, concentración,
   edición, si es tester.

---

## 4. Descripción

Sigue la plantilla de `BRAND.md` §8. Frases cortas, voz activa, sin signos de
exclamación, sin adjetivos de relleno.

**Estructura:**

1. Familia olfativa + momento de uso (día/noche, clima, ocasión).
2. Salida: qué se siente primero y cómo se comporta.
3. Corazón: qué define el perfume y qué lo separa de sus parecidos.
4. Fondo: cómo cierra.
5. Duración y proyección, en rango honesto.
6. Tamaño en ml al final, cuando está confirmado.

**Prohibido:**

- "Experiencia sensorial única", "despierta tus sentidos", "atrévete a ser tú" y
  cualquier frase genérica de perfumería.
- Mencionar el perfume de nicho o designer al que el producto se parece. Ni "inspirado
  en", ni "clon de", ni "versión de", ni el nombre del original en ninguna parte.
  Es el principio 1 de `PRODUCT.md` y no tiene excepciones.
- Copy sexual o de desenfreno, aunque la casa lo use. Si el nombre del producto ya carga
  la provocación, la ficha no la repite.
- Describir el nombre en vez del producto. Si un perfume se llama "Amber Oud" y no lleva
  oud, la ficha no menciona oud.

**Duración y proyección:** se escribe el rango que reportan los usuarios reales, no el
que promete la tienda. Prometer de más genera reclamos; advertir de menos vende igual.
Cuando el cliente pruebe el producto, su experiencia pesa más que las reseñas.

---

## 5. Notas olfativas

- **Máximo 7 barras.** Las pirámides de 20 notas no se cargan completas: una escalera de
  20 barras no es notación, es una lista de ingredientes, y en móvil ocupa la pantalla.
- **Orden: la más fuerte abajo**, de salida a fondo.
- **Menos de 7 si la fórmula es corta.** No se inventa una séptima nota para llenar.
- **Qué se deja fuera:** moléculas que nadie reconoce (Ambrofix, Georgywood, ambroxan),
  notas redundantes con otra ya presente, y notas genéricas cuando ya hay dos en la
  escalera. Todo lo que se deja fuera se menciona en la descripción.
- **Qué se deja fuera por color:** si dos notas del mismo color quedarían en barras
  consecutivas y no se pueden separar, se saca la menos relevante. Ejemplo real:
  en Odyssey Mandarin Sky se sacó la naranja porque mandarina, naranja y azafrán habrían
  sido tres naranjas idénticos en las tres primeras barras.

---

## 6. Color de las notas

### Reglas

1. **Contraste mínimo 3:1 contra el fondo claro** (`#F7F5F1`). Es el mínimo de WCAG para
   objetos gráficos y `BRAND.md` §10 pide no improvisarlo. Se calcula, no se estima.
2. **Variante clara para fondo Ónix** cuando el hex principal no llega a 3:1 contra
   `#201E1F`. Se entrega junto a la ficha.
3. **Saturación baja.** El dorado de marca está en HSL 39° 55%; si las notas entran
   saturadas a tope compiten con el único acento de la marca y rompen la regla del
   60/30/10.
4. **Mismo hex para la misma nota en todo el catálogo.** Si la bergamota es verde en un
   perfume y naranja en otro, la escalera deja de ser notación y pasa a ser decoración.
5. **Barras consecutivas siempre distinguibles.** Cuando el perfume es monocromático
   (cuatro marrones, tres verdes), se separan por luminosidad y por tono, y se avisa para
   revisarlo montado en pantalla.

### Decisión de arquitectura pendiente

La escalera de notas aparece en la ficha de producto (fondo claro) y en el hero del home
(potencialmente fondo Ónix). Hoy el modelo guarda **un solo color por nota**, y muchos
hex no pasan contraste en los dos fondos. Hay que resolver una de tres:

- guardar dos hex por nota (claro / oscuro),
- restringir la escalera a fondos claros,
- pasar el hero a fondo claro.

Mientras no se decida, cada ficha entrega el hex principal y las variantes para Ónix.

---

## 7. Diccionario de notas

Valores canónicos. Cuando se cargue una nota nueva, se agrega aquí.

### Cítricos y frutas

| Nota | Hex | Variante Ónix |
|---|---|---|
| Bergamota | `#7E8A47` | — |
| Limón | `#8F8A2E` | `#A9A33B` |
| Hoja de cítricos | `#828C31` | — |
| Mandarina / naranja tangerina | `#B8752A` | — |
| Naranja | `#C4761F` | — |
| Toronja | `#C1614C` | — |
| Piña | `#A38425` | — |
| Mango | `#C06A24` | — |
| Melón | `#BC7A54` | — |
| Frutas tropicales | `#C47C46` | — |
| Coco | `#918974` | — |
| Granada | `#8E2F42` | `#B85368` |
| Frutos rojos | `#A63A48` | `#C25462` |
| Grosella negra | `#5A3A52` | `#8C5E82` |
| Cereza negra | `#7A2638` | `#AE5265` |

### Especias

| Nota | Hex | Variante Ónix |
|---|---|---|
| Azafrán | `#C2662A` | — |
| Jengibre | `#B27A3A` | — |
| Cardamomo | `#6F7A5E` | — |
| Nuez moscada | `#8A5B3A` | `#B0764B` |
| Clavo | `#6E3A28` | `#A8613F` |
| Pimienta de Timut | `#9A7A3C` | — |
| Pimienta rosa | `#B67682` | — |
| Pimienta verde | `#6E8A5E` | — |
| Especias (genérico) | `#9A5530` | `#B87048` |

### Hierbas y verdes

| Nota | Hex | Variante Ónix |
|---|---|---|
| Albahaca tailandesa | `#5E7A45` | `#7E9C62` |
| Salvia | `#5F7458` | `#82997A` |
| Abrótano | `#6E7C52` | — |
| Menta / hierbabuena | `#57937A` | — |
| Hierba cortada | `#4F7A3C` | `#6E9C58` |
| Ciprés | `#46664A` | `#6E9472` |
| Vetiver | `#4A5A3C` | `#7C9166` |
| Lavanda | `#6E6390` | `#948AB4` |

### Flores

| Nota | Hex | Variante Ónix |
|---|---|---|
| Rosa (Bulgaria / mayo) | `#A85A6E` | — |
| Jazmín | `#948769` | — |
| Fresia | `#A86E8C` | — |
| Violeta | `#6A4E8C` | `#9080B4` |
| Gardenia | `#948A6C` | — |
| Orquídea | `#A86A94` | — |
| Heliotropo | `#8A7AAE` | — |

### Maderas, resinas y fondo

| Nota | Hex | Variante Ónix |
|---|---|---|
| Oud | `#4E3B2C` | `#8E6E50` |
| Akigalawood | `#7A4F30` | `#B0764B` |
| Cedro | `#8A6248` | — |
| Sándalo | `#A07A62` | — |
| Madera de guayaco | `#6B5C4A` | `#948373` |
| Abedul | `#6E6154` | `#938575` |
| Pachulí | `#4F5232` | `#82855A` |
| Cashmeran | `#7C7684` | — |
| Ámbar | `#A96E22` | — |
| Ámbar gris | `#8A7550` | `#AB9269` |
| Incienso | `#6B6A63` | `#95948C` |
| Mirra | `#7A5230` | `#AE7A4C` |

### Dulces, almizcles y acordes

| Nota | Hex | Variante Ónix |
|---|---|---|
| Vainilla | `#A8863F` | — |
| Haba tonka / cumarina | `#6B4327` | `#A06840` |
| Caramelo / acorde goloso | `#9A6326` | `#BA7F3E` |
| Azúcar moreno | `#8C5A2E` | — |
| Almizcle | `#968973` | — |
| Gamuza | `#9C7C5C` | — |
| Té rooibos | `#A14A2C` | `#C0673F` |
| Coñac | `#8E4A22` | `#B4653A` |
| Ron | `#96602A` | `#B8804A` |
| Notas marinas / acorde marino | `#3D6B7E` | `#5E90A4` |
| Notas verdes (genérico) | `#5E7A45` | `#7E9C62` |

### Conflictos pendientes de unificar

Valores que cambiaron sobre la marcha o que quedaron duplicados. Hay que corregirlos
antes de cargar el catálogo:

- **Cedro:** las fichas de Bois Impérial, Dynasty y Nautica Voyage N-83 usan `#5F4A38`;
  Hawas Highness usa `#6F4C36`. El canónico es `#8A6248`.
- **Pachulí:** Bois Impérial, Eros Najim, Sugardaddy y Pomegranoudh usan `#5A4B33`.
  El canónico es `#4F5232`.
- **Ámbar:** Arabians Tonka, Drunk Lovers y Pomegranoudh usan `#B07C2F`.
  El canónico es `#A96E22`.
- **Frambuesa** (`#A83E56`, en Dynasty) y **frutos rojos** (`#A63A48`) son prácticamente
  el mismo color. Decidir si se consolidan en una sola entrada.
- **Notas verdes** comparte hex con **albahaca tailandesa**. Nunca coinciden en el mismo
  producto, pero conviene separarlas.

---

## 8. Verificaciones obligatorias antes de publicar

- **Tamaño.** Muchas casas venden el mismo perfume en 30, 50, 100, 120 y 200 ml.
  Si la foto no da escala, se confirma contra el frasco.
- **Concentración.** EDT, EDP, Extrait y Parfum no son intercambiables y el comprador
  que paga precio de Extrait lo sabe.
- **Flanker.** Casi todos los productos del catálogo pertenecen a líneas con cinco o más
  variantes que comparten frasco cambiando solo el color. El nombre va completo, siempre.
  Casos ya detectados: Bois Impérial vs Bois Impérial Extrait · Odyssey Mandarin Sky vs
  Mandarin Sky Elixir · Yara vs Yara Pink vs Yara Moi/Tous/Candy/Elixir · Bade'e Al Oud
  Oud For Glory vs Honor & Glory · Amber Oud Gold Edition vs Gold Edition Extreme ·
  Hawas For Him vs Ice/Black/Alpha/Highness.
- **Tester.** Si la caja dice TESTER / PROBADOR / FLACON DÉMONSTRATION, el producto es
  original pero no está destinado a reventa: viene en caja blanca y normalmente sin tapa.
  **Hay que declararlo en la ficha.** Ocultarlo genera el reclamo garantizado.
- **Falsificación.** Creed, Lattafa (Yara, Bade'e Al Oud) y los designers masivos son los
  más falsificados del mercado colombiano.

---

## 9. Cómo se comunica la autenticidad

No se pone un sello de "100% ORIGINAL" al lado del producto. En este mercado ese sello lo
usa justamente quien vende falsificaciones, y el comprador informado lo lee como alerta.

La autenticidad se comunica con:

- fotografía real del frasco que tiene el cliente, no la foto de catálogo del proveedor,
- código de lote visible cuando se pueda,
- una descripción precisa que demuestre conocimiento del producto.

Un vendedor que sabe de notas genera más confianza que un badge.

---

## 10. Fotografía

Reglas de `BRAND.md` §7, resumidas:

- Mismo fondo y misma luz en todo el catálogo. Un catálogo de fotos mezcladas destruye
  más la percepción de marca que cualquier error tipográfico.
- Frasco completo, sin recortes creativos, tamaño consistente entre productos.
- Tarjeta 4:5 · ficha 1:1.
- `alt` con el nombre real del perfume.
- Fotos de frascos usados, sin tapa o sobre mesa doméstica sirven como referencia para
  escribir la ficha, no como imagen de producto.

**Convención de nombre de archivo:** `casa-producto-edicion-NN.webp`, todo en minúscula
y con guiones. Ejemplo: `armaf-club-de-nuit-intense-man-01.webp`. Sin nombres escritos a
mano: con 40 productos en el bucket, los errores de tipeo son imposibles de rastrear.

---

## 11. Decisiones abiertas que afectan toda la carga

Ninguna está resuelta. Cada ficha nueva las hace más caras de cambiar.

1. **Taxonomía de categoría.** El backend guarda una sola categoría por producto y se está
   usando para género (Hombre / Mujer / Unisex). Eso deja sin resolver la navegación por
   casa y por familia olfativa. Ya se manifestó por dos lados: dos Fugazzi que pedirían
   agrupación por casa, y pares que se pisan por perfil (Vulcan Feu / Tropical Vibe,
   Odyssey Aqua / Odyssey Mandarin Sky).
2. **Posicionamiento "nicho".** El sitio dice que vende perfumes de nicho. El catálogo
   real mezcla nicho (Montale, Essential Parfums, Fugazzi, Creed) con árabe de volumen
   (Lattafa, Armaf, Rasasi, Al Haramain) y designer masivo (Versace, Carolina Herrera,
   Nautica). O se ajusta el texto de posicionamiento, o se ajusta el catálogo.
3. **Productos con reputación de versión.** Ocho de los dieciséis cargados se venden en
   el mercado declarándose inspirados en fragancias de nicho. Las fichas no lo mencionan
   nunca, pero el cliente necesita una respuesta lista para cuando se lo pregunten por
   WhatsApp, coherente con su propio posicionamiento.
4. **Decants como producto principal en referencias caras.** En Creed y en general en todo
   lo que pase cierto precio, el decant de 5 ml no es un extra: es la forma en que la
   gente compra en Colombia. La ficha de esos productos debería empujar el decant primero.

---

## 12. Productos ya documentados

| # | Producto | Casa | Categoría | Concentración |
|---|---|---|---|---|
| 1 | Arabians Tonka | Montale | Unisex | EDP 100 ml |
| 2 | Bois Impérial | Essential Parfums | Unisex | EDP 16% — tamaño por confirmar |
| 3 | Dynasty | Lattafa | Unisex | EDP 100 ml |
| 4 | Drunk Lovers | BORNTOSTANDOUT | Unisex | EDP — tamaño por confirmar |
| 5 | Eros Najim | Versace | Hombre | Parfum 200 ml |
| 6 | Club de Nuit Intense Man | Armaf | Hombre | EDT 105 ml |
| 7 | Vulcan Feu | French Avenue | Unisex | EDP 100 ml |
| 8 | Voyage N-83 | Nautica | Hombre | EDT 100 ml |
| 9 | Sugardaddy | Fugazzi | Unisex | Extrait — tamaño por confirmar |
| 10 | Pomegranoudh | Fugazzi | Unisex | Extrait — tamaño por confirmar |
| 11 | Carmina | Creed | Mujer | EDP — tamaño por confirmar |
| 12 | Hawas For Him Highness | Rasasi | Hombre | EDP — tamaño por confirmar |
| 13 | 212 Men NYC | Carolina Herrera | Hombre | EDT 100 ml — tester por confirmar |
| 14 | Tropical Vibe | Rayhaan | Unisex | EDP 100 ml |
| 15 | Amber Oud Gold Edition | Al Haramain | Unisex | EDP — tamaño por confirmar |
| 16 | Odyssey Mandarin Sky | Armaf | Hombre | EDP 100 ml |
| 17 | Yara | Lattafa | Mujer | EDP 100 ml |
| 18 | Bade'e Al Oud — Oud For Glory | Lattafa | Unisex | EDP 100 ml |
| 19 | Odyssey Aqua Edition | Armaf | Hombre | EDP 100 ml |

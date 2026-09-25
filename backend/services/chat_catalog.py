"""Contexto de catálogo para el chatbot.

El asistente vive en n8n y no tiene acceso a la base de datos, así que sin
esto no puede saber qué vende la tienda y solo puede hablar en general. En
cada mensaje se le manda, junto al `customer_context`, un resumen en texto
plano de las clases y los perfumes activos (precio final, descuento, notas,
decants, disponibilidad y enlace a la ficha) para que recomiende solo lo que
de verdad hay.

Solo sale información pública: lo mismo que ya ve cualquier visitante en el
catálogo — productos y clases activos, nunca stock exacto ni nada del panel.
"""
import logging
import os
import re
import unicodedata

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from models.category import Category
from models.product import Product, product_categories

logger = logging.getLogger("jg_parfums.chat")

# Cuántos productos activos (los más recientes) se consideran como máximo —
# alcanza de sobra para una tienda de nicho y evita traer todo si crece.
_MAX_PRODUCTS_LOADED = 300

# Tope de caracteres del texto que va al prompt (~2.500 tokens). Si el
# catálogo no cabe, se prioriza lo más relevante para lo que escribió el
# cliente y se avisa cuántos quedaron fuera.
_MAX_CATALOG_CHARS = 9000

_MAX_DESCRIPTION_CHARS = 140

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
# Palabras que aparecen en casi cualquier mensaje y no dicen nada del
# producto: contarlas como "coincidencia" desordenaría la relevancia.
_STOPWORDS = {
    "que", "los", "las", "para", "con", "por", "una", "uno", "del", "como", "quiero", "busco",
    "tienen", "tiene", "algo", "mas", "muy", "hay", "perfume", "perfumes", "favor", "hola",
    "buenas", "buenos", "dias", "tardes", "noches", "necesito", "recomiendas", "recomienda",
    "recomendar", "gustaria", "cual", "cuales", "sobre", "esta", "este", "son", "ser",
}


def _site_url() -> str:
    return os.environ.get("SITE_URL", "https://jgparfums.com.co").rstrip("/")


def _format_cop(amount: int) -> str:
    return f"${amount:,}".replace(",", ".")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _message_tokens(message: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(_normalize(message)) if t not in _STOPWORDS]


def _haystack(product: Product) -> str:
    parts = [
        product.name, product.house or "", product.concentration or "", product.description or "",
        *[c.name for c in product.categories],
        *[n.name for n in product.notes],
    ]
    return _normalize(" ".join(parts))


def _relevance(tokens: list[str], haystack: str) -> int:
    # También prueba el token sin "s" final: "amaderados" debe encontrar
    # "amaderado" (y viceversa entra por la búsqueda por subcadena).
    return sum(1 for t in tokens if t in haystack or (t.endswith("s") and t[:-1] in haystack))


def _shorten(text: str, max_chars: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _price_text(product: Product) -> str:
    if product.discount_percent:
        return (
            f"{_format_cop(product.final_price)} (antes {_format_cop(product.price)}, "
            f"{product.discount_percent}% de descuento)"
        )
    return _format_cop(product.price)


def _decants_text(product: Product) -> str:
    active = [v for v in product.variants if v.is_active]
    if not active:
        return "sin decants"
    items = [
        f"{v.size_ml} ml {_format_cop(v.final_price)}" if v.stock > 0 else f"{v.size_ml} ml agotado"
        for v in active
    ]
    return "decants: " + ", ".join(items)


def _product_line(product: Product, site_url: str) -> str:
    head = product.name + (f" ({product.house})" if product.house else "")
    parts = [head]
    if product.concentration:
        parts.append(product.concentration)
    parts.append(f"{product.size_ml} ml")
    parts.append(_price_text(product))
    parts.append("frasco disponible" if product.stock > 0 else "frasco agotado")
    parts.append(_decants_text(product))
    if product.categories:
        parts.append("clases: " + ", ".join(c.name for c in product.categories))
    if product.notes:
        # position 0 es la nota más suave (ver ProductNote): se listan de
        # más suave a más fuerte, tal cual las ve el cliente en la ficha.
        parts.append("notas (de más suave a más fuerte): " + ", ".join(n.name for n in product.notes))
    description = _shorten(product.description, _MAX_DESCRIPTION_CHARS)
    if description:
        parts.append(f"descripción: {description}")
    parts.append(f"{site_url}/producto.html?slug={product.slug}")
    return "- " + " · ".join(parts)


def _build_classes_block(db: Session, site_url: str) -> str:
    categories = (
        db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.sort_order, Category.id).all()
    )
    if not categories:
        return ""
    counts = dict(
        db.query(product_categories.c.category_id, func.count())
        .join(Product, Product.id == product_categories.c.product_id)
        .filter(Product.is_active.is_(True))
        .group_by(product_categories.c.category_id)
        .all()
    )
    lines = ["CLASES DISPONIBLES (cada una filtra el catálogo):"]
    for c in categories:
        count = counts.get(c.id, 0)
        detail = f" — {_shorten(c.eyebrow, 80)}" if c.eyebrow else ""
        noun = "perfume" if count == 1 else "perfumes"
        lines.append(f"- {c.name}{detail}: {count} {noun} · {site_url}/catalogo.html?category_id={c.id}")
    return "\n".join(lines)


def _build_catalog_context(db: Session, message: str) -> str:
    site_url = _site_url()
    products = (
        db.query(Product)
        .options(selectinload(Product.notes), selectinload(Product.variants), selectinload(Product.categories))
        .filter(Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
        .limit(_MAX_PRODUCTS_LOADED)
        .all()
    )
    classes_block = _build_classes_block(db, site_url)
    if not products:
        empty = "PERFUMES: el catálogo no tiene perfumes activos por ahora."
        return "\n\n".join(b for b in (classes_block, empty) if b)

    tokens = _message_tokens(message)
    # Más relevantes primero; a igual relevancia, lo disponible antes que lo
    # agotado, lo destacado antes y lo más reciente antes (el orden de la
    # consulta ya viene por fecha, y sorted es estable).
    ranked = sorted(
        products,
        key=lambda p: (-_relevance(tokens, _haystack(p)), p.stock <= 0, not p.is_featured),
    )

    budget = _MAX_CATALOG_CHARS - len(classes_block) - 200
    lines: list[str] = []
    used = 0
    for product in ranked:
        line = _product_line(product, site_url)
        if used + len(line) + 1 > budget and lines:
            break
        lines.append(line)
        used += len(line) + 1

    block = [f"PERFUMES ACTIVOS ({len(lines)} de {len(products)}):", *lines]
    if len(lines) < len(products):
        block.append(
            f"(Faltan {len(products) - len(lines)} perfumes que no caben acá; el catálogo completo está en {site_url}/catalogo.html)"
        )
    return "\n\n".join(b for b in (classes_block, "\n".join(block)) if b)


def build_catalog_context(db: Session, message: str) -> str:
    """Texto plano con las clases y los perfumes activos, ordenados por
    relevancia respecto a `message`. Nunca rompe el chat: si algo falla se
    devuelve vacío y el asistente sigue respondiendo, solo que sin catálogo
    (su prompt le dice que en ese caso no invente productos)."""
    try:
        return _build_catalog_context(db, message)
    except Exception:  # noqa: BLE001 - el chat no puede caerse por el catálogo
        logger.exception("No se pudo armar el contexto de catálogo del chat")
        return ""

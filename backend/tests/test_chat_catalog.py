from models.category import Category
from models.product import Product
from models.product_note import ProductNote
from models.product_variant import ProductVariant
from services.chat_catalog import build_catalog_context


def _category(db, name, slug, **kwargs):
    category = Category(name=name, slug=slug, **kwargs)
    db.add(category)
    db.flush()
    return category


def _product(db, slug, name, categories=(), notes=(), variants=(), **kwargs):
    defaults = dict(description="Un perfume.", size_ml=100, price=300000, stock=5, is_active=True)
    defaults.update(kwargs)
    product = Product(slug=slug, name=name, **defaults)
    product.categories = list(categories)
    db.add(product)
    db.flush()
    for position, note in enumerate(notes):
        db.add(ProductNote(product_id=product.id, name=note, color="#D3AE6A", position=position))
    for size_ml, price, stock, is_active in variants:
        db.add(ProductVariant(product_id=product.id, size_ml=size_ml, price=price, stock=stock, is_active=is_active))
    db.commit()
    return product


def test_catalog_context_lists_classes_and_products_with_price_notes_decants_and_url(db):
    arabes = _category(db, "Árabes", "arabes", eyebrow="Intensos y resinosos")
    _product(
        db, "oud-royal", "Oud Royal", categories=[arabes], house="Casa Nube", concentration="EDP",
        price=350000, discount_percent=10, notes=["Bergamota", "Rosa", "Oud"],
        variants=[(5, 40000, 3, True), (10, 70000, 0, True)],
        description="Amaderado y profundo.",
    )
    db.commit()

    text = build_catalog_context(db, "Hola")

    assert "CLASES DISPONIBLES" in text
    assert "- Árabes — Intensos y resinosos: 1 perfume · https://jgparfums.com.co/catalogo.html?category_id=" in text
    assert "Oud Royal (Casa Nube)" in text
    assert "EDP" in text and "100 ml" in text
    # 350.000 con 10% de descuento = 315.000; el precio de antes también sale.
    assert "$315.000 (antes $350.000, 10% de descuento)" in text
    assert "frasco disponible" in text
    # El decant se cobra con el descuento del producto; el agotado no lleva precio.
    assert "decants: 5 ml $36.000, 10 ml agotado" in text
    assert "clases: Árabes" in text
    assert "notas (de más suave a más fuerte): Bergamota, Rosa, Oud" in text
    assert "descripción: Amaderado y profundo." in text
    assert "https://jgparfums.com.co/producto.html?slug=oud-royal" in text


def test_catalog_context_excludes_inactive_products_and_classes_and_hides_exact_stock(db):
    activa = _category(db, "Florales", "florales")
    _category(db, "Oculta", "oculta", is_active=False)
    _product(db, "visible", "Visible", categories=[activa], stock=7)
    _product(db, "apagado", "Apagado", is_active=False)
    db.commit()

    text = build_catalog_context(db, "")

    assert "Visible" in text
    assert "Apagado" not in text
    assert "Oculta" not in text
    # Nunca el número exacto de unidades: solo disponible/agotado.
    assert "7" not in text.split("Visible", 1)[1].split("\n")[0].replace("100 ml", "")


def test_catalog_context_marks_sold_out_bottle_and_product_without_decants(db):
    _product(db, "agotado", "Agotado", stock=0)
    db.commit()

    text = build_catalog_context(db, "")

    assert "frasco agotado" in text
    assert "sin decants" in text


def test_catalog_context_puts_relevant_products_first(db):
    citrico = _category(db, "Cítricos", "citricos")
    _product(db, "aa", "Zeta Oscuro", notes=["Oud"])
    _product(db, "bb", "Brisa", categories=[citrico], notes=["Limón"])
    db.commit()

    text = build_catalog_context(db, "Busco algo cítrico")

    assert text.index("Brisa") < text.index("Zeta Oscuro")


def test_catalog_context_matches_plural_and_accents(db):
    _product(db, "aa", "Zeta", description="Familia amaderada y cálida.")
    _product(db, "bb", "Otro", description="Fresco.")
    db.commit()

    text = build_catalog_context(db, "quiero perfumes AMADERADAS")

    assert text.index("Zeta") < text.index("Otro")


def test_catalog_context_truncates_by_budget_keeping_most_relevant(db, monkeypatch):
    for i in range(6):
        _product(db, f"p{i}", f"Perfume {i}", description="x" * 100)
    _product(db, "rosa", "Rosa Nocturna", notes=["Rosa"])
    db.commit()
    monkeypatch.setattr("services.chat_catalog._MAX_CATALOG_CHARS", 900)

    text = build_catalog_context(db, "una rosa")

    assert "Rosa Nocturna" in text
    assert "Faltan" in text
    assert "https://jgparfums.com.co/catalogo.html" in text


def test_catalog_context_empty_catalog_says_so_instead_of_being_blank(db):
    text = build_catalog_context(db, "hola")

    assert "no tiene perfumes activos" in text


def test_catalog_context_uses_site_url_env(db, monkeypatch):
    _product(db, "x", "X")
    db.commit()
    monkeypatch.setenv("SITE_URL", "https://staging.example.com/")

    assert "https://staging.example.com/producto.html?slug=x" in build_catalog_context(db, "")


def test_catalog_context_never_breaks_the_chat(db, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("db caída")

    monkeypatch.setattr("services.chat_catalog._build_catalog_context", _boom)

    assert build_catalog_context(db, "hola") == ""


def test_chat_message_forwards_catalog_context_to_n8n(client, db, monkeypatch):
    _product(db, "oud-royal", "Oud Royal")
    db.commit()
    captured = {}

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"reply": "ok"}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    response = client.post("/chat/message", json={"message": "hola", "session_id": "s1"})

    assert response.status_code == 200
    assert "Oud Royal" in captured["json"]["catalog_context"]
    # El contexto del cliente sigue separado y vacío para un visitante.
    assert captured["json"]["customer_context"] == ""


# --- sanitize_reply_links ----------------------------------------------------

from services.chat_catalog import sanitize_reply_links  # noqa: E402

SITE = "https://jgparfums.com.co"


def test_sanitize_keeps_valid_product_link_and_leaves_punctuation_outside(db):
    _product(db, "ya-ra", "Yara")
    url = f"{SITE}/producto.html?slug=ya-ra"

    assert sanitize_reply_links(db, f"Mira {url}.") == f"Mira {url}."
    assert sanitize_reply_links(db, f"Mira ({url}) ahora") == f"Mira ({url}) ahora"
    assert sanitize_reply_links(db, f"[Yara]({url}) es dulce") == f"[Yara]({url}) es dulce"
    assert sanitize_reply_links(db, f"**{url}**") == f"**{url}**"


def test_sanitize_sends_unknown_or_inactive_product_to_catalog(db):
    _product(db, "apagado", "Apagado", is_active=False)

    assert sanitize_reply_links(db, f"{SITE}/producto.html?slug=no-existe.") == f"{SITE}/catalogo.html."
    assert sanitize_reply_links(db, f"{SITE}/producto.html?slug=apagado") == f"{SITE}/catalogo.html"
    assert sanitize_reply_links(db, f"{SITE}/producto.html") == f"{SITE}/catalogo.html"


def test_sanitize_fixes_slug_case_and_clean_url_form(db):
    _product(db, "ya-ra", "Yara")

    assert sanitize_reply_links(db, f"{SITE}/producto?slug=YA-RA") == f"{SITE}/producto.html?slug=ya-ra"


def test_sanitize_rewrites_misspelled_brand_domain(db):
    _product(db, "ya-ra", "Yara")

    assert (
        sanitize_reply_links(db, "Ficha: https://jgparfums.com/producto.html?slug=ya-ra")
        == f"Ficha: {SITE}/producto.html?slug=ya-ra"
    )
    assert sanitize_reply_links(db, "Mira https://www.jgparfums.com.co/perfumes/oud") == f"Mira {SITE}/catalogo.html"


def test_sanitize_validates_category_filter(db):
    activa = _category(db, "Florales", "florales")
    inactiva = _category(db, "Oculta", "oculta", is_active=False)
    db.commit()

    assert sanitize_reply_links(db, f"{SITE}/catalogo.html?category_id={activa.id}") == f"{SITE}/catalogo.html?category_id={activa.id}"
    assert sanitize_reply_links(db, f"{SITE}/catalogo.html?category_id=9999") == f"{SITE}/catalogo.html"
    assert sanitize_reply_links(db, f"{SITE}/catalogo.html?category_id={inactiva.id}") == f"{SITE}/catalogo.html"
    assert sanitize_reply_links(db, f"{SITE}/catalogo.html?has_decant=true") == f"{SITE}/catalogo.html?has_decant=true"


def test_sanitize_keeps_known_pages_and_replaces_invented_ones(db):
    assert sanitize_reply_links(db, f"{SITE}/politicas.html#cookies-y-almacenamiento-en-tu-navegador") == f"{SITE}/politicas.html#cookies-y-almacenamiento-en-tu-navegador"
    assert sanitize_reply_links(db, f"{SITE}/contacto") == f"{SITE}/contacto.html"
    assert sanitize_reply_links(db, f"{SITE}/") == f"{SITE}/"
    assert sanitize_reply_links(db, f"{SITE}/tienda/ofertas") == f"{SITE}/catalogo.html"


def test_sanitize_does_not_touch_external_links(db):
    text = "Escríbenos: https://wa.me/573001234567?text=Hola y https://instagram.com/jg_parfums."

    assert sanitize_reply_links(db, text) == text


def test_sanitize_never_breaks_the_reply(db, monkeypatch):
    monkeypatch.setattr("services.chat_catalog._fix_own_url", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))

    assert sanitize_reply_links(db, f"{SITE}/catalogo.html") == f"{SITE}/catalogo.html"


def test_chat_route_returns_verified_links(client, db, monkeypatch):
    _product(db, "ya-ra", "Yara")

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"reply": f"Prueba {SITE}/producto.html?slug=ya-ra-inventado. Y también {SITE}/producto.html?slug=ya-ra."}

    monkeypatch.setattr("services.chat_service.httpx.post", lambda *a, **k: _Resp())

    reply = client.post("/chat/message", json={"message": "hola", "session_id": "s1"}).json()["reply"]

    assert reply == f"Prueba {SITE}/catalogo.html. Y también {SITE}/producto.html?slug=ya-ra."

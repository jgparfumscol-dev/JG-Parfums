from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.category import Category
from models.product import Product, ProductImage
from models.product_detail_section import ProductDetailSection
from models.product_media_item import ProductMediaItem
from models.product_note import ProductNote
from models.product_variant import ProductVariant
from models.user import User
from schemas.product import (
    ProductCreate,
    ProductDetailSectionCreate,
    ProductDetailSectionMove,
    ProductDetailSectionResponse,
    ProductDetailSectionUpdate,
    ProductImageCreate,
    ProductImageResponse,
    ProductListResponse,
    ProductMediaItemCreate,
    ProductMediaItemMove,
    ProductMediaItemResponse,
    ProductMediaItemUpdate,
    ProductNoteCreate,
    ProductNoteMove,
    ProductNoteResponse,
    ProductNoteUpdate,
    ProductResponse,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    category_id: int | None = None,
    search: str | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    has_decant: bool = False,
    is_featured: bool | None = None,
    include_inactive: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
):
    query = db.query(Product)
    # Solo un admin puede pedir productos inactivos (ej. para reactivarlos en el panel).
    if not (include_inactive and user is not None and user.is_admin):
        query = query.filter(Product.is_active.is_(True))
    if category_id is not None:
        query = query.filter(Product.categories.any(Category.id == category_id))
    if search:
        like = f"%{search}%"
        query = query.filter(Product.name.ilike(like) | Product.house.ilike(like))
    # El filtro de precio es sobre lo que el cliente paga: con el descuento aplicado.
    final_price = (Product.price * (100 - Product.discount_percent) + 50) // 100
    if min_price is not None:
        query = query.filter(final_price >= min_price)
    if max_price is not None:
        query = query.filter(final_price <= max_price)
    if has_decant:
        query = query.filter(Product.variants.any(ProductVariant.is_active.is_(True)))
    if is_featured is not None:
        query = query.filter(Product.is_featured.is_(is_featured))

    total = query.count()
    items = query.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ProductListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{slug}", response_model=ProductResponse)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_active.is_(True)).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    existing = db.query(Product).filter(Product.slug == payload.slug).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un producto con ese slug")

    data = payload.model_dump()
    category_ids = data.pop("category_ids")

    product = Product(**data)
    if category_ids:
        product.categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    data = payload.model_dump(exclude_unset=True)
    # La ficha destacada del home solo puede mostrar un producto a la vez:
    # marcar este como destacado desmarca cualquier otro que lo estuviera.
    if data.get("is_featured") is True:
        db.query(Product).filter(Product.id != product_id, Product.is_featured.is_(True)).update(
            {"is_featured": False}
        )
    # category_ids no es una columna real (es la relación N:N `categories`)
    # — se resuelve aparte en vez de por setattr directo. Ausente en el
    # payload = no tocar las clases actuales; presente (aunque sea []) =
    # reemplazarlas por esta lista.
    if "category_ids" in data:
        category_ids = data.pop("category_ids")
        product.categories = db.query(Category).filter(Category.id.in_(category_ids)).all() if category_ids else []
    for field, value in data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, hard: bool = False, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if hard:
        # Eliminación permanente: los pedidos históricos no dependen de esta fila,
        # OrderItem guarda su propio snapshot (product_name, unit_price, size_ml) y
        # su product_id cae a NULL (ondelete=SET NULL) — el recibo no se pierde.
        db.delete(product)
    else:
        # soft delete (default): un producto vendido antes no debe desaparecer de
        # pedidos históricos sin que el admin lo pida explícitamente.
        product.is_active = False
    db.commit()


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
def add_product_image(
    product_id: int,
    payload: ProductImageCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    image = ProductImage(product_id=product_id, **payload.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(image_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")
    db.delete(image)
    db.commit()


@router.post(
    "/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED
)
def add_product_variant(
    product_id: int,
    payload: ProductVariantCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    variant = ProductVariant(product_id=product_id, **payload.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.put("/variants/{variant_id}", response_model=ProductVariantResponse)
def update_product_variant(
    variant_id: int,
    payload: ProductVariantUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentación no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_variant(
    variant_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentación no encontrada")
    # hard delete: a diferencia del producto, una presentación sin pedidos asociados
    # (order_items.product_variant_id queda en null por ondelete=SET NULL) no necesita
    # conservarse — el admin la agrega de nuevo si se equivocó.
    db.delete(variant)
    db.commit()


@router.post("/{product_id}/notes", response_model=ProductNoteResponse, status_code=status.HTTP_201_CREATED)
def add_product_note(
    product_id: int,
    payload: ProductNoteCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    max_position = (
        db.query(ProductNote.position)
        .filter(ProductNote.product_id == product_id)
        .order_by(ProductNote.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0

    note = ProductNote(product_id=product_id, position=next_position, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/notes/{note_id}", response_model=ProductNoteResponse)
def update_product_note(
    note_id: int, payload: ProductNoteUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    note = db.query(ProductNote).filter(ProductNote.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


@router.put("/notes/{note_id}/move", response_model=ProductNoteResponse)
def move_product_note(
    note_id: int, payload: ProductNoteMove, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    note = db.query(ProductNote).filter(ProductNote.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")

    siblings = (
        db.query(ProductNote)
        .filter(ProductNote.product_id == note.product_id)
        .order_by(ProductNote.position)
        .all()
    )
    index = next(i for i, n in enumerate(siblings) if n.id == note.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        note.position, neighbor.position = neighbor.position, note.position
        db.commit()
        db.refresh(note)
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_note(note_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    note = db.query(ProductNote).filter(ProductNote.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")
    # hard delete: igual que las presentaciones, sin pedidos que referencien la nota.
    db.delete(note)
    db.commit()


@router.post(
    "/{product_id}/detail-sections",
    response_model=ProductDetailSectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_product_detail_section(
    product_id: int,
    payload: ProductDetailSectionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    max_position = (
        db.query(ProductDetailSection.position)
        .filter(ProductDetailSection.product_id == product_id)
        .order_by(ProductDetailSection.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0

    section = ProductDetailSection(product_id=product_id, position=next_position, **payload.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.put("/detail-sections/{section_id}", response_model=ProductDetailSectionResponse)
def update_product_detail_section(
    section_id: int,
    payload: ProductDetailSectionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(ProductDetailSection).filter(ProductDetailSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    db.commit()
    db.refresh(section)
    return section


@router.put("/detail-sections/{section_id}/move", response_model=ProductDetailSectionResponse)
def move_product_detail_section(
    section_id: int,
    payload: ProductDetailSectionMove,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(ProductDetailSection).filter(ProductDetailSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    siblings = (
        db.query(ProductDetailSection)
        .filter(ProductDetailSection.product_id == section.product_id)
        .order_by(ProductDetailSection.position)
        .all()
    )
    index = next(i for i, s in enumerate(siblings) if s.id == section.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        section.position, neighbor.position = neighbor.position, section.position
        db.commit()
        db.refresh(section)
    return section


@router.delete("/detail-sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_detail_section(
    section_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    section = db.query(ProductDetailSection).filter(ProductDetailSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")
    db.delete(section)
    db.commit()


@router.post("/{product_id}/media", response_model=ProductMediaItemResponse, status_code=status.HTTP_201_CREATED)
def add_product_media_item(
    product_id: int,
    payload: ProductMediaItemCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    max_position = (
        db.query(ProductMediaItem.position)
        .filter(ProductMediaItem.product_id == product_id)
        .order_by(ProductMediaItem.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0

    item = ProductMediaItem(product_id=product_id, position=next_position, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/media/{item_id}", response_model=ProductMediaItemResponse)
def update_product_media_item(
    item_id: int,
    payload: ProductMediaItemUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    item = db.query(ProductMediaItem).filter(ProductMediaItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloque de medio no encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.put("/media/{item_id}/move", response_model=ProductMediaItemResponse)
def move_product_media_item(
    item_id: int,
    payload: ProductMediaItemMove,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    item = db.query(ProductMediaItem).filter(ProductMediaItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloque de medio no encontrado")

    siblings = (
        db.query(ProductMediaItem)
        .filter(ProductMediaItem.product_id == item.product_id)
        .order_by(ProductMediaItem.position)
        .all()
    )
    index = next(i for i, m in enumerate(siblings) if m.id == item.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        item.position, neighbor.position = neighbor.position, item.position
        db.commit()
        db.refresh(item)
    return item


@router.delete("/media/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_media_item(item_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    item = db.query(ProductMediaItem).filter(ProductMediaItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloque de medio no encontrado")
    db.delete(item)
    db.commit()

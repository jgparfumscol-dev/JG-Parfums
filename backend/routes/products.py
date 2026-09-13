from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.product import Product, ProductImage
from models.product_note import ProductNote
from models.product_variant import ProductVariant
from models.user import User
from schemas.product import (
    ProductCreate,
    ProductImageCreate,
    ProductImageResponse,
    ProductListResponse,
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
    include_inactive: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
):
    query = db.query(Product)
    # Solo un admin puede pedir productos inactivos (ej. para reactivarlos en el panel).
    if not (include_inactive and user is not None and user.is_admin):
        query = query.filter(Product.is_active.is_(True))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if search:
        like = f"%{search}%"
        query = query.filter(Product.name.ilike(like) | Product.house.ilike(like))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if has_decant:
        query = query.filter(Product.variants.any(ProductVariant.is_active.is_(True)))

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

    product = Product(**payload.model_dump())
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

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    # soft delete: un producto vendido antes no debe desaparecer de pedidos históricos
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

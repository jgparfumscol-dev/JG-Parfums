from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.brand import Brand
from models.user import User
from schemas.brand import BrandCreate, BrandMove, BrandResponse, BrandUpdate

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=list[BrandResponse])
def list_brands(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Igual que /page-sections: solo un admin autenticado puede pedir las
    # inactivas (para poder reactivarlas desde el panel). El público siempre
    # ve solo las activas, ordenadas — es el contrato del carrusel de marcas.
    is_admin_request = include_inactive and user is not None and user.is_admin
    query = db.query(Brand)
    if not is_admin_request:
        query = query.filter(Brand.is_active.is_(True))
    return query.order_by(Brand.sort_order, Brand.id).all()


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    max_order = db.query(Brand.sort_order).order_by(Brand.sort_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0

    brand = Brand(**payload.model_dump(), sort_order=next_order)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.put("/{brand_id}", response_model=BrandResponse)
def update_brand(
    brand_id: int, payload: BrandUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, value)
    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca no encontrada")
    db.delete(brand)
    db.commit()


@router.put("/{brand_id}/move", response_model=BrandResponse)
def move_brand(
    brand_id: int, payload: BrandMove, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca no encontrada")

    siblings = db.query(Brand).order_by(Brand.sort_order, Brand.id).all()
    index = next(i for i, b in enumerate(siblings) if b.id == brand.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        brand.sort_order, neighbor.sort_order = neighbor.sort_order, brand.sort_order
        db.commit()
        db.refresh(brand)
    return brand

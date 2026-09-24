from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin
from models.category import Category
from models.user import User
from schemas.category import CategoryCreate, CategoryMove, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    # Sin filtrar por is_active a propósito: este endpoint también alimenta
    # el filtro del catálogo, la ficha de producto y la sección "Productos"
    # del editor — el carrusel de clases filtra is_active del lado del
    # cliente (ver renderClassesCarousel en sections.js), no acá.
    return db.query(Category).order_by(Category.sort_order, Category.id).all()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    existing = db.query(Category).filter(Category.slug == payload.slug).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una categoría con ese slug")

    # sort_order no es parte del payload: se calcula acá, igual que
    # PageSection.position — el orden solo cambia después con /move.
    max_order = db.query(Category.sort_order).order_by(Category.sort_order.desc()).first()
    next_order = (max_order[0] + 1) if max_order else 0

    category = Category(**payload.model_dump(), sort_order=next_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    # ondelete=CASCADE en la tabla puente product_categories: los productos
    # que la usaban pierden esta clase (les puede quedar alguna otra si
    # tenían más de una), no se borran.
    db.delete(category)
    db.commit()


@router.put("/{category_id}/move", response_model=CategoryResponse)
def move_category(
    category_id: int, payload: CategoryMove, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")

    siblings = db.query(Category).order_by(Category.sort_order, Category.id).all()
    index = next(i for i, c in enumerate(siblings) if c.id == category.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        category.sort_order, neighbor.sort_order = neighbor.sort_order, category.sort_order
        db.commit()
        db.refresh(category)
    return category

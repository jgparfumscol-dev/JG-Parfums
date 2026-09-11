from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.page_section import PageSection
from models.user import User
from schemas.page_section import (
    PageSectionCreate,
    PageSectionMove,
    PageSectionResponse,
    PageSectionUpdate,
)

router = APIRouter(prefix="/page-sections", tags=["page-sections"])


@router.get("", response_model=list[PageSectionResponse])
def list_page_sections(
    page: str,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    query = db.query(PageSection).filter(PageSection.page == page)
    # Solo un admin puede pedir secciones ocultas (ej. para reactivarlas en el editor).
    if not (include_inactive and user is not None and user.is_admin):
        query = query.filter(PageSection.is_active.is_(True))
    return query.order_by(PageSection.position).all()


@router.post("", response_model=PageSectionResponse, status_code=status.HTTP_201_CREATED)
def create_page_section(
    payload: PageSectionCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    max_position = (
        db.query(PageSection.position)
        .filter(PageSection.page == payload.page)
        .order_by(PageSection.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0

    section = PageSection(**payload.model_dump(), position=next_position)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.put("/{section_id}", response_model=PageSectionResponse)
def update_page_section(
    section_id: int,
    payload: PageSectionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    db.commit()
    db.refresh(section)
    return section


@router.put("/{section_id}/move", response_model=PageSectionResponse)
def move_page_section(
    section_id: int,
    payload: PageSectionMove,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    siblings = (
        db.query(PageSection)
        .filter(PageSection.page == section.page)
        .order_by(PageSection.position)
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


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page_section(
    section_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")
    db.delete(section)
    db.commit()

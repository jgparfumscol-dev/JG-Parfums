from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.page_section import PageSection
from models.page_section_history import PageSectionHistory
from models.user import User
from schemas.page_section import (
    PageSectionCreate,
    PageSectionHistoryResponse,
    PageSectionMove,
    PageSectionResponse,
    PageSectionUpdate,
)

router = APIRouter(prefix="/page-sections", tags=["page-sections"])


def _snapshot(section: PageSection, action: str, db: Session) -> None:
    """Guarda una copia autocontenida del estado actual de `section`. No
    depende de que la fila original siga existiendo después — por eso el
    historial sobrevive a un borrado real.
    """
    db.add(
        PageSectionHistory(
            section_id=section.id,
            page=section.page,
            key=section.key,
            type=section.type,
            content=section.content,
            is_active=section.is_active,
            position=section.position,
            action=action,
        )
    )


# Los endpoints de /history van antes de /{section_id}: Starlette resuelve
# rutas en orden de registro, así que si /{section_id} (int) quedara primero,
# "history" se intentaría parsear como section_id y rompería con 422 — el
# mismo bug que ya pasó una vez con los webhooks de pagos.
@router.get("/history", response_model=list[PageSectionHistoryResponse])
def list_page_section_history(
    page: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return (
        db.query(PageSectionHistory)
        .filter(PageSectionHistory.page == page)
        .order_by(PageSectionHistory.created_at.desc(), PageSectionHistory.id.desc())
        .limit(limit)
        .all()
    )


@router.post("/history/{history_id}/restore", response_model=PageSectionResponse)
def restore_page_section(
    history_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    entry = db.query(PageSectionHistory).filter(PageSectionHistory.id == history_id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión no encontrada")

    section = (
        db.query(PageSection).filter(PageSection.id == entry.section_id).first()
        if entry.section_id is not None
        else None
    )
    if section is not None:
        # La sección todavía existe: se le devuelve el contenido de esa versión.
        section.content = entry.content
        section.is_active = entry.is_active
    else:
        # La sección fue borrada: reaparece como una fila nueva, en el mismo lugar.
        max_position = (
            db.query(PageSection.position)
            .filter(PageSection.page == entry.page)
            .order_by(PageSection.position.desc())
            .first()
        )
        next_position = (max_position[0] + 1) if max_position else 0
        section = PageSection(
            page=entry.page,
            key=entry.key,
            type=entry.type,
            content=entry.content,
            is_active=entry.is_active,
            is_builtin=entry.key is not None,
            position=entry.position if entry.key is not None else next_position,
        )
        db.add(section)

    db.flush()
    _snapshot(section, "restored", db)
    db.commit()
    db.refresh(section)
    return section


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
    db.flush()
    _snapshot(section, "created", db)
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
    _snapshot(section, "updated", db)
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
    _snapshot(section, "deleted", db)
    db.delete(section)
    db.commit()

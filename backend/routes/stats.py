from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from main import limiter
from middleware.auth import get_current_admin
from models.order import Order, PaymentStatus
from models.order_item import OrderItem
from models.page_view import PageView
from models.user import User
from schemas.stats import DayCount, PageViewCreate, PathCount, ProductCount, StatsSummary

router = APIRouter(prefix="/stats", tags=["stats"])


@router.post("/track", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
def track_page_view(request: Request, payload: PageViewCreate, db: Session = Depends(get_db)):
    """Público y sin autenticación a propósito: lo llama cada página del
    sitio al cargar. Sin cookies, sin IP ni user-agent guardados."""
    db.add(PageView(path=payload.path, referrer=payload.referrer))
    db.commit()


@router.get("/summary", response_model=StatsSummary)
def get_summary(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)
    since_14d = now - timedelta(days=14)
    since_30d = now - timedelta(days=30)

    views_7d = db.query(PageView).filter(PageView.created_at >= since_7d).count()
    views_30d = db.query(PageView).filter(PageView.created_at >= since_30d).count()

    day_expr = func.date(PageView.created_at)
    views_by_day_rows = (
        db.query(day_expr.label("day"), func.count(PageView.id))
        .filter(PageView.created_at >= since_14d)
        .group_by(day_expr)
        .order_by(day_expr)
        .all()
    )
    views_by_day = [DayCount(date=str(row[0]), count=row[1]) for row in views_by_day_rows]

    top_pages_rows = (
        db.query(PageView.path, func.count(PageView.id).label("n"))
        .filter(PageView.created_at >= since_30d)
        .group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(5)
        .all()
    )
    top_pages = [PathCount(path=row[0], count=row[1]) for row in top_pages_rows]

    total_orders = db.query(Order).count()
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.payment_status == PaymentStatus.approved)
        .scalar()
        or 0
    )

    status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    orders_by_status = {row[0].value: row[1] for row in status_rows}

    top_products_rows = (
        db.query(OrderItem.product_name, func.sum(OrderItem.quantity).label("qty"))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_products = [ProductCount(name=row[0], quantity=int(row[1])) for row in top_products_rows]

    return StatsSummary(
        views_7d=views_7d,
        views_30d=views_30d,
        views_by_day=views_by_day,
        top_pages=top_pages,
        total_orders=total_orders,
        total_revenue=int(total_revenue),
        orders_by_status=orders_by_status,
        top_products=top_products,
    )

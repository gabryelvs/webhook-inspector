from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db import get_db
from app.models import Bin, CapturedRequest
from app.schemas import BinOut

router = APIRouter(prefix="/api/bins", tags=["bins"])
limiter = Limiter(key_func=get_remote_address)

BIN_TTL_DAYS = 7


def _expire_old_bins(db: Session) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=BIN_TTL_DAYS)
    stale_ids = db.scalars(select(Bin.id).where(Bin.created_at < cutoff)).all()
    if not stale_ids:
        return
    db.execute(delete(CapturedRequest).where(CapturedRequest.bin_id.in_(stale_ids)))
    db.execute(delete(Bin).where(Bin.id.in_(stale_ids)))
    db.commit()


@router.post("", response_model=BinOut, status_code=201)
@limiter.limit("10/minute")
def create_bin(request: Request, db: Session = Depends(get_db)):
    _expire_old_bins(db)
    b = Bin()
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/{bin_id}", response_model=BinOut)
def get_bin(bin_id: str, db: Session = Depends(get_db)):
    b = db.get(Bin, bin_id)
    if b is None:
        raise HTTPException(status_code=404, detail="bin not found")
    return b

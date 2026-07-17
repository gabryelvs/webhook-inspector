from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bin, CapturedRequest
from app.schemas import RequestOut

router = APIRouter(prefix="/api", tags=["requests"])

MAX_PAGE_SIZE = 200


@router.get("/bins/{bin_id}/requests", response_model=list[RequestOut])
def list_requests(
    bin_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if db.get(Bin, bin_id) is None:
        raise HTTPException(status_code=404, detail="bin not found")
    return db.scalars(
        select(CapturedRequest)
        .where(CapturedRequest.bin_id == bin_id)
        .order_by(CapturedRequest.received_at.desc(), CapturedRequest.id.desc())
        .limit(min(max(limit, 1), MAX_PAGE_SIZE))
        .offset(max(offset, 0))
    ).all()


@router.get("/requests/{request_id}", response_model=RequestOut)
def get_request(request_id: str, db: Session = Depends(get_db)):
    r = db.get(CapturedRequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="request not found")
    return r


@router.delete("/requests/{request_id}", status_code=204)
def delete_request(request_id: str, db: Session = Depends(get_db)):
    r = db.get(CapturedRequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail="request not found")
    db.delete(r)
    db.commit()

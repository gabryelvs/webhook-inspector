import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.client_ip import client_ip
from app.db import get_db
from app.models import Bin, CapturedRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["capture"])

MAX_BODY_BYTES = 1_000_000
MAX_REQUESTS_PER_BIN = 500
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@router.api_route("/in/{bin_id}", methods=METHODS)
@router.api_route("/in/{bin_id}/{path:path}", methods=METHODS)
async def capture(
    bin_id: str,
    request: Request,
    path: str = "",
    db: Session = Depends(get_db),
):
    try:
        if db.get(Bin, bin_id) is None:
            raise HTTPException(status_code=404, detail="bin not found")

        raw = bytearray()
        truncated = False
        async for chunk in request.stream():
            if len(raw) < MAX_BODY_BYTES:
                need = MAX_BODY_BYTES - len(raw)
                raw.extend(chunk[:need])
                if len(chunk) > need:
                    truncated = True
            elif chunk:
                truncated = True
        body_text = bytes(raw).decode("utf-8", errors="replace")

        captured = CapturedRequest(
            bin_id=bin_id,
            method=request.method,
            path="/" + path,
            headers=dict(request.headers),
            query=dict(request.query_params),
            body=body_text,
            content_type=(request.headers.get("content-type") or "")[:255] or None,
            source_ip=client_ip(request),
            truncated=truncated,
        )
        db.add(captured)
        db.commit()
        _prune(db, bin_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("failed to capture request for bin %s", bin_id)

    return {"ok": True}


def _prune(db: Session, bin_id: str) -> None:
    stale_ids = db.scalars(
        select(CapturedRequest.id)
        .where(CapturedRequest.bin_id == bin_id)
        .order_by(CapturedRequest.received_at.desc(), CapturedRequest.id.desc())
        .offset(MAX_REQUESTS_PER_BIN)
    ).all()
    if stale_ids:
        db.execute(delete(CapturedRequest).where(CapturedRequest.id.in_(stale_ids)))
        db.commit()

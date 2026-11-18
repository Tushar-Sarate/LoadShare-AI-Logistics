import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.concurrency import run_in_threadpool

from app.config import ALGORITHM, SECRET_KEY
from app.database import SessionLocal
from app.models.user import User
from app.services import realtime


router = APIRouter(
    prefix="/events",
    tags=["Realtime"]
)

bearer = HTTPBearer()


def _user_from_token(token: str) -> dict:
    """Short database session, closed before the stream starts."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"id": user.id, "role": getattr(user.role, "value", user.role)}
    finally:
        db.close()


# Live event stream (Server-Sent Events)
@router.get("/stream")
async def stream(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = await run_in_threadpool(_user_from_token, credentials.credentials)

    async def event_generator():
        queue = realtime.subscribe(user["id"], user["role"])
        try:
            yield "retry: 3000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            realtime.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
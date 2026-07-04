"""AI routes (auto-mounted at /api): upload, query, stream, chat sessions/messages."""
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.ingest import ingest_document
from ai.rag import answer_question, stream_answer
from backend.routers.auth import get_current_user
from database.config import SessionLocal, get_db
from database.models import ChatMessage, ChatSession, Document, User

router = APIRouter(tags=["AI"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None


@router.post("/ai/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit")
    name = (file.filename or "").lower()
    if not (name.endswith(".pdf") or name.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files are supported")
    doc = Document(user_id=user.id, filename=file.filename, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    try:
        n_chunks = ingest_document(db, doc.id, file.filename, data)
        doc.status = "ready"
        db.commit()
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not process document: {e}")
    return {"document_id": doc.id, "filename": doc.filename, "chunks_indexed": n_chunks}


@router.get("/ai/documents")
async def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    return [
        {"id": d.id, "filename": d.filename, "status": d.status, "created_at": str(d.created_at)}
        for d in docs
    ]


def _get_or_create_session(db: Session, user: User, session_id: Optional[str], title_seed: str) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id, ChatSession.user_id == user.id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    session = ChatSession(user_id=user.id, title=(title_seed[:60] or "New chat"))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/ai/query")
async def query(
    body: QueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_or_create_session(db, user, body.session_id, body.question)
    db.add(ChatMessage(session_id=session.id, role="user", content=body.question))
    result = answer_question(db, body.question, document_id=body.document_id)
    db.add(ChatMessage(
        session_id=session.id, role="assistant", content=result["answer"],
        meta_data=json.dumps({"citations": result["citations"]}),
    ))
    db.commit()
    return {"session_id": session.id, "answer": result["answer"], "citations": result["citations"]}


@router.post("/ai/stream")
async def stream(
    body: QueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_or_create_session(db, user, body.session_id, body.question)
    session_id = session.id            # capture as a plain scalar: the ORM object is expired
    question = body.question           # after commit and detached once the stream drains, so
    document_id = body.document_id     # reading session.id inside the generator would raise.
    db.add(ChatMessage(session_id=session_id, role="user", content=question))
    db.commit()

    def event_gen():
        collected = []
        for token in stream_answer(db, question, document_id=document_id):
            collected.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"
        # Persist the assistant reply in a FRESH session — the request-scoped `db` (and the
        # `session` ORM object) may be closed/detached by the time the stream finishes.
        with SessionLocal() as write_db:
            write_db.add(ChatMessage(session_id=session_id, role="assistant",
                                     content="".join(collected)))
            write_db.commit()
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/ai/sessions")
async def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(
        ChatSession.created_at.desc()).all()
    return [{"id": s.id, "title": s.title, "created_at": str(s.created_at)} for s in sessions]


@router.get("/ai/sessions/{session_id}/messages")
async def list_messages(
    session_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
        ChatMessage.created_at.asc()).all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": str(m.created_at)}
        for m in msgs
    ]

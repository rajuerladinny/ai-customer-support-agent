"""Local single-user support API. Fictional demonstration data only."""
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "data" / "support.db"
CASES = [
    ("CS-104", "Damaged headphones", "Maya Patel", "NS-1042"),
    ("CS-103", "Delivery running late", "Alex Morgan", "NS-1038"),
    ("CS-102", "Unanswered product question", "Jordan Lee", None),
]
ORDERS = {"NS-1042": {"id":"NS-1042","item":"Wireless headphones","status":"Delivered","delivered":"12 Nov (sample)"}, "NS-1038": {"id":"NS-1038","item":"Portable speaker","status":"Delayed in transit","delivered":None}}
POLICIES = [
    {"name":"Returns & replacements · §2","text":"Damaged items may be reported within 14 days of delivery. Replacement requests require support approval."},
    {"name":"Delivery support · §1","text":"If an order is delayed, support can check tracking and provide an updated delivery estimate when available."},
]
STOP=set("the and are can how what when where would could please tell about that this with have from does they your their will order item items need want policy our you for was has not its into".split())

def tokens(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w)>2 and w not in STOP}

def search(question, documents):
    terms=tokens(question)
    minimum=2 if len(terms)>=2 else 1
    results=[]
    for doc in POLICIES+documents:
        score=len(tokens(doc["text"]) & terms)
        sentences=[s.strip() for s in re.findall(r"[^.!?\n]+[.!?]?", doc["text"])]
        sentences.sort(key=lambda s:len(tokens(s)&terms),reverse=True)
        if score>=minimum and sentences and tokens(sentences[0]) & terms:
            results.append((score,doc["name"],sentences[0]))
    if not results:
        return {"answer":"No matching information found. Please ask a support person.","source":None,"mode":"no_match"}
    results.sort(key=lambda r:r[0],reverse=True)
    return {"answer":results[0][2],"source":results[0][1],"mode":"extractive","notice":"Matching excerpt; not an AI-generated answer."}

class Message(BaseModel):
    caseId: Literal["CS-104", "CS-103", "CS-102"]
    who: Literal["customer", "assistant"]
    message: str = Field(min_length=1, max_length=4000)

class Decision(BaseModel):
    decision: Literal["Approved", "Rejected"]

class Document(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=15000)

class DocumentName(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

class Escalation(BaseModel):
    caseId: Literal["CS-104", "CS-103", "CS-102"]
    summary: str = Field(min_length=1, max_length=1000)

class Resolve(BaseModel):
    id: str = Field(min_length=1, max_length=100)


def create_app(db_path=None):
    path=Path(db_path or os.environ.get("RESOLVE_DB_PATH",str(DEFAULT_PATH)))
    path.parent.mkdir(parents=True,exist_ok=True)
    @contextmanager
    def connect():
        db=sqlite3.connect(path,timeout=5)
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, title TEXT NOT NULL, customer TEXT NOT NULL, order_id TEXT);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL REFERENCES cases(id), role TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY CHECK(id=1), decision TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents(name TEXT PRIMARY KEY COLLATE NOCASE, content TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), summary TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, resolved_at TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS one_open_review ON reviews(case_id) WHERE status='open';
        ''')
        db.executemany('INSERT OR IGNORE INTO cases VALUES(?,?,?,?)',CASES)
        db.execute("INSERT OR IGNORE INTO approvals VALUES(1,'pending')")
    app=FastAPI(title="Resolve Support API",version="0.7.0")
    @app.middleware('http')
    async def guard(request: Request, call_next):
        # This app is bound to localhost by default and does not support production users.
        if request.method in ('POST','PUT','DELETE','PATCH'):
            origin=request.headers.get('origin')
            if origin:
                parsed=urlparse(origin)
                if parsed.scheme!='http' or parsed.netloc!=request.headers.get('host'):
                    return JSONResponse({'error':'Origin not allowed'},status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response
    @app.get('/')
    def frontend():
        return FileResponse(ROOT/'worker'/'index.html')
    @app.get('/api/health')
    def health():
        with connect() as db: db.execute('SELECT 1').fetchone()
        return {'status':'ok','storage':'sqlite','ai':'not_configured'}
    @app.get('/api/cases')
    def cases():
        with connect() as db: rows=db.execute('SELECT * FROM cases ORDER BY id DESC').fetchall()
        return {'cases':[dict(r) for r in rows]}
    def state(db):
        approval=db.execute('SELECT decision FROM approvals WHERE id=1').fetchone()[0]
        logs={}
        for row in db.execute('SELECT case_id,role,body FROM messages ORDER BY id'):
            logs.setdefault(row['case_id'],[]).append([row['role'],row['body']])
        docs=[{'name':r['name'],'text':r['content']} for r in db.execute('SELECT * FROM documents ORDER BY rowid')]
        reviews=[{'id':r['id'],'caseId':r['case_id'],'summary':r['summary'],'status':r['status'],'createdAt':r['created_at'],'resolvedAt':r['resolved_at']} for r in db.execute('SELECT * FROM reviews ORDER BY created_at,id')]
        return {'approval':approval,'logs':logs,'documents':docs,'escalations':reviews}
    @app.get('/api/state')
    def get_state():
        with connect() as db: return state(db)
    @app.get('/api/documents')
    def get_documents():
        with connect() as db: return {'documents':state(db)['documents']}
    @app.post('/api/documents',status_code=201)
    def add_document(doc: Document):
        if not doc.name.strip() or not doc.name.lower().endswith('.txt') or not doc.text.strip() or len(doc.text.encode())>15000:
            raise HTTPException(400,'Provide a non-empty .txt file up to 15 KB.')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]>=5: raise HTTPException(409,'Maximum 5 documents')
            try: db.execute('INSERT INTO documents VALUES (?,?)',(doc.name,doc.text))
            except sqlite3.IntegrityError: raise HTTPException(409,'Document name already exists')
        return {'ok':True}
    @app.post('/api/documents/delete')
    def delete_document(doc:DocumentName):
        with connect() as db:
            if not db.execute('DELETE FROM documents WHERE name=?',(doc.name,)).rowcount: raise HTTPException(404,'Document not found')
        return {'ok':True}
    @app.get('/api/order')
    def order(id:str=''):
        result=ORDERS.get(id.upper())
        if not result: raise HTTPException(404,'Sample order not found')
        return result
    @app.post('/api/answer')
    def answer(q:Question):
        if not q.question.strip(): raise HTTPException(400,'Question cannot be blank')
        with connect() as db: docs=[{'name':r['name'],'text':r['content']} for r in db.execute('SELECT * FROM documents ORDER BY rowid')]
        return search(q.question,docs)
    @app.post('/api/messages')
    def add_message(m:Message):
        if not m.message.strip(): raise HTTPException(400,'Message cannot be blank')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(*) FROM messages WHERE case_id=?',(m.caseId,)).fetchone()[0]>=200: raise HTTPException(409,'Message limit reached')
            db.execute('INSERT INTO messages(case_id,role,body) VALUES(?,?,?)',(m.caseId,m.who,m.message))
        return {'ok':True}
    @app.post('/api/approval')
    def approval(d:Decision):
        with connect() as db:
            changed=db.execute("UPDATE approvals SET decision=? WHERE id=1 AND decision='pending'",(d.decision,)).rowcount
            if not changed: raise HTTPException(409,'Approval already decided')
        return {'approval':d.decision}
    @app.get('/api/escalations')
    def reviews():
        with connect() as db:return {'escalations':state(db)['escalations']}
    @app.post('/api/escalations',status_code=201)
    def add_review(e:Escalation):
        if not e.summary.strip(): raise HTTPException(400,'Summary cannot be blank')
        ident=str(uuid.uuid4()); timestamp=datetime.now(timezone.utc).isoformat()
        with connect() as db:
            try: db.execute("INSERT INTO reviews VALUES(?,?,?,'open',?,NULL)",(ident,e.caseId,e.summary.strip(),timestamp))
            except sqlite3.IntegrityError: raise HTTPException(409,'An open review already exists for this case.')
        return {'id':ident,'caseId':e.caseId,'summary':e.summary.strip(),'status':'open','createdAt':timestamp,'resolvedAt':None}
    @app.post('/api/escalations/resolve')
    def resolve_review(review:Resolve):
        with connect() as db:
            changed=db.execute("UPDATE reviews SET status='resolved',resolved_at=? WHERE id=? AND status='open'",(datetime.now(timezone.utc).isoformat(),review.id)).rowcount
            if not changed:
                exists=db.execute('SELECT 1 FROM reviews WHERE id=?',(review.id,)).fetchone()
                raise HTTPException(409 if exists else 404,'Review already resolved' if exists else 'Review not found')
        return {'ok':True}
    @app.post('/api/reset')
    def reset():
        with connect() as db:
            for table in ('messages','documents','reviews'): db.execute(f'DELETE FROM {table}')
            db.execute("UPDATE approvals SET decision='pending' WHERE id=1")
        return {'ok':True}
    return app

app=create_app()

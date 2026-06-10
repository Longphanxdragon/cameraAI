"""
Chart2Code — FastAPI Backend
- JWT Auth (register / login / me)
- Chart generation endpoint (credit-based)
- Generation history
- Stripe subscription checkout + webhook
- Serves frontend static files
"""

import os
import sqlite3
import stripe
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    FastAPI, HTTPException, Depends, UploadFile, File,
    Request, Header
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# ── Configuration ──────────────────────────────────────────────────────────────
SECRET_KEY          = os.getenv("SECRET_KEY", "chart2code-dev-secret-CHANGE-ME")
ALGORITHM           = "HS256"
TOKEN_EXPIRE_DAYS   = 30
DB_PATH             = os.path.join(os.path.dirname(__file__), "chart2code.db")
FRONTEND_DIR        = os.path.join(os.path.dirname(__file__), "..", "frontend")
YOUR_DOMAIN         = os.getenv("YOUR_DOMAIN", "http://localhost:8000")

stripe.api_key          = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET   = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID     = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_TEAM_PRICE_ID    = os.getenv("STRIPE_TEAM_PRICE_ID", "")

PLAN_CREDITS = {"free": 5, "pro": 100, "team": 500}


# ── Database ───────────────────────────────────────────────────────────────────
def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                email                  TEXT    UNIQUE NOT NULL,
                password_hash          TEXT    NOT NULL,
                plan                   TEXT    DEFAULT 'free',
                credits_used           INTEGER DEFAULT 0,
                credits_reset          TEXT    DEFAULT CURRENT_TIMESTAMP,
                stripe_customer_id     TEXT,
                stripe_subscription_id TEXT,
                created_at             TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                image_name     TEXT,
                generated_code TEXT,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def _user_by_email(email: str):
    with _conn() as db:
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    return dict(row) if row else None


def _user_by_id(uid: int):
    with _conn() as db:
        row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None


def _create_user(email: str, pw_hash: str) -> int:
    with _conn() as db:
        cur = db.execute(
            "INSERT INTO users (email,password_hash) VALUES (?,?)", (email, pw_hash)
        )
        db.commit()
    return cur.lastrowid


def _update_user(uid: int, **kw):
    if not kw:
        return
    sets = ", ".join(f"{k}=?" for k in kw)
    vals = list(kw.values()) + [uid]
    with _conn() as db:
        db.execute(f"UPDATE users SET {sets} WHERE id=?", vals)
        db.commit()


def _save_generation(uid: int, fname: str, code: str):
    with _conn() as db:
        db.execute(
            "INSERT INTO generations (user_id,image_name,generated_code) VALUES (?,?,?)",
            (uid, fname, code),
        )
        db.commit()


def _get_history(uid: int, limit: int = 20):
    with _conn() as db:
        rows = db.execute(
            "SELECT * FROM generations WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (uid, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Auth ───────────────────────────────────────────────────────────────────────
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_pw(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def make_token(uid: int) -> str:
    exp = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(uid), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def current_uid(creds: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Credit helper ──────────────────────────────────────────────────────────────
def use_credit(user: dict) -> bool:
    """Resets monthly if needed, returns False when limit reached."""
    reset = datetime.fromisoformat(user["credits_reset"])
    if (datetime.utcnow() - reset).days >= 30:
        _update_user(user["id"], credits_used=0, credits_reset=datetime.utcnow().isoformat())
        user["credits_used"] = 0

    limit = PLAN_CREDITS.get(user["plan"], 5)
    if user["credits_used"] >= limit:
        return False

    _update_user(user["id"], credits_used=user["credits_used"] + 1)
    return True


# ── Pydantic schemas ───────────────────────────────────────────────────────────
class AuthReq(BaseModel):
    email: str
    password: str


class CheckoutReq(BaseModel):
    plan: str  # "pro" | "team"


# ── App lifecycle ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[OK] DB ready")
    yield


app = FastAPI(title="Chart2Code API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth routes ────────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(req: AuthReq):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if _user_by_email(req.email):
        raise HTTPException(400, "Email already registered")
    uid   = _create_user(req.email, hash_pw(req.password))
    token = make_token(uid)
    return {"token": token, "message": "Account created!"}


@app.post("/api/auth/login")
async def login(req: AuthReq):
    user = _user_by_email(req.email)
    if not user or not verify_pw(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    return {"token": make_token(user["id"])}


@app.get("/api/auth/me")
async def me(uid: int = Depends(current_uid)):
    user = _user_by_id(uid)
    if not user:
        raise HTTPException(404, "User not found")
    limit = PLAN_CREDITS.get(user["plan"], 5)
    return {
        "id":                user["id"],
        "email":             user["email"],
        "plan":              user["plan"],
        "credits_used":      user["credits_used"],
        "credits_limit":     limit,
        "credits_remaining": max(0, limit - user["credits_used"]),
    }


# ── Generate route ─────────────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate(
    file: UploadFile = File(...),
    uid:  int        = Depends(current_uid),
):
    user = _user_by_id(uid)
    if not user:
        raise HTTPException(404, "User not found")

    if not use_credit(user):
        limit = PLAN_CREDITS.get(user["plan"], 5)
        raise HTTPException(
            402,
            f"You've used all {limit} credits this month on the '{user['plan']}' plan. "
            "Please upgrade to continue.",
        )

    img_bytes = await file.read()
    if len(img_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large — maximum 10 MB")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "File must be an image (PNG, JPG, etc.)")

    try:
        from backend.ml_service import ml_service
        code = ml_service.generate_code(img_bytes)
    except Exception as exc:
        raise HTTPException(500, f"Model error: {exc}")

    _save_generation(uid, file.filename or "chart.png", code)

    limit = PLAN_CREDITS.get(user["plan"], 5)
    return {
        "code":              code,
        "credits_remaining": max(0, limit - user["credits_used"] - 1),
    }


# ── History route ──────────────────────────────────────────────────────────────
@app.get("/api/history")
async def history(uid: int = Depends(current_uid)):
    return _get_history(uid)


# ── Stripe routes ──────────────────────────────────────────────────────────────
@app.post("/api/billing/checkout")
async def create_checkout(req: CheckoutReq, uid: int = Depends(current_uid)):
    if not stripe.api_key:
        raise HTTPException(503, "Payment gateway not configured")

    user     = _user_by_id(uid)
    price_id = STRIPE_PRO_PRICE_ID if req.plan == "pro" else STRIPE_TEAM_PRICE_ID
    if not price_id:
        raise HTTPException(503, "Stripe price not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=user["email"],
            success_url=f"{YOUR_DOMAIN}/app.html?success=1",
            cancel_url=f"{YOUR_DOMAIN}/app.html?canceled=1",
            metadata={"user_id": str(uid)},
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@app.post("/api/billing/portal")
async def billing_portal(uid: int = Depends(current_uid)):
    if not stripe.api_key:
        raise HTTPException(503, "Payment gateway not configured")
    user = _user_by_id(uid)
    if not user.get("stripe_customer_id"):
        raise HTTPException(400, "No active subscription found")
    try:
        portal = stripe.billing_portal.Session.create(
            customer=user["stripe_customer_id"],
            return_url=f"{YOUR_DOMAIN}/app.html",
        )
        return {"url": portal.url}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@app.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
):
    if not STRIPE_WEBHOOK_SECRET:
        return {"status": "webhook not configured"}

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(400, "Invalid Stripe signature")

    etype = event["type"]

    if etype == "checkout.session.completed":
        sess    = event["data"]["object"]
        uid     = int(sess["metadata"]["user_id"])
        cust_id = sess["customer"]
        sub_id  = sess["subscription"]

        sub      = stripe.Subscription.retrieve(sub_id)
        pid      = sub["items"]["data"][0]["price"]["id"]
        plan     = "pro" if pid == STRIPE_PRO_PRICE_ID else "team"
        _update_user(
            uid,
            plan=plan,
            stripe_customer_id=cust_id,
            stripe_subscription_id=sub_id,
            credits_used=0,
        )

    elif etype in ("customer.subscription.deleted", "customer.subscription.paused"):
        cust_id = event["data"]["object"]["customer"]
        with _conn() as db:
            db.execute(
                "UPDATE users SET plan='free' WHERE stripe_customer_id=?", (cust_id,)
            )
            db.commit()

    return {"status": "ok"}


# ── Serve frontend ─────────────────────────────────────────────────────────────
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

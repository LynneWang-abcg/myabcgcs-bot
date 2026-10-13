from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update

from app.bot import build_application
from app.storage import IssueStore


DATA_DIR = os.environ.get("DATA_DIR", "data")
DATABASE_PATH = os.environ.get("DATABASE_PATH", f"{DATA_DIR}/bot.db")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "telegram")
PUBLIC_URL = os.environ.get("PUBLIC_URL")

store = IssueStore(DATABASE_PATH)
telegram_app = build_application(store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    if PUBLIC_URL:
        await telegram_app.bot.set_webhook(f"{PUBLIC_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}")
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request) -> dict[str, str]:
    if secret != WEBHOOK_SECRET:
        return {"status": "ignored"}
    payload = await request.json()
    update = Update.de_json(payload, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

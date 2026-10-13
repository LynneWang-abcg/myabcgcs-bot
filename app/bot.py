from __future__ import annotations

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.storage import Issue, IssueStore
from app.text_utils import is_simplified_chinese
from app.translator import translate_to_simplified_chinese


KIND_LABELS = {
    "unclassified": "未分类",
    "requirement": "需求",
    "problem": "问题",
}

STATUS_LABELS = {
    "unprocessed": "未处理",
    "in_progress": "处理中",
    "done": "已处理",
}


def build_application(store: IssueStore) -> Application:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    application = Application.builder().token(token).build()
    application.bot_data["store"] = store
    application.bot_data["translator_email"] = os.environ.get("TRANSLATOR_EMAIL")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_open))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "把客户消息转发给我，或直接粘贴文本。我会翻译成简体中文，并帮你记录处理状态。"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return

    text = update.message.text or ""
    if is_simplified_chinese(text):
        translated_text = text
        source_language = "zh-CN"
    else:
        try:
            result = await translate_to_simplified_chinese(
                text,
                email=context.application.bot_data.get("translator_email"),
            )
            translated_text = result.text
            source_language = result.source_language
        except Exception:
            translated_text = text
            source_language = "unknown"

    store: IssueStore = context.application.bot_data["store"]
    issue = store.create_issue(
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        original_text=text,
        translated_text=translated_text,
        source_language=source_language,
    )

    await update.message.reply_text(
        _format_issue(issue),
        reply_markup=_issue_keyboard(issue.id),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    action, issue_id_text, value = query.data.split(":", 2)
    store: IssueStore = context.application.bot_data["store"]
    issue_id = int(issue_id_text)

    if action == "kind":
        issue = store.update_issue(issue_id, kind=value)
    elif action == "status":
        issue = store.update_issue(issue_id, status=value)
    else:
        return

    await query.edit_message_text(
        _format_issue(issue),
        reply_markup=_issue_keyboard(issue.id),
    )


async def list_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    store: IssueStore = context.application.bot_data["store"]
    issues = store.list_open_issues(update.effective_chat.id)
    await update.message.reply_text(_format_issue_list(issues, empty="目前没有未完成事项。"))


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("用法：/search 关键词")
        return
    store: IssueStore = context.application.bot_data["store"]
    issues = store.search_issues(update.effective_chat.id, keyword)
    await update.message.reply_text(_format_issue_list(issues, empty="没有找到相关记录。"))


def _issue_keyboard(issue_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("需求", callback_data=f"kind:{issue_id}:requirement"),
                InlineKeyboardButton("问题", callback_data=f"kind:{issue_id}:problem"),
            ],
            [
                InlineKeyboardButton("未处理", callback_data=f"status:{issue_id}:unprocessed"),
                InlineKeyboardButton("处理中", callback_data=f"status:{issue_id}:in_progress"),
                InlineKeyboardButton("已处理", callback_data=f"status:{issue_id}:done"),
            ],
        ]
    )


def _format_issue(issue: Issue) -> str:
    return (
        f"#{issue.id}\n"
        f"类型：{KIND_LABELS.get(issue.kind, issue.kind)}\n"
        f"状态：{STATUS_LABELS.get(issue.status, issue.status)}\n"
        f"来源语言：{issue.source_language}\n\n"
        f"原文：\n{issue.original_text}\n\n"
        f"简中：\n{issue.translated_text}"
    )


def _format_issue_list(issues: list[Issue], *, empty: str) -> str:
    if not issues:
        return empty
    lines = []
    for issue in issues:
        lines.append(
            f"#{issue.id} [{KIND_LABELS.get(issue.kind, issue.kind)} / "
            f"{STATUS_LABELS.get(issue.status, issue.status)}] {issue.translated_text[:80]}"
        )
    return "\n".join(lines)

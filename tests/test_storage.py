from app.storage import IssueStore


def test_creates_issue_with_default_status(tmp_path):
    store = IssueStore(tmp_path / "bot.db")

    issue = store.create_issue(
        chat_id=123,
        message_id=456,
        original_text="The checkout button fails.",
        translated_text="结账按钮失败。",
        source_language="en",
    )

    assert issue.id == 1
    assert issue.kind == "unclassified"
    assert issue.status == "unprocessed"


def test_updates_issue_kind_and_status(tmp_path):
    store = IssueStore(tmp_path / "bot.db")
    issue = store.create_issue(
        chat_id=123,
        message_id=456,
        original_text="Necesito una función nueva.",
        translated_text="我需要一个新功能。",
        source_language="es",
    )

    store.update_issue(issue.id, kind="requirement", status="in_progress")
    updated = store.get_issue(issue.id)

    assert updated.kind == "requirement"
    assert updated.status == "in_progress"


def test_lists_open_issues_only(tmp_path):
    store = IssueStore(tmp_path / "bot.db")
    first = store.create_issue(1, 10, "A", "A", "zh")
    second = store.create_issue(1, 11, "B", "B", "zh")
    store.update_issue(second.id, status="done")

    open_issues = store.list_open_issues(chat_id=1)

    assert [issue.id for issue in open_issues] == [first.id]

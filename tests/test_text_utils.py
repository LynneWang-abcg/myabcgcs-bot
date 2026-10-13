from app.text_utils import is_simplified_chinese


def test_detects_simplified_chinese_text():
    assert is_simplified_chinese("客户反馈：登录页面打不开，需要尽快处理。")


def test_rejects_english_text_as_simplified_chinese():
    assert not is_simplified_chinese("The login page is not working.")


def test_rejects_traditional_chinese_text_as_simplified_chinese():
    assert not is_simplified_chinese("客戶反饋：登入頁面打不開，需要儘快處理。")

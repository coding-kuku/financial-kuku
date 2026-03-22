"""Unit tests for cli-anything-wukong core modules.

No server required — all network calls are mocked.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from cli_anything.wukong.utils.wukong_backend import (
    WukongClient,
    WukongAPIError,
    WukongAuthError,
    WukongConnectionError,
)
from cli_anything.wukong.core import (
    auth as _auth,
    account as _account,
    subject as _subject,
    certificate as _cert,
    ledger as _ledger,
    voucher_word as _voucher,
    adjuvant as _adjuvant,
    statement as _statement,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_session_dir(tmp_path, monkeypatch):
    """Redirect session storage to a temp directory."""
    import cli_anything.wukong.core.session as sess_mod
    monkeypatch.setattr(sess_mod, "_SESSION_DIR", tmp_path)
    monkeypatch.setattr(sess_mod, "_SESSION_FILE", tmp_path / "session.json")
    return tmp_path


@pytest.fixture
def client():
    """A WukongClient with a fake token (no real server)."""
    return WukongClient(base_url="http://localhost:44316", token="test-token-123")


def _mock_post(client, path, resp_data, status_code=200):
    """Helper: mock a single POST call to return resp_data."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"code": 200, "data": resp_data, "msg": "success"}
    return mock_resp


# ── session.py tests ──────────────────────────────────────────────────

class TestSession:
    def test_load_session_defaults(self, tmp_session_dir):
        from cli_anything.wukong.core.session import load_session
        sess = load_session()
        assert sess["base_url"] == "http://localhost:44316"
        assert sess["token"] is None
        assert sess["account_id"] is None

    def test_save_and_load_session(self, tmp_session_dir):
        from cli_anything.wukong.core.session import save_session, load_session
        data = {"base_url": "http://test:9999", "token": "tok123", "account_id": 5}
        save_session(data)
        loaded = load_session()
        assert loaded["base_url"] == "http://test:9999"
        assert loaded["token"] == "tok123"
        assert loaded["account_id"] == 5

    def test_set_token(self, tmp_session_dir):
        from cli_anything.wukong.core.session import set_token, load_session
        set_token("mytoken")
        assert load_session()["token"] == "mytoken"

    def test_set_account_id(self, tmp_session_dir):
        from cli_anything.wukong.core.session import set_account_id, load_session
        set_account_id(42)
        assert load_session()["account_id"] == 42

    def test_set_base_url(self, tmp_session_dir):
        from cli_anything.wukong.core.session import set_base_url, load_session
        set_base_url("http://myserver:8080/")
        assert load_session()["base_url"] == "http://myserver:8080"

    def test_clear_session(self, tmp_session_dir):
        from cli_anything.wukong.core.session import set_token, set_account_id, clear_session, load_session
        set_token("tok")
        set_account_id(7)
        clear_session()
        sess = load_session()
        assert sess["token"] is None
        assert sess["account_id"] is None


# ── wukong_backend.py tests ───────────────────────────────────────────

class TestWukongClient:
    def test_post_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": {"userId": 1}, "msg": "ok"}
        with patch("requests.post", return_value=mock_resp):
            result = client.post("/test")
        assert result == {"userId": 1}

    def test_post_auth_error_401(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"code": 401, "data": None, "msg": "Unauthorized"}
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(WukongAuthError):
                client.post("/protected")

    def test_post_api_error_business_code(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 400, "data": None, "msg": "用户名或密码错误"}
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(WukongAPIError) as exc_info:
                client.post("/login", auth=False)
        assert "400" in str(exc_info.value)

    def test_post_connection_error(self, client):
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(WukongConnectionError):
                client.post("/test")

    def test_post_no_auth_header(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": "token123", "msg": "ok"}
        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.post("/login", {"user": "a"}, auth=False)
        call_kwargs = mock_post.call_args.kwargs
        headers = call_kwargs.get("headers", {})
        assert "AUTH-TOKEN" not in headers

    def test_post_raw_response(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        full_resp = {"code": 200, "data": [1, 2, 3], "msg": "ok"}
        mock_resp.json.return_value = full_resp
        with patch("requests.post", return_value=mock_resp):
            result = client.post("/test", raw_response=True)
        assert result == full_resp


# ── auth.py tests ─────────────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": "uuid-token-abc", "msg": "ok"}
        with patch("requests.post", return_value=mock_resp):
            token = _auth.login(client, "admin", "123456")
        assert token == "uuid-token-abc"

    def test_login_bad_credentials(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 400, "data": None, "msg": "用户名或密码错误"}
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(WukongAPIError):
                _auth.login(client, "admin", "wrongpass")

    def test_whoami(self, client):
        user = {"userId": 1, "username": "admin", "nickname": "管理员", "isAdmin": True}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": user, "msg": "ok"}
        with patch("requests.post", return_value=mock_resp):
            result = _auth.whoami(client)
        assert result["userId"] == 1
        assert result["username"] == "admin"


# ── account.py tests ──────────────────────────────────────────────────

class TestAccount:
    def test_list_accounts(self, client):
        accounts = [
            {"accountSetId": 1, "accountName": "默认账套", "companyName": "示例公司"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": accounts, "msg": "ok"}
        with patch("requests.post", return_value=mock_resp):
            result = _account.list_accounts(client)
        assert len(result) == 1
        assert result[0]["accountName"] == "默认账套"

    def test_switch_account(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": None, "msg": "ok"}
        with patch("requests.post", return_value=mock_resp) as mock_post:
            _account.switch_account(client, 42)
        call_params = mock_post.call_args.kwargs.get("params", {})
        assert call_params.get("accountId") == 42

    def test_create_account(self, client):
        # create_account calls addAccount then list_all_accounts (two POST calls)
        mock_resp_add = MagicMock()
        mock_resp_add.status_code = 200
        mock_resp_add.json.return_value = {"code": 200, "data": None, "msg": "ok"}
        mock_resp_list = MagicMock()
        mock_resp_list.status_code = 200
        mock_resp_list.json.return_value = {
            "code": 200,
            "data": [{"accountId": "123", "companyName": "示例公司", "status": 0}],
            "msg": "ok",
        }
        with patch("requests.post", side_effect=[mock_resp_add, mock_resp_list]) as mock_post:
            account_id = _account.create_account(client, "示例公司")
        add_call = mock_post.call_args_list[0]
        body = add_call.kwargs.get("json", {})
        assert body["companyName"] == "示例公司"
        assert account_id == 123


# ── subject.py tests ──────────────────────────────────────────────────

class TestSubject:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_list_subjects_flat(self, client):
        subjects = [
            {"subjectId": 1, "subjectNumber": "1001", "subjectName": "库存现金", "subjectType": 1}
        ]
        with patch("requests.post", return_value=self._mock(subjects)):
            result = _subject.list_subjects(client, is_tree=0)
        assert result[0]["subjectNumber"] == "1001"

    def test_list_subjects_tree(self, client):
        with patch("requests.post", return_value=self._mock([])) as mock_post:
            _subject.list_subjects(client, is_tree=1)
        params = mock_post.call_args.kwargs.get("params", {})
        assert params.get("isTree") == 1

    def test_add_subject(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _subject.add_subject(client, "1001", "库存现金", 1, parent_id=10)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["number"] == "1001"       # API field is "number", not "subjectNumber"
        assert body["subjectName"] == "库存现金"
        assert body["type"] == 1              # API field is "type", not "subjectType"
        assert body["parentId"] == 10         # API field is "parentId", not "pid"

    def test_delete_subjects(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _subject.delete_subjects(client, [1, 2, 3])
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["ids"] == [1, 2, 3]


# ── certificate.py tests ──────────────────────────────────────────────

class TestCertificate:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_list_certificates_pagination(self, client):
        page_result = {"records": [], "total": 0, "pages": 1}
        with patch("requests.post", return_value=self._mock(page_result)) as mock_post:
            _cert.list_certificates(client, page_no=2, page_size=50)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["pageNo"] == 2
        assert body["pageSize"] == 50

    def test_get_certificate(self, client):
        cert = {"certificateId": 99, "voucherName": "记", "details": []}
        with patch("requests.post", return_value=self._mock(cert)):
            result = _cert.get_certificate(client, 99)
        assert result["certificateId"] == 99

    def test_add_certificate(self, client):
        details = [
            {"subjectId": 1, "digestContent": "memo", "debtorBalance": 1000, "creditBalance": 0},
            {"subjectId": 2, "digestContent": "memo", "debtorBalance": 0, "creditBalance": 1000},
        ]
        with patch("requests.post", return_value=self._mock({"certificateId": 1})) as mock_post:
            _cert.add_certificate(client, 1, "2024-06-01", details)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["voucherId"] == 1
        assert body["certificateTime"] == "2024-06-01"
        assert len(body["certificateDetails"]) == 2

    def test_review_certificates(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _cert.review_certificates(client, [10, 11], 1)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["ids"] == [10, 11]
        assert body["status"] == 1


# ── ledger.py tests ───────────────────────────────────────────────────

class TestLedger:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_query_detail_account(self, client):
        rows = [{"date": "2024-01-01", "debit": 1000, "credit": 0}]
        with patch("requests.post", return_value=self._mock(rows)) as mock_post:
            result = _ledger.query_detail_account(client, 123, "2024-01-01", "2024-06-30")
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["subjectId"] == 123
        assert body["startTime"] == "2024-01-01"
        assert result == rows

    def test_query_subject_balance_optional_filters(self, client):
        with patch("requests.post", return_value=self._mock([])) as mock_post:
            _ledger.query_subject_balance(client, "2024-01-01", "2024-12-31", level=1)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["level"] == 1
        assert "subjectId" not in body


# ── certificate update tests ───────────────────────────────────────────

class TestCertificateUpdate:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_update_certificate(self, client):
        details = [
            {"subjectId": 1, "digestContent": "修改", "debtorBalance": 500, "creditBalance": 0},
            {"subjectId": 2, "digestContent": "修改", "debtorBalance": 0, "creditBalance": 500},
        ]
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _cert.update_certificate(client, 42, 1, "2024-06-15", details)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["certificateId"] == 42
        assert body["voucherId"] == 1
        assert body["certificateTime"] == "2024-06-15"
        assert len(body["certificateDetails"]) == 2

    def test_update_certificate_with_num(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _cert.update_certificate(client, 10, 2, "2024-03-01", [], certificate_num=5)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["certificateNum"] == 5


# ── adjuvant.py tests ─────────────────────────────────────────────────

class TestAdjuvant:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_list_adjuvants(self, client):
        items = [
            {"adjuvantId": "1", "adjuvantName": "部门", "label": 5, "adjuvantType": 1},
        ]
        with patch("requests.post", return_value=self._mock(items)):
            result = _adjuvant.list_adjuvants(client)
        assert len(result) == 1
        assert result[0]["adjuvantName"] == "部门"

    def test_add_adjuvant(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _adjuvant.add_adjuvant(client, "研发中心", label=5)
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["adjuvantName"] == "研发中心"
        assert body["label"] == 5

    def test_add_adjuvant_default_label(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _adjuvant.add_adjuvant(client, "自定义维度")
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["label"] == 7  # default = 自定义

    def test_delete_adjuvant(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _adjuvant.delete_adjuvant(client, 99)
        call_params = mock_post.call_args.kwargs.get("params", {})
        assert call_params.get("adjuvantId") == 99


# ── statement.py tests ────────────────────────────────────────────────

class TestStatement:
    def _mock(self, data):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "data": data, "msg": "ok"}
        return mock_resp

    def test_query_statement(self, client):
        vo = {"settleTime": "2024-01-31T00:00:00", "number": 5, "accountId": 1, "statements": []}
        with patch("requests.post", return_value=self._mock(vo)):
            result = _statement.query_statement(client)
        assert result["number"] == 5

    def test_close_period(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _statement.close_period(client, "2024-01-31")
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["type"] == 1
        assert body["certificateTime"] == "2024-01-31"

    def test_reopen_period(self, client):
        with patch("requests.post", return_value=self._mock(None)) as mock_post:
            _statement.reopen_period(client, "2024-01-31")
        body = mock_post.call_args.kwargs.get("json", {})
        assert body["type"] == 2
        assert body["certificateTime"] == "2024-01-31"

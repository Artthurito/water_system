import pytest

from app.core.security import API_KEY_PREFIX, generate_api_key, hash_api_key, require_admin
from app.domain.errors import InvalidAdminKeyError


def test_generated_key_has_prefix_and_is_unique():
    first = generate_api_key()
    second = generate_api_key()

    assert first.startswith(API_KEY_PREFIX)
    assert first != second


def test_hash_is_deterministic_sha256_hex():
    assert hash_api_key("ws_abc") == hash_api_key("ws_abc")
    assert len(hash_api_key("ws_abc")) == 64


def test_different_keys_have_different_hashes():
    assert hash_api_key("ws_abc") != hash_api_key("ws_abd")


def test_require_admin_accepts_configured_key(settings):
    assert require_admin(settings.admin_api_key, settings) is None


@pytest.mark.parametrize("admin_key", [None, "", "wrong-key", "chave-com-acentuação"])
def test_require_admin_rejects_missing_or_wrong_key(settings, admin_key):
    with pytest.raises(InvalidAdminKeyError):
        require_admin(admin_key, settings)

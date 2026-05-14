import pytest

from app.domain.exceptions.user import WeakPasswordException
from app.domain.services.password_validator import PasswordValidator


class TestPasswordValidator:
    @pytest.fixture
    def base_config(self):
        return {
            "min_length": 0,
            "max_length": 1024,
            "require_uppercase": False,
            "require_lowercase": False,
            "require_digits": False,
            "require_special": False,
            "forbidden_passwords": [],
        }

    def test_validate_success(self):
        PasswordValidator.validate("SecurePass123!")

    def test_validate_too_short(self, base_config):
        base_config["min_length"] = 1
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("", **base_config)
        assert "at least 1 characters" in exc.value.message

    def test_validate_too_long(self, base_config):
        base_config["max_length"] = 0
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("p", **base_config)
        assert "at most 0 characters" in exc.value.message

    def test_validate_no_uppercase(self, base_config):
        base_config["require_uppercase"] = True
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("password", **base_config)
        assert "at least one uppercase letter" in exc.value.message

    def test_validate_no_lowercase(self, base_config):
        base_config["require_lowercase"] = True
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("PASSWORD", **base_config)
        assert "at least one lowercase letter" in exc.value.message

    def test_validate_no_digit(self, base_config):
        base_config["require_digits"] = True
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("password", **base_config)
        assert "at least one digit" in exc.value.message

    def test_validate_no_special(self, base_config):
        base_config["require_special"] = True
        base_config["special_chars"] = "@"
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("password", **base_config)
        assert "at least one special character" in exc.value.message

    def test_validate_forbidden_passwords(self, base_config):
        base_config["forbidden_passwords"] = ["password", "qwerty"]
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("password", **base_config)
        assert "too common" in exc.value.message

    def test_validate_case_insensitive_forbidden(self, base_config):
        base_config["forbidden_passwords"] = ["PassWord", "qwerty"]
        with pytest.raises(WeakPasswordException) as exc:
            PasswordValidator.validate("password", **base_config)
        assert "too common" in exc.value.message

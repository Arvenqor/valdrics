import os
import unittest
from unittest.mock import patch
from app.shared.core.config import Settings

FAKE_KDF_SALT = "S0RGX1NBTFRfRk9SX1RFU1RJTkdfMzJfQllURVNfT0s="


class TestRedisConfig(unittest.TestCase):
    def test_explicit_redis_url_is_loaded(self):
        """Test that REDIS_URL must be provided explicitly when Redis is used."""
        env = {
            "REDIS_URL": "redis://redis-test:6380",
            "CSRF_SECRET_KEY": "c" * 32,
            "ENCRYPTION_KEY": "k" * 32,
            "KDF_SALT": FAKE_KDF_SALT,
            "SUPABASE_JWT_SECRET": "test_secret_32_chars_long_xxxxxxxx",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None, DEBUG=True)
            self.assertEqual(settings.REDIS_URL, "redis://redis-test:6380")

    def test_removed_legacy_host_port_fields_are_ignored(self):
        """Test that removed REDIS_HOST/REDIS_PORT compat fields are not part of Settings."""
        env = {
            "REDIS_URL": "redis://explicit-host:9999",
            "CSRF_SECRET_KEY": "c" * 32,
            "ENCRYPTION_KEY": "k" * 32,
            "KDF_SALT": FAKE_KDF_SALT,
            "SUPABASE_JWT_SECRET": "test_secret_32_chars_long_xxxxxxxx",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings(_env_file=None, DEBUG=True)
            self.assertEqual(settings.REDIS_URL, "redis://explicit-host:9999")
            self.assertNotIn("REDIS_HOST", Settings.model_fields)
            self.assertNotIn("REDIS_PORT", Settings.model_fields)


if __name__ == "__main__":
    unittest.main()

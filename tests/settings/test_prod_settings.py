import os
import subprocess
import sys


def _load_prod_settings_without(variable: str) -> subprocess.CompletedProcess[str]:
    """Prod sozlamalarini ko'rsatilgan majburiy o'zgaruvchisiz yuklaydi."""
    environment = os.environ.copy()
    environment.update(
        {
            'DJANGO_SETTINGS_MODULE': 'config.settings.prod',
            'SECRET_KEY': 'test-only-not-real',
            'ALLOWED_HOSTS': 'example.com',
            'DATABASE_URL': 'postgres://alora:alora_password@localhost:5432/alora',
            'REDIS_URL': 'redis://localhost:6379/0',
        }
    )
    environment[variable] = ''
    return subprocess.run(
        [sys.executable, '-c', 'import config.settings.prod'],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_prod_settings_secret_key_majburiy() -> None:
    """SECRET_KEY bo'lmasa prod sozlamalari xato berishi kerak."""
    result = _load_prod_settings_without('SECRET_KEY')

    assert result.returncode != 0
    assert 'ImproperlyConfigured' in result.stderr


def test_prod_settings_allowed_hosts_majburiy() -> None:
    """ALLOWED_HOSTS bo'lmasa prod sozlamalari xato berishi kerak."""
    result = _load_prod_settings_without('ALLOWED_HOSTS')

    assert result.returncode != 0
    assert 'ImproperlyConfigured' in result.stderr

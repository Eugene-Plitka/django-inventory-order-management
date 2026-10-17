import os
from pathlib import Path

from .settings import *  # noqa: F401, F403


def read_secret(name):
    file_path = os.environ.get(f"{name}_FILE")

    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()

    return os.environ.get(name, "")


DEBUG = False

SECRET_KEY = read_secret("SECRET_KEY")

ALLOWED_HOSTS = [
    "ordermanagement.eugene-dev-hub.space",
]

CSRF_TRUSTED_ORIGINS = [
    "https://ordermanagement.eugene-dev-hub.space",
]

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

DATABASES["default"]["PASSWORD"] = read_secret("POSTGRES_PASSWORD")

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]

# JWT signing key is separate from the Django SECRET_KEY.
# It can be rotated during a demo environment reset.

JWT_SIGNING_KEY = read_secret("JWT_SIGNING_KEY")

if not JWT_SIGNING_KEY:
    raise RuntimeError("JWT_SIGNING_KEY must be configured for production.")

SIMPLE_JWT = {
    **SIMPLE_JWT,
    "SIGNING_KEY": JWT_SIGNING_KEY,
}

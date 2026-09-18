"""Production settings. Every secret must come from the environment."""

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, DATABASES, env

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False

# Render publishes the service's own hostname; trusting it means the deploy
# works before you know the URL, and keeps working if you rename the service.
RENDER_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_HOSTNAME:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_HOSTNAME]

# A leading dot in ALLOWED_HOSTS means "any subdomain"; the CSRF setting spells
# that as an explicit wildcard, so ".onrender.com" becomes "https://*.onrender.com".
CSRF_TRUSTED_ORIGINS = [
    f"https://*{host}" if host.startswith(".") else f"https://{host}"
    for host in ALLOWED_HOSTS
    if host != "*"
]

# Hashed, compressed filenames so the admin's assets can be cached forever.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# A persistent process, unlike serverless: hold connections open between
# requests rather than paying Neon's TLS handshake every time.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

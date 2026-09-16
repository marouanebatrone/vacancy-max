"""Developer machine settings."""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env  # noqa: F401

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

"""Custom user model.

Declared in commit #1 even though M0-M4 ship anonymously: swapping AUTH_USER_MODEL
after tables exist is one of Django's genuinely painful migrations.
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass

from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.utils.translation import gettext as _
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class CoreModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        to=User,
        editable=False,
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True


def get_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.created_by)}-{uuid.uuid4()}{extension}"
    dirname = f"{slugify(type(instance).__name__)}s"

    return os.path.join("uploads", dirname, filename)


class UserProfile(CoreModel):
    bio = models.TextField()
    image = models.ImageField(
        blank=True, null=True, upload_to=get_image_file_path
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["created_by"], name="unique_created_by"
            )
        ]

    def __str__(self):
        return f"{self.id}: {self.created_by}"


class UserProfileFollow(CoreModel):
    following = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_by = models.ForeignKey(
        to=get_user_model(),
        editable=False,
        on_delete=models.CASCADE,
        related_name="followings",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "following"], name="unique_follows"
            )
        ]

    def validate_following(self):
        if self.created_by == self.following:
            raise ValidationError("Cannot follow/unfollow your own profile.")

    def save(self, *args, **kwargs):
        self.validate_following()
        super(UserProfileFollow, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.created_by} follows {self.following}"

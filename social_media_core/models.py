import os.path
import uuid

from django.db import models
from django.conf import settings
from django.utils.text import slugify

from user.models import CoreModel, UserProfile


class HashTag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.id}: {self.name}"


def get_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"
    dirname = f"{slugify(type(instance).__name__)}s"

    return os.path.join("uploads", dirname, filename)


class Post(CoreModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    hashtags = models.ManyToManyField(
        HashTag, related_name="posts", blank=True
    )
    content = models.TextField()
    image = models.ImageField(
        null=True, blank=True, upload_to=get_image_file_path
    )
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    is_visible = models.BooleanField(default=True)
    scheduled_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.id}: {self.title}"


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="post_comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    comment_contents = models.CharField(max_length=255)

    def __str__(self):
        return f"Comment by {self.user} posted {self.created_at}"


class Like(CoreModel):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post_id", "created_by_id"], name="unique_likes"
            )
        ]

    def __str__(self):
        return f"Liked by {self.created_by}"

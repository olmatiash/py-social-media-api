from django.contrib import admin

from social_media_core.models import HashTag, Post, Comment

from social_media_core.models import Like

admin.site.register(HashTag)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)

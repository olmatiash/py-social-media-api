from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import UserProfileFollow, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
            "is_staff",
            "username",
            "first_name",
            "last_name",
        )
        read_only_fields = ("is_staff",)
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class UserDetailSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = ("userprofile",) + UserSerializer.Meta.fields
        read_only_fields = ("userprofile", "is_staff")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}


class CoreModelSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = UserSerializer(many=False, read_only=True)

    class Meta:
        fields = (
            "created_at",
            "updated_at",
            "created_by",
        )


class UserProfileFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileFollow
        fields = ("id", "created_by", "following")
        read_only_fields = ("created_by",)


class UserProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("id", "image")


class UserProfileSerializer(CoreModelSerializer, serializers.ModelSerializer):
    followings = serializers.SerializerMethodField(read_only=True)
    followers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "bio",
            "image",
            "followers",
            "followings",
        ) + CoreModelSerializer.Meta.fields

    def get_followings(self, obj):
        qs = UserProfileFollow.objects.filter(created_by=obj.created_by)
        return [follow.following_id for follow in qs]

    def get_followers(self, obj):
        qs = UserProfileFollow.objects.filter(following=obj.created_by)
        return [follow.created_by_id for follow in qs]


class UserProfileListSerializer(UserProfileSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    followings_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "bio",
            "image",
            "followers_count",
            "followings_count",
            "posts_count",
        ) + CoreModelSerializer.Meta.fields


class UserProfileDetailSerializer(UserProfileSerializer):
    posts = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = UserProfileSerializer.Meta.fields + ("posts", "followings")

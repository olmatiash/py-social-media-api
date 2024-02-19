from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics, views, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import UserSerializer, UserDetailSerializer, UserProfileDetailSerializer, \
    UserProfileListSerializer, UserProfileImageSerializer, UserProfileSerializer, UserProfileFollowSerializer

from social_media_core.permissions import IsOwnerOrReadOnly
from user.models import UserProfile, UserProfileFollow


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    authentication_classes = (JWTAuthentication,)

    def get_object(self):
        return self.request.user


class LogoutView(views.APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(views.APIView):
    def post(self, request):
        tokens = OutstandingToken.objects.filter(user_id=request.user.id)
        for token in tokens:
            t, _ = BlacklistedToken.objects.get_or_create(token=token)

        return Response(status=status.HTTP_205_RESET_CONTENT)


class CoreModelMixin:
    def perform_create(self, serializer, *args, **kwargs):
        return serializer.save(created_by=self.request.user, *args, **kwargs)


class UserProfilePagination(PageNumberPagination):
    page_size = 3
    max_page_size = 100


class UserProfileViewSet(CoreModelMixin, viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    pagination_class = UserProfilePagination
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly,
    ]

    def get_queryset(self):
        queryset = self.queryset.annotate(
            followers_count=(Count("created_by__followers")),
            followings_count=(Count("created_by__followings")),
            posts_count=(Count("posts")),
        )

        if self.action != "create":
            queryset.select_related(
                "created_by__followers", "created_by__followings"
            ).prefetch_related("posts")

        queryset = self.filter_queryset(queryset)
        return queryset

    def filter_queryset(self, queryset):
        for param_name in ["email", "first_name", "last_name", "username"]:
            param = self.request.query_params.get(param_name)

            if param:
                queryset = queryset.filter(
                    **{f"created_by__{param_name}__icontains": param}
                )

        created_by = self.request.query_params.get("user_id")
        if created_by:
            queryset = queryset.filter(created_by=created_by)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return UserProfileListSerializer

        if self.action == "retrieve":
            return UserProfileDetailSerializer

        if self.action == "upload_image":
            return UserProfileImageSerializer

        return UserProfileSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific user profile"""
        user_profile = self.get_object()
        serializer = self.get_serializer(user_profile, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email",
                description="Filter by email (ex. ?email=example@gmail.com)",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="first_name",
                description="Filter by first name (ex. ?first_name=John)",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="last_name",
                description="Filter by last name (ex. ?last_name=Smith)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="username",
                description="Filter by username (ex. ?username=mate)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="created_by",
                description="Filter by user id (ex. ?created_by=2)",
                type=OpenApiTypes.STR,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class UserProfileFollowViewSet(CoreModelMixin, viewsets.ModelViewSet):
    queryset = UserProfileFollow.objects.all()
    serializer_class = UserProfileFollowSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly,
    ]

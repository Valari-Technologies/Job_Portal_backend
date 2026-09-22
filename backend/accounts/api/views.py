from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q

from .permissions import IsSuperAdminRole
from .serializers import (
    CandidateRegisterSerializer,
    HRRegisterSerializer,
    AdminCreateUserSerializer,
    AdminUserSerializer,
    GoogleLoginSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileUpdateSerializer
)

User = get_user_model()


class CandidateRegisterView(generics.CreateAPIView):
    """
    API endpoint for registering Candidate users.
    """
    queryset = User.objects.all()
    serializer_class = CandidateRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "message": "Account created successfully.",
                "user": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class HRRegisterView(generics.CreateAPIView):
    """
    API endpoint for registering HR users (Super Admin restricted).
    """
    queryset = User.objects.all()
    serializer_class = HRRegisterSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            {
                "message": "HR created successfully.",
                "user": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class AdminCreateUserView(generics.CreateAPIView):
    """
    API endpoint for Super Admin to create ADMIN or HR accounts.
    """
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "message": f"{serializer.validated_data.get('role')} account created successfully.",
                "user": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class AdminListView(generics.ListAPIView):
    """
    API endpoint for Super Admin to list created Admin accounts.
    """
    serializer_class = AdminUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.Role.ADMIN
        ).exclude(
            status=User.Status.DELETED
        ).select_related('created_by').order_by('-created_at', '-id')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(status__icontains=search)
            )

        return queryset


class GoogleLoginView(APIView):
    """
    API endpoint for Google OAuth authentication.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data['tokens'], status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens with custom user payload.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve or update the authenticated user's profile.
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class CurrentUserMeView(APIView):
    """
    API endpoint to retrieve safe identity payload for current authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        return Response({
            "id": user.id,
            "name": full_name,
            "fullName": full_name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }, status=status.HTTP_200_OK)


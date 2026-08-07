from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    CandidateRegisterSerializer,
    HRRegisterSerializer,
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

        # serializer.data is built by to_representation() from the created user,
        # so no credentials are echoed back.
        return Response(
            {
                "message": "Account created successfully.",
                "user": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class HRRegisterView(generics.CreateAPIView):
    """
    API endpoint for registering HR users.
    """
    queryset = User.objects.all()
    serializer_class = HRRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Omit password in response
        response_data = serializer.data
        return Response(
            {
                "message": "HR registered successfully.",
                "user": response_data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )


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

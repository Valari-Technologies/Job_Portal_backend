from ..models import HRProfile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
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
    UserProfileUpdateSerializer,
    LocationSerializer,
    EmployerUserSerializer,
    CandidateUserSerializer,
    EmployerProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
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
    serializer_class = UserProfileUpdateSerializer,
    LocationSerializer,
    EmployerUserSerializer,
    CandidateUserSerializer,
    EmployerProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
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
        
        data = {
            "id": user.id,
            "user_id": user.id,
            "name": full_name,
            "full_name": full_name,
            "fullName": full_name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "phone_number": user.phone_number,
        }

        if user.role == User.Role.HR:
            hr_profile = getattr(user, 'hr_profile', None)
            if not hr_profile:
                hr_profile, _ = HRProfile.objects.get_or_create(user=user)
            if hr_profile:
                data.update({
                    "company_name": hr_profile.company_name or "",
                    "company_email": hr_profile.company_email or user.email,
                    "company_phone": hr_profile.company_phone or user.phone_number or "",
                    "company_website": hr_profile.company_website or "",
                    "company_address": hr_profile.company_address or "",
                    "company_description": hr_profile.company_description or "",
                    "company_logo": hr_profile.company_logo or "",
                    "designation": hr_profile.designation or "",
                    "verification_status": hr_profile.verification_status or "PENDING",
                    "trust_level": hr_profile.trust_level or "NEW",
                    "location_id": hr_profile.location_id,
                })

        return Response(data, status=status.HTTP_200_OK)




class EmployerProfileView(APIView):
    """
    API endpoint to retrieve or update the authenticated Employer/HR company profile.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.role != User.Role.HR:
            return Response(
                {"detail": "Only Employers/HR can access this profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile, _ = HRProfile.objects.get_or_create(user=request.user)
        serializer = EmployerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        if request.user.role != User.Role.HR:
            return Response(
                {"detail": "Only Employers/HR can update this profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile, _ = HRProfile.objects.get_or_create(user=request.user)
        
        # Enforce profile ownership strictly to request.user
        if profile.user != request.user:
            return Response(
                {"detail": "You do not have permission to edit this profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EmployerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Sync User fields if full_name or phone_number sent
        full_name = request.data.get('full_name') or request.data.get('fullName')
        if full_name:
            names = full_name.strip().split(' ', 1)
            request.user.first_name = names[0]
            request.user.last_name = names[1] if len(names) > 1 else ''
            request.user.save(update_fields=['first_name', 'last_name', 'updated_at'])

        if 'phone_number' in request.data:
            request.user.phone_number = request.data['phone_number']
            request.user.save(update_fields=['phone_number', 'updated_at'])

        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    API endpoint to initiate secure password reset request.
    Always returns generic success message to prevent user enumeration.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        safe_response = {
            "message": "If an account exists for this email, reset instructions will be sent."
        }

        try:
            user = User.objects.filter(email__iexact=email).first()
            if user and user.is_active and user.status == User.Status.ACTIVE:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = f"http://localhost:5173/reset-password/{uid}/{token}"

                # Try sending email, catch silently or log if SMTP is unconfigured in development
                try:
                    send_mail(
                        subject="State Jobz / TN Jobz Password Reset",
                        message=f"Hello {user.username},\n\nPlease use the link below to reset your password:\n{reset_link}\n\nThis link is valid for 24 hours.",
                        from_email=None,
                        recipient_list=[user.email],
                        fail_silently=True
                    )
                except Exception:
                    pass
        except Exception:
            pass

        return Response(safe_response, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API endpoint to confirm password reset with token and new password.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid_b64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        try:
            uid = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired password reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired password reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(password, user)
        except DjangoValidationError as exc:
            return Response(
                {"password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.save()

        return Response(
            {"message": "Password reset successfully."},
            status=status.HTTP_200_OK
        )



class CandidateListView(generics.ListAPIView):
    """
    API endpoint for Super Admin to list created Candidate accounts.
    """
    serializer_class = CandidateUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.Role.CANDIDATE
        ).exclude(
            status=User.Status.DELETED
        ).select_related('candidate_profile', 'candidate_profile__location').order_by('-created_at', '-id')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(candidate_profile__full_name__icontains=search)
            )

        status_param = self.request.query_params.get('status', '').strip()
        if status_param and status_param.lower() != 'all':
            queryset = queryset.filter(status__iexact=status_param)

        state_param = self.request.query_params.get('state', '').strip()
        if state_param and state_param.lower() != 'all':
            queryset = queryset.filter(
                Q(candidate_profile__location__name__icontains=state_param) |
                Q(candidate_profile__location__parent__name__icontains=state_param) |
                Q(candidate_profile__location__parent__parent__name__icontains=state_param) |
                Q(candidate_profile__location__parent__parent__parent__name__icontains=state_param)
            )

        district_param = self.request.query_params.get('district', '').strip()
        if district_param and district_param.lower() != 'all':
            queryset = queryset.filter(
                Q(candidate_profile__location__name__icontains=district_param) |
                Q(candidate_profile__location__parent__name__icontains=district_param) |
                Q(candidate_profile__location__parent__parent__name__icontains=district_param)
            )

        return queryset


class EmployerListView(generics.ListAPIView):
    """
    API endpoint for Super Admin to list created Employer accounts.
    """
    serializer_class = EmployerUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.Role.HR
        ).exclude(
            status=User.Status.DELETED
        ).select_related('hr_profile', 'hr_profile__location').order_by('-created_at', '-id')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(hr_profile__company_name__icontains=search) |
                Q(hr_profile__company_email__icontains=search)
            )

        status_param = self.request.query_params.get('status', '').strip()
        if status_param and status_param.lower() != 'all':
            queryset = queryset.filter(status__iexact=status_param)

        verification_status = self.request.query_params.get('verification_status', '').strip()
        if verification_status and verification_status.lower() != 'all':
            queryset = queryset.filter(hr_profile__verification_status__iexact=verification_status)

        state_param = self.request.query_params.get('state', '').strip()
        if state_param and state_param.lower() != 'all':
            queryset = queryset.filter(
                Q(hr_profile__company_address__icontains=state_param) |
                Q(hr_profile__location__name__icontains=state_param) |
                Q(hr_profile__location__parent__name__icontains=state_param) |
                Q(hr_profile__location__parent__parent__name__icontains=state_param)
            )

        return queryset


class LocationListView(generics.ListCreateAPIView):
    """
    API endpoint to list active locations and create new location items.
    GET is public / authenticated; POST is restricted to Super Admin.
    """
    serializer_class = LocationSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsSuperAdminRole()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Location.objects.filter(is_active=True).select_related('parent').order_by('name')
        
        location_type = self.request.query_params.get('location_type', '').strip()
        if location_type:
            queryset = queryset.filter(location_type__iexact=location_type)
            
        parent_id = self.request.query_params.get('parent_id', '').strip()
        if parent_id:
            if parent_id.lower() == 'null' or parent_id == '0':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)

        return queryset

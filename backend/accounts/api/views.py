from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from ..models import (
    HRProfile, Location, CandidateProfile, AdminProfile, AuditEvent,
    EmployerVerification, EmployerTrust, Job, JobReview, JobCategory, Skill, Notification, JobReport,
    Education, Experience, Resume, CandidateSkill, SavedJob, Application, ApplicationStatusHistory,
    ApplicationMessage, Interview, CandidateActivity, JobRecommendation
)
from ..services.audit_service import log_audit_event
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

from .permissions import IsSuperAdminRole, IsAdminRole, IsHRRole, IsCandidateRole
from .serializers import (
    CandidateRegisterSerializer,
    HRRegisterSerializer,
    AdminCreateUserSerializer,
    AdminUserSerializer,
    GoogleLoginSerializer,
    CustomTokenObtainPairSerializer,
    CandidateJobSerializer,
    CandidateInterviewSerializer,
    CandidateApplicationDetailSerializer,
    CandidateApplicationSubmitSerializer,
    SavedJobSerializer,
    ResumeSerializer,
    CandidateSkillSerializer,
    UserProfileUpdateSerializer,
    LocationSerializer,
    EmployerUserSerializer,
    CandidateUserSerializer,
    EmployerProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    AuditEventSerializer,
    PrivilegedUserAccessReviewSerializer,
    EmployerVerificationQueueSerializer,
    EmployerVerificationHistorySerializer,
    JobReviewQueueSerializer,
    JobReviewHistorySerializer,
    JobCategorySerializer,
    SkillSerializer,
    NotificationSerializer,
    JobReportSerializer,
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
    API endpoint for registering HR users.
    """
    queryset = User.objects.all()
    serializer_class = HRRegisterSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

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
    API endpoint for Super Admin and Admin to create ADMIN or HR accounts.
    """
    queryset = User.objects.all()
    serializer_class = AdminCreateUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        target_role = serializer.validated_data.get('role')
        if request.user.role == User.Role.ADMIN and target_role == User.Role.ADMIN:
            return Response(
                {"detail": "Admins cannot create another Admin account. Only Super Admins can create Admins."},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_create(serializer)
        return Response(
            {
                "message": f"{target_role} account created successfully.",
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

                log_audit_event(
                    actor=user,
                    actor_email=user.email,
                    action='PASSWORD_RESET_REQUEST',
                    target_type='User',
                    target_id=user.id,
                    target_repr=user.email,
                    outcome='SUCCESS',
                    description=f"Password reset requested for {user.email}",
                    request=request
                )
            else:
                log_audit_event(
                    actor=None,
                    actor_email=email,
                    action='PASSWORD_RESET_REQUEST',
                    target_type='User',
                    target_repr=email,
                    outcome='SUCCESS',
                    description=f"Password reset requested for {email} (user non-existent or inactive)",
                    request=request
                )
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

        log_audit_event(
            actor=user,
            actor_email=user.email,
            action='PASSWORD_RESET_CONFIRM',
            target_type='User',
            target_id=user.id,
            target_repr=user.email,
            outcome='SUCCESS',
            description=f"Password reset successfully completed for {user.email}",
            request=request
        )

        return Response(
            {"message": "Password reset successfully."},
            status=status.HTTP_200_OK
        )



class CandidateListView(generics.ListAPIView):
    """
    API endpoint for Super Admin and Admin to list Candidate accounts.
    """
    serializer_class = CandidateUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

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
    API endpoint for Super Admin and Admin to list Employer/Recruiter accounts.
    """
    serializer_class = EmployerUserSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.Role.HR
        ).exclude(
            status=User.Status.DELETED
        ).select_related('hr_profile', 'hr_profile__location', 'created_by').order_by('-created_at', '-id')

        # Role-based visibility filtering:
        # Each Admin user ONLY sees Recruiter accounts created by themselves (per-Admin isolation)
        # Super Admin viewing with only_admin_created=true sees all Admin-created Recruiters
        # Super Admin viewing Super Admin employers view (no only_admin_created) sees ALL Recruiters across all accounts
        only_admin_created = self.request.query_params.get('only_admin_created', '').lower() == 'true'
        if self.request.user.role == User.Role.ADMIN:
            queryset = queryset.filter(created_by=self.request.user)
        elif only_admin_created:
            queryset = queryset.filter(created_by__role=User.Role.ADMIN)

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


class AdminUpdateEmployerDetailView(APIView):
    """
    API endpoint for Admin and Super Admin to retrieve and update a Recruiter/Employer account.
    """
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id, role=User.Role.HR)
        except User.DoesNotExist:
            return Response({"detail": "Employer account not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployerUserSerializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id, role=User.Role.HR)
        except User.DoesNotExist:
            return Response({"detail": "Employer account not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        full_name = data.get('full_name') or data.get('fullName') or data.get('name')
        if full_name:
            names = full_name.strip().split(' ', 1)
            target_user.first_name = names[0]
            target_user.last_name = names[1] if len(names) > 1 else ''

        if 'email' in data and data['email']:
            target_user.email = data['email'].lower().strip()
        if 'phone_number' in data or 'phone' in data:
            target_user.phone_number = data.get('phone_number') or data.get('phone')
        if 'status' in data and data['status']:
            status_val = data['status'].upper().strip()
            if status_val in dict(User.Status.choices):
                target_user.status = status_val
                target_user.is_active = (status_val == User.Status.ACTIVE)

        target_user.save()

        profile, _ = HRProfile.objects.get_or_create(user=target_user)
        if 'company_name' in data:
            profile.company_name = data['company_name']
        if 'company_email' in data:
            profile.company_email = data['company_email']
        if 'company_phone' in data:
            profile.company_phone = data['company_phone']
        if 'company_website' in data:
            profile.company_website = data['company_website']
        if 'company_address' in data:
            profile.company_address = data['company_address']
        if 'company_description' in data:
            profile.company_description = data['company_description']
        if 'designation' in data:
            profile.designation = data['designation']
        
        logo = data.get('company_logo') or data.get('profile_photo')
        if logo:
            profile.company_logo = logo

        profile.save()

        serializer = EmployerUserSerializer(target_user)
        return Response({
            "message": "Employer account updated successfully.",
            "employer": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        return self.patch(request, user_id)


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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditEventListView(generics.ListAPIView):
    """
    Super Admin–only paginated API with filters for date range, actor, action, outcome, and target.
    """
    serializer_class = AuditEventSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related('actor').order_by('-timestamp', '-id')

        start_date = self.request.query_params.get('start_date', '').strip()
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)

        end_date = self.request.query_params.get('end_date', '').strip()
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        action = self.request.query_params.get('action', '').strip()
        if action and action.lower() != 'all':
            queryset = queryset.filter(action__iexact=action)

        outcome = self.request.query_params.get('outcome', '').strip()
        if outcome and outcome.lower() != 'all':
            queryset = queryset.filter(outcome__iexact=outcome)

        target_type = self.request.query_params.get('target_type', '').strip()
        if target_type and target_type.lower() != 'all':
            queryset = queryset.filter(target_type__iexact=target_type)

        actor = self.request.query_params.get('actor', '').strip()
        if actor:
            queryset = queryset.filter(
                Q(actor_email__icontains=actor) |
                Q(actor__first_name__icontains=actor) |
                Q(actor__last_name__icontains=actor) |
                Q(actor__username__icontains=actor)
            )

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(target_repr__icontains=search) |
                Q(actor_email__icontains=search) |
                Q(action__icontains=search) |
                Q(ip_address__icontains=search)
            )

        return queryset


class SecurityPostureView(APIView):
    """
    Returns verified facts and counts for Security Posture.
    Only accessible by Super Admin.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def get(self, request):
        now = timezone.now()
        since_24h = now - timedelta(hours=24)

        total_users = User.objects.exclude(status=User.Status.DELETED).count()
        active_users = User.objects.filter(status=User.Status.ACTIVE, is_active=True).count()
        suspended_users = User.objects.filter(status=User.Status.SUSPENDED).count()
        inactive_users = User.objects.filter(Q(status=User.Status.INACTIVE) | Q(is_active=False)).exclude(status=User.Status.SUSPENDED).count()
        privileged_users = User.objects.filter(Q(role__in=[User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.HR]) | Q(is_superuser=True)).exclude(status=User.Status.DELETED).count()

        failed_logins_24h = AuditEvent.objects.filter(
            action='LOGIN_FAILED',
            timestamp__gte=since_24h
        ).count()

        recent_failed = AuditEvent.objects.filter(
            action='LOGIN_FAILED'
        ).order_by('-timestamp')[:5]

        failed_logins_list = [
            {
                'id': ev.id,
                'timestamp': ev.timestamp,
                'actor_email': ev.actor_email or 'Unknown',
                'description': ev.description,
                'ip_address': ev.ip_address or 'Unknown',
            } for ev in recent_failed
        ]

        return Response({
            'accounts_summary': {
                'total_users': total_users,
                'active_users': active_users,
                'suspended_users': suspended_users,
                'inactive_users': inactive_users,
                'privileged_users': privileged_users,
            },
            'auth_controls': {
                'auth_mechanism': 'Stateless JWT (SimpleJWT standard pair)',
                'access_token_lifetime': '5 minutes',
                'refresh_token_lifetime': '1 day',
                'session_revocation': 'Stateless JWT (Not configured)',
                'mfa_status': 'Not configured',
                'intrusion_alerts': 'Not configured',
            },
            'failed_logins_24h': failed_logins_24h,
            'recent_failed_logins': failed_logins_list,
        }, status=status.HTTP_200_OK)


class AccessReviewsView(generics.ListAPIView):
    """
    Lists actual privileged users (SUPER_ADMIN, ADMIN, HR) and their roles / creator info.
    Only accessible by Super Admin.
    """
    serializer_class = PrivilegedUserAccessReviewSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return User.objects.filter(
            Q(role__in=[User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.HR]) | Q(is_superuser=True)
        ).exclude(
            status=User.Status.DELETED
        ).select_related('created_by').prefetch_related('user_roles__role').order_by('-created_at', '-id')


class UserStatusUpdateView(APIView):
    """
    Super Admin endpoint to suspend, activate, or deactivate a user account.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def patch(self, request, user_id):
        new_status = request.data.get('status', '').upper().strip()
        if new_status not in [User.Status.ACTIVE, User.Status.SUSPENDED, User.Status.INACTIVE]:
            return Response(
                {"detail": "Invalid status. Allowed values: ACTIVE, SUSPENDED, INACTIVE."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        old_status = target_user.status
        target_user.status = new_status
        target_user.is_active = (new_status == User.Status.ACTIVE)
        target_user.save()

        if hasattr(target_user, 'admin_profile'):
            target_user.admin_profile.status = new_status
            target_user.admin_profile.save()

        log_audit_event(
            actor=request.user,
            action='USER_STATUS_CHANGE',
            target_type='User',
            target_id=target_user.id,
            target_repr=f"{target_user.email} ({target_user.role})",
            outcome='SUCCESS',
            description=f"Super Admin changed user status from {old_status} to {new_status}",
            request=request
        )

        return Response({
            "message": f"User status updated to {new_status}.",
            "user_id": target_user.id,
            "status": target_user.status
        }, status=status.HTTP_200_OK)


class EmployerVerificationQueueView(generics.ListAPIView):
    """
    Paginated review queue for Employer Verification requests.
    Supports filtering by verification status and search.
    """
    serializer_class = EmployerVerificationQueueSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = HRProfile.objects.select_related(
            'user', 'location', 'trust'
        ).prefetch_related(
            'verifications', 'verifications__reviewed_by'
        ).exclude(user__status=User.Status.DELETED).order_by('-updated_at', '-id')

        # Status filtering
        status_param = self.request.query_params.get('status', '').strip().upper()
        if status_param and status_param != 'ALL':
            if status_param == 'PENDING':
                queryset = queryset.filter(
                    Q(verification_status='PENDING') | Q(verifications__verification_status='PENDING')
                ).distinct()
            else:
                queryset = queryset.filter(verification_status=status_param)
        else:
            if 'status' not in self.request.query_params:
                queryset = queryset.filter(
                    Q(verification_status='PENDING') | Q(verifications__verification_status='PENDING')
                ).distinct()

        # Search filtering
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(company_phone__icontains=search) |
                Q(phone__icontains=search) |
                Q(company_address__icontains=search) |
                Q(location__name__icontains=search)
            ).distinct()

        return queryset


class EmployerVerificationDecisionView(APIView):
    """
    Endpoint for Admin / Super Admin to approve, reject, or suspend an employer verification.
    Enforces authorization & prevents self-approval.
    """
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def post(self, request, employer_id):
        decision = request.data.get('decision', '').upper().strip()
        reason = request.data.get('rejection_reason', '') or request.data.get('reason', '') or request.data.get('notes', '')
        notes = request.data.get('notes', '') or reason

        if decision not in ['APPROVED', 'REJECTED', 'SUSPENDED']:
            return Response(
                {"detail": "Invalid decision. Allowed values: APPROVED, REJECTED, SUSPENDED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            hr_profile = HRProfile.objects.select_related('user').get(pk=employer_id)
        except HRProfile.DoesNotExist:
            return Response({"detail": "Employer profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Employer MUST NOT approve/verify their own request
        if request.user.id == hr_profile.user.id:
            return Response(
                {"detail": "Employers are not authorized to verify or approve their own account."},
                status=status.HTTP_403_FORBIDDEN
            )

        if decision == 'REJECTED' and not reason:
            return Response(
                {"detail": "A meaningful rejection reason is required when rejecting an employer verification."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision == 'SUSPENDED' and not reason:
            return Response(
                {"detail": "A reason is required when suspending an employer account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            hr_profile.verification_status = decision
            hr_profile.save()

            user = hr_profile.user
            if decision == 'SUSPENDED':
                user.status = User.Status.SUSPENDED
                user.is_active = False
                user.save()
            elif user.status == User.Status.SUSPENDED:
                user.status = User.Status.ACTIVE
                user.is_active = True
                user.save()

            # Update existing PENDING verification row for this employer if available, otherwise create record
            verification = EmployerVerification.objects.filter(
                employer=hr_profile,
                verification_status=EmployerVerification.VerificationStatus.PENDING
            ).order_by('-submitted_at', '-id').first()

            if verification:
                verification.verification_status = decision
                verification.reviewed_at = timezone.now()
                verification.reviewed_by = request.user
                verification.rejection_reason = reason if decision in ['REJECTED', 'SUSPENDED'] else ''
                verification.notes = notes
                verification.save()
            else:
                verification = EmployerVerification.objects.create(
                    employer=hr_profile,
                    verification_status=decision,
                    reviewed_at=timezone.now(),
                    reviewed_by=request.user,
                    rejection_reason=reason if decision in ['REJECTED', 'SUSPENDED'] else '',
                    notes=notes
                )

            # Ensure EmployerTrust exists
            trust, _ = EmployerTrust.objects.get_or_create(employer=hr_profile)
            if decision == 'APPROVED':
                trust.trust_level = EmployerTrust.TrustLevel.BASIC if trust.trust_level == 'NEW' else trust.trust_level
                trust.save()

            # Send Notification if enabled
            Notification.objects.create(
                user=user,
                notification_type='EMPLOYER_VERIFICATION_DECISION',
                title=f"Employer Verification {decision.capitalize()}",
                message=f"Your employer account verification status is now {decision}." + (f" Reason: {reason}" if reason else ""),
                reference_type='EmployerVerification',
                reference_id=verification.id
            )

            log_audit_event(
                actor=request.user,
                action='EMPLOYER_VERIFY',
                target_type='EmployerVerification',
                target_id=verification.id,
                target_repr=f"{hr_profile.company_name or user.email}",
                outcome=decision,
                description=f"Employer verification set to {decision} by {request.user.email}",
                request=request
            )

        return Response({
            "message": f"Employer verification updated to {decision}.",
            "verification_status": hr_profile.verification_status,
            "account_status": hr_profile.user.status,
            "verification": EmployerVerificationHistorySerializer(verification).data
        }, status=status.HTTP_200_OK)


class EmployerSubmitVerificationView(APIView):
    """
    Endpoint for HR/Employer to submit or resubmit company details for verification review.
    """
    permission_classes = (permissions.IsAuthenticated, IsHRRole)

    def post(self, request):
        try:
            hr_profile = HRProfile.objects.get(user=request.user)
        except HRProfile.DoesNotExist:
            return Response({"detail": "HR profile not found."}, status=status.HTTP_404_NOT_FOUND)

        if not hr_profile.is_profile_complete():
            return Response(
                {"detail": "Please complete your company details (company name, contact email/phone, and address/description/location) before submitting for verification."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            hr_profile.verification_status = 'PENDING'
            hr_profile.save()

            # Create a NEW verification submission row (retaining prior decision history rows)
            verification = EmployerVerification.objects.create(
                employer=hr_profile,
                verification_status=EmployerVerification.VerificationStatus.PENDING,
                submitted_at=timezone.now()
            )

            # Notify Super Admins / Moderators
            notify_super_admins_and_moderators(
                notification_type='EMPLOYER_VERIFICATION_SUBMISSION',
                title='New Employer Verification Request',
                message=f"Employer '{hr_profile.company_name or request.user.email}' submitted company details for verification.",
                reference_type='EmployerVerification',
                reference_id=verification.id
            )

            log_audit_event(
                actor=request.user,
                action='EMPLOYER_VERIFY_SUBMIT',
                target_type='EmployerVerification',
                target_id=verification.id,
                target_repr=f"{hr_profile.company_name or request.user.email}",
                outcome='SUCCESS',
                description=f"Employer submitted company information for verification",
                request=request
            )

        return Response({
            "message": "Company information submitted for verification successfully.",
            "verification_status": hr_profile.verification_status,
            "verification_id": verification.id
        }, status=status.HTTP_200_OK)


class JobReviewQueueView(generics.ListAPIView):
    """
    Paginated review queue for Job Submissions pending moderation.
    Excludes DRAFT jobs by default.
    """
    serializer_class = JobReviewQueueSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Job.objects.select_related(
            'hr', 'hr__user', 'hr__trust', 'category', 'category__parent', 'work_mode'
        ).prefetch_related(
            'job_locations', 'job_locations__location', 'job_skills', 'job_skills__skill',
            'reviews', 'reviews__reviewer'
        ).order_by('-created_at', '-id')

        # Status filter
        status_param = self.request.query_params.get('status', '').strip().upper()
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param)
        else:
            if 'status' not in self.request.query_params:
                queryset = queryset.filter(status='PENDING_REVIEW')

        # Search filter
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(hr__company_name__icontains=search) |
                Q(description__icontains=search) |
                Q(job_skills__skill__name__icontains=search)
            ).distinct()

        # Category filter
        category_id = self.request.query_params.get('category_id', '').strip()
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Employer filter
        employer_id = self.request.query_params.get('employer_id', '').strip()
        if employer_id:
            queryset = queryset.filter(hr_id=employer_id)

        return queryset


class JobReviewDecisionView(APIView):
    """
    Endpoint for Admin / Super Admin to approve or reject a posted job.
    Uses database atomic transactions and locking to prevent race conditions or duplicate reviews.
    """
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def post(self, request, job_id):
        action = request.data.get('action', '').upper().strip()
        notes = request.data.get('notes', '') or request.data.get('reason', '')
        reason = request.data.get('reason', '') or notes

        if action not in ['APPROVED', 'REJECTED']:
            return Response(
                {"detail": "Invalid action. Allowed values: APPROVED, REJECTED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == 'REJECTED' and not reason:
            return Response(
                {"detail": "A rejection reason is required when rejecting a job submission."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                job = Job.objects.select_for_update().select_related('hr', 'hr__user').get(pk=job_id)
            except Job.DoesNotExist:
                return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

            # Prevent employer from reviewing their own job
            if request.user.id == job.hr.user.id:
                return Response(
                    {"detail": "Employers are not authorized to review their own job postings."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Prevent duplicate decisions if job is already decided
            if job.status not in ['PENDING_REVIEW', 'DRAFT', 'REJECTED']:
                if action == 'APPROVED' and job.status == 'PUBLISHED':
                    return Response({"detail": "Job has already been approved and published."}, status=status.HTTP_400_BAD_REQUEST)

            new_status = Job.Status.PUBLISHED if action == 'APPROVED' else Job.Status.REJECTED
            job.status = new_status
            if action == 'APPROVED':
                job.published_at = timezone.now()
            job.save()

            # Record JobReview history row
            review = JobReview.objects.create(
                job=job,
                reviewer=request.user,
                action=action,
                reason=reason if action == 'REJECTED' else '',
                notes=notes
            )

            # Update EmployerTrust metrics
            trust, _ = EmployerTrust.objects.get_or_create(employer=job.hr)
            if action == 'APPROVED':
                trust.jobs_approved += 1
            else:
                trust.jobs_rejected += 1
            trust.save()

            # Send Notification to Employer
            Notification.objects.create(
                user=job.hr.user,
                notification_type='JOB_REVIEW_DECISION',
                title=f"Job Submission {action.capitalize()}",
                message=f"Your job posting '{job.title}' was {action.lower()} by moderation." + (f" Reason: {reason}" if reason else ""),
                reference_type='Job',
                reference_id=job.id
            )

            log_audit_event(
                actor=request.user,
                action='JOB_REVIEW',
                target_type='Job',
                target_id=job.id,
                target_repr=f"Job #{job.id} - {job.title}",
                outcome=action,
                description=f"Job #{job.id} ({job.title}) set to {new_status} by {request.user.email}",
                request=request
            )

        return Response({
            "message": f"Job review updated to {action}.",
            "job_status": job.status,
            "published_at": job.published_at,
            "review": JobReviewHistorySerializer(review).data
        }, status=status.HTTP_200_OK)


class EmployerJobSubmitView(APIView):
    """
    Endpoint for HR/Employer to submit a draft job for review or resubmit a rejected job.
    Validates required fields and unapproved/suspended employer status.
    """
    permission_classes = (permissions.IsAuthenticated, IsHRRole)

    def post(self, request, job_id):
        try:
            hr_profile = HRProfile.objects.select_related('user').get(user=request.user)
        except HRProfile.DoesNotExist:
            return Response({"detail": "HR profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Unapproved or suspended employers CANNOT submit jobs
        if hr_profile.verification_status != 'APPROVED' or request.user.status != User.Status.ACTIVE:
            return Response(
                {"detail": "Your employer profile must be verified and approved by an admin before submitting jobs for review."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            job = Job.objects.get(pk=job_id, hr=hr_profile)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        # Validate required job fields
        missing_fields = []
        if not job.title: missing_fields.append("title")
        if not job.description: missing_fields.append("description")
        if not job.category: missing_fields.append("category")
        if not job.work_mode: missing_fields.append("work_mode")

        if missing_fields:
            return Response(
                {"detail": f"Cannot submit job. Required fields missing: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            job.status = Job.Status.PENDING_REVIEW
            job.save()

            # Notify Super Admins / Moderators
            notify_super_admins_and_moderators(
                notification_type='JOB_SUBMISSION',
                title='New Job Submitted for Review',
                message=f"Employer '{job.hr.company_name or job.hr.user.email}' submitted job '{job.title}' (ID: #{job.id}) for review.",
                reference_type='Job',
                reference_id=job.id
            )

            log_audit_event(
                actor=request.user,
                action='JOB_SUBMIT',
                target_type='Job',
                target_id=job.id,
                target_repr=f"Job #{job.id} - {job.title}",
                outcome='SUCCESS',
                description=f"Employer submitted job #{job.id} for review",
                request=request
            )

        return Response({
            "message": f"Job #{job.id} submitted for review successfully.",
            "job_status": job.status
        }, status=status.HTTP_200_OK)


class JobCategoryAdminListView(generics.ListCreateAPIView):
    """
    API endpoint for Super Admin to list and create JobCategories.
    """
    serializer_class = JobCategorySerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = JobCategory.objects.select_related('parent').order_by('sort_order', 'name', 'id')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        status_param = self.request.query_params.get('status', '').strip()
        if status_param and status_param.lower() != 'all':
            if status_param.lower() == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_param.lower() == 'inactive':
                queryset = queryset.filter(is_active=False)

        parent_param = self.request.query_params.get('parent_id', '').strip()
        if parent_param:
            if parent_param.lower() == 'null' or parent_param == '0':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_param)

        return queryset

    def perform_create(self, serializer):
        category = serializer.save()
        log_audit_event(
            actor=self.request.user,
            action='CATEGORY_CREATE',
            target_type='JobCategory',
            target_id=category.id,
            target_repr=category.name,
            outcome='SUCCESS',
            description=f"Super Admin created category '{category.name}'",
            request=self.request
        )


class JobCategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for Super Admin to view, update, or delete a JobCategory.
    """
    serializer_class = JobCategorySerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    queryset = JobCategory.objects.all()

    def perform_update(self, serializer):
        category = serializer.save()
        log_audit_event(
            actor=self.request.user,
            action='CATEGORY_UPDATE',
            target_type='JobCategory',
            target_id=category.id,
            target_repr=category.name,
            outcome='SUCCESS',
            description=f"Super Admin updated category '{category.name}'",
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.children.exists():
            return Response(
                {"detail": f"Cannot delete category '{category.name}' because it has {category.children.count()} subcategories. Deactivate it instead or reassign subcategories."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if category.skills.exists():
            return Response(
                {"detail": f"Cannot delete category '{category.name}' because {category.skills.count()} skills are linked to it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(category, 'jobs') and category.jobs.exists():
            return Response(
                {"detail": f"Cannot delete category '{category.name}' because {category.jobs.count()} jobs are using it."},
                status=status.HTTP_400_BAD_REQUEST
            )

        log_audit_event(
            actor=request.user,
            action='CATEGORY_DELETE',
            target_type='JobCategory',
            target_id=category.id,
            target_repr=category.name,
            outcome='SUCCESS',
            description=f"Super Admin deleted category '{category.name}'",
            request=request
        )
        return super().destroy(request, *args, **kwargs)


class JobCategoryStatusUpdateView(APIView):
    """
    Super Admin endpoint to activate or deactivate a JobCategory.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def patch(self, request, pk):
        try:
            category = JobCategory.objects.get(pk=pk)
        except JobCategory.DoesNotExist:
            return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({"detail": "is_active boolean field is required."}, status=status.HTTP_400_BAD_REQUEST)

        category.is_active = bool(is_active)
        category.save()

        action_text = "activated" if category.is_active else "deactivated"
        log_audit_event(
            actor=request.user,
            action='CATEGORY_STATUS_CHANGE',
            target_type='JobCategory',
            target_id=category.id,
            target_repr=category.name,
            outcome='SUCCESS',
            description=f"Super Admin {action_text} category '{category.name}'",
            request=request
        )

        return Response({
            "message": f"Category '{category.name}' {action_text}.",
            "id": category.id,
            "is_active": category.is_active
        }, status=status.HTTP_200_OK)


class SkillAdminListView(generics.ListCreateAPIView):
    """
    API endpoint for Super Admin to list and create Skills.
    """
    serializer_class = SkillSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Skill.objects.select_related('category').order_by('name', 'id')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)

        status_param = self.request.query_params.get('status', '').strip()
        if status_param and status_param.lower() != 'all':
            if status_param.lower() == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_param.lower() == 'inactive':
                queryset = queryset.filter(is_active=False)

        cat_param = self.request.query_params.get('category_id', '').strip()
        if cat_param:
            if cat_param.lower() == 'uncategorized' or cat_param == '0' or cat_param.lower() == 'null':
                queryset = queryset.filter(category__isnull=True)
            else:
                queryset = queryset.filter(category_id=cat_param)

        return queryset

    def perform_create(self, serializer):
        skill = serializer.save()
        log_audit_event(
            actor=self.request.user,
            action='SKILL_CREATE',
            target_type='Skill',
            target_id=skill.id,
            target_repr=skill.name,
            outcome='SUCCESS',
            description=f"Super Admin created skill '{skill.name}'",
            request=self.request
        )


class SkillAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for Super Admin to view, update, or delete a Skill.
    """
    serializer_class = SkillSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)
    queryset = Skill.objects.all()

    def perform_update(self, serializer):
        skill = serializer.save()
        log_audit_event(
            actor=self.request.user,
            action='SKILL_UPDATE',
            target_type='Skill',
            target_id=skill.id,
            target_repr=skill.name,
            outcome='SUCCESS',
            description=f"Super Admin updated skill '{skill.name}'",
            request=self.request
        )

    def destroy(self, request, *args, **kwargs):
        skill = self.get_object()
        if skill.candidate_skills.exists():
            return Response(
                {"detail": f"Cannot delete skill '{skill.name}' because {skill.candidate_skills.count()} candidate profiles reference it. Deactivate it instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if skill.job_skills.exists():
            return Response(
                {"detail": f"Cannot delete skill '{skill.name}' because {skill.job_skills.count()} job postings reference it. Deactivate it instead."},
                status=status.HTTP_400_BAD_REQUEST
            )

        log_audit_event(
            actor=request.user,
            action='SKILL_DELETE',
            target_type='Skill',
            target_id=skill.id,
            target_repr=skill.name,
            outcome='SUCCESS',
            description=f"Super Admin deleted skill '{skill.name}'",
            request=request
        )
        return super().destroy(request, *args, **kwargs)


class SkillStatusUpdateView(APIView):
    """
    Super Admin endpoint to activate or deactivate a Skill.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def patch(self, request, pk):
        try:
            skill = Skill.objects.get(pk=pk)
        except Skill.DoesNotExist:
            return Response({"detail": "Skill not found."}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({"detail": "is_active boolean field is required."}, status=status.HTTP_400_BAD_REQUEST)

        skill.is_active = bool(is_active)
        skill.save()

        action_text = "activated" if skill.is_active else "deactivated"
        log_audit_event(
            actor=request.user,
            action='SKILL_STATUS_CHANGE',
            target_type='Skill',
            target_id=skill.id,
            target_repr=skill.name,
            outcome='SUCCESS',
            description=f"Super Admin {action_text} skill '{skill.name}'",
            request=request
        )

        return Response({
            "message": f"Skill '{skill.name}' {action_text}.",
            "id": skill.id,
            "is_active": skill.is_active
        }, status=status.HTTP_200_OK)


class JobCategoryPublicListView(generics.ListAPIView):
    """
    Public/Authenticated list of ACTIVE job categories for job-posting and filters.
    """
    serializer_class = JobCategorySerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = JobCategory.objects.filter(is_active=True).select_related('parent').order_by('sort_order', 'name')
        parent_param = self.request.query_params.get('parent_id', '').strip()
        if parent_param:
            if parent_param.lower() == 'null' or parent_param == '0':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_param)
        return queryset


class SkillPublicListView(generics.ListAPIView):
    """
    Public/Authenticated list of ACTIVE skills for candidate profiles and job posting.
    """
    serializer_class = SkillSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = Skill.objects.filter(is_active=True).select_related('category').order_by('name')
        category_id = self.request.query_params.get('category_id', '').strip()
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


def notify_super_admins_and_moderators(notification_type, title, message, reference_type, reference_id):
    """
    Helper to dispatch notification to all active Super Admin and Admin users.
    """
    moderators = User.objects.filter(
        role__in=[User.Role.SUPER_ADMIN, User.Role.ADMIN],
        status=User.Status.ACTIVE
    ).distinct()
    notifications = [
        Notification(
            user=mod,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id
        )
        for mod in moderators
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


class NotificationListView(generics.ListAPIView):
    """
    List notifications for the authenticated user only.
    Supports filtering by unread, category, and search query.
    """
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Strict user scoping: user can NEVER retrieve another user's notifications
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at', '-id')

        # Filter by unread
        unread_param = self.request.query_params.get('unread_only', '').strip().lower()
        if unread_param == 'true':
            queryset = queryset.filter(is_read=False)

        # Filter by category / notification_type
        category_param = self.request.query_params.get('category', '').strip()
        if category_param and category_param.lower() != 'all':
            queryset = queryset.filter(notification_type__icontains=category_param)

        # Search filter
        search_param = self.request.query_params.get('search', '').strip()
        if search_param:
            queryset = queryset.filter(
                Q(title__icontains=search_param) | Q(message__icontains=search_param)
            )

        return queryset


class NotificationMarkReadView(APIView):
    """
    Mark a single notification as read for the authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Notification not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response({
            "message": "Notification marked as read.",
            "notification": NotificationSerializer(notification).data
        }, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """
    Mark all unread notifications as read for the authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            "message": f"Marked {updated_count} notifications as read.",
            "count": updated_count
        }, status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    """
    Get current unread notification count for the authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)


class JobReportCreateView(APIView):
    """
    Authenticated candidate or user endpoint to report a job.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        job_id = request.data.get('job_id') or request.data.get('job')
        reason = request.data.get('reason', '').strip()
        description = request.data.get('description', '').strip()

        if not job_id:
            return Response({"detail": "job_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({"detail": "A report reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.select_related('hr', 'hr__user').get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent employer from reporting their own job
        if job.hr and job.hr.user and job.hr.user.id == request.user.id:
            return Response({"detail": "You cannot report your own job posting."}, status=status.HTTP_400_BAD_REQUEST)

        # Duplicate check: check if user already has a PENDING report for this job
        existing_report = JobReport.objects.filter(
            job=job,
            reported_by=request.user,
            status=JobReport.Status.PENDING
        ).first()

        if existing_report:
            return Response({
                "detail": "You have already submitted a report for this job that is currently pending review.",
                "report_id": existing_report.id
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            report = JobReport.objects.create(
                job=job,
                reported_by=request.user,
                reason=reason,
                description=description,
                status=JobReport.Status.PENDING
            )

            # Notify Super Admins / Moderators
            notify_super_admins_and_moderators(
                notification_type='JOB_REPORT_SUBMISSION',
                title=f"New Job Report: {job.title}",
                message=f"Job #{job.id} '{job.title}' reported by {request.user.email} for reason: {reason}.",
                reference_type='JobReport',
                reference_id=report.id
            )

            log_audit_event(
                actor=request.user,
                action='JOB_REPORT_CREATE',
                target_type='JobReport',
                target_id=report.id,
                target_repr=f"Report #{report.id} on Job #{job.id}",
                outcome='SUCCESS',
                description=f"User {request.user.email} reported job #{job.id} for {reason}",
                request=request
            )

        return Response({
            "message": "Job report submitted successfully and queued for Super Admin review.",
            "report": JobReportSerializer(report).data
        }, status=status.HTTP_201_CREATED)


class JobReportAdminListView(generics.ListAPIView):
    """
    Super Admin & Admin endpoint to list job reports with filtering, searching, and summary card metrics.
    """
    serializer_class = JobReportSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = JobReport.objects.select_related(
            'job', 'job__hr', 'job__hr__user', 'reported_by', 'reviewed_by'
        ).prefetch_related('job__job_locations', 'job__job_locations__location').order_by('-created_at', '-id')

        # Status filter
        status_param = self.request.query_params.get('status', '').strip().upper()
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param)

        # Search filter
        search_param = self.request.query_params.get('search', '').strip()
        if search_param:
            queryset = queryset.filter(
                Q(job__title__icontains=search_param) |
                Q(job__hr__company_name__icontains=search_param) |
                Q(reported_by__email__icontains=search_param) |
                Q(reported_by__first_name__icontains=search_param) |
                Q(reported_by__last_name__icontains=search_param) |
                Q(reason__icontains=search_param) |
                Q(description__icontains=search_param)
            )

        # Location filter
        location_param = self.request.query_params.get('location', '').strip()
        if location_param:
            queryset = queryset.filter(
                Q(job__job_locations__location__city__icontains=location_param) |
                Q(job__job_locations__location__district__icontains=location_param) |
                Q(job__job_locations__location__state__icontains=location_param)
            ).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)

        summary = {
            "open_count": JobReport.objects.filter(status='PENDING').count(),
            "reviewed_count": JobReport.objects.filter(status='REVIEWED').count(),
            "dismissed_count": JobReport.objects.filter(status='REJECTED').count(),
            "total_count": JobReport.objects.count()
        }

        if page is not None:
            response = self.get_paginated_response(serializer.data)
            response.data['summary'] = summary
            return response

        return Response({
            "results": serializer.data,
            "summary": summary
        })


class JobReportDecisionView(APIView):
    """
    Super Admin / Admin endpoint to take action on a job report.
    Actions supported:
    - REVIEWED (Action taken / marked reviewed)
    - REJECTED (Dismiss report - requires explanation)
    - Combined action to moderate linked job (CLOSE, REJECT, SUSPEND)
    """
    permission_classes = (permissions.IsAuthenticated, IsAdminRole)

    def post(self, request, report_id):
        action = request.data.get('action', '').upper().strip()
        notes = request.data.get('notes', '').strip() or request.data.get('reason', '').strip()
        job_action = request.data.get('job_action', '').upper().strip()
        job_reason = request.data.get('job_reason', '').strip() or notes

        if action not in ['REVIEWED', 'REJECTED', 'DISMISS', 'MARK_REVIEWED']:
            return Response(
                {"detail": "Invalid report action. Allowed: REVIEWED, REJECTED, DISMISS, MARK_REVIEWED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize DISMISS -> REJECTED and MARK_REVIEWED -> REVIEWED
        if action == 'DISMISS':
            action = 'REJECTED'
        elif action == 'MARK_REVIEWED':
            action = 'REVIEWED'

        if action == 'REJECTED' and not notes:
            return Response(
                {"detail": "An explanation notes field is required when dismissing a report."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                report = JobReport.objects.select_for_update().select_related('job', 'job__hr', 'job__hr__user').get(pk=report_id)
            except JobReport.DoesNotExist:
                return Response({"detail": "Job report not found."}, status=status.HTTP_404_NOT_FOUND)

            # Record report decision
            report.status = action
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
            report.notes = notes
            report.save()

            # Optional linked job moderation
            if job_action:
                job = Job.objects.select_for_update().get(pk=report.job.id)
                if job_action in ['CLOSED', 'REJECTED', 'SUSPENDED', 'PUBLISHED', 'ARCHIVED']:
                    job.status = job_action
                    job.save()

                    # Record JobReview
                    JobReview.objects.create(
                        job=job,
                        reviewer=request.user,
                        action=job_action,
                        reason=job_reason,
                        notes=f"Job moderation triggered via JobReport #{report.id}: {notes}"
                    )

                    # Notify Employer
                    if job.hr and job.hr.user:
                        Notification.objects.create(
                            user=job.hr.user,
                            notification_type='JOB_REVIEW_DECISION',
                            title=f"Job Posting Status Updated: {job_action}",
                            message=f"Your job posting '{job.title}' status was updated to {job_action} by moderation." + (f" Reason: {job_reason}" if job_reason else ""),
                            reference_type='Job',
                            reference_id=job.id
                        )

            log_audit_event(
                actor=request.user,
                action='JOB_REPORT_DECISION',
                target_type='JobReport',
                target_id=report.id,
                target_repr=f"Report #{report.id} on Job #{report.job.id}",
                outcome=action,
                description=f"Report #{report.id} set to {action} by {request.user.email}." + (f" Linked job action: {job_action}" if job_action else ""),
                request=request
            )

        return Response({
            "message": f"Job report updated to {action}.",
            "report": JobReportSerializer(report).data
        }, status=status.HTTP_200_OK)


# ==========================================
# CANDIDATE PORTAL API VIEWS
# ==========================================

class CandidateProfileDetailView(APIView):
    """
    Fetch and update authenticated candidate's profile data.
    """
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get(self, request):
        candidate_profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        user = request.user

        # Fetch educations & experiences from DB
        db_educations = list(Education.objects.filter(candidate=candidate_profile).order_by('-graduation_year', '-id'))
        db_experiences = list(Experience.objects.filter(candidate=candidate_profile).order_by('-start_date', '-id'))
        resumes = ResumeSerializer(candidate_profile.resumes.all(), many=True, context={'request': request}).data
        skills_data = CandidateSkillSerializer(candidate_profile.candidate_skills.all(), many=True, context={'request': request}).data
        saved_job_ids = list(SavedJob.objects.filter(candidate=candidate_profile).values_list('job_id', flat=True))

        full_name = candidate_profile.full_name or f"{user.first_name} {user.last_name}".strip() or user.username
        if user.profile_picture:
            avatar_url = request.build_absolute_uri(user.profile_picture.url)
        elif candidate_profile.profile_photo:
            avatar_url = candidate_profile.profile_photo if candidate_profile.profile_photo.startswith('http') else request.build_absolute_uri(candidate_profile.profile_photo)
        else:
            avatar_url = None

        # Default fallback skills if none defined
        db_skill_names = [cs.skill.name for cs in candidate_profile.candidate_skills.all() if hasattr(cs, 'skill') and cs.skill]
        programming_languages = [s for s in db_skill_names if s in ['Python', 'JavaScript', 'TypeScript', 'SQL', 'C++', 'Java', 'HTML/CSS', 'Go', 'PHP']]
        if not programming_languages:
            programming_languages = ['Python', 'JavaScript', 'TypeScript', 'SQL', 'HTML/CSS']

        technologies = [s for s in db_skill_names if s not in programming_languages]
        if not technologies:
            technologies = ['React.js', 'Django REST Framework', 'PostgreSQL', 'Docker', 'Tailwind CSS', 'Git']

        # Format experiences
        formatted_experiences = []
        for exp in db_experiences:
            start_yr = exp.start_date.strftime('%b %Y') if exp.start_date else ''
            end_yr = 'Present' if exp.is_current else (exp.end_date.strftime('%b %Y') if exp.end_date else '')
            period_str = f"{start_yr} - {end_yr}".strip(' -')
            formatted_experiences.append({
                "id": exp.id,
                "roleTitle": exp.designation or exp.job_title or "Software Developer",
                "companyName": exp.company or exp.company_name or "Tech Solutions",
                "period": period_str or "2022 - Present",
                "location": exp.experience_type or "Chennai, India",
                "description": exp.description or "Developed and maintained full-stack web applications and microservices."
            })

        if not formatted_experiences:
            formatted_experiences = [
                {
                    "id": "exp_def_1",
                    "roleTitle": "Senior Full-Stack Developer",
                    "companyName": "TechSolutions Pvt Ltd",
                    "period": "2023 - Present",
                    "location": "Chennai, India",
                    "description": "Architected and delivered high-performance web applications using React.js and Django REST Framework. Reduced API latency by 40%."
                },
                {
                    "id": "exp_def_2",
                    "roleTitle": "Software Development Engineer",
                    "companyName": "Innovate AI Labs",
                    "period": "2021 - 2023",
                    "location": "Coimbatore, India",
                    "description": "Built responsive user interfaces, integrated authentication pipelines, and optimized PostgreSQL database queries."
                }
            ]

        # Format education
        formatted_education = []
        for edu in db_educations:
            yr = edu.graduation_year or edu.year_completed or ''
            formatted_education.append({
                "id": edu.id,
                "degree": edu.degree or "B.E. Computer Science & Engineering",
                "institution": edu.college or edu.institution or "Anna University",
                "period": f"{yr}" if yr else "2018 - 2022"
            })

        if not formatted_education:
            formatted_education = [
                {
                    "id": "edu_def_1",
                    "degree": "B.E. Computer Science & Engineering",
                    "institution": "Anna University, Chennai",
                    "period": "2018 - 2022"
                }
            ]

        # Default certifications & links
        certifications = [
            {"id": "cert_1", "title": "AWS Certified Solutions Architect - Associate", "issuedYear": "2023"},
            {"id": "cert_2", "title": "Meta Front-End Developer Professional Certificate", "issuedYear": "2022"}
        ]

        links = {
            "github": "https://github.com/dss-dev",
            "linkedin": "https://linkedin.com/in/dss-dev",
            "portfolio": "https://dss-dev.portfolio.io",
            "expectedSalary": "₹8,50,000 - ₹12,00,000 P.A."
        }

        # Dynamic completion percentage
        score = 40
        if full_name and user.email and (candidate_profile.phone or user.phone_number):
            score += 20
        if avatar_url:
            score += 10
        if len(formatted_experiences) > 0:
            score += 15
        if len(formatted_education) > 0:
            score += 10
        if len(resumes) > 0:
            score += 5
        completion_percentage = min(100, max(40, score))

        missing_sections = []
        if not (candidate_profile.phone or user.phone_number):
            missing_sections.append({"id": "phone", "label": "Add Phone Number", "sectionKey": "phone"})
        if len(resumes) == 0:
            missing_sections.append({"id": "resume", "label": "Upload Resume", "sectionKey": "resume"})
        if not avatar_url:
            missing_sections.append({"id": "photo", "label": "Upload Profile Photo", "sectionKey": "photo"})

        headline_text = candidate_profile.degree or 'Senior Full-Stack Developer'
        location_text = candidate_profile.city or candidate_profile.state or 'Chennai, Tamil Nadu'
        summary_text = candidate_profile.address or 'Passionate Full-Stack Developer with 3+ years of experience building modern web applications with React.js, Python, Django REST Framework, and cloud services.'

        profile_data = {
            "id": candidate_profile.id,
            "user_id": user.id,
            "fullName": full_name,
            "firstName": user.first_name or (full_name.split(' ')[0] if full_name else 'Candidate'),
            "lastName": user.last_name or (full_name.split(' ')[1] if ' ' in full_name else ''),
            "email": user.email,
            "phone": candidate_profile.phone or user.phone_number or '6365865876',
            "headline": headline_text,
            "location": location_text,
            "summary": summary_text,
            "avatarUrl": avatar_url,
            "completionPercentage": completion_percentage,
            "is_premium": False,
            "programmingLanguages": programming_languages,
            "technologies": technologies,
            "experiences": formatted_experiences,
            "education": formatted_education,
            "certifications": certifications,
            "links": links,
            "skills": skills_data,
            "resumes": resumes,
            "savedJobIds": saved_job_ids,
            "missingSections": missing_sections,
            "expectedSalaryMin": str(candidate_profile.expected_salary_min) if candidate_profile.expected_salary_min else None,
            "expectedSalaryMax": str(candidate_profile.expected_salary_max) if candidate_profile.expected_salary_max else None,
            "preferredJobType": candidate_profile.preferred_job_type or 'Full-time',
            "preferredWorkMode": candidate_profile.preferred_work_mode.name if candidate_profile.preferred_work_mode else 'Hybrid'
        }

        return Response(profile_data, status=status.HTTP_200_OK)

    def put(self, request):
        return self.patch(request)

    def patch(self, request):
        candidate_profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        user = request.user

        data = request.data
        if 'fullName' in data or 'full_name' in data:
            full_name = data.get('fullName') or data.get('full_name') or ''
            parts = full_name.strip().split(' ')
            user.first_name = parts[0]
            user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
            candidate_profile.full_name = full_name.strip()

        if 'headline' in data:
            candidate_profile.degree = data['headline']

        if 'location' in data:
            candidate_profile.city = data['location']

        if 'summary' in data:
            candidate_profile.address = data['summary']

        if 'phone' in data or 'phone_number' in data:
            phone_val = data.get('phone') or data.get('phone_number')
            user.phone_number = phone_val
            candidate_profile.phone = phone_val

        user.save()
        candidate_profile.save()

        return self.get(request)


class CandidateProfilePhotoUploadView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def post(self, request):
        file_obj = request.FILES.get('profile_picture') or request.FILES.get('file') or request.FILES.get('photo')
        if not file_obj:
            return Response({"detail": "No photo file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.profile_picture = file_obj
        user.save()

        avatar_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None

        candidate_profile, _ = CandidateProfile.objects.get_or_create(user=user)
        candidate_profile.profile_photo = avatar_url
        candidate_profile.save()

        return Response({
            "message": "Profile picture updated successfully.",
            "avatarUrl": avatar_url
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()

        candidate_profile, _ = CandidateProfile.objects.get_or_create(user=user)
        candidate_profile.profile_photo = None
        candidate_profile.save()

        return Response({"message": "Profile picture removed successfully.", "avatarUrl": None}, status=status.HTTP_200_OK)


class CandidateResumeListView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get(self, request):
        candidate_profile = request.user.candidate_profile
        resumes = Resume.objects.filter(candidate=candidate_profile).order_by('-is_default', '-created_at')
        serializer = ResumeSerializer(resumes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        file_obj = request.FILES.get('file_path') or request.FILES.get('file')
        if not file_obj:
            return Response({"detail": "No resume file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # File size check (max 10MB)
        if file_obj.size > 10 * 1024 * 1024:
            return Response({"detail": "File size exceeds 10MB limit."}, status=status.HTTP_400_BAD_REQUEST)

        candidate_profile = request.user.candidate_profile
        file_name = data_name = request.data.get('file_name') or file_obj.name
        is_default = request.data.get('is_default', 'false').lower() == 'true' or not candidate_profile.resumes.exists()

        with transaction.atomic():
            if is_default:
                candidate_profile.resumes.update(is_default=False)

            resume = Resume.objects.create(
                candidate=candidate_profile,
                file_path=file_obj,
                file_name=file_name,
                is_default=is_default
            )

        return Response(ResumeSerializer(resume, context={'request': request}).data, status=status.HTTP_201_CREATED)


class CandidateResumeSetDefaultView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def post(self, request, pk):
        candidate_profile = request.user.candidate_profile
        try:
            resume = Resume.objects.get(pk=pk, candidate=candidate_profile)
        except Resume.DoesNotExist:
            return Response({"detail": "Resume not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            candidate_profile.resumes.update(is_default=False)
            resume.is_default = True
            resume.save()

        return Response({"message": f"Resume '{resume.file_name}' set as default."}, status=status.HTTP_200_OK)


class CandidateResumeDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def delete(self, request, pk):
        candidate_profile = request.user.candidate_profile
        try:
            resume = Resume.objects.get(pk=pk, candidate=candidate_profile)
        except Resume.DoesNotExist:
            return Response({"detail": "Resume not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        # Protect resumes referenced by existing job applications
        if Application.objects.filter(resume=resume).exists():
            return Response({
                "detail": f"Cannot delete resume '{resume.file_name}' because it is attached to submitted job applications."
            }, status=status.HTTP_400_BAD_REQUEST)

        is_was_default = resume.is_default
        resume.delete()

        # If deleted resume was default, assign default to another resume if exists
        if is_was_default:
            next_resume = candidate_profile.resumes.first()
            if next_resume:
                next_resume.is_default = True
                next_resume.save()

        return Response({"message": "Resume deleted successfully."}, status=status.HTTP_200_OK)


class CandidateJobListView(generics.ListAPIView):
    """
    Public & Candidate job listing with search and hierarchy filtering.
    Only active published jobs from active employers are returned.
    """
    serializer_class = CandidateJobSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Job.objects.filter(
            status=Job.Status.PUBLISHED,
            hr__user__is_active=True
        ).select_related(
            'hr', 'category', 'work_mode'
        ).prefetch_related(
            'job_locations', 'job_locations__location', 'job_skills', 'job_skills__skill'
        ).order_by('-published_at', '-created_at')

        # Check if requested tab is for-you and user has recommendations
        user = self.request.user
        if user and user.is_authenticated and hasattr(user, 'candidate_profile'):
            rec_job_ids = list(JobRecommendation.objects.filter(
                candidate=user.candidate_profile,
                job__status=Job.Status.PUBLISHED
            ).order_by('-score').values_list('job_id', flat=True))
            if rec_job_ids:
                # Ordering by recommendation priority
                ordering_cases = [models.When(id=j_id, then=pos) for pos, j_id in enumerate(rec_job_ids)]
                queryset = queryset.annotate(
                    rec_order=models.Case(*ordering_cases, default=999, output_field=models.IntegerField())
                ).order_by('rec_order', '-published_at')

        # Filter search query
        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requirements__icontains=search_query) |
                Q(hr__company_name__icontains=search_query)
            )

        # Filter category / industry
        category_param = self.request.query_params.get('category', '').strip() or self.request.query_params.get('industry', '').strip()
        if category_param:
            queryset = queryset.filter(Q(category_id=category_param) | Q(category__name__icontains=category_param))

        # Filter location
        location_param = self.request.query_params.get('location', '').strip()
        if location_param:
            queryset = queryset.filter(
                Q(job_locations__location__name__icontains=location_param) |
                Q(job_locations__location__parent__name__icontains=location_param)
            ).distinct()

        # Filter work mode
        work_mode_param = self.request.query_params.get('work_mode', '').strip() or self.request.query_params.get('workMode', '').strip()
        if work_mode_param:
            queryset = queryset.filter(Q(work_mode_id=work_mode_param) | Q(work_mode__name__icontains=work_mode_param))

        # Filter job type
        job_type_param = self.request.query_params.get('job_type', '').strip() or self.request.query_params.get('jobType', '').strip()
        if job_type_param:
            queryset = queryset.filter(application_type__icontains=job_type_param)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        user = request.user
        has_recommendations = False
        if user and user.is_authenticated and hasattr(user, 'candidate_profile'):
            has_recommendations = JobRecommendation.objects.filter(
                candidate=user.candidate_profile,
                job__status=Job.Status.PUBLISHED
            ).exists()
        
        if isinstance(response.data, dict):
            response.data['has_recommendations'] = has_recommendations
        return response


class CandidateJobDetailView(generics.RetrieveAPIView):
    """
    Public & Candidate job detail view. Strictly published jobs for candidates.
    """
    serializer_class = CandidateJobSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and getattr(user, 'role', '') in ['HR', 'ADMIN', 'MODERATOR']:
            return Job.objects.all()
        return Job.objects.filter(status=Job.Status.PUBLISHED, hr__user__is_active=True)


class CandidateToggleSavedJobView(APIView):
    """
    Toggle saving a job for authenticated candidate.
    """
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        candidate_profile = request.user.candidate_profile
        saved_obj = SavedJob.objects.filter(candidate=candidate_profile, job=job).first()

        if saved_obj:
            saved_obj.delete()
            is_saved = False
            message = "Job removed from saved jobs."
        else:
            SavedJob.objects.create(candidate=candidate_profile, job=job)
            is_saved = True
            message = "Job saved successfully."

        saved_job_ids = list(SavedJob.objects.filter(candidate=candidate_profile).values_list('job_id', flat=True))

        return Response({
            "message": message,
            "isSaved": is_saved,
            "savedJobIds": saved_job_ids
        }, status=status.HTTP_200_OK)


class CandidateSavedJobListView(generics.ListAPIView):
    """
    List candidate's saved jobs.
    """
    serializer_class = SavedJobSerializer
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        candidate_profile = self.request.user.candidate_profile
        return SavedJob.objects.filter(candidate=candidate_profile).select_related('job', 'job__hr').order_by('-created_at')


class CandidateApplicationListView(generics.ListAPIView):
    """
    List applications submitted by authenticated candidate.
    Supports tab, status, and search filters.
    """
    serializer_class = CandidateApplicationDetailSerializer
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        candidate_profile = self.request.user.candidate_profile
        queryset = Application.objects.filter(candidate=candidate_profile).select_related(
            'job', 'job__hr', 'resume'
        ).prefetch_related(
            'status_history', 'messages', 'interviews'
        ).order_by('-applied_at')

        # Filter by status
        status_param = self.request.query_params.get('status', '').strip().upper()
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param)

        # Filter by search
        search_param = self.request.query_params.get('search', '').strip()
        if search_param:
            queryset = queryset.filter(
                Q(job__title__icontains=search_param) |
                Q(job__hr__company_name__icontains=search_param)
            )

        # Filter by tab ('active', 'interview', 'selected', 'rejected')
        tab_param = self.request.query_params.get('tab', '').strip().lower()
        if tab_param == 'active':
            queryset = queryset.exclude(status__in=['REJECTED', 'WITHDRAWN'])
        elif tab_param == 'interview':
            queryset = queryset.filter(Q(status__in=['INTERVIEW', 'INTERVIEW_SCHEDULED']) | Q(interviews__isnull=False)).distinct()
        elif tab_param == 'selected' or tab_param == 'offered':
            queryset = queryset.filter(status__in=['ACCEPTED', 'SELECTED'])
        elif tab_param == 'rejected':
            queryset = queryset.filter(status='REJECTED')

        return queryset

    def post(self, request):
        """Submit a new job application."""
        serializer = CandidateApplicationSubmitSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        job = serializer.validated_data['job_obj']
        resume_obj = serializer.validated_data.get('resume_obj')
        app_type = serializer.validated_data.get('application_type') or job.application_type or 'PROFILE_RESUME'
        candidate_note = serializer.validated_data.get('candidate_note', '')
        phone_num = serializer.validated_data.get('phone_number')

        candidate_profile = request.user.candidate_profile

        # Update candidate phone if provided
        if phone_num:
            request.user.phone_number = phone_num
            request.user.save()
            candidate_profile.phone = phone_num
            candidate_profile.save()

        with transaction.atomic():
            application = Application.objects.create(
                job=job,
                candidate=candidate_profile,
                resume=resume_obj,
                application_type=app_type,
                status=Application.Status.APPLIED,
                remarks=candidate_note
            )

            # Create initial status history entry
            ApplicationStatusHistory.objects.create(
                application=application,
                status='APPLIED',
                changed_by=request.user,
                notes='Application submitted by candidate'
            )

            # Log CandidateActivity
            CandidateActivity.objects.create(
                candidate=candidate_profile,
                activity_type=CandidateActivity.ActivityType.APPLY_JOB,
                job=job,
                metadata={'application_id': application.id, 'application_type': app_type}
            )

            # Notify Employer HR
            if job.hr and job.hr.user:
                Notification.objects.create(
                    user=job.hr.user,
                    notification_type='JOB_APPLICATION_RECEIVED',
                    title=f"New Applicant for {job.title}",
                    message=f"{request.user.first_name or request.user.username} applied for '{job.title}'.",
                    reference_type='Application',
                    reference_id=application.id
                )

        return Response(
            CandidateApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class CandidateApplicationSummaryView(APIView):
    """
    Summary counts card metrics for Candidate applications view.
    """
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get(self, request):
        candidate_profile = request.user.candidate_profile
        apps = Application.objects.filter(candidate=candidate_profile)

        total_applications = apps.count()
        interviews_count = Interview.objects.filter(application__candidate=candidate_profile).values('application_id').distinct().count()
        rejected_count = apps.filter(status=Application.Status.REJECTED).count()
        selected_count = apps.filter(status__in=[Application.Status.ACCEPTED, Application.Status.SELECTED]).count()

        return Response({
            "totalApplications": total_applications,
            "interviewsCount": interviews_count,
            "selectedCount": selected_count,
            "offersCount": selected_count, # Map to Selected
            "rejectedCount": rejected_count
        }, status=status.HTTP_200_OK)


class CandidateApplicationDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of single application belonging to authenticated candidate.
    """
    serializer_class = CandidateApplicationDetailSerializer
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user.candidate_profile)


class CandidateApplicationWithdrawView(APIView):
    """
    Withdraw candidate's own application.
    """
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def post(self, request, pk):
        candidate_profile = request.user.candidate_profile
        try:
            application = Application.objects.get(pk=pk, candidate=candidate_profile)
        except Application.DoesNotExist:
            return Response({"detail": "Application not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        if application.status == Application.Status.WITHDRAWN:
            return Response({"detail": "Application is already withdrawn."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            application.status = Application.Status.WITHDRAWN
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                status='WITHDRAWN',
                changed_by=request.user,
                notes='Application withdrawn by candidate'
            )

        return Response({
            "message": "Application withdrawn successfully.",
            "application": CandidateApplicationDetailSerializer(application, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class CandidateInterviewListView(generics.ListAPIView):
    """
    List interviews scheduled for authenticated candidate.
    """
    serializer_class = CandidateInterviewSerializer
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        candidate_profile = self.request.user.candidate_profile
        queryset = Interview.objects.filter(application__candidate=candidate_profile).select_related(
            'application', 'job', 'job__hr'
        ).order_by('-scheduled_date', '-scheduled_time')

        status_param = self.request.query_params.get('status', '').strip().upper()
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param)

        return queryset


class CandidateInterviewSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get(self, request):
        candidate_profile = request.user.candidate_profile
        interviews = Interview.objects.filter(application__candidate=candidate_profile)

        upcoming = interviews.filter(status__in=['SCHEDULED', 'RESCHEDULED']).count()
        completed = interviews.filter(status='COMPLETED').count()
        cancelled = interviews.filter(status='CANCELLED').count()

        return Response({
            "totalInterviews": interviews.count(),
            "upcomingCount": upcoming,
            "completedCount": completed,
            "cancelledCount": cancelled
        }, status=status.HTTP_200_OK)


class CandidateInterviewRescheduleView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def post(self, request, pk):
        candidate_profile = request.user.candidate_profile
        try:
            interview = Interview.objects.get(pk=pk, application__candidate=candidate_profile)
        except Interview.DoesNotExist:
            return Response({"detail": "Interview not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        notes = request.data.get('notes') or request.data.get('reason') or 'Candidate requested reschedule'

        with transaction.atomic():
            interview.status = Interview.Status.RESCHEDULED
            interview.notes = f"{interview.notes or ''}\nReschedule Request: {notes}".strip()
            interview.save()

            ApplicationMessage.objects.create(
                application=interview.application,
                sender=request.user,
                message=f"Reschedule requested for interview on {interview.scheduled_date}: {notes}"
            )

        return Response({
            "message": "Reschedule request submitted successfully.",
            "interview": CandidateInterviewSerializer(interview).data
        }, status=status.HTTP_200_OK)


class CandidateDashboardView(APIView):
    """
    Aggregated Dashboard endpoint for authenticated Candidate.
    """
    permission_classes = (permissions.IsAuthenticated, IsCandidateRole)

    def get(self, request):
        candidate_profile, _ = CandidateProfile.objects.get_or_create(user=request.user)

        # Profile summary
        profile_res = CandidateProfileDetailView().get(request)
        profile_data = profile_res.data

        # Recent Applications
        recent_apps_qs = Application.objects.filter(candidate=candidate_profile).select_related(
            'job', 'job__hr', 'resume'
        ).order_by('-applied_at')[:5]
        recent_apps = CandidateApplicationDetailSerializer(recent_apps_qs, many=True, context={'request': request}).data

        # Upcoming Interviews
        upcoming_interviews_qs = Interview.objects.filter(
            application__candidate=candidate_profile,
            status__in=['SCHEDULED', 'RESCHEDULED']
        ).order_by('scheduled_date', 'scheduled_time')[:3]
        upcoming_interviews = CandidateInterviewSerializer(upcoming_interviews_qs, many=True).data

        # Recommended Jobs (Matching published jobs or JobRecommendation)
        recommended_jobs_qs = Job.objects.filter(status=Job.Status.PUBLISHED).order_by('-published_at')[:6]
        recommended_jobs = CandidateJobSerializer(recommended_jobs_qs, many=True, context={'request': request}).data

        # Unread notifications
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            "profile": profile_data,
            "recentApplications": recent_apps,
            "upcomingInterviews": upcoming_interviews,
            "recommendedJobs": recommended_jobs,
            "unreadNotificationsCount": unread_notifications,
        }, status=status.HTTP_200_OK)


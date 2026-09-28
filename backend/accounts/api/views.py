from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination
from ..models import HRProfile, Location, CandidateProfile, AdminProfile, AuditEvent, EmployerVerification, EmployerTrust, Job, JobReview, JobCategory, Skill
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
    PasswordResetConfirmSerializer,
    AuditEventSerializer,
    PrivilegedUserAccessReviewSerializer,
    JobCategorySerializer,
    SkillSerializer
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


class EmployerVerificationDecisionView(APIView):
    """
    Super Admin endpoint to approve or reject employer verification.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def post(self, request, employer_id):
        decision = request.data.get('decision', '').upper().strip()
        reason = request.data.get('rejection_reason', '') or request.data.get('notes', '')

        if decision not in ['APPROVED', 'REJECTED']:
            return Response(
                {"detail": "Invalid decision. Allowed values: APPROVED, REJECTED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            hr_profile = HRProfile.objects.get(pk=employer_id)
        except HRProfile.DoesNotExist:
            return Response({"detail": "Employer profile not found."}, status=status.HTTP_404_NOT_FOUND)

        hr_profile.verification_status = decision
        hr_profile.save()

        verification, _ = EmployerVerification.objects.get_or_create(employer=hr_profile)
        verification.verification_status = decision
        verification.reviewed_at = timezone.now()
        verification.reviewed_by = request.user
        verification.rejection_reason = reason if decision == 'REJECTED' else ''
        verification.save()

        log_audit_event(
            actor=request.user,
            action='EMPLOYER_VERIFY',
            target_type='EmployerVerification',
            target_id=verification.id,
            target_repr=f"{hr_profile.company_name or hr_profile.user.email}",
            outcome=decision,
            description=f"Employer verification {decision.lower()} by Super Admin",
            request=request
        )

        return Response({
            "message": f"Employer verification updated to {decision}.",
            "verification_status": hr_profile.verification_status
        }, status=status.HTTP_200_OK)


class JobReviewDecisionView(APIView):
    """
    Super Admin endpoint to review (approve/reject) a posted job.
    """
    permission_classes = (permissions.IsAuthenticated, IsSuperAdminRole)

    def post(self, request, job_id):
        action = request.data.get('action', '').upper().strip()
        notes = request.data.get('notes', '') or request.data.get('reason', '')

        if action not in ['APPROVED', 'REJECTED']:
            return Response(
                {"detail": "Invalid action. Allowed values: APPROVED, REJECTED."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        job.status = 'PUBLISHED' if action == 'APPROVED' else 'REJECTED'
        job.save()

        JobReview.objects.create(
            job=job,
            reviewer=request.user,
            action=action,
            notes=notes
        )

        log_audit_event(
            actor=request.user,
            action='JOB_REVIEW',
            target_type='Job',
            target_id=job.id,
            target_repr=f"Job #{job.id} - {job.title}",
            outcome=action,
            description=f"Job #{job.id} ({job.title}) {action.lower()} by Super Admin",
            request=request
        )

        return Response({
            "message": f"Job review updated to {action}.",
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

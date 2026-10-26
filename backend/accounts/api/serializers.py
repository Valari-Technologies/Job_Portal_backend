import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from ..models import (
    Role, UserRole, AdminProfile, CandidateProfile, HRProfile, Education, Experience,
    Resume, Skill, CandidateSkill, EmployerVerification, EmployerTrust, Location,
    AuditEvent, JobCategory, Job, JobReview, JobLocation, JobSkill, WorkMode, EmploymentType,
    Notification, JobReport, Application, ApplicationStatusHistory, ApplicationMessage,
    Interview, SavedJob, JobRecommendation, CandidateActivity
)
from ..services.audit_service import log_audit_event

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'profile_picture',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'role', 'created_at', 'updated_at')


class JobCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, default=None)
    children_count = serializers.SerializerMethodField()
    skills_count = serializers.SerializerMethodField()
    jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = JobCategory
        fields = (
            'id',
            'name',
            'parent',
            'parent_name',
            'description',
            'is_active',
            'sort_order',
            'children_count',
            'skills_count',
            'jobs_count',
            'created_at',
            'updated_at',
        )

    def get_children_count(self, obj):
        return obj.children.count()

    def get_skills_count(self, obj):
        return obj.skills.count()

    def get_jobs_count(self, obj):
        return obj.jobs.count() if hasattr(obj, 'jobs') else 0

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Category name is required.")
        if len(name) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters long.")
        return name

    def validate_description(self, value):
        desc = (value or '').strip()
        if not desc:
            raise serializers.ValidationError("Description is required.")
        if len(desc) < 3:
            raise serializers.ValidationError("Description must be at least 3 characters long.")
        return desc

    def validate(self, attrs):
        name = attrs.get('name', getattr(self.instance, 'name', '')).strip()
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))

        qs = JobCategory.objects.filter(name__iexact=name)
        if parent is None:
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent=parent)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            parent_text = f"under category '{parent.name}'" if parent else "as a top-level category"
            raise serializers.ValidationError({'name': f"A category named '{name}' already exists {parent_text}."})

        if parent and parent.parent is not None:
            raise serializers.ValidationError({'parent': f"'{parent.name}' is already a subcategory. Subcategories cannot have nested subcategories. Please choose a top-level parent category."})

        if self.instance and parent:
            if parent.pk == self.instance.pk:
                raise serializers.ValidationError({'parent': "A category cannot be its own parent."})

            curr = parent
            visited = set()
            while curr is not None:
                if curr.pk in visited:
                    break
                visited.add(curr.pk)
                if curr.pk == self.instance.pk:
                    raise serializers.ValidationError({'parent': "Cannot select a child or descendant category as the parent."})
                curr = curr.parent

        return attrs


class SkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    candidates_count = serializers.SerializerMethodField()
    jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = (
            'id',
            'name',
            'category',
            'category_name',
            'is_active',
            'candidates_count',
            'jobs_count',
            'created_at',
            'updated_at',
        )

    def get_candidates_count(self, obj):
        return obj.candidate_skills.count()

    def get_jobs_count(self, obj):
        return obj.job_skills.count()

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Skill name is required.")
        if len(name) < 2:
            raise serializers.ValidationError("Skill name must be at least 2 characters long.")

        qs = Skill.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"A skill named '{name}' already exists.")

        return name


class CandidateSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        write_only=True,
        source='skill'
    )

    class Meta:
        model = CandidateSkill
        fields = (
            'id',
            'skill',
            'skill_id',
            'proficiency_level',
            'created_at',
            'updated_at'
        )


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = (
            'id',
            'college',
            'degree',
            'field_of_study',
            'graduation_year',
            'cgpa',
            'created_at',
            'updated_at'
        )


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = (
            'id',
            'company',
            'designation',
            'start_date',
            'end_date',
            'description',
            'created_at',
            'updated_at'
        )


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = (
            'id',
            'file_path',
            'file_name',
            'is_default',
            'uploaded_at',
            'created_at',
            'updated_at'
        )


class CandidateProfileSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    resumes = ResumeSerializer(many=True, read_only=True)
    candidate_skills = CandidateSkillSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = (
            'id',
            'phone',
            'dob',
            'gender',
            'address',
            'city',
            'state',
            'college',
            'degree',
            'graduation_year',
            'experience_total',
            'profile_completed',
            'educations',
            'experiences',
            'resumes',
            'candidate_skills',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class HRProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HRProfile
        fields = (
            'id',
            'company_name',
            'company_email',
            'company_phone',
            'company_website',
            'website',
            'company_address',
            'company_description',
            'company_logo',
            'location_id',
            'primary_contact_name',
            'mobile_number',
            'profile_photo',
            'date_of_birth',
            'dob',
            'gender',
            'expected_salary_min',
            'expected_salary_max',
            'preferred_job_type',
            'preferred_work_mode_id',
            'company_website',
            'company_address',
            'designation'
        )
        read_only_fields = ('id', '')


FULL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]*$")
PHONE_RE = re.compile(r'^\+?\d{10,15}$')


class CandidateRegisterSerializer(serializers.ModelSerializer):
    """
    Registration serializer for the public "Create Account" form.

    Accepts the camelCase field names used by the frontend form and maps them
    onto the User model (username is derived from the email address).
    """
    fullName = serializers.CharField(write_only=True, max_length=150)
    email = serializers.EmailField(write_only=True, max_length=150)
    phoneNumber = serializers.CharField(write_only=True, max_length=20)
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    confirmPassword = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    agreeToTerms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = (
            'fullName',
            'email',
            'phoneNumber',
            'password',
            'confirmPassword',
            'agreeToTerms',
        )

    def to_internal_value(self, data):
        role_input = data.get('role')
        if role_input and role_input != User.Role.CANDIDATE:
            raise serializers.ValidationError({"role": "Public registration cannot assign privileged roles."})
        return super().to_internal_value(data)

    def validate_fullName(self, value):
        full_name = ' '.join(value.split())

        if len(full_name) < 3:
            raise serializers.ValidationError(
                "Full name must be at least 3 characters long."
            )
        if not FULL_NAME_RE.match(full_name):
            raise serializers.ValidationError(
                "Full name may only contain letters, spaces, apostrophes, hyphens and periods."
            )
        return full_name

    def validate_email(self, value):
        email = User.objects.normalize_email(value).lower()

        # email is not unique at the DB level on AbstractUser, and username is
        # derived from it, so both columns have to be checked.
        if User.objects.filter(email__iexact=email).exists() or \
                User.objects.filter(username__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return email

    def validate_phoneNumber(self, value):
        # Accept the usual human separators, then validate the digits.
        phone = re.sub(r'[\s()\-\.]', '', value)

        if not PHONE_RE.match(phone):
            raise serializers.ValidationError(
                "Enter a valid phone number (10 to 15 digits, optionally prefixed with +)."
            )
        return phone

    def validate_agreeToTerms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must accept the Terms & Conditions to create an account."
            )
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword')

        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirmPassword": "Passwords do not match."}
            )

        # AUTH_PASSWORD_VALIDATORS are not applied by create_user(), so run them
        # here against an unsaved user so similarity checks have something to
        # compare against.
        full_name = attrs.get('fullName', '')
        names = full_name.split(' ', 1)
        candidate = User(
            username=attrs.get('email', ''),
            email=attrs.get('email', ''),
            first_name=names[0] if names else '',
            last_name=names[1] if len(names) > 1 else ''
        )
        try:
            validate_password(password, candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirmPassword', None)
        validated_data.pop('agreeToTerms', None)
        full_name = validated_data.pop('fullName')
        phone_number = validated_data.pop('phoneNumber')

        names = full_name.split(' ', 1)
        email = validated_data['email']

        # Generate a unique username based on the full name
        base_username = full_name.strip()
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=username).exists():
            username = f"{base_username} {counter}"
            counter += 1

        validated_data['username'] = username
        validated_data['first_name'] = names[0]
        validated_data['last_name'] = names[1] if len(names) > 1 else ''
        validated_data['phone_number'] = phone_number
        validated_data['role'] = User.Role.CANDIDATE

        with transaction.atomic():
            try:
                user = User.objects.create_user(**validated_data)
            except IntegrityError:
                raise serializers.ValidationError(
                    {"email": "A user with this email already exists."}
                )

            # The post_save signal creates the CandidateProfile; mirror the
            # phone number onto it so profile screens have it from day one.
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            profile.phone = phone_number
            profile.save(update_fields=['phone', 'updated_at'])

            log_audit_event(
                actor=user,
                action='USER_REGISTER',
                target_type='User',
                target_id=user.id,
                target_repr=f"{user.email} (Candidate)",
                outcome='SUCCESS',
                description=f"Candidate registered account: {user.email}",
                request=self.context.get('request')
            )

        return user

    def to_representation(self, instance):
        # Every input field is write_only, so build the response from the
        # created user instead of echoing the payload back.
        return {
            'id': instance.id,
            'fullName': f"{instance.first_name} {instance.last_name}".strip(),
            'email': instance.email,
            'phoneNumber': instance.phone_number,
            'role': instance.role
        }


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer used by Super Admin to create ADMIN or HR accounts.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    confirmPassword = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    full_name = serializers.CharField(required=False, allow_blank=True)
    fullName = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[(User.Role.ADMIN, 'Admin'), (User.Role.HR, 'HR'), (User.Role.CANDIDATE, 'Candidate')], default=User.Role.ADMIN)
    status = serializers.ChoiceField(choices=User.Status.choices, default=User.Status.ACTIVE, required=False)
    account_status = serializers.CharField(required=False, allow_blank=True)
    account_email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    company_email = serializers.CharField(required=False, allow_blank=True)
    company_phone = serializers.CharField(required=False, allow_blank=True)
    company_website = serializers.CharField(required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)
    company_address = serializers.CharField(required=False, allow_blank=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    company_logo = serializers.CharField(required=False, allow_blank=True)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    primary_contact_name = serializers.CharField(required=False, allow_blank=True)
    mobile_number = serializers.CharField(required=False, allow_blank=True)
    profile_photo = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.CharField(required=False, allow_blank=True)
    dob = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    expected_salary_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    expected_salary_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    preferred_job_type = serializers.CharField(required=False, allow_blank=True)
    preferred_work_mode_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'account_email',
            'password',
            'confirm_password',
            'confirmPassword',
            'full_name',
            'fullName',
            'name',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'status',
            'account_status',
            'company_name',
            'company_email',
            'company_phone',
            'company_website',
            'website',
            'company_address',
            'company_description',
            'company_logo',
            'location_id',
            'primary_contact_name',
            'mobile_number',
            'profile_photo',
            'date_of_birth',
            'dob',
            'gender',
            'expected_salary_min',
            'expected_salary_max',
            'preferred_job_type',
            'preferred_work_mode_id',
            'designation',
        )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            if not data.get('email') and data.get('account_email'):
                data['email'] = data['account_email']
            if not data.get('account_email') and data.get('email'):
                data['account_email'] = data['email']
        return super().to_internal_value(data)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email address already exists. Please choose a different account email.")
        return email

    def validate_role(self, value):
        if value not in [User.Role.ADMIN, User.Role.HR, User.Role.CANDIDATE]:
            raise serializers.ValidationError("Only ADMIN, HR, or CANDIDATE roles can be created by Super Admin.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword') or attrs.get('confirm_password')

        if confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirmPassword": "Passwords do not match."})

        # Apply Django password validators
        raw_name = attrs.get('full_name') or attrs.get('fullName') or attrs.get('name') or f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip()
        names = raw_name.split(' ', 1) if raw_name else ['', '']
        dummy_user = User(
            username=attrs.get('email', ''),
            email=attrs.get('email', ''),
            first_name=names[0],
            last_name=names[1] if len(names) > 1 else ''
        )
        try:
            validate_password(password, dummy_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('account_email', None)
        validated_data.pop('confirmPassword', None)
        validated_data.pop('confirm_password', None)
        company_name = validated_data.pop('company_name', None)
        company_email = validated_data.pop('company_email', None)
        company_phone = validated_data.pop('company_phone', None)
        company_website = validated_data.pop('company_website', None) or validated_data.pop('website', None)
        company_address = validated_data.pop('company_address', None)
        company_description = validated_data.pop('company_description', None)
        company_logo = validated_data.pop('company_logo', None)
        location_id = validated_data.pop('location_id', None)
        primary_contact_name = validated_data.pop('primary_contact_name', None)
        mobile_number = validated_data.pop('mobile_number', None)
        profile_photo = validated_data.pop('profile_photo', None)
        date_of_birth = validated_data.pop('date_of_birth', None) or validated_data.pop('dob', None)
        gender = validated_data.pop('gender', None)
        expected_salary_min = validated_data.pop('expected_salary_min', None)
        expected_salary_max = validated_data.pop('expected_salary_max', None)
        preferred_job_type = validated_data.pop('preferred_job_type', None)
        preferred_work_mode_id = validated_data.pop('preferred_work_mode_id', None)
        if mobile_number and not validated_data.get('phone_number'):
            validated_data['phone_number'] = mobile_number
        designation = validated_data.pop('designation', None)

        raw_status = validated_data.pop('account_status', None)
        if raw_status:
            status_upper = raw_status.upper().strip()
            if status_upper in dict(User.Status.choices):
                validated_data['status'] = status_upper
            elif status_upper == 'ACTIVE' or raw_status.lower() == 'active':
                validated_data['status'] = User.Status.ACTIVE
            elif status_upper == 'INACTIVE' or raw_status.lower() == 'inactive':
                validated_data['status'] = User.Status.INACTIVE

        raw_name = validated_data.pop('full_name', None) or validated_data.pop('fullName', None) or validated_data.pop('name', None)
        if raw_name:
            names = raw_name.strip().split(' ', 1)
            validated_data['first_name'] = names[0]
            validated_data['last_name'] = names[1] if len(names) > 1 else ''

        email = validated_data['email'].lower().strip()
        validated_data['email'] = email

        request = self.context.get('request')
        creator = request.user if request and request.user.is_authenticated else None

        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() or email.split('@')[0]

        base_username = full_name
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=username).exists():
            username = f"{base_username} {counter}"
            counter += 1

        validated_data['username'] = username
        validated_data['created_by'] = creator

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            
            # Ensure UserRole mapping is synced
            role_obj, _ = Role.objects.get_or_create(
                name=user.role,
                defaults={"description": f"{user.get_role_display()} role"}
            )
            UserRole.objects.get_or_create(user=user, role=role_obj)

            # Ensure AdminProfile or HRProfile row is created transactionally
            if user.role == User.Role.ADMIN:
                from accounts.models import AdminProfile
                admin_prof, _ = AdminProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "name": full_name,
                        "email": user.email,
                        "status": user.status
                    }
                )
                admin_prof.name = full_name
                admin_prof.email = user.email
                admin_prof.status = user.status
                admin_prof.save()
            elif user.role == User.Role.CANDIDATE:
                profile, _ = CandidateProfile.objects.get_or_create(user=user)
                if full_name:
                    profile.full_name = full_name
                if user.phone_number:
                    profile.phone = user.phone_number
                if profile_photo:
                    profile.profile_photo = profile_photo
                if date_of_birth:
                    profile.dob = date_of_birth
                if gender:
                    profile.gender = gender
                if location_id:
                    profile.location_id = location_id
                if expected_salary_min is not None:
                    profile.expected_salary_min = expected_salary_min
                if expected_salary_max is not None:
                    profile.expected_salary_max = expected_salary_max
                if preferred_job_type:
                    profile.preferred_job_type = preferred_job_type
                if preferred_work_mode_id:
                    profile.preferred_work_mode_id = preferred_work_mode_id
                profile.save()
            elif user.role == User.Role.HR:
                profile, _ = HRProfile.objects.get_or_create(user=user)
                if company_name:
                    profile.company_name = company_name
                if company_email:
                    profile.company_email = company_email
                elif user.email:
                    profile.company_email = user.email
                if company_phone:
                    profile.company_phone = company_phone
                elif user.phone_number:
                    profile.company_phone = user.phone_number
                if company_website:
                    profile.company_website = company_website
                if company_address:
                    profile.company_address = company_address
                if company_description:
                    profile.company_description = company_description
                logo_val = company_logo or profile_photo
                if logo_val:
                    profile.company_logo = logo_val
                if location_id:
                    profile.location_id = location_id
                if designation:
                    profile.designation = designation
                profile.verification_status = 'PENDING'
                profile.trust_level = 'NEW'
                profile.save()

                EmployerVerification.objects.get_or_create(
                    employer=profile,
                    defaults={'verification_status': EmployerVerification.VerificationStatus.PENDING}
                )
                EmployerTrust.objects.get_or_create(
                    employer=profile,
                    defaults={'trust_level': EmployerTrust.TrustLevel.NEW, 'trust_score': 0, 'is_trusted': False}
                )

            log_audit_event(
                actor=creator,
                action='USER_CREATE',
                target_type='User',
                target_id=user.id,
                target_repr=f"{user.email} ({user.role})",
                outcome='SUCCESS',
                description=f"Created {user.get_role_display()} account for {user.email}",
                request=request
            )

        return user

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'name': f"{instance.first_name} {instance.last_name}".strip() or instance.username,
            'fullName': f"{instance.first_name} {instance.last_name}".strip() or instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'role': instance.role,
            'status': instance.status,
            'phone_number': instance.phone_number,
            'created_by': instance.created_by.id if instance.created_by else None,
            'created_at': instance.created_at,
        }


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer used by Super Admin to list created Admin accounts safely.
    """
    name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    account_status = serializers.CharField(source='status')
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'full_name',
            'username',
            'email',
            'role',
            'status',
            'account_status',
            'created_at',
            'created_by'
        )

    def get_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username

    def get_full_name(self, obj):
        return self.get_name(obj)

    def get_created_by(self, obj):
        if not obj.created_by:
            return None
        cb_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return {
            'id': obj.created_by.id,
            'email': obj.created_by.email,
            'name': cb_name
        }



class HRRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    # Optional fields for initial profile setup
    company_name = serializers.CharField(required=False, allow_blank=True)
    company_website = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    company_address = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    company_email = serializers.CharField(required=False, allow_blank=True)
    company_phone = serializers.CharField(required=False, allow_blank=True)
    company_website = serializers.CharField(required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)
    company_address = serializers.CharField(required=False, allow_blank=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    company_logo = serializers.CharField(required=False, allow_blank=True)
    location_id = serializers.IntegerField(required=False, allow_null=True)
    primary_contact_name = serializers.CharField(required=False, allow_blank=True)
    mobile_number = serializers.CharField(required=False, allow_blank=True)
    profile_photo = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.CharField(required=False, allow_blank=True)
    dob = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    expected_salary_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    expected_salary_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    preferred_job_type = serializers.CharField(required=False, allow_blank=True)
    preferred_work_mode_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'profile_picture',
            'company_name',
            'company_email',
            'company_phone',
            'company_website',
            'website',
            'company_address',
            'company_description',
            'company_logo',
            'location_id',
            'primary_contact_name',
            'mobile_number',
            'profile_photo',
            'date_of_birth',
            'dob',
            'gender',
            'expected_salary_min',
            'expected_salary_max',
            'preferred_job_type',
            'preferred_work_mode_id',
            'company_website',
            'company_address',
            'designation'
        )

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', None)
        company_email = validated_data.pop('company_email', None)
        company_phone = validated_data.pop('company_phone', None)
        company_website = validated_data.pop('company_website', None) or validated_data.pop('website', None)
        company_address = validated_data.pop('company_address', None)
        company_description = validated_data.pop('company_description', None)
        company_logo = validated_data.pop('company_logo', None)
        location_id = validated_data.pop('location_id', None)
        primary_contact_name = validated_data.pop('primary_contact_name', None)
        mobile_number = validated_data.pop('mobile_number', None)
        profile_photo = validated_data.pop('profile_photo', None)
        date_of_birth = validated_data.pop('date_of_birth', None) or validated_data.pop('dob', None)
        gender = validated_data.pop('gender', None)
        expected_salary_min = validated_data.pop('expected_salary_min', None)
        expected_salary_max = validated_data.pop('expected_salary_max', None)
        preferred_job_type = validated_data.pop('preferred_job_type', None)
        preferred_work_mode_id = validated_data.pop('preferred_work_mode_id', None)
        if mobile_number and not validated_data.get('phone_number'):
            validated_data['phone_number'] = mobile_number
        company_website = validated_data.pop('company_website', None)
        company_address = validated_data.pop('company_address', None)
        designation = validated_data.pop('designation', None)
        
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = validated_data.get('email', '').split('@')[0]

        # Generate a unique username based on the full name
        base_username = full_name
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=username).exists():
            username = f"{base_username} {counter}"
            counter += 1

        validated_data['username'] = username
        validated_data['role'] = User.Role.HR
        user = User.objects.create_user(**validated_data)
        
        profile = getattr(user, 'hr_profile', None)
        if profile:
            if company_name is not None:
                profile.company_name = company_name
            if company_website is not None:
                profile.company_website = company_website
            if company_address is not None:
                profile.company_address = company_address
            if designation is not None:
                profile.designation = designation
            profile.save()
            
        log_audit_event(
            actor=user,
            action='USER_CREATE',
            target_type='User',
            target_id=user.id,
            target_repr=f"{user.email} (HR)",
            outcome='SUCCESS',
            description=f"HR registered account: {user.email}",
            request=self.context.get('request')
        )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    expected_role = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.CharField(write_only=True, required=False, allow_blank=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        token['user_id'] = user.id
        return token

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        if not email:
            raise serializers.ValidationError({"email": "This field is required."})
        if not password:
            raise serializers.ValidationError({"password": "This field is required."})

        # Validate email format manually since SimpleJWT overrides the email field definition in __init__
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_email(email)
        except DjangoValidationError:
            raise serializers.ValidationError({"email": "Enter a valid email address."})

        # Check if user exists and active status
        try:
            user = User.objects.get(email__iexact=email)
            if not user.is_active or user.status != User.Status.ACTIVE:
                log_audit_event(
                    actor=user,
                    actor_email=email,
                    action='LOGIN_FAILED',
                    target_type='User',
                    target_id=user.id,
                    target_repr=email,
                    outcome='FAILED',
                    description=f"Failed login attempt for {email}: Account is inactive or suspended",
                    request=self.context.get('request')
                )
                raise serializers.ValidationError({"detail": "User account is inactive or suspended."})
        except User.DoesNotExist:
            pass

        # Authenticate user
        from django.contrib.auth import authenticate
        self.user = authenticate(username=email, password=password)
        
        if not self.user:
            log_audit_event(
                actor=None,
                actor_email=email,
                action='LOGIN_FAILED',
                target_type='User',
                target_repr=email,
                outcome='FAILED',
                description=f"Failed login attempt for {email}: Invalid credentials",
                request=self.context.get('request')
            )
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        # Check expected role if provided
        expected_role = (
            attrs.get('expected_role') or 
            attrs.get('role') or 
            (self.context.get('request') and self.context.get('request').data.get('expected_role')) or 
            (self.context.get('request') and self.context.get('request').data.get('role'))
        )
        if expected_role:
            exp = expected_role.strip().upper()
            if exp == 'CANDIDATE' and self.user.role != User.Role.CANDIDATE:
                log_audit_event(
                    actor=self.user,
                    actor_email=email,
                    action='LOGIN_FAILED',
                    target_type='User',
                    target_id=self.user.id,
                    target_repr=email,
                    outcome='FAILED',
                    description=f"Failed login attempt for {email}: Role mismatch (expected CANDIDATE, actual {self.user.role})",
                    request=self.context.get('request')
                )
                msg = (
                    "This account is registered as an HR / Recruiter. Please switch to the 'HR / Recruiter' tab to login."
                    if self.user.role == User.Role.HR
                    else "Access denied. Candidate login only."
                )
                raise serializers.ValidationError({"detail": msg})

            elif exp in ['HR', 'RECRUITER'] and self.user.role != User.Role.HR:
                log_audit_event(
                    actor=self.user,
                    actor_email=email,
                    action='LOGIN_FAILED',
                    target_type='User',
                    target_id=self.user.id,
                    target_repr=email,
                    outcome='FAILED',
                    description=f"Failed login attempt for {email}: Role mismatch (expected HR, actual {self.user.role})",
                    request=self.context.get('request')
                )
                msg = (
                    "This account is registered as a Candidate. Please switch to the 'Candidate' tab to login."
                    if self.user.role == User.Role.CANDIDATE
                    else "Access denied. HR / Recruiter login only."
                )
                raise serializers.ValidationError({"detail": msg})

            elif exp in ['ADMIN', 'SUPER_ADMIN', 'ADMIN_PORTAL'] and self.user.role not in [User.Role.ADMIN, User.Role.SUPER_ADMIN]:
                log_audit_event(
                    actor=self.user,
                    actor_email=email,
                    action='LOGIN_FAILED',
                    target_type='User',
                    target_id=self.user.id,
                    target_repr=email,
                    outcome='FAILED',
                    description=f"Failed login attempt for {email}: Role mismatch (expected ADMIN, actual {self.user.role})",
                    request=self.context.get('request')
                )
                raise serializers.ValidationError({"detail": "Access denied. Candidate and HR users must log in at /login."})

        log_audit_event(
            actor=self.user,
            action='LOGIN_SUCCESS',
            target_type='User',
            target_id=self.user.id,
            target_repr=self.user.email,
            outcome='SUCCESS',
            description=f"User {self.user.email} logged in successfully",
            request=self.context.get('request')
        )

        # Generate tokens
        refresh = self.get_token(self.user)

        user_payload = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'phone_number': self.user.phone_number,
            'fullName': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
            'status': self.user.status,
        }

        if self.user.role == User.Role.CANDIDATE:
            candidate_profile = getattr(self.user, 'candidate_profile', None)
            user_payload['profile_completed'] = candidate_profile.profile_completed if candidate_profile else False
            user_payload['profile_completion'] = candidate_profile.profile_completion if candidate_profile else 0

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_payload
        }
        return data


class GoogleLoginSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token = attrs.get('token')
        import urllib.request
        import json
        from decouple import config

        google_client_id = config('GOOGLE_CLIENT_ID', default=None)

        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except Exception:
            raise serializers.ValidationError({"token": "Invalid Google token."})

        google_id = payload.get('sub')
        email = payload.get('email', '').lower().strip()
        aud = payload.get('aud')

        if not google_id or not email:
            raise serializers.ValidationError({"token": "Invalid Google token payload."})

        if google_client_id and aud != google_client_id:
            raise serializers.ValidationError({"token": "Google client ID mismatch."})

        user = User.objects.filter(provider='GOOGLE', provider_user_id=google_id).first()
        if not user:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                if not user.provider:
                    user.provider = 'GOOGLE'
                    user.provider_user_id = google_id
                    user.save(update_fields=['provider', 'provider_user_id', 'updated_at'])
            else:
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    role=User.Role.CANDIDATE,
                    provider='GOOGLE',
                    provider_user_id=google_id,
                )

        if not user.is_active or user.status != User.Status.ACTIVE:
            raise serializers.ValidationError({"detail": "User account is inactive or suspended."})

        refresh = CustomTokenObtainPairSerializer.get_token(user)

        user_payload = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone_number': user.phone_number,
            'fullName': f"{user.first_name} {user.last_name}".strip(),
            'status': user.status,
        }

        attrs['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_payload
        }
        attrs['user'] = user
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    candidate_profile = CandidateProfileSerializer(required=False)
    hr_profile = HRProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'profile_picture',
            'role',
            'candidate_profile',
            'hr_profile'
        )
        read_only_fields = ('id', 'username', 'role')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.role == User.Role.CANDIDATE:
            rep.pop('hr_profile', None)
        elif instance.role == User.Role.HR:
            rep.pop('candidate_profile', None)
        else:
            rep.pop('candidate_profile', None)
            rep.pop('hr_profile', None)
        return rep

    def update(self, instance, validated_data):
        candidate_profile_data = validated_data.pop('candidate_profile', None)
        hr_profile_data = validated_data.pop('hr_profile', None)
        
        # Update core User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update linked Profile fields
        if instance.role == User.Role.CANDIDATE and candidate_profile_data is not None:
            profile, _ = CandidateProfile.objects.get_or_create(user=instance)
            for attr, value in candidate_profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        elif instance.role == User.Role.HR and hr_profile_data is not None:
            profile, _ = HRProfile.objects.get_or_create(user=instance)
            for attr, value in hr_profile_data.items():
                setattr(profile, attr, value)
            profile.save()
            
        return instance



class EmployerProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    status = serializers.CharField(source='user.status', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = HRProfile
        fields = (
            'id',
            'user_id',
            'full_name',
            'email',
            'phone_number',
            'role',
            'status',
            'company_name',
            'company_email',
            'company_phone',
            'company_website',
            'company_address',
            'company_description',
            'company_logo',
            'designation',
            'location',
            'verification_status',
            'trust_level',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'email', 'role', 'status', 'verification_status', 'trust_level', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    confirmPassword = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword') or attrs.get('confirm_password')

        if confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return attrs



class LocationSerializer(serializers.ModelSerializer):
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    state = serializers.CharField(source='get_state', read_only=True)
    district = serializers.CharField(source='get_district', read_only=True)

    class Meta:
        model = Location
        fields = (
            'id',
            'name',
            'location_type',
            'parent',
            'is_active',
            'full_path',
            'state',
            'district',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'full_path', 'state', 'district', 'created_at', 'updated_at')

    def validate(self, attrs):
        location_type = attrs.get('location_type')
        parent = attrs.get('parent')

        if location_type == Location.LocationType.STATE:
            if parent is not None:
                raise serializers.ValidationError({"parent": "State location level cannot have a parent."})
        elif location_type == Location.LocationType.DISTRICT:
            if not parent or parent.location_type not in [Location.LocationType.STATE, Location.LocationType.STATE_DISTRICT]:
                raise serializers.ValidationError({"parent": "District parent must be a State."})
        elif location_type == Location.LocationType.CITY:
            if not parent or parent.location_type not in [Location.LocationType.DISTRICT, Location.LocationType.STATE_DISTRICT]:
                raise serializers.ValidationError({"parent": "City / Town parent must be a District."})
        elif location_type == Location.LocationType.LOCALITY:
            if not parent or parent.location_type != Location.LocationType.CITY:
                raise serializers.ValidationError({"parent": "Locality parent must be a City / Town."})

        return attrs


class CandidateUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    gender = serializers.CharField(source='candidate_profile.gender', read_only=True)
    date_of_birth = serializers.CharField(source='candidate_profile.dob', read_only=True)
    profile_photo = serializers.SerializerMethodField()
    profile_completion = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    expected_salary_min = serializers.DecimalField(source='candidate_profile.expected_salary_min', max_digits=12, decimal_places=2, read_only=True)
    expected_salary_max = serializers.DecimalField(source='candidate_profile.expected_salary_max', max_digits=12, decimal_places=2, read_only=True)
    preferred_job_type = serializers.CharField(source='candidate_profile.preferred_job_type', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone_number',
            'role',
            'status',
            'full_name',
            'name',
            'location',
            'gender',
            'date_of_birth',
            'profile_photo',
            'profile_completion',
            'applications',
            'last_active',
            'expected_salary_min',
            'expected_salary_max',
            'preferred_job_type',
            'created_at',
            'updated_at',
        )

    def get_full_name(self, obj):
        if hasattr(obj, 'candidate_profile') and obj.candidate_profile and obj.candidate_profile.full_name:
            return obj.candidate_profile.full_name
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username

    def get_name(self, obj):
        return self.get_full_name(obj)

    def get_profile_photo(self, obj):
        request = self.context.get('request')
        if obj.profile_picture:
            try:
                return request.build_absolute_uri(obj.profile_picture.url) if request else obj.profile_picture.url
            except Exception:
                pass
        if hasattr(obj, 'candidate_profile') and obj.candidate_profile and obj.candidate_profile.profile_photo:
            photo = obj.candidate_profile.profile_photo
            if photo.startswith('http') or not request:
                return photo
            return request.build_absolute_uri(photo)
        return None

    def get_location(self, obj):
        if hasattr(obj, 'candidate_profile') and obj.candidate_profile:
            cp = obj.candidate_profile
            if cp.location:
                return LocationSerializer(cp.location).data
            state = cp.state or ''
            city = cp.city or ''
            district = getattr(cp, 'district', '') or ''
            address = cp.address or ''
            display_name = f"{city}, {state}".strip(', ') if (city or state) else (address if address else 'Tamil Nadu')
            return {
                'name': display_name,
                'city': city,
                'district': district,
                'state': state or 'Tamil Nadu',
                'full_path': display_name
            }
        return {'name': 'Tamil Nadu', 'state': 'Tamil Nadu', 'district': '', 'city': ''}

    def get_profile_completion(self, obj):
        if hasattr(obj, 'candidate_profile') and obj.candidate_profile:
            cp = obj.candidate_profile
            if cp.profile_completion and cp.profile_completion > 0:
                return cp.profile_completion
            score = 20
            if cp.full_name or obj.first_name:
                score += 15
            if obj.phone_number or cp.phone:
                score += 15
            if cp.city or cp.state or cp.location:
                score += 15
            if cp.degree or cp.college:
                score += 15
            if hasattr(cp, 'resumes') and cp.resumes.exists():
                score += 20
            return min(score, 100)
        return 20

    def get_applications(self, obj):
        if hasattr(obj, 'candidate_profile') and obj.candidate_profile:
            return Application.objects.filter(candidate=obj.candidate_profile).count()
        return 0

    def get_last_active(self, obj):
        dt = obj.last_login or obj.updated_at or obj.created_at
        if dt:
            return dt.strftime("%b %d, %Y")
        return "Active"


class EmployerUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='hr_profile.company_name', read_only=True)
    company_email = serializers.CharField(source='hr_profile.company_email', read_only=True)
    company_phone = serializers.CharField(source='hr_profile.company_phone', read_only=True)
    company_website = serializers.CharField(source='hr_profile.company_website', read_only=True)
    company_address = serializers.CharField(source='hr_profile.company_address', read_only=True)
    company_description = serializers.CharField(source='hr_profile.company_description', read_only=True)
    company_logo = serializers.CharField(source='hr_profile.company_logo', read_only=True)
    profile_photo = serializers.SerializerMethodField()
    designation = serializers.CharField(source='hr_profile.designation', read_only=True)
    verification_status = serializers.CharField(source='hr_profile.verification_status', read_only=True)
    trust_level = serializers.CharField(source='hr_profile.trust_level', read_only=True)
    location = LocationSerializer(source='hr_profile.location', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone_number',
            'role',
            'status',
            'full_name',
            'name',
            'company_name',
            'company_email',
            'company_phone',
            'company_website',
            'company_address',
            'company_description',
            'company_logo',
            'profile_photo',
            'designation',
            'verification_status',
            'trust_level',
            'location',
            'created_at',
            'updated_at',
        )

    def get_profile_photo(self, obj):
        hr = getattr(obj, 'hr_profile', None)
        if hr and hr.company_logo:
            return hr.company_logo
        if obj.profile_picture:
            return obj.profile_picture.url
        return None

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username

    def get_name(self, obj):
        return self.get_full_name(obj)


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = (
            'id',
            'timestamp',
            'actor',
            'actor_email',
            'actor_name',
            'action',
            'target_type',
            'target_id',
            'target_repr',
            'outcome',
            'description',
            'ip_address',
        )

    def get_actor_name(self, obj):
        if obj.actor:
            name = f"{obj.actor.first_name} {obj.actor.last_name}".strip()
            return name if name else obj.actor.username
        return obj.actor_email or "System / Anonymous"


class PrivilegedUserAccessReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    roles_assigned = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'name',
            'role',
            'status',
            'is_active',
            'is_superuser',
            'created_at',
            'created_by_info',
            'roles_assigned',
        )

    def get_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username

    def get_created_by_info(self, obj):
        if obj.created_by:
            name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
            return {'id': obj.created_by.id, 'email': obj.created_by.email, 'name': name}
        # Fallback to searching AuditEvent for USER_CREATE target_id
        event = AuditEvent.objects.filter(action='USER_CREATE', target_type='User', target_id=str(obj.id)).first()
        if event and event.actor:
            name = f"{event.actor.first_name} {event.actor.last_name}".strip() or event.actor.username
            return {'id': event.actor.id, 'email': event.actor.email, 'name': name}
        elif event and event.actor_email:
            return {'id': None, 'email': event.actor_email, 'name': event.actor_email}
        return None

    def get_roles_assigned(self, obj):
        return list(obj.user_roles.values_list('role__name', flat=True))


class EmployerVerificationHistorySerializer(serializers.ModelSerializer):
    reviewed_by_name = serializers.SerializerMethodField()
    reviewed_by_email = serializers.SerializerMethodField()

    class Meta:
        model = EmployerVerification
        fields = (
            'id',
            'verification_status',
            'submitted_at',
            'reviewed_at',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_by_email',
            'rejection_reason',
            'notes',
        )

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.last_name}".strip() or obj.reviewed_by.username
        return None

    def get_reviewed_by_email(self, obj):
        return obj.reviewed_by.email if obj.reviewed_by else None


class EmployerVerificationQueueSerializer(serializers.ModelSerializer):
    employer_id = serializers.IntegerField(source='id')
    user_id = serializers.IntegerField(source='user.id')
    company_name = serializers.CharField()
    employer_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')
    phone = serializers.SerializerMethodField()
    account_status = serializers.CharField(source='user.status')
    location_details = serializers.SerializerMethodField()
    is_profile_complete = serializers.SerializerMethodField()
    trust_info = serializers.SerializerMethodField()
    latest_verification = serializers.SerializerMethodField()
    verification_history = serializers.SerializerMethodField()

    class Meta:
        model = HRProfile
        fields = (
            'employer_id',
            'user_id',
            'company_name',
            'employer_name',
            'email',
            'phone',
            'company_phone',
            'company_website',
            'company_address',
            'company_description',
            'company_logo',
            'designation',
            'verification_status',
            'account_status',
            'location',
            'location_details',
            'is_profile_complete',
            'trust_info',
            'latest_verification',
            'verification_history',
            'created_at',
            'updated_at',
        )

    def get_employer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_phone(self, obj):
        return obj.company_phone or obj.phone or obj.user.phone_number

    def get_is_profile_complete(self, obj):
        return obj.is_profile_complete()

    def get_location_details(self, obj):
        if obj.location:
            return {
                'id': obj.location.id,
                'name': obj.location.name,
                'full_path': obj.location.get_full_path(),
                'state': obj.location.get_state(),
                'district': obj.location.get_district(),
            }
        return None

    def get_trust_info(self, obj):
        if hasattr(obj, 'trust') and obj.trust:
            return {
                'trust_level': obj.trust.trust_level,
                'jobs_posted': obj.trust.jobs_posted,
                'jobs_approved': obj.trust.jobs_approved,
                'jobs_rejected': obj.trust.jobs_rejected,
                'trust_score': obj.trust.trust_score,
                'is_trusted': obj.trust.is_trusted,
            }
        return {'trust_level': 'NEW', 'is_trusted': False, 'trust_score': 0}

    def get_latest_verification(self, obj):
        latest = obj.verifications.order_by('-submitted_at', '-id').first()
        if latest:
            return EmployerVerificationHistorySerializer(latest).data
        return None

    def get_verification_history(self, obj):
        verifications = obj.verifications.order_by('-submitted_at', '-id')
        return EmployerVerificationHistorySerializer(verifications, many=True).data


class JobReviewHistorySerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    reviewer_email = serializers.SerializerMethodField()

    class Meta:
        model = JobReview
        fields = (
            'id',
            'action',
            'reason',
            'notes',
            'reviewer',
            'reviewer_name',
            'reviewer_email',
            'created_at',
        )

    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return f"{obj.reviewer.first_name} {obj.reviewer.last_name}".strip() or obj.reviewer.username
        return None

    def get_reviewer_email(self, obj):
        return obj.reviewer.email if obj.reviewer else None


class JobReviewQueueSerializer(serializers.ModelSerializer):
    employer = serializers.SerializerMethodField()
    category_info = serializers.SerializerMethodField()
    work_mode_info = serializers.SerializerMethodField()
    locations = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    review_history = serializers.SerializerMethodField()
    latest_review = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id',
            'title',
            'description',
            'responsibilities',
            'requirements',
            'education_requirement',
            'experience_min',
            'experience_max',
            'experience_required',
            'salary_min',
            'salary_max',
            'salary_period',
            'status',
            'application_type',
            'application_deadline',
            'published_at',
            'closed_at',
            'created_at',
            'updated_at',
            'employer',
            'category',
            'category_info',
            'work_mode',
            'work_mode_info',
            'locations',
            'skills',
            'review_history',
            'latest_review',
        )

    def get_employer(self, obj):
        hr = obj.hr
        if not hr:
            return None
        trust_level = hr.trust.trust_level if hasattr(hr, 'trust') and hr.trust else 'NEW'
        is_trusted = hr.trust.is_trusted if hasattr(hr, 'trust') and hr.trust else False
        return {
            'employer_id': hr.id,
            'user_id': hr.user.id,
            'company_name': hr.company_name or f"Company #{hr.id}",
            'company_logo': hr.company_logo,
            'contact_name': f"{hr.user.first_name} {hr.user.last_name}".strip() or hr.user.username,
            'email': hr.user.email,
            'verification_status': hr.verification_status,
            'account_status': hr.user.status,
            'trust_level': trust_level,
            'is_trusted': is_trusted,
        }

    def get_category_info(self, obj):
        if obj.category:
            return {
                'id': obj.category.id,
                'name': obj.category.name,
                'parent_id': obj.category.parent.id if obj.category.parent else None,
                'parent_name': obj.category.parent.name if obj.category.parent else None,
            }
        return None

    def get_work_mode_info(self, obj):
        if obj.work_mode:
            return {
                'id': obj.work_mode.id,
                'name': obj.work_mode.name,
            }
        return None

    def get_locations(self, obj):
        locs = []
        for jl in obj.job_locations.select_related('location', 'location__parent', 'location__parent__parent').all():
            loc = jl.location
            locs.append({
                'id': loc.id,
                'name': loc.name,
                'location_type': loc.location_type,
                'full_path': loc.get_full_path(),
                'state': loc.get_state(),
                'district': loc.get_district(),
            })
        return locs

    def get_skills(self, obj):
        skills_list = []
        for js in obj.job_skills.select_related('skill').all():
            skills_list.append({
                'id': js.skill.id,
                'name': js.skill.name,
                'is_required': js.is_required,
            })
        return skills_list

    def get_review_history(self, obj):
        reviews = obj.reviews.order_by('-created_at', '-id')
        return JobReviewHistorySerializer(reviews, many=True).data

    def get_latest_review(self, obj):
        latest = obj.reviews.order_by('-created_at', '-id').first()
        if latest:
            return JobReviewHistorySerializer(latest).data
        return None


class NotificationSerializer(serializers.ModelSerializer):
    formatted_time = serializers.SerializerMethodField()
    recipient_email = serializers.CharField(source='user.email', read_only=True)
    recipient_name = serializers.SerializerMethodField()
    recipient_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'user_id',
            'recipient_email',
            'recipient_name',
            'recipient_role',
            'notification_type',
            'title',
            'message',
            'reference_type',
            'reference_id',
            'is_read',
            'created_at',
            'formatted_time',
        )
        read_only_fields = ('id', 'user_id', 'created_at')

    def get_recipient_name(self, obj):
        if not obj.user:
            return 'User'
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_formatted_time(self, obj):
        if not obj.created_at:
            return 'Just now'
        now = timezone.now()
        diff = now - obj.created_at
        if diff.total_seconds() < 60:
            return 'Just now'
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() // 60)
            return f'{mins} min{"s" if mins > 1 else ""} ago'
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() // 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        else:
            days = int(diff.total_seconds() // 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'


class JobReportSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField(source='job.id', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.SerializerMethodField()
    job_status = serializers.CharField(source='job.status', read_only=True)
    job_locations = serializers.SerializerMethodField()
    reported_by_name = serializers.SerializerMethodField()
    reported_by_email = serializers.CharField(source='reported_by.email', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True)
    reason_display = serializers.CharField(source='reason', read_only=True)
    job_details = serializers.SerializerMethodField()
    reporter_details = serializers.SerializerMethodField()
    reviewer_details = serializers.SerializerMethodField()

    class Meta:
        model = JobReport
        fields = (
            'id',
            'job',
            'job_id',
            'job_title',
            'company_name',
            'job_status',
            'job_locations',
            'job_details',
            'reported_by',
            'reported_by_name',
            'reported_by_email',
            'reporter_details',
            'reason',
            'reason_display',
            'description',
            'status',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_by_email',
            'reviewer_details',
            'reviewed_at',
            'notes',
            'created_at',
        )
        read_only_fields = ('id', 'reported_by', 'reviewed_by', 'reviewed_at', 'created_at')

    def get_company_name(self, obj):
        if obj.job and obj.job.hr:
            return obj.job.hr.company_name or 'Unknown Company'
        return 'Unknown Company'

    def get_job_locations(self, obj):
        if not obj.job:
            return []
        locs = []
        for jl in obj.job.job_locations.select_related('location').all():
            locs.append({
                'id': jl.location.id,
                'name': jl.location.name,
                'full_path': jl.location.get_full_path(),
                'state': jl.location.get_state(),
                'district': jl.location.get_district(),
                'formatted': jl.location.get_full_path(),
            })
        return locs

    def get_reported_by_name(self, obj):
        if not obj.reported_by:
            return 'Candidate User'
        u = obj.reported_by
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_reviewed_by_name(self, obj):
        if not obj.reviewed_by:
            return None
        u = obj.reviewed_by
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_job_details(self, obj):
        if not obj.job:
            return None
        j = obj.job
        hr = j.hr
        locs = []
        for jl in j.job_locations.select_related('location').all():
            locs.append({
                'id': jl.location.id,
                'name': jl.location.name,
                'full_path': jl.location.get_full_path(),
                'state': jl.location.get_state(),
                'district': jl.location.get_district(),
            })
        return {
            'id': j.id,
            'title': j.title,
            'status': j.status,
            'company_name': hr.company_name if hr else 'Unknown',
            'employer_id': hr.id if hr else None,
            'employer_email': hr.user.email if hr and hr.user else None,
            'employer_verification_status': hr.verification_status if hr else None,
            'category_name': j.category.name if j.category else None,
            'work_mode_name': j.work_mode.name if j.work_mode else None,
            'locations': locs,
        }

    def get_reporter_details(self, obj):
        if not obj.reported_by:
            return None
        u = obj.reported_by
        name = f"{u.first_name} {u.last_name}".strip() or u.username
        return {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'name': name,
            'role': u.role,
        }

    def get_reviewer_details(self, obj):
        if not obj.reviewed_by:
            return None
        u = obj.reviewed_by
        name = f"{u.first_name} {u.last_name}".strip() or u.username
        return {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'name': name,
        }


# ==========================================
# CANDIDATE PORTAL SERIALIZERS
# ==========================================

class CandidateJobSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    company_initials = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    work_mode_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    locations = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id',
            'title',
            'status',
            'company_name',
            'company_logo',
            'company_initials',
            'category',
            'category_name',
            'work_mode',
            'work_mode_name',
            'location_name',
            'locations',
            'skills',
            'salary_min',
            'salary_max',
            'salary_period',
            'experience_min',
            'experience_max',
            'education_requirement',
            'application_type',
            'application_deadline',
            'description',
            'responsibilities',
            'is_saved',
            'is_applied',
            'is_expired',
            'published_at',
            'created_at',
        )

    def get_company_name(self, obj):
        return obj.hr.company_name if (obj.hr and obj.hr.company_name) else 'Employer'

    def get_company_logo(self, obj):
        if not obj.hr:
            return None
        logo = getattr(obj.hr, 'company_logo', None)
        if not logo and hasattr(obj.hr, 'user') and obj.hr.user:
            logo = getattr(obj.hr.user, 'profile_photo', None)
        if not logo:
            return None
        if hasattr(logo, 'url'):
            try:
                return logo.url
            except Exception:
                pass
        if isinstance(logo, str) and logo.strip():
            return logo.strip()
        return None

    def get_company_initials(self, obj):
        c_name = self.get_company_name(obj)
        return c_name[0].upper() if c_name else 'E'

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_work_mode_name(self, obj):
        return obj.work_mode.name if obj.work_mode else None

    def get_location_name(self, obj):
        locs = obj.job_locations.select_related('location').all()
        if locs.exists():
            return locs[0].location.get_full_path()
        return 'Location Not Specified'

    def get_locations(self, obj):
        res = []
        for jl in obj.job_locations.select_related('location').all():
            res.append({
                'id': jl.location.id,
                'name': jl.location.name,
                'full_path': jl.location.get_full_path(),
                'state': jl.location.get_state(),
                'district': jl.location.get_district(),
            })
        return res

    def get_skills(self, obj):
        res = []
        for js in obj.job_skills.select_related('skill').all():
            res.append({
                'id': js.skill.id,
                'name': js.skill.name,
                'is_required': js.is_required,
            })
        return res

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and hasattr(request.user, 'candidate_profile'):
            return SavedJob.objects.filter(candidate=request.user.candidate_profile, job=obj).exists()
        return False

    def get_is_applied(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and hasattr(request.user, 'candidate_profile'):
            return Application.objects.filter(candidate=request.user.candidate_profile, job=obj).exists()
        return False

    def get_is_expired(self, obj):
        if obj.status == Job.Status.EXPIRED:
            return True
        if obj.application_deadline and obj.application_deadline < timezone.now().date():
            return True
        return False


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationStatusHistory
        fields = (
            'id',
            'status',
            'changed_by',
            'changed_by_name',
            'notes',
            'created_at',
        )

    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return 'System'
        u = obj.changed_by
        return f"{u.first_name} {u.last_name}".strip() or u.username


class ApplicationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationMessage
        fields = (
            'id',
            'application',
            'sender',
            'sender_name',
            'sender_role',
            'message',
            'is_read',
            'created_at',
        )

    def get_sender_name(self, obj):
        u = obj.sender
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_sender_role(self, obj):
        return obj.sender.role if obj.sender else 'UNKNOWN'


class CandidateInterviewSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    scheduled_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = (
            'id',
            'application',
            'job',
            'job_title',
            'company_name',
            'interview_type',
            'scheduled_date',
            'scheduled_time',
            'scheduled_at_formatted',
            'location',
            'meeting_link',
            'phone_number',
            'notes',
            'status',
            'result',
            'created_at',
            'updated_at',
        )

    def get_job_title(self, obj):
        return obj.job.title if obj.job else (obj.application.job.title if obj.application and obj.application.job else 'Position')

    def get_company_name(self, obj):
        job_obj = obj.job or (obj.application.job if obj.application else None)
        if job_obj and job_obj.hr:
            return job_obj.hr.company_name or 'Employer'
        return 'Employer'

    def get_scheduled_at_formatted(self, obj):
        if obj.scheduled_date and obj.scheduled_time:
            return f"{obj.scheduled_date} at {obj.scheduled_time.strftime('%I:%M %p')}"
        elif obj.scheduled_date:
            return str(obj.scheduled_date)
        return 'TBD'


class CandidateApplicationDetailSerializer(serializers.ModelSerializer):
    job = CandidateJobSerializer(read_only=True)
    resume = ResumeSerializer(read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    messages = ApplicationMessageSerializer(many=True, read_only=True)
    interview = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            'id',
            'job',
            'candidate',
            'status',
            'application_type',
            'applied_at',
            'reviewed_at',
            'remarks',
            'resume',
            'status_history',
            'messages',
            'interview',
            'created_at',
            'updated_at',
        )

    def get_interview(self, obj):
        active_interview = obj.interviews.order_by('-created_at').first()
        if active_interview:
            return CandidateInterviewSerializer(active_interview).data
        return None


class CandidateApplicationSubmitSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(required=True)
    resume_id = serializers.IntegerField(required=False, allow_null=True)
    application_type = serializers.CharField(required=False, default='PROFILE_RESUME')
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    candidate_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        job_id = attrs.get('job_id')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError({"job_id": "Job does not exist."})

        if job.status != Job.Status.PUBLISHED:
            raise serializers.ValidationError({"job_id": "This job is not active or accepting applications."})

        if job.application_deadline and job.application_deadline < timezone.now().date():
            if job.status != Job.Status.EXPIRED:
                job.status = Job.Status.EXPIRED
                job.save(update_fields=['status'])
            raise serializers.ValidationError({"job_id": f"This job listing has expired as of {job.application_deadline} and is no longer accepting applications."})

        request = self.context.get('request')
        candidate_profile = request.user.candidate_profile

        existing_app = Application.objects.filter(candidate=candidate_profile, job=job).first()
        if existing_app:
            attrs['existing_app'] = existing_app
            attrs['job_obj'] = job
            return attrs

        raw_app_type = str(attrs.get('application_type') or job.application_type or 'PROFILE_RESUME').upper()
        if 'SIMPLE' in raw_app_type or 'LOCAL' in raw_app_type:
            app_type = 'SIMPLE_LOCAL'
        else:
            app_type = 'PROFILE_RESUME'
        attrs['application_type'] = app_type
        resume_id = attrs.get('resume_id')

        if app_type == 'PROFILE_RESUME':
            if not resume_id:
                # Fall back to candidate's default resume if available
                default_resume = candidate_profile.resumes.filter(is_default=True).first()
                if default_resume:
                    attrs['resume_obj'] = default_resume
                else:
                    first_resume = candidate_profile.resumes.first()
                    if first_resume:
                        attrs['resume_obj'] = first_resume
                    else:
                        raise serializers.ValidationError({"resume_id": "A resume is required for professional applications. Please upload a resume first."})
            else:
                try:
                    resume_obj = Resume.objects.get(id=resume_id, candidate=candidate_profile)
                    attrs['resume_obj'] = resume_obj
                except Resume.DoesNotExist:
                    raise serializers.ValidationError({"resume_id": "Selected resume does not exist or belong to your profile."})
        else:
            attrs['resume_obj'] = None

        attrs['job_obj'] = job
        return attrs


class SavedJobSerializer(serializers.ModelSerializer):
    job = CandidateJobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = (
            'id',
            'candidate',
            'job',
            'created_at',
        )

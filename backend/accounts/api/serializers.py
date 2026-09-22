import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from ..models import Role, UserRole, AdminProfile, CandidateProfile, HRProfile, Education, Experience, Resume, Skill, CandidateSkill

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


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'created_at', 'updated_at')


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
    role = serializers.ChoiceField(choices=[(User.Role.ADMIN, 'Admin'), (User.Role.HR, 'HR')], default=User.Role.ADMIN)
    status = serializers.ChoiceField(choices=User.Status.choices, default=User.Status.ACTIVE, required=False)
    account_status = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'email',
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
            'designation',
        )

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_role(self, value):
        if value not in [User.Role.ADMIN, User.Role.HR]:
            raise serializers.ValidationError("Only ADMIN or HR roles can be created by Super Admin.")
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
        validated_data.pop('confirmPassword', None)
        validated_data.pop('confirm_password', None)
        company_name = validated_data.pop('company_name', None)
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
            elif user.role == User.Role.HR:
                profile, _ = HRProfile.objects.get_or_create(user=user)
                if company_name:
                    profile.company_name = company_name
                if designation:
                    profile.designation = designation
                profile.save()

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
            'company_website',
            'company_address',
            'designation'
        )

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', None)
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
            
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

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
                raise serializers.ValidationError({"detail": "User account is inactive or suspended."})
        except User.DoesNotExist:
            pass

        # Authenticate user
        from django.contrib.auth import authenticate
        self.user = authenticate(username=email, password=password)
        
        if not self.user:
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        # Generate tokens
        refresh = self.get_token(self.user)

        user_payload = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'phone_number': self.user.phone_number,
            'fullName': f"{self.user.first_name} {self.user.last_name}".strip(),
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

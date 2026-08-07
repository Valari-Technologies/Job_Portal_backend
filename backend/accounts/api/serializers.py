import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from ..models import CandidateProfile, HRProfile, Education, Experience, Resume, Skill, CandidateSkill

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
            'agreeToTerms'
        )

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

        validated_data['username'] = email
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
        return token

    def validate(self, attrs):
        email = attrs.get('email')
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

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "No account found with this email."})

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is inactive."})

        # Authenticate user
        from django.contrib.auth import authenticate
        self.user = authenticate(username=email, password=password)
        
        if not self.user:
            raise serializers.ValidationError({"detail": "Wrong password."})

        # Generate tokens
        refresh = self.get_token(self.user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'role': self.user.role,
                'phone_number': self.user.phone_number,
            }
        }
        return data


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

from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.signals import post_save
from django.dispatch import receiver


class Role(models.Model):
    """
    Lookup table for the ERD's ROLES entity.

    Note: ``User.role`` (a TextChoices CharField) remains the authoritative
    role for authentication, registration and JWT claims. This table exists as
    the normalized lookup shown in the ERD; it is deliberately not wired as a
    FK on User to avoid two sources of truth for the same value.
    """
    name = models.CharField(
        max_length=50,
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Department(models.Model):
    """
    Organisational department. HR profiles belong to one, jobs are posted
    against one.
    """
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Adopts the pre-existing (empty) accounts_departments table rather
        # than creating a second table for the same entity.
        db_table = 'accounts_departments'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Location(models.Model):
    class LocationType(models.TextChoices):
        STATE = "STATE", "State"
        DISTRICT = "DISTRICT", "District"
        CITY = "CITY", "City / Town"
        LOCALITY = "LOCALITY", "Locality"
        STATE_DISTRICT = "STATE_DISTRICT", "State District"

    name = models.CharField(max_length=100)
    location_type = models.CharField(
        max_length=50,
        choices=LocationType.choices,
        default=LocationType.CITY
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="children"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_path(self):
        parts = []
        curr = self
        visited = set()
        while curr and curr.id not in visited:
            visited.add(curr.id)
            parts.append(curr.name)
            curr = curr.parent
        return " -> ".join(reversed(parts))

    def get_state(self):
        curr = self
        visited = set()
        while curr and curr.id not in visited:
            visited.add(curr.id)
            if curr.location_type in [self.LocationType.STATE, self.LocationType.STATE_DISTRICT] or not curr.parent:
                return curr.name
            curr = curr.parent
        return None

    def get_district(self):
        curr = self
        visited = set()
        while curr and curr.id not in visited:
            visited.add(curr.id)
            if curr.location_type in [self.LocationType.DISTRICT, self.LocationType.STATE_DISTRICT]:
                return curr.name
            curr = curr.parent
        return None

    def __str__(self):
        return self.get_full_path()


class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="children"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'job categories'

    def __str__(self):
        return self.name


class WorkMode(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class EmploymentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if email:
            email = self.normalize_email(email).lower().strip()
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('role') != User.Role.SUPER_ADMIN:
            raise ValueError('Superuser must have role=SUPER_ADMIN.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        HR = "HR", "HR"
        CANDIDATE = "CANDIDATE", "Candidate"

    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        },
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CANDIDATE
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_users'
    )

    # Social sign-in bookkeeping (ERD: accounts.provider / provider_user_id).
    provider = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    provider_user_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"
        DELETED = "DELETED", "Deleted"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    is_mobile_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = CustomUserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'provider_user_id'],
                name='unique_provider_identity',
                condition=models.Q(provider__isnull=False) & models.Q(provider_user_id__isnull=False)
            )
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class UserRole(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role'],
                name='unique_user_role'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    email = models.EmailField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        default=User.Status.ACTIVE
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'admin'

    def __str__(self):
        return f"Admin Profile for {self.user.email}"



class CandidateProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate_profile"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    college = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    degree = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    graduation_year = models.IntegerField(
        blank=True,
        null=True
    )
    experience_total = models.IntegerField(
        default=0
    )
    profile_completed = models.BooleanField(
        default=False
    )
    dob = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    gender = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    address = models.TextField(
        blank=True,
        null=True
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    full_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    profile_photo = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='candidates'
    )
    expected_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    expected_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    preferred_job_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    preferred_work_mode = models.ForeignKey(
        WorkMode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='candidates'
    )
    profile_completion = models.IntegerField(
        default=0
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username}'s Candidate Profile"


class Education(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="educations"
    )
    college = models.CharField(
        max_length=150
    )
    degree = models.CharField(
        max_length=100
    )
    field_of_study = models.CharField(
        max_length=150
    )
    graduation_year = models.IntegerField()
    cgpa = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    education_level = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    qualification = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    institution = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    year_completed = models.IntegerField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.candidate.user.username}'s Education - {self.degree}"


class Experience(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="experiences"
    )
    company = models.CharField(
        max_length=150
    )
    designation = models.CharField(
        max_length=100
    )
    start_date = models.DateField()
    end_date = models.DateField(
        blank=True,
        null=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    job_title = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    company_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    experience_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    is_current = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.candidate.user.username}'s Experience at {self.company}"


class Resume(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="resumes"
    )
    # ERD types this as TEXT; FileField defaults to max_length=100, which real
    # upload paths (nested dirs + Django's uniquifying suffix) can exceed.
    file_path = models.FileField(
        upload_to="resumes/",
        max_length=500
    )
    file_name = models.CharField(
        max_length=255
    )
    is_default = models.BooleanField(
        default=False
    )
    file_url = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.candidate.user.username}'s Resume - {self.file_name}"


class Skill(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    category = models.ForeignKey(
        'JobCategory',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="skills"
    )
    is_active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class CandidateSkill(models.Model):
    class Proficiency(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="candidate_skills"
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="candidate_skills"
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=Proficiency.choices,
        default=Proficiency.BEGINNER
    )
    proficiency = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    years_experience = models.IntegerField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Candidate <-> Skill is many-to-many; one row per pair.
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'skill'],
                name='unique_candidate_skill'
            )
        ]

    def __str__(self):
        return f"{self.candidate.user.username}'s Skill - {self.skill.name} ({self.proficiency_level})"



class HRProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hr_profile"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="hr_profiles",
        blank=True,
        null=True
    )
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    company_website = models.URLField(
        blank=True,
        null=True
    )
    company_address = models.TextField(
        blank=True,
        null=True
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    company_description = models.TextField(
        blank=True,
        null=True
    )
    company_logo = models.TextField(
        blank=True,
        null=True
    )
    company_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    company_email = models.EmailField(
        blank=True,
        null=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='employers'
    )
    verification_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='UNSUBMITTED'
    )
    trust_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='NEW'
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def is_profile_complete(self):
        return bool(
            self.company_name and
            (self.company_phone or self.phone or self.company_email or (self.user and self.user.email)) and
            (self.company_description or self.company_address or self.location)
        )

    def __str__(self):
        return f"{self.user.username}'s HR Profile"


class Job(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        PUBLISHED = "PUBLISHED", "Published"
        REJECTED = "REJECTED", "Rejected"
        CLOSED = "CLOSED", "Closed"
        EXPIRED = "EXPIRED", "Expired"

    # PROTECT: removing an HR profile must not silently destroy their jobs,
    # the applications against them, or the activity audit trail. Jobs are
    # closed via `status`, and must be reassigned before an HR can be deleted.
    hr = models.ForeignKey(
        HRProfile,
        on_delete=models.PROTECT,
        related_name="jobs"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="jobs",
        blank=True,
        null=True
    )
    title = models.CharField(
        max_length=200
    )
    description = models.TextField()
    requirements = models.TextField(
        blank=True,
        null=True
    )
    employment_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    experience_required = models.IntegerField(
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="jobs"
    )
    responsibilities = models.TextField(
        blank=True,
        null=True
    )
    education_requirement = models.TextField(
        blank=True,
        null=True
    )
    experience_min = models.IntegerField(
        blank=True,
        null=True
    )
    experience_max = models.IntegerField(
        blank=True,
        null=True
    )
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    salary_period = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    work_mode = models.ForeignKey(
        WorkMode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="jobs"
    )
    application_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    application_deadline = models.DateField(
        blank=True,
        null=True
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True
    )
    closed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.title} ({self.status})"


class JobSkill(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_skills"
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="job_skills"
    )
    is_required = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        # Job <-> Skill is many-to-many; one row per pair.
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'skill'],
                name='unique_job_skill'
            )
        ]

    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview Scheduled"
        ACCEPTED = "ACCEPTED", "Accepted"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    # PROTECT: a job with applications against it cannot be deleted out from
    # under them -- close it instead (Job.Status.CLOSED).
    job = models.ForeignKey(
        Job,
        on_delete=models.PROTECT,
        related_name="applications"
    )
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED
    )
    applied_at = models.DateTimeField(
        auto_now_add=True
    )
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="applications"
    )
    application_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ('-applied_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_candidate_job_application'
            )
        ]

    def __str__(self):
        return f"{self.candidate.user.username} -> {self.job.title} ({self.status})"


class ApplicationActivity(models.Model):
    """Audit trail of status changes on an application."""

    class Action(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        REVIEWED = "REVIEWED", "Reviewed"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="activities"
    )
    # Optional acting user (dashed relationship in the ERD): the audit row
    # outlives the account that performed the action.
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="application_activities",
        blank=True,
        null=True
    )
    action = models.CharField(
        max_length=50,
        choices=Action.choices
    )
    performed_at = models.DateTimeField(
        auto_now_add=True
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('-performed_at',)
        verbose_name_plural = 'application activities'

    def __str__(self):
        return f"{self.action} on application #{self.application_id}"


class EmployerVerification(models.Model):
    class VerificationStatus(models.TextChoices):
        UNSUBMITTED = "UNSUBMITTED", "Unsubmitted"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    employer = models.ForeignKey(HRProfile, on_delete=models.CASCADE, related_name="verifications")
    verification_status = models.CharField(
        max_length=50,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNSUBMITTED
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_verifications")
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Verification for {self.employer.company_name} - {self.verification_status}"


class EmployerTrust(models.Model):
    class TrustLevel(models.TextChoices):
        NEW = "NEW", "New"
        BASIC = "BASIC", "Basic"
        TRUSTED = "TRUSTED", "Trusted"
        HIGH = "HIGH", "High"

    employer = models.OneToOneField(HRProfile, on_delete=models.CASCADE, related_name="trust")
    trust_level = models.CharField(
        max_length=50,
        choices=TrustLevel.choices,
        default=TrustLevel.NEW
    )
    jobs_posted = models.IntegerField(default=0)
    jobs_approved = models.IntegerField(default=0)
    jobs_rejected = models.IntegerField(default=0)
    trust_score = models.IntegerField(default=0)
    is_trusted = models.BooleanField(default=False)
    trusted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trust Profile for {self.employer.company_name} - {self.trust_level}"


class JobLocation(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_locations")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="job_locations")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'location'],
                name='unique_job_location'
            )
        ]

    def __str__(self):
        return f"{self.job.title} in {self.location.name}"


class JobEmploymentType(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_employment_types")
    employment_type = models.ForeignKey(EmploymentType, on_delete=models.CASCADE, related_name="job_employment_types")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'employment_type'],
                name='unique_job_employment_type'
            )
        ]

    def __str__(self):
        return f"{self.job.title} - {self.employment_type.name}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="changed_application_statuses")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'application status histories'

    def __str__(self):
        return f"History for app #{self.application_id} - {self.status}"


class Interview(models.Model):
    class InterviewType(models.TextChoices):
        IN_PERSON = "IN_PERSON", "In Person"
        ONLINE = "ONLINE", "Online"
        PHONE = "PHONE", "Phone"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"

    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="interviews")
    scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="scheduled_interviews")
    interview_type = models.CharField(max_length=50, choices=InterviewType.choices, default=InterviewType.ONLINE)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    meeting_link = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.SCHEDULED)
    result = models.CharField(max_length=50, choices=Result.choices, default=Result.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interview for Application #{self.application_id} - {self.status}"


class ApplicationMessage(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} on app #{self.application_id}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    message = models.TextField()
    reference_type = models.CharField(max_length=100, blank=True, null=True)
    reference_id = models.BigIntegerField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.title}"


class JobReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="reports")
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_reports")
    reason = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_job_reports")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on Job #{self.job_id} by {self.reported_by.username}"


class JobReview(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_reviews")
    action = models.CharField(max_length=100)
    reason = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review on Job #{self.job_id} by {self.reviewer.username}"


class SavedJob(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_saved_job'
            )
        ]

    def __str__(self):
        return f"{self.candidate.user.username} saved {self.job.title}"


class JobRecommendation(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="recommendations")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="recommendations")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_job_recommendation'
            )
        ]

    def __str__(self):
        return f"Recommendation for {self.candidate.user.username} - Job #{self.job_id}"


class CandidateActivity(models.Model):
    class ActivityType(models.TextChoices):
        SEARCH = "SEARCH", "Search"
        VIEW_JOB = "VIEW_JOB", "View Job"
        SAVE_JOB = "SAVE_JOB", "Save Job"
        APPLY_JOB = "APPLY_JOB", "Apply Job"
        VIEW_CATEGORY = "VIEW_CATEGORY", "View Category"

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True, related_name="candidate_activities")
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name="candidate_activities")
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, blank=True, null=True, related_name="candidate_activities")
    search_query = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'candidate activities'

    def __str__(self):
        return f"{self.candidate.user.username} - {self.activity_type}"


class AuditEvent(models.Model):
    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="audit_events"
    )
    actor_email = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    target_repr = models.CharField(max_length=255, blank=True, null=True)
    outcome = models.CharField(
        max_length=20,
        choices=Outcome.choices,
        default=Outcome.SUCCESS,
        db_index=True
    )
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ('-timestamp',)
        verbose_name_plural = 'audit events'

    def __str__(self):
        return f"[{self.timestamp}] {self.action} by {self.actor_email or 'System'} - {self.outcome}"


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    with transaction.atomic():
        if instance.role:
            role_obj, _ = Role.objects.get_or_create(
                name=instance.role,
                defaults={"description": f"{instance.get_role_display()} role"}
            )
            UserRole.objects.filter(user=instance).exclude(role=role_obj).delete()
            UserRole.objects.get_or_create(
                user=instance,
                role=role_obj
            )

        if instance.role == User.Role.HR:
            HRProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Role.CANDIDATE:
            CandidateProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Role.ADMIN:
            AdminProfile.objects.get_or_create(
                user=instance,
                defaults={
                    "name": f"{instance.first_name} {instance.last_name}".strip() or instance.email,
                    "email": instance.email,
                    "status": instance.status or User.Status.ACTIVE
                }
            )

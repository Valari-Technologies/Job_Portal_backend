from django.db import models
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


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        HR = "HR", "HR"
        CANDIDATE = "CANDIDATE", "Candidate"

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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username


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
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username}'s HR Profile"


class Job(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED = "CLOSED", "Closed"

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
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

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
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ('-applied_at',)

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


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.HR:
            HRProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Role.CANDIDATE:
            CandidateProfile.objects.get_or_create(user=instance)
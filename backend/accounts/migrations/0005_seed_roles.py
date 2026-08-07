from django.db import migrations


ROLES = [
    ("ADMIN", "Portal administrator with full access."),
    ("HR", "Recruiter who creates departments' jobs and reviews applications."),
    ("CANDIDATE", "Job seeker who maintains a profile and applies to jobs."),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for name, description in ROLES:
        Role.objects.get_or_create(
            name=name,
            defaults={"description": description}
        )


def unseed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(name__in=[name for name, _ in ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_application_applicationactivity_department_job_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]

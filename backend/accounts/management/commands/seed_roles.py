from django.core.management.base import BaseCommand
from accounts.models import Role, User


class Command(BaseCommand):
    help = "Seed initial roles into the lookup table idempotently."

    def handle(self, *args, **options):
        roles_data = [
            (User.Role.SUPER_ADMIN, "Super Administrator with highest privileges"),
            (User.Role.ADMIN, "Portal administrator with full access."),
            (User.Role.HR, "Recruiter who creates departments' jobs and reviews applications."),
            (User.Role.CANDIDATE, "Job seeker who maintains a profile and applies to jobs."),
        ]
        created_count = 0
        for name, description in roles_data:
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={"description": description}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created role: {name}"))
            else:
                self.stdout.write(f"Role already exists: {name}")

        self.stdout.write(self.style.SUCCESS(f"Role seeding completed ({created_count} created)."))

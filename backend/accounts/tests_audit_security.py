from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import AuditEvent, Role, UserRole
from accounts.services.audit_service import log_audit_event

User = get_user_model()


class AuditSecurityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Super Admin
        self.super_admin = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password="SuperPassword123!",
            role=User.Role.SUPER_ADMIN,
        )

        # Admin
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword123!",
            role=User.Role.ADMIN,
            created_by=self.super_admin
        )

        # HR
        self.hr_user = User.objects.create_user(
            username="hruser",
            email="hr@example.com",
            password="HrPassword123!",
            role=User.Role.HR,
            created_by=self.super_admin
        )

        # Candidate
        self.candidate_user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="CandidatePassword123!",
            role=User.Role.CANDIDATE,
        )

    def test_permission_enforcement(self):
        """Verify only active Super Admin can access audit & security APIs."""
        urls = [
            "/accounts/admin/audit-events/",
            "/accounts/admin/security-posture/",
            "/accounts/admin/access-reviews/",
        ]

        # Anonymous access denied
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Candidate access denied (403)
        self.client.force_authenticate(user=self.candidate_user)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # HR access denied (403)
        self.client.force_authenticate(user=self.hr_user)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin access denied (403)
        self.client.force_authenticate(user=self.admin_user)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Super Admin access granted (200)
        self.client.force_authenticate(user=self.super_admin)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_logging_on_login_and_creation(self):
        """Verify audit events are created on user creation and login."""
        # Test creation logging by super admin creating HR account
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "email": "newhr@example.com",
            "password": "NewHrPassword123!",
            "full_name": "New HR",
            "role": "HR",
            "company_name": "Test Company"
        }
        create_res = self.client.post("/accounts/admin/create-user/", payload, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        event = AuditEvent.objects.filter(action="USER_CREATE", target_repr__contains="newhr@example.com").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.actor, self.super_admin)
        self.assertEqual(event.outcome, "SUCCESS")

        # Test login success logging
        self.client.logout()
        login_res = self.client.post("/accounts/login/", {"email": "superadmin@example.com", "password": "SuperPassword123!"})
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)

        login_event = AuditEvent.objects.filter(action="LOGIN_SUCCESS", actor_email="superadmin@example.com").first()
        self.assertIsNotNone(login_event)

        # Test login failed logging
        fail_res = self.client.post("/accounts/login/", {"email": "superadmin@example.com", "password": "WrongPassword!"})
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)

        fail_event = AuditEvent.objects.filter(action="LOGIN_FAILED", actor_email="superadmin@example.com").first()
        self.assertIsNotNone(fail_event)
        self.assertEqual(fail_event.outcome, "FAILED")

    def test_secret_redaction(self):
        """Verify secrets are never saved in audit logs."""
        log_audit_event(
            actor=self.super_admin,
            action="TEST_ACTION",
            outcome="SUCCESS",
            description="Created user with email user@test.com",
        )
        event = AuditEvent.objects.filter(action="TEST_ACTION").first()
        self.assertNotIn("SuperPassword123!", event.description)
        self.assertNotIn("password", event.description.lower())

    def test_audit_event_filtering(self):
        """Verify filtering audit events by action and outcome."""
        log_audit_event(actor=self.super_admin, action="ACTION_A", outcome="SUCCESS", description="A success")
        log_audit_event(actor=self.super_admin, action="ACTION_B", outcome="FAILED", description="B failure")

        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get("/accounts/admin/audit-events/?action=ACTION_A")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["action"], "ACTION_A")

    def test_security_posture_view(self):
        """Verify Security Posture endpoint returns truthful metrics."""
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get("/accounts/admin/security-posture/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        self.assertIn("accounts_summary", data)
        self.assertIn("auth_controls", data)
        self.assertEqual(data["auth_controls"]["session_revocation"], "Stateless JWT (Not configured)")
        self.assertEqual(data["auth_controls"]["mfa_status"], "Not configured")

    def test_access_reviews_view(self):
        """Verify Access Reviews list privileged accounts accurately."""
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get("/accounts/admin/access-reviews/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        emails = [u["email"] for u in results]
        self.assertIn("superadmin@example.com", emails)
        self.assertIn("admin@example.com", emails)
        self.assertIn("hr@example.com", emails)
        self.assertNotIn("candidate@example.com", emails)

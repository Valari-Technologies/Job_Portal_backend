from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Role, UserRole, CandidateProfile, HRProfile, AdminProfile


class SuperAdminToAdminCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="superadmin@example.com", password="SuperPassword123!"
        )
        self.admin_user = User.objects.create_user(
            username="normaladmin", email="normaladmin@example.com", password="AdminPassword123!", role=User.Role.ADMIN
        )
        self.hr_user = User.objects.create_user(
            username="hruser", email="hr@example.com", password="HrPassword123!", role=User.Role.HR
        )
        self.candidate_user = User.objects.create_user(
            username="canduser", email="cand@example.com", password="CandPassword123!", role=User.Role.CANDIDATE
        )
        self.create_url = reverse('admin_create_user')
        self.login_url = reverse('token_obtain_pair')

    def test_24_super_admin_creates_admin_with_hashed_password_and_admin_profile(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "name": "Jane Admin",
            "email": "janeadmin@example.com",
            "password": "StrongPassword123!",
            "confirmPassword": "StrongPassword123!",
            "status": "ACTIVE"
        }
        res = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data.get("user", {}))
        self.assertNotIn("access", res.data.get("user", {}))

        new_admin = User.objects.get(email="janeadmin@example.com")
        self.assertEqual(new_admin.role, User.Role.ADMIN)
        self.assertEqual(new_admin.status, User.Status.ACTIVE)
        self.assertNotEqual(new_admin.password, "StrongPassword123!")
        self.assertTrue(new_admin.check_password("StrongPassword123!"))

        # Verify AdminProfile in db_table='admin'
        self.assertTrue(AdminProfile.objects.filter(user=new_admin).exists())
        admin_prof = AdminProfile.objects.get(user=new_admin)
        self.assertEqual(admin_prof.name, "Jane Admin")
        self.assertEqual(admin_prof.email, "janeadmin@example.com")

        # Verify UserRole mapping
        role_obj = Role.objects.get(name=User.Role.ADMIN)
        self.assertTrue(UserRole.objects.filter(user=new_admin, role=role_obj).exists())

    def test_25_admin_creation_fails_for_anonymous_or_unauthorized_users(self):
        payload = {
            "name": "Rogue Admin",
            "email": "rogue@example.com",
            "password": "StrongPassword123!",
            "status": "ACTIVE"
        }
        # Anonymous
        res_anon = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Normal Admin
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)

        # HR
        self.client.force_authenticate(user=self.hr_user)
        res_hr = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res_hr.status_code, status.HTTP_403_FORBIDDEN)

        # Candidate
        self.client.force_authenticate(user=self.candidate_user)
        res_cand = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(res_cand.status_code, status.HTTP_403_FORBIDDEN)

    def test_26_admin_creation_status_and_duplicate_email(self):
        self.client.force_authenticate(user=self.superadmin)
        payload1 = {
            "name": "Inactive Admin",
            "email": "inactiveadmin@example.com",
            "password": "StrongPassword123!",
            "confirmPassword": "StrongPassword123!",
            "status": "INACTIVE"
        }
        res1 = self.client.post(self.create_url, payload1, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        inactive_admin = User.objects.get(email="inactiveadmin@example.com")
        self.assertEqual(inactive_admin.status, User.Status.INACTIVE)

        # Duplicate email
        payload_dup = {
            "name": "Duplicate Admin",
            "email": "inactiveadmin@example.com",
            "password": "StrongPassword123!",
            "confirmPassword": "StrongPassword123!",
            "status": "ACTIVE"
        }
        res_dup = self.client.post(self.create_url, payload_dup, format='json')
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_27_created_admin_can_login_when_active_and_blocked_when_inactive(self):
        # Create active admin
        self.client.force_authenticate(user=self.superadmin)
        payload_active = {
            "name": "Active Login Admin",
            "email": "activeadminlogin@example.com",
            "password": "AdminLoginPass123!",
            "confirmPassword": "AdminLoginPass123!",
            "status": "ACTIVE"
        }
        self.client.post(self.create_url, payload_active, format='json')

        # Create inactive admin
        payload_inactive = {
            "name": "Inactive Login Admin",
            "email": "inactiveadminlogin@example.com",
            "password": "AdminLoginPass123!",
            "confirmPassword": "AdminLoginPass123!",
            "status": "INACTIVE"
        }
        self.client.post(self.create_url, payload_inactive, format='json')

        # Login active admin
        self.client.logout()
        res_active = self.client.post(
            self.login_url,
            {"email": "activeadminlogin@example.com", "password": "AdminLoginPass123!"},
            format='json'
        )
        self.assertEqual(res_active.status_code, status.HTTP_200_OK)
        self.assertIn("access", res_active.data)
        self.assertEqual(res_active.data["user"]["role"], User.Role.ADMIN)

        # Login inactive admin
        res_inactive = self.client.post(
            self.login_url,
            {"email": "inactiveadminlogin@example.com", "password": "AdminLoginPass123!"},
            format='json'
        )
        self.assertEqual(res_inactive.status_code, status.HTTP_400_BAD_REQUEST)


User = get_user_model()


class SuperUserAndRoleFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_01_superuser_creation_gives_super_admin(self):
        user = User.objects.create_superuser(username="superadmin", email="superadmin@example.com", password="SuperPassword123!")
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)

    def test_02_superuser_has_is_staff_true(self):
        user = User.objects.create_superuser(username="superadmin", email="superadmin@example.com", password="SuperPassword123!")
        self.assertTrue(user.is_staff)

    def test_03_superuser_has_is_superuser_true(self):
        user = User.objects.create_superuser(username="superadmin", email="superadmin@example.com", password="SuperPassword123!")
        self.assertTrue(user.is_superuser)

    def test_04_superuser_password_is_hashed(self):
        password = "SuperPassword123!"
        user = User.objects.create_superuser(username="superadmin", email="superadmin@example.com", password=password)
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))

    def test_05_matching_role_and_user_role_rows_created(self):
        user = User.objects.create_superuser(username="superadmin", email="superadmin@example.com", password="SuperPassword123!")
        role_obj = Role.objects.get(name=User.Role.SUPER_ADMIN)
        self.assertTrue(UserRole.objects.filter(user=user, role=role_obj).exists())


class CandidateRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register_candidate')

    def test_06_public_signup_always_creates_candidate(self):
        payload = {
            "fullName": "Test Candidate",
            "email": "candidate@example.com",
            "phoneNumber": "9876543210",
            "password": "Password123!",
            "confirmPassword": "Password123!",
            "agreeToTerms": True
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="candidate@example.com")
        self.assertEqual(user.role, User.Role.CANDIDATE)

    def test_07_public_signup_cannot_create_admin(self):
        payload = {
            "fullName": "Fake Admin",
            "email": "fakeadmin@example.com",
            "phoneNumber": "9876543210",
            "password": "Password123!",
            "confirmPassword": "Password123!",
            "agreeToTerms": True,
            "role": "ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_08_public_signup_cannot_create_hr(self):
        payload = {
            "fullName": "Fake HR",
            "email": "fakehr@example.com",
            "phoneNumber": "9876543210",
            "password": "Password123!",
            "confirmPassword": "Password123!",
            "agreeToTerms": True,
            "role": "HR"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_09_public_signup_cannot_create_super_admin(self):
        payload = {
            "fullName": "Fake SuperAdmin",
            "email": "fakesuper@example.com",
            "phoneNumber": "9876543210",
            "password": "Password123!",
            "confirmPassword": "Password123!",
            "agreeToTerms": True,
            "role": "SUPER_ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivilegedAccountCreationAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="superadmin@example.com", password="SuperPassword123!"
        )
        self.admin = User.objects.create_user(
            username="adminuser", email="admin@example.com", password="Password123!", role=User.Role.ADMIN
        )
        self.hr = User.objects.create_user(
            username="hruser", email="hr@example.com", password="Password123!", role=User.Role.HR
        )
        self.candidate = User.objects.create_user(
            username="candidateuser", email="cand@example.com", password="Password123!", role=User.Role.CANDIDATE
        )
        self.url = reverse('admin_create_user')

    def test_10_only_super_admin_can_create_admin(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "email": "newadmin@example.com",
            "password": "Password123!",
            "first_name": "New",
            "last_name": "Admin",
            "role": "ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_admin = User.objects.get(email="newadmin@example.com")
        self.assertEqual(new_admin.role, User.Role.ADMIN)

    def test_11_only_super_admin_can_create_hr(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "email": "newhr@example.com",
            "password": "Password123!",
            "first_name": "New",
            "last_name": "HR",
            "role": "HR"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_hr = User.objects.get(email="newhr@example.com")
        self.assertEqual(new_hr.role, User.Role.HR)

    def test_12_admin_cannot_create_super_admin(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "email": "trysuper@example.com",
            "password": "Password123!",
            "role": "SUPER_ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_hr_cannot_create_admin(self):
        self.client.force_authenticate(user=self.hr)
        payload = {
            "email": "tryadmin@example.com",
            "password": "Password123!",
            "role": "ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_14_candidate_cannot_create_admin_or_hr(self):
        self.client.force_authenticate(user=self.candidate)
        payload = {
            "email": "tryadmin2@example.com",
            "password": "Password123!",
            "role": "ADMIN"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class LoginAndSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('token_obtain_pair')
        self.active_user = User.objects.create_user(
            username="activeuser", email="active@example.com", password="Password123!", role=User.Role.CANDIDATE, status=User.Status.ACTIVE
        )
        self.suspended_user = User.objects.create_user(
            username="suspendeduser", email="suspended@example.com", password="Password123!", role=User.Role.CANDIDATE, status=User.Status.SUSPENDED
        )
        self.deleted_user = User.objects.create_user(
            username="deleteduser", email="deleted@example.com", password="Password123!", role=User.Role.CANDIDATE, status=User.Status.DELETED
        )

    def test_15_suspended_users_cannot_log_in(self):
        res = self.client.post(self.login_url, {"email": "suspended@example.com", "password": "Password123!"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_16_deleted_users_cannot_log_in(self):
        res = self.client.post(self.login_url, {"email": "deleted@example.com", "password": "Password123!"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_17_duplicate_email_is_rejected(self):
        with self.assertRaises(Exception):
            User.objects.create_user(username="dupuser", email="active@example.com", password="Password123!")

    def test_18_duplicate_google_provider_identity_is_rejected(self):
        User.objects.create_user(username="guser1", email="g1@example.com", password="Password123!", provider="GOOGLE", provider_user_id="123456789")
        with self.assertRaises(Exception):
            User.objects.create_user(username="guser2", email="g2@example.com", password="Password123!", provider="GOOGLE", provider_user_id="123456789")

    def test_19_jwt_login_returns_backend_role(self):
        res = self.client.post(self.login_url, {"email": "active@example.com", "password": "Password123!"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertEqual(res.data["user"]["role"], User.Role.CANDIDATE)


class ProfileRulesAndGoogleAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_20_google_authentication_never_creates_a_privileged_role(self):
        user = User.objects.create_user(
            username="googledemo",
            email="gdemo@example.com",
            role=User.Role.CANDIDATE,
            provider="GOOGLE",
            provider_user_id="999888777"
        )
        self.assertEqual(user.role, User.Role.CANDIDATE)
        self.assertNotEqual(user.role, User.Role.ADMIN)
        self.assertNotEqual(user.role, User.Role.SUPER_ADMIN)

    def test_21_hr_profile_is_created_only_for_hr(self):
        hr_user = User.objects.create_user(username="hr1", email="hr1@example.com", password="Password123!", role=User.Role.HR)
        self.assertTrue(HRProfile.objects.filter(user=hr_user).exists())
        self.assertFalse(CandidateProfile.objects.filter(user=hr_user).exists())

    def test_22_candidate_profile_is_created_only_for_candidate(self):
        cand_user = User.objects.create_user(username="cand1", email="cand1@example.com", password="Password123!", role=User.Role.CANDIDATE)
        self.assertTrue(CandidateProfile.objects.filter(user=cand_user).exists())
        self.assertFalse(HRProfile.objects.filter(user=cand_user).exists())

    def test_23_super_admin_does_not_receive_a_candidate_or_hr_profile(self):
        super_user = User.objects.create_superuser(username="super1", email="super1@example.com", password="SuperPassword123!")
        self.assertFalse(CandidateProfile.objects.filter(user=super_user).exists())
        self.assertFalse(HRProfile.objects.filter(user=super_user).exists())


class AdminListAndCurrentMeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="superadmin@example.com", password="SuperPassword123!"
        )
        self.admin1 = User.objects.create_user(
            username="admin1", email="admin1@example.com", password="Password123!", role=User.Role.ADMIN, first_name="Alice", last_name="Admin"
        )
        self.admin2 = User.objects.create_user(
            username="admin2", email="admin2@example.com", password="Password123!", role=User.Role.ADMIN, first_name="Bob", last_name="Admin"
        )
        self.hr = User.objects.create_user(
            username="hruser", email="hr@example.com", password="Password123!", role=User.Role.HR
        )
        self.candidate = User.objects.create_user(
            username="canduser", email="cand@example.com", password="Password123!", role=User.Role.CANDIDATE
        )
        self.admins_url = reverse('admin_list')
        self.me_url = reverse('current_user_me')

    def test_28_super_admin_can_fetch_admin_list(self):
        self.client.force_authenticate(user=self.superadmin)
        res = self.client.get(self.admins_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        emails = [item['email'] for item in data]
        
        self.assertIn("admin1@example.com", emails)
        self.assertIn("admin2@example.com", emails)
        self.assertNotIn("superadmin@example.com", emails)
        self.assertNotIn("hr@example.com", emails)
        self.assertNotIn("cand@example.com", emails)

    def test_29_admin_list_access_denied_for_non_super_admins(self):
        # Anonymous
        res_anon = self.client.get(self.admins_url)
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Normal Admin
        self.client.force_authenticate(user=self.admin1)
        res_admin = self.client.get(self.admins_url)
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)

        # HR
        self.client.force_authenticate(user=self.hr)
        res_hr = self.client.get(self.admins_url)
        self.assertEqual(res_hr.status_code, status.HTTP_403_FORBIDDEN)

        # Candidate
        self.client.force_authenticate(user=self.candidate)
        res_cand = self.client.get(self.admins_url)
        self.assertEqual(res_cand.status_code, status.HTTP_403_FORBIDDEN)

    def test_30_current_user_me_endpoint_returns_authenticated_identity(self):
        self.client.force_authenticate(user=self.admin1)
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "admin1@example.com")
        self.assertEqual(res.data["role"], User.Role.ADMIN)
        self.assertEqual(res.data["name"], "Alice Admin")
        self.assertNotIn("password", res.data)


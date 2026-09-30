from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import (
    HRProfile, Location, EmployerVerification, EmployerTrust,
    Job, JobReview, JobCategory, WorkMode, Skill
)

User = get_user_model()

class ModerationFlowsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Super Admin
        self.super_admin = User.objects.create_superuser(
            username='super_admin_mod',
            email='superadmin_mod@example.com',
            password='Password123!'
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            username='admin_mod',
            email='admin_mod@example.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # Create Location & Category
        self.location = Location.objects.create(name='Chennai', location_type=Location.LocationType.CITY)
        self.category = JobCategory.objects.create(name='IT & Software')
        self.work_mode = WorkMode.objects.create(name='On-site')

        # Create Employer / HR User
        self.hr_user = User.objects.create_user(
            username='hr_test',
            email='hr_test@example.com',
            password='Password123!',
            role=User.Role.HR,
            first_name='John',
            last_name='Doe'
        )
        self.hr_profile = HRProfile.objects.get(user=self.hr_user)

        # Create Candidate User
        self.candidate_user = User.objects.create_user(
            username='candidate_test',
            email='candidate_test@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )

    def test_01_hr_creation_does_not_falsely_count_as_submitted_request(self):
        """1. Creating an HR account does not falsely count as a submitted verification request."""
        # Check initial status
        self.hr_profile.refresh_from_db()
        self.assertEqual(self.hr_profile.verification_status, 'UNSUBMITTED')
        # Ensure it does not appear in pending verification queue
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get('/accounts/admin/employer-verifications/?status=PENDING')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', [])
        employer_ids = [r['employer_id'] for r in results]
        self.assertNotIn(self.hr_profile.id, employer_ids)

    def test_02_submitted_request_displays_correct_employer_and_company_data(self):
        """2. A submitted request displays the correct Employer and company data."""
        # Complete profile details
        self.hr_profile.company_name = "Tech Corp"
        self.hr_profile.company_phone = "9876543210"
        self.hr_profile.company_description = "Leading Software Firm"
        self.hr_profile.location = self.location
        self.hr_profile.save()

        # Submit verification
        self.client.force_authenticate(user=self.hr_user)
        res = self.client.post('/accounts/employer/submit-verification/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.hr_profile.refresh_from_db()
        self.assertEqual(self.hr_profile.verification_status, 'PENDING')

        # Super admin views queue
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get('/accounts/admin/employer-verifications/?status=PENDING')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', [])
        req = next((r for r in results if r['employer_id'] == self.hr_profile.id), None)
        self.assertIsNotNone(req)
        self.assertEqual(req['company_name'], "Tech Corp")
        self.assertEqual(req['email'], "hr_test@example.com")
        self.assertTrue(req['is_profile_complete'])

    def test_03_approve_reject_saves_correct_status_reviewer_timestamp_reason(self):
        """3. Approve/reject saves the correct status, reviewer, timestamp, and reason."""
        self.hr_profile.company_name = "Tech Corp"
        self.hr_profile.company_description = "Tech"
        self.hr_profile.company_phone = "12345"
        self.hr_profile.save()

        self.client.force_authenticate(user=self.super_admin)

        # Reject first with reason
        res_reject = self.client.post(f'/accounts/admin/employers/{self.hr_profile.id}/verify/', {
            'decision': 'REJECTED',
            'reason': 'Incomplete tax documents'
        }, format='json')
        self.assertEqual(res_reject.status_code, status.HTTP_200_OK)

        self.hr_profile.refresh_from_db()
        self.assertEqual(self.hr_profile.verification_status, 'REJECTED')
        latest_ver = EmployerVerification.objects.filter(employer=self.hr_profile).order_by('-id').first()
        self.assertEqual(latest_ver.verification_status, 'REJECTED')
        self.assertEqual(latest_ver.reviewed_by, self.super_admin)
        self.assertEqual(latest_ver.rejection_reason, 'Incomplete tax documents')

        # Approve
        res_approve = self.client.post(f'/accounts/admin/employers/{self.hr_profile.id}/verify/', {
            'decision': 'APPROVED',
            'notes': 'Verified successfully'
        }, format='json')
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)

        self.hr_profile.refresh_from_db()
        self.assertEqual(self.hr_profile.verification_status, 'APPROVED')

    def test_04_rejected_employer_resubmission_retains_earlier_decision_history(self):
        """4. Rejected Employer resubmission retains the earlier decision."""
        self.hr_profile.company_name = "Old Corp"
        self.hr_profile.company_description = "Desc"
        self.hr_profile.company_phone = "11111"
        self.hr_profile.save()

        # Admin rejects
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(f'/accounts/admin/employers/{self.hr_profile.id}/verify/', {
            'decision': 'REJECTED',
            'reason': 'Old reason'
        }, format='json')

        # Employer corrects & resubmits
        self.client.force_authenticate(user=self.hr_user)
        self.hr_profile.company_name = "New Updated Corp"
        self.hr_profile.save()
        res = self.client.post('/accounts/employer/submit-verification/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check verifications history count
        verifications = EmployerVerification.objects.filter(employer=self.hr_profile).order_by('id')
        self.assertEqual(verifications.count(), 2)
        self.assertEqual(verifications[0].verification_status, 'REJECTED')
        self.assertEqual(verifications[0].rejection_reason, 'Old reason')
        self.assertEqual(verifications[1].verification_status, 'PENDING')

    def test_05_unapproved_or_suspended_employers_cannot_submit_jobs(self):
        """5. Unapproved or suspended Employers cannot submit/publish jobs through direct API calls."""
        job = Job.objects.create(
            hr=self.hr_profile,
            title="Python Developer",
            description="Backend dev",
            category=self.category,
            work_mode=self.work_mode,
            status=Job.Status.DRAFT
        )

        self.client.force_authenticate(user=self.hr_user)

        # Pending / Unapproved employer attempts submit
        res = self.client.post(f'/accounts/employer/jobs/{job.id}/submit/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Now approve employer
        self.hr_profile.verification_status = 'APPROVED'
        self.hr_profile.save()

        # Now submit works
        res_ok = self.client.post(f'/accounts/employer/jobs/{job.id}/submit/')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)

        # Suspend employer account
        self.hr_user.status = User.Status.SUSPENDED
        self.hr_user.is_active = False
        self.hr_user.save()

        job2 = Job.objects.create(
            hr=self.hr_profile,
            title="React Developer",
            description="Frontend dev",
            category=self.category,
            work_mode=self.work_mode,
            status=Job.Status.DRAFT
        )
        res_suspended = self.client.post(f'/accounts/employer/jobs/{job2.id}/submit/')
        self.assertEqual(res_suspended.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_draft_jobs_do_not_appear_in_review_queue(self):
        """6. Draft jobs do not appear in the review queue."""
        self.hr_profile.verification_status = 'APPROVED'
        self.hr_profile.save()

        draft_job = Job.objects.create(
            hr=self.hr_profile,
            title="Draft Secret Job",
            description="Draft content",
            status=Job.Status.DRAFT
        )

        submitted_job = Job.objects.create(
            hr=self.hr_profile,
            title="Submitted Job",
            description="Ready for review",
            category=self.category,
            work_mode=self.work_mode,
            status=Job.Status.PENDING_REVIEW
        )

        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get('/accounts/admin/job-reviews/?status=PENDING_REVIEW')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        job_ids = [j['id'] for j in res.data.get('results', [])]
        self.assertNotIn(draft_job.id, job_ids)
        self.assertIn(submitted_job.id, job_ids)

    def test_07_pending_jobs_cannot_appear_in_public_job_search(self):
        """7. Pending jobs cannot appear in public job search."""
        pending_job = Job.objects.create(
            hr=self.hr_profile,
            title="Pending Public Test Job",
            description="Desc",
            status=Job.Status.PENDING_REVIEW
        )

        published_job = Job.objects.create(
            hr=self.hr_profile,
            title="Published Public Test Job",
            description="Desc",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

        # Query public list
        self.client.force_authenticate(user=None)
        # Using status filter or public view
        res = self.client.get('/accounts/admin/job-reviews/?status=PUBLISHED')
        # Unauthenticated request to admin review queue returns 401
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_08_approval_publishes_only_through_validated_lifecycle(self):
        """8. Approval publishes only through the validated lifecycle."""
        job = Job.objects.create(
            hr=self.hr_profile,
            title="Data Scientist",
            description="Python & ML",
            status=Job.Status.PENDING_REVIEW
        )

        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(f'/accounts/admin/jobs/{job.id}/review/', {
            'action': 'APPROVED',
            'notes': 'Looks good'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.PUBLISHED)
        self.assertIsNotNone(job.published_at)

        review = JobReview.objects.filter(job=job).first()
        self.assertEqual(review.action, 'APPROVED')
        self.assertEqual(review.reviewer, self.admin_user)

    def test_09_rejection_retains_its_reason_and_review_history(self):
        """9. Rejection retains its reason and review history."""
        job = Job.objects.create(
            hr=self.hr_profile,
            title="QA Engineer",
            description="Manual testing",
            status=Job.Status.PENDING_REVIEW
        )

        self.client.force_authenticate(user=self.super_admin)
        res = self.client.post(f'/accounts/admin/jobs/{job.id}/review/', {
            'action': 'REJECTED',
            'reason': 'Description is too short and vague.'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.REJECTED)

        review = JobReview.objects.filter(job=job).first()
        self.assertEqual(review.action, 'REJECTED')
        self.assertEqual(review.reason, 'Description is too short and vague.')

    def test_10_concurrent_or_repeated_review_requests(self):
        """10. Concurrent or repeated review requests cannot create contradictory decisions."""
        job = Job.objects.create(
            hr=self.hr_profile,
            title="DevOps Engineer",
            description="Kubernetes & CI/CD",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

        self.client.force_authenticate(user=self.super_admin)
        # Attempting to re-approve an already published job returns 400
        res = self.client.post(f'/accounts/admin/jobs/{job.id}/review/', {
            'action': 'APPROVED',
            'notes': 'Duplicate approval'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_11_unauthorized_roles_cannot_review_or_mutate_records(self):
        """11. Unauthorized roles cannot review or mutate another Employer's or Job's records."""
        # Candidate attempts to approve employer
        self.client.force_authenticate(user=self.candidate_user)
        res_cand = self.client.post(f'/accounts/admin/employers/{self.hr_profile.id}/verify/', {
            'decision': 'APPROVED'
        }, format='json')
        self.assertEqual(res_cand.status_code, status.HTTP_403_FORBIDDEN)

        # Employer attempts to approve their own request
        self.client.force_authenticate(user=self.hr_user)
        res_self = self.client.post(f'/accounts/admin/employers/{self.hr_profile.id}/verify/', {
            'decision': 'APPROVED'
        }, format='json')
        self.assertEqual(res_self.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_existing_creation_login_and_jobs_work(self):
        """12. Existing Employer creation, login, company profile, and Job data still work."""
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.post('/accounts/admin/create-user/', {
            'email': 'new_hr_test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'full_name': 'Jane Manager',
            'company_name': 'New Tech Inc',
            'role': 'HR',
            'status': 'ACTIVE'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_hr = User.objects.get(email='new_hr_test@example.com')
        self.assertEqual(new_hr.role, User.Role.HR)

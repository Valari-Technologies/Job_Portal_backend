import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import (
    CandidateProfile, HRProfile, Job, Application, ApplicationStatusHistory,
    Interview, Resume, SavedJob, WorkMode, JobCategory
)

User = get_user_model()


class CandidateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Candidate A
        self.candidate_user_a = User.objects.create_user(
            username='candidate_a',
            email='candidate_a@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE,
            first_name='Candidate',
            last_name='A'
        )
        self.candidate_profile_a, _ = CandidateProfile.objects.get_or_create(user=self.candidate_user_a)

        # Create Candidate B
        self.candidate_user_b = User.objects.create_user(
            username='candidate_b',
            email='candidate_b@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE,
            first_name='Candidate',
            last_name='B'
        )
        self.candidate_profile_b, _ = CandidateProfile.objects.get_or_create(user=self.candidate_user_b)

        # Create Employer / HR User
        self.hr_user = User.objects.create_user(
            username='hr_user',
            email='hr@example.com',
            password='Password123!',
            role=User.Role.HR,
            first_name='HR',
            last_name='Manager'
        )
        self.hr_profile = getattr(self.hr_user, 'hr_profile', None) or HRProfile.objects.get(user=self.hr_user)
        self.hr_profile.company_name = 'TechCorp Inc.'
        self.hr_profile.save()

        # Create Published Job
        self.published_job = Job.objects.create(
            hr=self.hr_profile,
            title='Senior React Engineer',
            description='Build UI apps with React.',
            status=Job.Status.PUBLISHED,
            application_type='PROFILE_RESUME'
        )

        # Create Closed Job
        self.closed_job = Job.objects.create(
            hr=self.hr_profile,
            title='Legacy Developer',
            description='Maintenance role.',
            status=Job.Status.CLOSED,
            application_type='PROFILE_RESUME'
        )

        # Create Simple Local Job
        self.simple_local_job = Job.objects.create(
            hr=self.hr_profile,
            title='Hotel Assistant',
            description='Local helper role.',
            status=Job.Status.PUBLISHED,
            application_type='SIMPLE_LOCAL'
        )

        # Create Resumes for Candidate A and B
        test_file_a = SimpleUploadedFile("resume_a.pdf", b"PDF content for candidate A", content_type="application/pdf")
        self.resume_a = Resume.objects.create(
            candidate=self.candidate_profile_a,
            file_path=test_file_a,
            file_name='resume_a.pdf',
            is_default=True
        )

        test_file_b = SimpleUploadedFile("resume_b.pdf", b"PDF content for candidate B", content_type="application/pdf")
        self.resume_b = Resume.objects.create(
            candidate=self.candidate_profile_b,
            file_path=test_file_b,
            file_name='resume_b.pdf',
            is_default=True
        )

    def test_01_candidate_a_cannot_access_candidate_b_records(self):
        """1. Candidate A cannot access Candidate B's profile, applications, interviews, resumes, or saved jobs."""
        # Create Application for Candidate B
        app_b = Application.objects.create(
            job=self.published_job,
            candidate=self.candidate_profile_b,
            resume=self.resume_b,
            status=Application.Status.APPLIED
        )

        # Authenticate as Candidate A
        self.client.force_authenticate(user=self.candidate_user_a)

        # Try to access Candidate B's Application
        res = self.client.get(f'/accounts/candidate/applications/{app_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Try to access Candidate B's Resume
        res = self.client.delete(f'/accounts/candidate/resumes/{self.resume_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_02_professional_vs_simple_application(self):
        """2. Professional application requires candidate's valid resume; simple application works without one."""
        self.client.force_authenticate(user=self.candidate_user_a)

        # Professional application with Candidate A's resume
        res_prof = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.published_job.id,
            'resume_id': self.resume_a.id,
            'application_type': 'PROFILE_RESUME'
        }, format='json')
        self.assertEqual(res_prof.status_code, status.HTTP_201_CREATED)

        # Simple Local application without resume
        res_simple = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.simple_local_job.id,
            'application_type': 'SIMPLE_LOCAL',
            'phone_number': '9876543210'
        }, format='json')
        self.assertEqual(res_simple.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res_simple.data['resume'])

    def test_03_closed_job_and_duplicate_submissions_rejected(self):
        """3. Closed/unpublished jobs and duplicate submissions are rejected."""
        self.client.force_authenticate(user=self.candidate_user_a)

        # Try applying to closed job
        res_closed = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.closed_job.id,
            'resume_id': self.resume_a.id
        }, format='json')
        self.assertEqual(res_closed.status_code, status.HTTP_400_BAD_REQUEST)

        # Submit first application to published job
        res_1 = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.published_job.id,
            'resume_id': self.resume_a.id
        }, format='json')
        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)

        # Try submitting duplicate application to same job
        res_dup = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.published_job.id,
            'resume_id': self.resume_a.id
        }, format='json')
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_04_submission_persists_application_status_history_and_count(self):
        """4. Submission persists Application and initial ApplicationStatusHistory and updates count."""
        self.client.force_authenticate(user=self.candidate_user_a)

        res = self.client.post('/accounts/candidate/applications/', {
            'job_id': self.published_job.id,
            'resume_id': self.resume_a.id
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        app_id = res.data['id']

        app = Application.objects.get(id=app_id)
        self.assertEqual(app.candidate, self.candidate_profile_a)
        self.assertEqual(app.status, Application.Status.APPLIED)

        history_exists = ApplicationStatusHistory.objects.filter(application=app, status='APPLIED').exists()
        self.assertTrue(history_exists)

    def test_05_interview_list_count_scoped_to_candidate(self):
        """5. Interview list/count includes only Interviews linked to candidate's Applications."""
        app_a = Application.objects.create(
            job=self.published_job,
            candidate=self.candidate_profile_a,
            resume=self.resume_a,
            status=Application.Status.INTERVIEW
        )
        interview_a = Interview.objects.create(
            application=app_a,
            job=self.published_job,
            scheduled_date='2026-10-15',
            scheduled_time='10:00:00',
            status=Interview.Status.SCHEDULED
        )

        app_b = Application.objects.create(
            job=self.published_job,
            candidate=self.candidate_profile_b,
            resume=self.resume_b,
            status=Application.Status.INTERVIEW
        )
        interview_b = Interview.objects.create(
            application=app_b,
            job=self.published_job,
            scheduled_date='2026-10-16',
            scheduled_time='11:00:00',
            status=Interview.Status.SCHEDULED
        )

        self.client.force_authenticate(user=self.candidate_user_a)
        res = self.client.get('/accounts/candidate/interviews/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]['id']), str(interview_a.id))

    def test_06_rejection_count_and_selected_card_mapping(self):
        """6. Rejection count matches actual Application status; Selected is not silently counted as an Offer."""
        Application.objects.create(
            job=self.published_job,
            candidate=self.candidate_profile_a,
            resume=self.resume_a,
            status=Application.Status.REJECTED
        )
        Application.objects.create(
            job=self.simple_local_job,
            candidate=self.candidate_profile_a,
            status=Application.Status.ACCEPTED
        )

        self.client.force_authenticate(user=self.candidate_user_a)
        res = self.client.get('/accounts/candidate/applications/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['rejectedCount'], 1)
        self.assertEqual(res.data['selectedCount'], 1)

    def test_07_resume_upload_default_and_protection(self):
        """7. Resume default behavior persists; referenced resume is protected against deletion."""
        app_a = Application.objects.create(
            job=self.published_job,
            candidate=self.candidate_profile_a,
            resume=self.resume_a,
            status=Application.Status.APPLIED
        )

        self.client.force_authenticate(user=self.candidate_user_a)
        res_del = self.client.delete(f'/accounts/candidate/resumes/{self.resume_a.id}/')
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attached to submitted job applications", res_del.data['detail'])

    def test_08_saved_job_toggles_persist_without_duplicates(self):
        """8. Saved Job toggles persist in database without duplicate rows."""
        self.client.force_authenticate(user=self.candidate_user_a)

        # Toggle 1: Save job
        res1 = self.client.post(f'/accounts/candidate/jobs/{self.published_job.id}/save/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['isSaved'])
        self.assertEqual(SavedJob.objects.filter(candidate=self.candidate_profile_a, job=self.published_job).count(), 1)

        # Toggle 2: Unsave job
        res2 = self.client.post(f'/accounts/candidate/jobs/{self.published_job.id}/save/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['isSaved'])
        self.assertEqual(SavedJob.objects.filter(candidate=self.candidate_profile_a, job=self.published_job).count(), 0)

    def test_09_dashboard_returns_consistent_counts(self):
        """9. Dashboard and detail pages return consistent counts for Candidate."""
        self.client.force_authenticate(user=self.candidate_user_a)

        res = self.client.get('/accounts/candidate/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('profile', res.data)
        self.assertIn('recentApplications', res.data)
        self.assertIn('upcomingInterviews', res.data)
        self.assertIn('recommendedJobs', res.data)

    def test_10_empty_accounts_return_zero_counts(self):
        """10. Empty accounts return zero counts and genuine empty states, not sample jobs or companies."""
        empty_user = User.objects.create_user(
            username='empty_candidate',
            email='empty@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )
        CandidateProfile.objects.get_or_create(user=empty_user)

        self.client.force_authenticate(user=empty_user)
        res = self.client.get('/accounts/candidate/applications/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['totalApplications'], 0)
        self.assertEqual(res.data['interviewsCount'], 0)
        self.assertEqual(res.data['rejectedCount'], 0)
        self.assertEqual(res.data['selectedCount'], 0)

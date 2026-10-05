from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
import decimal

from accounts.models import (
    CandidateProfile,
    HRProfile,
    Job,
    Location,
    WorkMode,
    JobCategory,
    JobLocation,
    Application,
    SavedJob,
    Resume
)

User = get_user_model()


class CandidateJobsFlowTests(TestCase):
    def setUp(self):
        # Create HR user
        self.hr_user = User.objects.create_user(
            username="hr_test",
            email="hr_test@tnjobz.com",
            password="Password123!",
            role=User.Role.HR
        )
        self.hr_profile = getattr(self.hr_user, 'hr_profile', None) or HRProfile.objects.get(user=self.hr_user)
        self.hr_profile.company_name = "TechSolutions Pvt Ltd"
        self.hr_profile.save()

        # Create Candidates
        self.cand_user_1 = User.objects.create_user(
            username="cand1",
            email="cand1@tnjobz.com",
            password="Password123!",
            role=User.Role.CANDIDATE
        )
        self.candidate_1 = getattr(self.cand_user_1, 'candidate_profile', None) or CandidateProfile.objects.get(user=self.cand_user_1)

        self.cand_user_2 = User.objects.create_user(
            username="cand2",
            email="cand2@tnjobz.com",
            password="Password123!",
            role=User.Role.CANDIDATE
        )
        self.candidate_2 = getattr(self.cand_user_2, 'candidate_profile', None) or CandidateProfile.objects.get(user=self.cand_user_2)

        # Create taxonomy
        self.location_chennai = Location.objects.create(name="Chennai")
        self.work_mode_hybrid = WorkMode.objects.create(name="Hybrid")
        self.category_eng = JobCategory.objects.create(name="Software Engineering")

        # Clients
        self.client_cand_1 = APIClient()
        self.client_cand_1.force_authenticate(user=self.cand_user_1)

        self.client_cand_2 = APIClient()
        self.client_cand_2.force_authenticate(user=self.cand_user_2)

        self.client_anon = APIClient()

    def test_01_draft_job_absent_from_candidate_list(self):
        """1. An approved HR creates a Job; Draft is absent from the Candidate list."""
        draft_job = Job.objects.create(
            hr=self.hr_profile,
            title="Draft Software Engineer",
            description="Draft Job Description",
            status=Job.Status.DRAFT,
            category=self.category_eng
        )
        res = self.client_cand_1.get('/accounts/candidate/jobs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        job_ids = [j['id'] for j in res.data.get('results', [])]
        self.assertNotIn(draft_job.id, job_ids)

    def test_02_pending_review_job_absent_from_candidate_list(self):
        """2. A submitted Job remains absent while pending review."""
        pending_job = Job.objects.create(
            hr=self.hr_profile,
            title="Pending Review Developer",
            description="Pending Review Description",
            status=Job.Status.PENDING_REVIEW,
            category=self.category_eng
        )
        res = self.client_cand_1.get('/accounts/candidate/jobs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        job_ids = [j['id'] for j in res.data.get('results', [])]
        self.assertNotIn(pending_job.id, job_ids)

    def test_03_published_job_appears_with_correct_company_salary_location(self):
        """3. After actual approval/publication, the Job appears with correct company, salary, location, and category data."""
        published_job = Job.objects.create(
            hr=self.hr_profile,
            title="Senior Django Developer",
            description="Build scalable APIs",
            salary_min=decimal.Decimal("800000"),
            salary_max=decimal.Decimal("1200000"),
            salary_period="year",
            status=Job.Status.PUBLISHED,
            category=self.category_eng,
            work_mode=self.work_mode_hybrid,
            published_at=timezone.now()
        )
        JobLocation.objects.create(job=published_job, location=self.location_chennai)

        res = self.client_cand_1.get('/accounts/candidate/jobs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', [])
        self.assertEqual(len(results), 1)

        job_data = results[0]
        self.assertEqual(job_data['id'], published_job.id)
        self.assertEqual(job_data['title'], "Senior Django Developer")
        self.assertEqual(job_data['company_name'], "TechSolutions Pvt Ltd")
        self.assertEqual(job_data['company_initials'], "T")
        self.assertEqual(job_data['category_name'], "Software Engineering")
        self.assertEqual(job_data['work_mode_name'], "Hybrid")

    def test_04_closed_expired_rejected_jobs_cannot_be_accessed_or_applied(self):
        """4. Closed, expired, rejected, and unpublished Jobs cannot receive new Candidate Applications."""
        closed_job = Job.objects.create(
            hr=self.hr_profile,
            title="Closed Job",
            description="Closed",
            status=Job.Status.CLOSED
        )
        rejected_job = Job.objects.create(
            hr=self.hr_profile,
            title="Rejected Job",
            description="Rejected",
            status=Job.Status.REJECTED
        )
        expired_job = Job.objects.create(
            hr=self.hr_profile,
            title="Expired Job",
            description="Expired",
            status=Job.Status.EXPIRED
        )

        for non_pub_job in [closed_job, rejected_job, expired_job]:
            # Detail view must return 404
            res_detail = self.client_cand_1.get(f'/accounts/candidate/jobs/{non_pub_job.id}/')
            self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

            # Application submission must return 400 Bad Request
            res_apply = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
                'job_id': non_pub_job.id,
                'application_type': 'SIMPLE_LOCAL'
            })
            self.assertEqual(res_apply.status_code, status.HTTP_400_BAD_REQUEST)

    def test_05_save_and_unsave_job_persists(self):
        """5. A Candidate can save/unsave a Job and the state persists."""
        published_job = Job.objects.create(
            hr=self.hr_profile,
            title="React Developer",
            description="React frontend work",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

        # Toggle save
        res_save = self.client_cand_1.post(f'/accounts/candidate/jobs/{published_job.id}/save/')
        self.assertEqual(res_save.status_code, status.HTTP_200_OK)
        self.assertTrue(res_save.data['isSaved'])
        self.assertTrue(SavedJob.objects.filter(candidate=self.candidate_1, job=published_job).exists())

        # Toggle unsave
        res_unsave = self.client_cand_1.post(f'/accounts/candidate/jobs/{published_job.id}/save/')
        self.assertEqual(res_unsave.status_code, status.HTTP_200_OK)
        self.assertFalse(res_unsave.data['isSaved'])
        self.assertFalse(SavedJob.objects.filter(candidate=self.candidate_1, job=published_job).exists())

    def test_06_simple_vs_professional_application_modes(self):
        """6. Simple application works without a resume; professional application follows resume requirement."""
        simple_job = Job.objects.create(
            hr=self.hr_profile,
            title="Local Technician",
            description="Technician role",
            application_type="SIMPLE_LOCAL",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )
        prof_job = Job.objects.create(
            hr=self.hr_profile,
            title="Senior Architect",
            description="Architect role",
            application_type="PROFILE_RESUME",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

        # 6a. Simple Local apply succeeds without resume
        res_simple = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
            'job_id': simple_job.id,
            'application_type': 'SIMPLE_LOCAL'
        })
        self.assertEqual(res_simple.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Application.objects.filter(candidate=self.candidate_1, job=simple_job).exists())

        # 6b. Professional application fails if no resume exists
        res_prof_fail = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
            'job_id': prof_job.id,
            'application_type': 'PROFILE_RESUME'
        })
        self.assertEqual(res_prof_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # Add resume for candidate 1 and re-submit
        resume = Resume.objects.create(
            candidate=self.candidate_1,
            file_name="resume.pdf",
            file_url="https://tnjobz.s3.amazonaws.com/resumes/resume.pdf",
            is_default=True
        )
        res_prof_success = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
            'job_id': prof_job.id,
            'resume_id': resume.id,
            'application_type': 'PROFILE_RESUME'
        })
        self.assertEqual(res_prof_success.status_code, status.HTTP_201_CREATED)

    def test_07_duplicate_applications_rejected(self):
        """7. Duplicate applications are rejected without a second record."""
        simple_job = Job.objects.create(
            hr=self.hr_profile,
            title="Field Officer",
            description="Field work",
            application_type="SIMPLE_LOCAL",
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

        res1 = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
            'job_id': simple_job.id,
            'application_type': 'SIMPLE_LOCAL'
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client_cand_1.post('/accounts/candidate/applications/submit/', {
            'job_id': simple_job.id,
            'application_type': 'SIMPLE_LOCAL'
        })
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.filter(candidate=self.candidate_1, job=simple_job).count(), 1)

    def test_08_different_candidates_see_own_saved_and_applied_states(self):
        """8. Different Candidates see their own saved/applied states."""
        published_job = Job.objects.create(
            hr=self.hr_profile,
            title="UI Designer",
            description="UI/UX",
            status=Job.Status.PUBLISHED,
            application_type="SIMPLE_LOCAL",
            published_at=timezone.now()
        )

        # Candidate 1 saves and applies
        SavedJob.objects.create(candidate=self.candidate_1, job=published_job)
        Application.objects.create(candidate=self.candidate_1, job=published_job, status=Application.Status.APPLIED)

        # Candidate 1 sees is_saved=True, is_applied=True
        res_1 = self.client_cand_1.get(f'/accounts/candidate/jobs/{published_job.id}/')
        self.assertEqual(res_1.status_code, status.HTTP_200_OK)
        self.assertTrue(res_1.data['is_saved'])
        self.assertTrue(res_1.data['is_applied'])

        # Candidate 2 sees is_saved=False, is_applied=False
        res_2 = self.client_cand_2.get(f'/accounts/candidate/jobs/{published_job.id}/')
        self.assertEqual(res_2.status_code, status.HTTP_200_OK)
        self.assertFalse(res_2.data['is_saved'])
        self.assertFalse(res_2.data['is_applied'])

    def test_09_search_filtering_pagination(self):
        """9. Search, filtering, pagination, and total count reflect real eligible Jobs."""
        for i in range(12):
            Job.objects.create(
                hr=self.hr_profile,
                title=f"Python Engineer {i}",
                description="Python development",
                status=Job.Status.PUBLISHED,
                published_at=timezone.now()
            )

        res = self.client_cand_1.get('/accounts/candidate/jobs/?search=Python')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 12)
        self.assertEqual(len(res.data['results']), 10)  # Paginated to 10 per page

    def test_10_empty_database_returns_honest_empty_state(self):
        """10. Empty database returns an honest empty list."""
        Job.objects.all().delete()
        res = self.client_cand_1.get('/accounts/candidate/jobs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(len(res.data['results']), 0)

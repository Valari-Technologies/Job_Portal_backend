from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import (
    HRProfile, Location, EmployerVerification, Job, JobReview,
    JobCategory, WorkMode, Notification, JobReport
)

User = get_user_model()


class ReportsAndNotificationsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Super Admin
        self.super_admin = User.objects.create_superuser(
            username='super_admin_rep',
            email='superadmin_rep@example.com',
            password='Password123!'
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            username='admin_rep',
            email='admin_rep@example.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # Create Location & Category & WorkMode
        self.location = Location.objects.create(name='Chennai', location_type=Location.LocationType.CITY)
        self.category = JobCategory.objects.create(name='IT & Software')
        self.work_mode = WorkMode.objects.create(name='On-site')

        # Create Approved Employer / HR User
        self.hr_user = User.objects.create_user(
            username='hr_rep',
            email='hr_rep@example.com',
            password='Password123!',
            role=User.Role.HR,
            first_name='Jane',
            last_name='Doe'
        )
        self.hr_profile = HRProfile.objects.get(user=self.hr_user)
        self.hr_profile.company_name = 'Acme Software'
        self.hr_profile.contact_email = 'contact@acme.com'
        self.hr_profile.contact_phone = '9876543210'
        self.hr_profile.address = '123 Tech Park'
        self.hr_profile.company_description = 'Tech company'
        self.hr_profile.verification_status = 'APPROVED'
        self.hr_profile.save()

        # Create Candidate User 1
        self.candidate_1 = User.objects.create_user(
            username='cand_rep_1',
            email='cand1@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )

        # Create Candidate User 2
        self.candidate_2 = User.objects.create_user(
            username='cand_rep_2',
            email='cand2@example.com',
            password='Password123!',
            role=User.Role.CANDIDATE
        )

        # Create a Published Job
        self.job = Job.objects.create(
            hr=self.hr_profile,
            title='Senior Backend Engineer',
            description='Django backend developer job post.',
            category=self.category,
            work_mode=self.work_mode,
            status=Job.Status.PUBLISHED,
            published_at=timezone.now()
        )

    def test_01_valid_job_report_saved(self):
        """1. A valid job report being saved with its actual reporter and job."""
        self.client.force_authenticate(user=self.candidate_1)
        response = self.client.post('/accounts/job-reports/', {
            'job_id': self.job.id,
            'reason': 'SPAM',
            'description': 'This job post contains duplicate spam content.'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('report', response.data)
        report_id = response.data['report']['id']

        report = JobReport.objects.get(pk=report_id)
        self.assertEqual(report.job.id, self.job.id)
        self.assertEqual(report.reported_by.id, self.candidate_1.id)
        self.assertEqual(report.reason, 'SPAM')
        self.assertEqual(report.status, 'PENDING')

    def test_02_unauthorized_or_invalid_report_submissions_rejected(self):
        """2. Unauthorized or invalid submissions being rejected."""
        # Unauthenticated request
        response = self.client.post('/accounts/job-reports/', {
            'job_id': self.job.id,
            'reason': 'SPAM'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated duplicate submission check
        self.client.force_authenticate(user=self.candidate_1)
        # First submission
        self.client.post('/accounts/job-reports/', {'job_id': self.job.id, 'reason': 'SPAM'}, format='json')
        # Duplicate submission attempt
        dup_resp = self.client.post('/accounts/job-reports/', {'job_id': self.job.id, 'reason': 'SPAM'}, format='json')
        self.assertEqual(dup_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already submitted a report', dup_resp.data['detail'])

        # Employer trying to report own job
        self.client.force_authenticate(user=self.hr_user)
        own_resp = self.client.post('/accounts/job-reports/', {'job_id': self.job.id, 'reason': 'MISLEADING'}, format='json')
        self.assertEqual(own_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_03_report_list_filtering_and_summary_counts(self):
        """3. Report list filtering and summary counts matching database records."""
        # Create 2 reports
        r1 = JobReport.objects.create(job=self.job, reported_by=self.candidate_1, reason='SPAM', status='PENDING')
        r2 = JobReport.objects.create(job=self.job, reported_by=self.candidate_2, reason='MISLEADING', status='REVIEWED')

        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/accounts/admin/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        summary = response.data['summary']
        self.assertEqual(summary['open_count'], 1)
        self.assertEqual(summary['reviewed_count'], 1)
        self.assertEqual(summary['dismissed_count'], 0)
        self.assertEqual(summary['total_count'], 2)

        # Filter by PENDING status
        pending_resp = self.client.get('/accounts/admin/reports/?status=PENDING')
        self.assertEqual(len(pending_resp.data['results']), 1)
        self.assertEqual(pending_resp.data['results'][0]['id'], r1.id)

    def test_04_review_and_dismissal_saving(self):
        """4. Review and dismissal saving status, reviewer, time, and explanation."""
        report = JobReport.objects.create(job=self.job, reported_by=self.candidate_1, reason='MISLEADING', status='PENDING')

        self.client.force_authenticate(user=self.admin_user)

        # Dismiss report without explanation should fail
        fail_resp = self.client.post(f'/accounts/admin/reports/{report.id}/decision/', {
            'action': 'REJECTED'
        }, format='json')
        self.assertEqual(fail_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Dismiss report with explanation notes
        dismiss_resp = self.client.post(f'/accounts/admin/reports/{report.id}/decision/', {
            'action': 'REJECTED',
            'notes': 'Job description verified as accurate.'
        }, format='json')
        self.assertEqual(dismiss_resp.status_code, status.HTTP_200_OK)

        report.refresh_from_db()
        self.assertEqual(report.status, 'REJECTED')
        self.assertEqual(report.reviewed_by.id, self.admin_user.id)
        self.assertIsNotNone(report.reviewed_at)
        self.assertEqual(report.notes, 'Job description verified as accurate.')

    def test_05_combined_linked_job_moderation_and_report_decision(self):
        """5. Combined linked-job moderation and report decision remaining consistent."""
        report = JobReport.objects.create(job=self.job, reported_by=self.candidate_1, reason='SCAM', status='PENDING')

        self.client.force_authenticate(user=self.super_admin)
        mod_resp = self.client.post(f'/accounts/admin/reports/{report.id}/decision/', {
            'action': 'REVIEWED',
            'job_action': 'CLOSED',
            'notes': 'Violated terms of service.',
            'job_reason': 'SCAM report confirmed.'
        }, format='json')

        self.assertEqual(mod_resp.status_code, status.HTTP_200_OK)

        report.refresh_from_db()
        self.job.refresh_from_db()

        self.assertEqual(report.status, 'REVIEWED')
        self.assertEqual(self.job.status, Job.Status.CLOSED)
        self.assertTrue(JobReview.objects.filter(job=self.job, action='CLOSED').exists())

    def test_06_two_review_attempts_consistency(self):
        """6. Two review attempts not producing contradictory results."""
        report = JobReport.objects.create(job=self.job, reported_by=self.candidate_1, reason='SPAM', status='PENDING')

        self.client.force_authenticate(user=self.super_admin)
        res1 = self.client.post(f'/accounts/admin/reports/{report.id}/decision/', {
            'action': 'REVIEWED',
            'notes': 'First decision'
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        res2 = self.client.post(f'/accounts/admin/reports/{report.id}/decision/', {
            'action': 'REJECTED',
            'notes': 'Second attempt'
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        report.refresh_from_db()
        self.assertEqual(report.status, 'REJECTED')
        self.assertEqual(report.notes, 'Second attempt')

    def test_07_notification_creation_after_real_events(self):
        """7. Notification creation after real verification/job/report submissions without duplicates."""
        # Candidate submits job report
        self.client.force_authenticate(user=self.candidate_1)
        self.client.post('/accounts/job-reports/', {'job_id': self.job.id, 'reason': 'SPAM'}, format='json')

        # Super Admin & Admin should receive notifications
        sa_notifs = Notification.objects.filter(user=self.super_admin, notification_type='JOB_REPORT_SUBMISSION')
        adm_notifs = Notification.objects.filter(user=self.admin_user, notification_type='JOB_REPORT_SUBMISSION')
        cand_notifs = Notification.objects.filter(user=self.candidate_1, notification_type='JOB_REPORT_SUBMISSION')

        self.assertEqual(sa_notifs.count(), 1)
        self.assertEqual(adm_notifs.count(), 1)
        self.assertEqual(cand_notifs.count(), 0)

    def test_08_user_sees_and_marks_only_own_notifications(self):
        """8. Each user seeing and marking only their own notifications."""
        n1 = Notification.objects.create(user=self.candidate_1, notification_type='TEST', title='Test 1', message='Msg 1')
        n2 = Notification.objects.create(user=self.candidate_2, notification_type='TEST', title='Test 2', message='Msg 2')

        # Candidate 1 lists notifications
        self.client.force_authenticate(user=self.candidate_1)
        list_resp = self.client.get('/accounts/notifications/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        results = list_resp.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], n1.id)

        # Candidate 1 attempts to mark Candidate 2's notification read
        mark_resp = self.client.post(f'/accounts/notifications/{n2.id}/mark-read/')
        self.assertEqual(mark_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Candidate 1 marks own notification read
        own_mark_resp = self.client.post(f'/accounts/notifications/{n1.id}/mark-read/')
        self.assertEqual(own_mark_resp.status_code, status.HTTP_200_OK)
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

    def test_09_read_state_and_unread_count_persistence(self):
        """9. Read state and unread count remaining correct after refresh."""
        n1 = Notification.objects.create(user=self.candidate_1, notification_type='TEST', title='T1', message='M1', is_read=False)
        n2 = Notification.objects.create(user=self.candidate_1, notification_type='TEST', title='T2', message='M2', is_read=False)

        self.client.force_authenticate(user=self.candidate_1)

        # Check initial unread count
        c1 = self.client.get('/accounts/notifications/unread-count/')
        self.assertEqual(c1.data['unread_count'], 2)

        # Mark all read
        self.client.post('/accounts/notifications/mark-all-read/')

        # Re-check unread count
        c2 = self.client.get('/accounts/notifications/unread-count/')
        self.assertEqual(c2.data['unread_count'], 0)

        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(n1.is_read)
        self.assertTrue(n2.is_read)

    def test_10_missing_or_unauthorized_reference_safe_handling(self):
        """10. A missing or unauthorized notification reference not exposing another record."""
        n = Notification.objects.create(
            user=self.candidate_1,
            notification_type='TEST',
            title='T1',
            message='M1',
            reference_type='JobReport',
            reference_id=999999
        )
        self.client.force_authenticate(user=self.candidate_1)
        resp = self.client.get('/accounts/notifications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0]['reference_id'], 999999)

    def test_11_super_admin_apis_deny_unauthorized_roles(self):
        """11. Super Admin APIs denying unauthorized roles and anonymous requests."""
        # Anonymous request
        anom_resp = self.client.get('/accounts/admin/reports/')
        self.assertEqual(anom_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Candidate user request to super admin endpoint
        self.client.force_authenticate(user=self.candidate_1)
        cand_resp = self.client.get('/accounts/admin/reports/')
        self.assertEqual(cand_resp.status_code, status.HTTP_403_FORBIDDEN)

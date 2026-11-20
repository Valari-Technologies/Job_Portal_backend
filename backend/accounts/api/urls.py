from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .candidate_ai_copilot import CandidateAICopilotChatView
from .candidate_ai_resume import CandidateAIResumeAnalyzeView, CandidateAIResumeSaveTailoredView
from .views import (
    CandidateRegisterView,
    HRRegisterView,
    AdminCreateUserView,
    AdminListView,
    GoogleLoginView,
    CustomTokenObtainPairView,
    UserProfileView,
    ChangePasswordView,
    AccountDeleteView,
    CurrentUserMeView,
    EmployerProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    LocationListView,
    EmployerListView,
    AdminUpdateEmployerDetailView,
    CandidateListView,
    AuditEventListView,
    SecurityPostureView,
    AccessReviewsView,
    UserStatusUpdateView,
    EmployerVerificationDecisionView,
    EmployerVerificationQueueView,
    EmployerSubmitVerificationView,
    JobReviewDecisionView,
    JobReviewQueueView,
    EmployerJobSubmitView,
    JobCategoryAdminListView,
    JobCategoryAdminDetailView,
    JobCategoryStatusUpdateView,
    SkillAdminListView,
    SkillAdminDetailView,
    SkillStatusUpdateView,
    JobCategoryPublicListView,
    SkillPublicListView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
    AdminBroadcastNotificationView,
    NotificationDeleteView,
    NotificationClearAllView,
    JobReportCreateView,
    JobReportAdminListView,
    JobReportDecisionView,
    CandidateProfileDetailView,
    CandidateProfilePhotoUploadView,
    CandidateResumeListView,
    CandidateResumeSetDefaultView,
    CandidateResumeDeleteView,
    CandidateJobListView,
    CandidateJobDetailView,
    CandidateToggleSavedJobView,
    CandidateSavedJobListView,
    CandidateApplicationListView,
    CandidateApplicationSummaryView,
    CandidateApplicationDetailView,
    CandidateApplicationWithdrawView,
    CandidateInterviewListView,
    CandidateInterviewSummaryView,
    CandidateInterviewRescheduleView,
    CandidateDashboardView,
    PublicCompanyListView,
    RecruiterApplicationListView,
    RecruiterApplicationStatusUpdateView,
    RecruiterApplicationScheduleInterviewView,
    RecruiterApplicationSendMessageView,
    RecruiterInterviewListView,
    RecruiterJobListView,
    RecruiterDashboardView,
    RecruiterCommerceSummaryView,
    RecruiterPlanSubscriptionView,
    AdminAnalyticsView,
    AdminDeleteCandidateView,
    AdminCandidateActionView,
    AdminGlobalSearchView,
    AdminDashboardView,
)

urlpatterns = [
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('companies/public/', PublicCompanyListView.as_view(), name='public_company_list'),
    path(
        'register/candidate/',
        CandidateRegisterView.as_view(),
        name='register_candidate'
    ),
    path(
        'register/hr/',
        HRRegisterView.as_view(),
        name='register_hr'
    ),
    path(
        'admin/create-user/',
        AdminCreateUserView.as_view(),
        name='admin_create_user'
    ),
    path(
        'admins/',
        AdminListView.as_view(),
        name='admin_list'
    ),
    path(
        'google/',
        GoogleLoginView.as_view(),
        name='google_login'
    ),
    path(
        'login/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'profile/',
        UserProfileView.as_view(),
        name='user_profile'
    ),
    path(
        'me/',
        CurrentUserMeView.as_view(),
        name='current_user_me'
    ),
    path(
        'employer/profile/',
        EmployerProfileView.as_view(),
        name='employer_profile'
    ),
    path(
        'change-password/',
        ChangePasswordView.as_view(),
        name='change_password'
    ),
    path(
        'delete-account/',
        AccountDeleteView.as_view(),
        name='delete_account'
    ),
    path(
        'password-reset/',
        PasswordResetRequestView.as_view(),
        name='password_reset_request'
    ),
    path(
        'password-reset/confirm/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'candidates/',
        CandidateListView.as_view(),
        name='candidate_list'
    ),
    path(
        'employers/',
        EmployerListView.as_view(),
        name='employer_list'
    ),
    path(
        'admin/employers/<int:user_id>/',
        AdminUpdateEmployerDetailView.as_view(),
        name='admin_employer_detail_update'
    ),
    path(
        'locations/',
        LocationListView.as_view(),
        name='location_list'
    ),
    path(
        'admin/audit-events/',
        AuditEventListView.as_view(),
        name='admin_audit_events'
    ),
    path(
        'admin/security-posture/',
        SecurityPostureView.as_view(),
        name='admin_security_posture'
    ),
    path(
        'admin/access-reviews/',
        AccessReviewsView.as_view(),
        name='admin_access_reviews'
    ),
    path(
        'admin/candidates/<int:user_id>/',
        AdminDeleteCandidateView.as_view(),
        name='admin_candidate_delete'
    ),
    path(
        'admin/candidates/<int:candidate_id>/action/',
        AdminCandidateActionView.as_view(),
        name='admin_candidate_action'
    ),
    path(
        'admin/search/',
        AdminGlobalSearchView.as_view(),
        name='admin_global_search'
    ),
    path(
        'admin/users/<int:user_id>/status/',
        UserStatusUpdateView.as_view(),
        name='admin_user_status_update'
    ),
    path(
        'admin/employer-verifications/',
        EmployerVerificationQueueView.as_view(),
        name='admin_employer_verification_queue'
    ),
    path(
        'admin/employers/verification-queue/',
        EmployerVerificationQueueView.as_view(),
        name='admin_employer_verification_queue_alias'
    ),
    path(
        'admin/employers/<int:employer_id>/verify/',
        EmployerVerificationDecisionView.as_view(),
        name='admin_employer_verify_decision'
    ),
    path(
        'employer/submit-verification/',
        EmployerSubmitVerificationView.as_view(),
        name='employer_submit_verification'
    ),
    path(
        'admin/job-reviews/',
        JobReviewQueueView.as_view(),
        name='admin_job_review_queue'
    ),
    path(
        'admin/jobs/review-queue/',
        JobReviewQueueView.as_view(),
        name='admin_job_review_queue_alias'
    ),
    path(
        'admin/jobs/<int:job_id>/review/',
        JobReviewDecisionView.as_view(),
        name='admin_job_review_decision'
    ),
    path(
        'employer/jobs/<int:job_id>/submit/',
        EmployerJobSubmitView.as_view(),
        name='employer_job_submit'
    ),
    path(
        'admin/categories/',
        JobCategoryAdminListView.as_view(),
        name='admin_categories_list'
    ),
    path(
        'admin/categories/<int:pk>/',
        JobCategoryAdminDetailView.as_view(),
        name='admin_categories_detail'
    ),
    path(
        'admin/categories/<int:pk>/status/',
        JobCategoryStatusUpdateView.as_view(),
        name='admin_categories_status'
    ),
    path(
        'admin/skills/',
        SkillAdminListView.as_view(),
        name='admin_skills_list'
    ),
    path(
        'admin/skills/<int:pk>/',
        SkillAdminDetailView.as_view(),
        name='admin_skills_detail'
    ),
    path(
        'admin/skills/<int:pk>/status/',
        SkillStatusUpdateView.as_view(),
        name='admin_skills_status'
    ),
    path(
        'job-categories/',
        JobCategoryPublicListView.as_view(),
        name='public_categories_list'
    ),
    path(
        'skills/',
        SkillPublicListView.as_view(),
        name='public_skills_list'
    ),

    # Notifications
    path(
        'notifications/',
        NotificationListView.as_view(),
        name='notification_list'
    ),
    path(
        'notifications/<int:pk>/mark-read/',
        NotificationMarkReadView.as_view(),
        name='notification_mark_read'
    ),
    path(
        'notifications/mark-all-read/',
        NotificationMarkAllReadView.as_view(),
        name='notification_mark_all_read'
    ),
    path(
        'notifications/unread-count/',
        NotificationUnreadCountView.as_view(),
        name='notification_unread_count'
    ),
    path(
        'admin/notifications/',
        NotificationListView.as_view(),
        name='admin_notifications_list'
    ),
    path(
        'admin/notifications/broadcast/',
        AdminBroadcastNotificationView.as_view(),
        name='admin_notifications_broadcast'
    ),
    path(
        'notifications/<int:pk>/delete/',
        NotificationDeleteView.as_view(),
        name='notification_delete'
    ),
    path(
        'notifications/clear-all/',
        NotificationClearAllView.as_view(),
        name='notification_clear_all'
    ),

    # Job Reports
    path(
        'job-reports/',
        JobReportCreateView.as_view(),
        name='job_report_create'
    ),
    path(
        'admin/reports/',
        JobReportAdminListView.as_view(),
        name='admin_reports_list'
    ),
    path(
        'admin/reports/<int:report_id>/decision/',
        JobReportDecisionView.as_view(),
        name='admin_report_decision'
    ),

    # Candidate Portal API Endpoints
    path('candidate/profile/', CandidateProfileDetailView.as_view(), name='candidate_profile_detail'),
    path('candidate/profile/photo/', CandidateProfilePhotoUploadView.as_view(), name='candidate_profile_photo'),
    path('candidate/resumes/', CandidateResumeListView.as_view(), name='candidate_resume_list'),
    path('candidate/resumes/<int:pk>/set-default/', CandidateResumeSetDefaultView.as_view(), name='candidate_resume_set_default'),
    path('candidate/resumes/<int:pk>/', CandidateResumeDeleteView.as_view(), name='candidate_resume_delete'),
    path('candidate/jobs/', CandidateJobListView.as_view(), name='candidate_job_list'),
    path('candidate/jobs/<int:pk>/', CandidateJobDetailView.as_view(), name='candidate_job_detail'),
    path('candidate/jobs/<int:pk>/save/', CandidateToggleSavedJobView.as_view(), name='candidate_job_save_toggle'),
    path('candidate/saved-jobs/', CandidateSavedJobListView.as_view(), name='candidate_saved_job_list'),
    path('candidate/applications/', CandidateApplicationListView.as_view(), name='candidate_application_list'),
    path('candidate/applications/submit/', CandidateApplicationListView.as_view(), name='candidate_application_submit'),
    path('candidate/applications/summary/', CandidateApplicationSummaryView.as_view(), name='candidate_application_summary'),
    path('candidate/applications/<int:pk>/', CandidateApplicationDetailView.as_view(), name='candidate_application_detail'),
    path('candidate/applications/<int:pk>/withdraw/', CandidateApplicationWithdrawView.as_view(), name='candidate_application_withdraw'),
    path('candidate/interviews/', CandidateInterviewListView.as_view(), name='candidate_interview_list'),
    path('candidate/interviews/summary/', CandidateInterviewSummaryView.as_view(), name='candidate_interview_summary'),
    path('candidate/interviews/<int:pk>/reschedule/', CandidateInterviewRescheduleView.as_view(), name='candidate_interview_reschedule'),
    path('candidate/dashboard/', CandidateDashboardView.as_view(), name='candidate_dashboard'),
    path('candidate/ai-copilot/chat/', CandidateAICopilotChatView.as_view(), name='candidate_ai_copilot_chat'),
    path('candidate/ai-resume/analyze/', CandidateAIResumeAnalyzeView.as_view(), name='candidate_ai_resume_analyze'),
    path('candidate/ai-resume/save-tailored/', CandidateAIResumeSaveTailoredView.as_view(), name='candidate_ai_resume_save_tailored'),

    # Recruiter Applications Endpoints
    path('recruiter/applications/', RecruiterApplicationListView.as_view(), name='recruiter_applications_list'),
    path('recruiter/applications/<int:pk>/status/', RecruiterApplicationStatusUpdateView.as_view(), name='recruiter_application_status_update'),
    path('recruiter/applications/<int:pk>/interview/', RecruiterApplicationScheduleInterviewView.as_view(), name='recruiter_application_schedule_interview'),
    path('recruiter/applications/<int:pk>/message/', RecruiterApplicationSendMessageView.as_view(), name='recruiter_application_send_message'),
    path('recruiter/interviews/', RecruiterInterviewListView.as_view(), name='recruiter_interviews_list'),
    path('recruiter/jobs/', RecruiterJobListView.as_view(), name='recruiter_jobs_list_create'),
    path('recruiter/dashboard/', RecruiterDashboardView.as_view(), name='recruiter_dashboard'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('recruiter/commerce-summary/', RecruiterCommerceSummaryView.as_view(), name='recruiter_commerce_summary'),
    path('recruiter/commerce/subscribe/', RecruiterPlanSubscriptionView.as_view(), name='recruiter_plan_subscribe'),
]

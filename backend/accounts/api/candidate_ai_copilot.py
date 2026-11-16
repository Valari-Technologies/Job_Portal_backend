import json
import logging
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from accounts.models import (
    CandidateProfile, Job, Application, ApplicationActivity, 
    ApplicationStatusHistory, Notification, Resume
)
from accounts.api.gemini_service import call_gemini, get_gemini_api_key

logger = logging.getLogger(__name__)


class IsCandidateRole(permissions.BasePermission):
    """Allows access only to authenticated candidate users."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'CANDIDATE'
        )


def _get_candidate_profile(user):
    try:
        return user.candidate_profile
    except Exception:
        return None


def get_recommended_jobs(candidate, query_text=""):
    """
    Intelligently retrieves and scores active published jobs matching
    the candidate's skills, experience, location, and past applications.
    """
    today = timezone.now().date()
    active_jobs = Job.objects.filter(
        status=Job.Status.PUBLISHED
    ).filter(
        Q(application_deadline__isnull=True) | Q(application_deadline__gte=today)
    ).select_related(
        'hr', 'category', 'work_mode'
    ).prefetch_related(
        'job_skills__skill', 'job_locations__location'
    ).order_by('-created_at')

    # Get already applied job IDs to avoid proposing already-applied jobs
    applied_job_ids = set(
        Application.objects.filter(candidate=candidate).values_list('job_id', flat=True)
    )

    candidate_skills = set(
        s.skill.name.lower() for s in candidate.candidate_skills.all()
    ) if hasattr(candidate, 'candidate_skills') else set()

    # Collect past applied job titles for preferences
    past_applied_titles = set(
        Application.objects.filter(candidate=candidate).values_list('job__title', flat=True)
    )

    job_recommendations = []
    query_lower = query_text.lower().strip() if query_text else ""

    for job in active_jobs:
        # Check if already applied
        is_already_applied = job.id in applied_job_ids

        # Skill match calculation
        job_skills = set(
            js.skill.name.lower() for js in job.job_skills.all()
        )
        matched_skills = list(candidate_skills.intersection(job_skills))
        skill_score = len(matched_skills) * 20

        # Location text
        locations = [jl.location.name for jl in job.job_locations.all()]
        loc_str = ", ".join(locations) if locations else "Tamil Nadu"

        # Query text match bonus
        query_score = 0
        if query_lower:
            if query_lower in job.title.lower():
                query_score += 40
            if any(query_lower in s for s in job_skills):
                query_score += 30
            if any(query_lower in loc.lower() for loc in locations):
                query_score += 25

        total_score = skill_score + query_score

        # Salary formatting
        salary_str = "Best in industry"
        if job.salary_min and job.salary_max:
            salary_str = f"₹{int(job.salary_min):,} - ₹{int(job.salary_max):,}/month"
        elif job.salary_min:
            salary_str = f"From ₹{int(job.salary_min):,}/month"

        raw_app_type = str(job.application_type or 'PROFILE_RESUME').upper()
        resume_required = not ('SIMPLE' in raw_app_type or 'LOCAL' in raw_app_type)

        job_recommendations.append({
            "id": job.id,
            "title": job.title,
            "company": job.hr.company_name if job.hr else "Verified Employer",
            "location": loc_str,
            "salary": salary_str,
            "work_mode": job.work_mode.name if job.work_mode else "On-site",
            "experience": f"{job.experience_min or 0}-{job.experience_max or 2} Yrs",
            "matched_skills": matched_skills,
            "skills": [js.skill.name for js in job.job_skills.all()[:4]],
            "already_applied": is_already_applied,
            "resume_required": resume_required,
            "score": total_score
        })

    # Sort: unapplied first, then by score, then recency
    job_recommendations.sort(key=lambda x: (not x["already_applied"], x["score"]), reverse=True)
    return job_recommendations[:8]


def apply_job_for_candidate(candidate, job_id, user):
    """
    Safely executes a job application for the candidate with atomic guarantees.
    Prevents duplicate submissions, enforces deadlines, and logs AI provenance.
    """
    try:
        job = Job.objects.select_related('hr', 'hr__user').get(pk=job_id)
    except Job.DoesNotExist:
        return {
            "success": False,
            "message": "Job listing not found or has been removed."
        }

    # 1. Enforce Job Status
    if job.status != Job.Status.PUBLISHED:
        return {
            "success": False,
            "message": f"This job is currently {job.get_status_display().lower()} and not accepting applications."
        }

    # 2. Check Application Deadline
    today = timezone.now().date()
    if job.application_deadline and job.application_deadline < today:
        return {
            "success": False,
            "message": f"The deadline for this job was {job.application_deadline.strftime('%b %d, %Y')}. Applications are closed."
        }

    # 3. Check for Duplicate Application
    existing = Application.objects.filter(candidate=candidate, job=job).first()
    if existing:
        return {
            "success": False,
            "message": f"You have already applied for '{job.title}' at {job.hr.company_name if job.hr else 'this employer'}. Current status: {existing.get_status_display()}."
        }

    # 4. Check Application Type & Resume Requirement
    raw_app_type = str(job.application_type or 'PROFILE_RESUME').upper()
    is_simple_local = 'SIMPLE' in raw_app_type or 'LOCAL' in raw_app_type
    effective_app_type = 'SIMPLE_LOCAL' if is_simple_local else 'PROFILE_RESUME'

    # Resolve candidate resume (Resume model uses is_default, not is_primary)
    resume_obj = Resume.objects.filter(candidate=candidate).order_by('-is_default', '-updated_at').first()

    # If the job requires a resume (Professional / Profile Resume) and candidate has none
    if not is_simple_local and not resume_obj:
        return {
            "success": False,
            "requires_resume": True,
            "job_id": job.id,
            "job_title": job.title,
            "company": job.hr.company_name if job.hr else "Company",
            "message": (
                f"📄 A resume is required for **'{job.title}'** at **{job.hr.company_name if job.hr else 'this company'}** (Professional Role).\n\n"
                f"You haven't uploaded a resume yet. Please upload your resume first on the Resume page, then click apply again!"
            )
        }

    # 5. Create Application in an atomic transaction
    with transaction.atomic():
        application = Application.objects.create(
            job=job,
            candidate=candidate,
            resume=resume_obj,
            application_type='AI_COPILOT',
            status=Application.Status.APPLIED,
            remarks='Applied via Nexiv on candidate instruction'
        )

        ApplicationStatusHistory.objects.create(
            application=application,
            status='APPLIED',
            changed_by=user,
            notes='Application submitted automatically by Nexiv on candidate command'
        )

        # Notify Recruiter/Employer
        if job.hr and job.hr.user:
            try:
                Notification.objects.create(
                    user=job.hr.user,
                    notification_type='NEW_APPLICATION',
                    title='New Job Application Received',
                    message=f"{user.get_full_name() or user.username} applied for '{job.title}'.",
                    reference_type='Application',
                    reference_id=application.id
                )
            except Exception as notify_err:
                logger.warning("Could not send recruiter notification: %s", notify_err)

    resume_note = ""
    if is_simple_local and not resume_obj:
        resume_note = "\n\n💡 *Note: For this job, a resume is not required (Simple / Local role), so your application was submitted directly with your candidate profile.*"

    return {
        "success": True,
        "application_id": application.id,
        "job_title": job.title,
        "company": job.hr.company_name if job.hr else "Company",
        "applied_at": application.applied_at.isoformat(),
        "message": f"Successfully applied for '{job.title}' at {job.hr.company_name if job.hr else 'Employer'}!{resume_note}"
    }


def get_candidate_application_summary(candidate):
    """Returns candidate's recent applications and their statuses."""
    apps = Application.objects.filter(
        candidate=candidate
    ).select_related('job', 'job__hr').order_by('-applied_at')[:6]

    results = []
    for app in apps:
        results.append({
            "id": app.id,
            "job_id": app.job.id,
            "title": app.job.title,
            "company": app.job.hr.company_name if app.job.hr else "Employer",
            "status": app.get_status_display(),
            "applied_via": app.application_type or "MANUAL",
            "applied_at": app.applied_at.strftime("%b %d, %Y")
        })
    return results


class CandidateAICopilotChatView(APIView):
    """
    Intelligent AI Career Copilot endpoint for candidates.
    Understands commands, queries live database jobs, executes automated
    job applications upon user command, and provides application tracking.
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def post(self, request):
        user = request.user
        candidate = _get_candidate_profile(user)
        if not candidate:
            return Response(
                {"error": "Candidate profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_message = request.data.get('message', '').strip()
        command_action = request.data.get('action') # Explicit action: 'APPLY_JOB' | 'RECOMMEND_JOBS' | 'TRACK_APPLICATIONS'
        target_job_id = request.data.get('job_id')

        # 1. DIRECT ACTION EXECUTION: 'APPLY_JOB'
        if command_action == 'APPLY_JOB' and target_job_id:
            apply_res = apply_job_for_candidate(candidate, target_job_id, user)
            if apply_res["success"]:
                reply = (
                    f"🎉 Done! I have submitted your application for **{apply_res['job_title']}** at **{apply_res['company']}**.\n\n"
                    f"You can track its live progress anytime in your **Applications** tab."
                )
            else:
                reply = f"⚠️ {apply_res['message']}"

            return Response({
                "reply": reply,
                "action_result": apply_res,
                "suggested_actions": ["Show my applications", "Find more jobs"]
            })

        # 2. DIRECT ACTION EXECUTION: 'TRACK_APPLICATIONS'
        if command_action == 'TRACK_APPLICATIONS' or any(kw in user_message.lower() for kw in ['track', 'my applications', 'applied jobs', 'status of my']):
            apps = get_candidate_application_summary(candidate)
            if not apps:
                reply = "You haven't submitted any job applications yet. Tell me what kind of job you're looking for, and I'll find matching openings for you!"
            else:
                ai_count = sum(1 for a in apps if a['applied_via'] == 'AI_COPILOT')
                reply = f"You have **{len(apps)} recent application(s)** on record"
                if ai_count > 0:
                    reply += f" ({ai_count} applied via Nexiv ✨)"
                reply += ". Here is your latest status:"

            return Response({
                "reply": reply,
                "applications": apps,
                "suggested_actions": ["Recommend jobs matching my skills", "Apply to a new job"]
            })

        # 3. DIRECT ACTION EXECUTION: 'RECOMMEND_JOBS' or natural language search
        lower_msg = user_message.lower()

        # Check if user commanded to apply by text (e.g., "apply to job 5" or "apply for react developer")
        if lower_msg.startswith("apply") or "apply to" in lower_msg or "apply for" in lower_msg:
            # Check if job_id was mentioned or find matching recommended job
            jobs = get_recommended_jobs(candidate, query_text=lower_msg.replace("apply", "").replace("to", "").replace("for", ""))
            unapplied = [j for j in jobs if not j["already_applied"]]

            if target_job_id:
                apply_res = apply_job_for_candidate(candidate, target_job_id, user)
                return Response({
                    "reply": f"🎉 {apply_res['message']}" if apply_res["success"] else f"⚠️ {apply_res['message']}",
                    "action_result": apply_res
                })

            if unapplied:
                top_job = unapplied[0]
                reply = (
                    f"I found a great match: **{top_job['title']}** at **{top_job['company']}** ({top_job['location']}).\n\n"
                    f"Would you like me to submit your application now?"
                )
                return Response({
                    "reply": reply,
                    "confirmation_required": True,
                    "target_job": top_job,
                    "suggested_actions": [f"Confirm Apply: {top_job['title']}", "Show other options"]
                })
            else:
                return Response({
                    "reply": "I couldn't find an open job matching that exact title. Here are current top opportunities matching your profile:",
                    "recommended_jobs": jobs[:4]
                })

        # Default: Personalized recommendations based on candidate's skills & history
        recommended = get_recommended_jobs(candidate, query_text=user_message)
        skills_list = [s.skill.name for s in candidate.candidate_skills.all()] if hasattr(candidate, 'candidate_skills') else []
        skills_str = ", ".join(skills_list[:3]) if skills_list else "your profile"

        if not recommended:
            reply = "I looked across all active listings, but there are no open vacancies right now. Check back soon as new jobs are published daily!"
        else:
            unapplied_count = sum(1 for j in recommended if not j['already_applied'])
            reply = (
                f"Based on {skills_str} and your preferences, I found **{unapplied_count} matching job opening(s)** for you.\n\n"
                f"You can click **Apply with AI** on any card below, or simply tell me *'Apply to {recommended[0]['title']}'*."
            )

        # Enhance reply with Gemini LLM if user asks conversational questions and API key is present
        if user_message and get_gemini_api_key() and len(user_message.split()) > 1:
            try:
                candidate_name = candidate.user.get_full_name() or candidate.user.username
                active_job_context = [{'title': j['title'], 'company': j['company'], 'salary': j['salary']} for j in recommended[:3]]
                llm_prompt = (
                    f"Candidate Name: {candidate_name}\n"
                    f"Candidate Skills: {skills_str}\n"
                    f"Top matching jobs on platform: {json.dumps(active_job_context)}\n"
                    f"Candidate message: {user_message}\n\n"
                    f"Give a friendly, direct, concise answer (under 3 sentences). "
                    f"Encourage them to apply or guide them to relevant opportunities."
                )
                llm_res = call_gemini(
                    llm_prompt,
                    system_instruction="You are Nexiv, the intelligent AI Career Assistant for TN Jobz. Helpful, polite, and practical assistant for job candidates. You understand English and Tamil."
                )
                if llm_res.get("success") and llm_res.get("text"):
                    reply = llm_res["text"].strip()
            except Exception as llm_err:
                logger.warning(f"Gemini conversational reply notice: {llm_err}")

        return Response({
            "reply": reply,
            "recommended_jobs": recommended,
            "suggested_actions": [
                f"Apply to {recommended[0]['title']}" if recommended else "Track my applications",
                "Show my applications",
                "Jobs in Tamil Nadu"
            ]
        })


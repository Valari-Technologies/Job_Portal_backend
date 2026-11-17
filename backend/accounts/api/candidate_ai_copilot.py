import re
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
    Intelligently retrieves and scores active published jobs.
    Returns: (exact_matches, profile_matches, specific_requested, filter_term)
    """
    today = timezone.now().date()
    active_jobs = Job.objects.filter(
        status=Job.Status.PUBLISHED
    ).filter(
        Q(application_deadline__isnull=True) | Q(application_deadline__gte=today)
    ).select_related(
        'hr', 'category', 'work_mode'
    ).prefetch_related(
        'job_skills__skill', 'job_locations__location', 'job_locations__location__parent'
    ).order_by('-created_at')

    # Get already applied job IDs
    applied_job_ids = set(
        Application.objects.filter(candidate=candidate).values_list('job_id', flat=True)
    )

    candidate_skills = set(
        s.skill.name.lower() for s in candidate.candidate_skills.all()
    ) if hasattr(candidate, 'candidate_skills') else set()

    # Identify specific search filter terms (e.g. location or specific title/skill)
    STOP_WORDS = {
        'job', 'jobs', 'in', 'at', 'for', 'the', 'a', 'an', 'me', 'show', 'find', 'recommend',
        'matching', 'my', 'skills', 'skill', 'openings', 'opening', 'vacancies', 'vacancy', 'please', 'all',
        'give', 'look', 'available', 'what', 'whats', "what's", 'who', 'whos', "who's", 'where', 'how', 'why',
        'when', 'is', 'are', 'am', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'tell', 'want', 'search',
        'portal', 'list', 'profile', 'status', 'strength', 'completion', 'detail', 'details', 'about', 'mine', 'to'
    }

    raw_query = (query_text or "").lower().strip()
    tokens = [re.sub(r'[^a-zA-Z0-9]', '', t) for t in raw_query.split()]
    meaningful_tokens = [t for t in tokens if t and t not in STOP_WORDS]
    filter_term = " ".join(meaningful_tokens).strip()
    specific_requested = bool(filter_term and len(filter_term) >= 2)

    exact_matches = []
    profile_matches = []

    for job in active_jobs:
        is_already_applied = job.id in applied_job_ids

        # Skill match calculation
        job_skills = set(js.skill.name.lower() for js in job.job_skills.all())
        matched_skills = list(candidate_skills.intersection(job_skills))
        skill_score = len(matched_skills) * 25

        # All locations including ancestors (state, district, city)
        loc_names = []
        for jl in job.job_locations.all():
            curr = jl.location
            while curr:
                loc_names.append(curr.name.lower())
                curr = curr.parent

        locations_display = [jl.location.name for jl in job.job_locations.all()]
        loc_str = ", ".join(locations_display) if locations_display else "Tamil Nadu"

        # Check if this job specifically matches the candidate's query
        is_query_match = False
        query_score = 0
        if specific_requested:
            # Check title, skills, company, or any location/state ancestor
            if any(t in job.title.lower() for t in meaningful_tokens):
                query_score += 50
                is_query_match = True
            if any(any(t in s for t in meaningful_tokens) for s in job_skills):
                query_score += 40
                is_query_match = True
            if any(any(t in l for t in meaningful_tokens) for l in loc_names):
                query_score += 50
                is_query_match = True
            if job.hr and any(t in (job.hr.company_name or '').lower() for t in meaningful_tokens):
                query_score += 30
                is_query_match = True

        total_score = skill_score + query_score

        # Salary formatting
        salary_str = "Best in industry"
        if job.salary_min and job.salary_max:
            salary_str = f"₹{int(job.salary_min):,} - ₹{int(job.salary_max):,}/month"
        elif job.salary_min:
            salary_str = f"From ₹{int(job.salary_min):,}/month"

        raw_app_type = str(job.application_type or 'PROFILE_RESUME').upper()
        resume_required = not ('SIMPLE' in raw_app_type or 'LOCAL' in raw_app_type)

        job_item = {
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
        }

        if is_query_match:
            exact_matches.append(job_item)
        profile_matches.append(job_item)

    exact_matches.sort(key=lambda x: (not x["already_applied"], x["score"]), reverse=True)
    profile_matches.sort(key=lambda x: (not x["already_applied"], x["score"]), reverse=True)

    return exact_matches[:8], profile_matches[:8], specific_requested, filter_term


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


def get_candidate_profile_summary(candidate):
    """
    Extracts structured summary of the candidate's real profile data.
    """
    skills = [s.skill.name for s in candidate.candidate_skills.all()] if hasattr(candidate, 'candidate_skills') else []
    profile_completion = getattr(candidate, 'profile_completion', 0) or 0
    experiences = list(candidate.experiences.all()) if hasattr(candidate, 'experiences') else []
    educations = list(candidate.educations.all()) if hasattr(candidate, 'educations') else []

    missing = []
    if not skills:
        missing.append("Skills & Tech Stack (Add programming languages & technologies)")
    if not experiences and (candidate.experience_total or 0) == 0:
        missing.append("Work Experience")
    if not educations and not candidate.college and not candidate.degree:
        missing.append("Education Details")
    if not candidate.user.first_name and not getattr(candidate, 'title', None):
        missing.append("Professional Headline")

    return {
        "skills": skills,
        "profile_completion": profile_completion,
        "experience_total": candidate.experience_total or 0,
        "has_skills": bool(skills),
        "is_complete": profile_completion >= 80,
        "missing_sections": missing,
        "college": candidate.college,
        "degree": candidate.degree,
        "full_name": candidate.user.get_full_name() or candidate.user.username
    }


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

        # 3. DIRECT INTENT: 'PROFILE_OR_SKILLS_QUERY'
        lower_msg = user_message.lower()
        is_profile_query = any(p in lower_msg for p in [
            'my skill', 'my skills', 'what are my skill', "what's my skill", "whats my skill",
            'what is my skill', 'list my skill', 'show my skill', 'tell my skill', 'check my skill',
            'my profile', 'profile status', 'profile strength', 'profile completion', 'finish my profile',
            'complete my profile', 'my experience', 'my education', 'about me', 'who am i', 'my details',
            'how is my profile', 'view my profile'
        ])

        if is_profile_query:
            prof_data = get_candidate_profile_summary(candidate)
            cand_name = prof_data["full_name"]

            if not prof_data["has_skills"]:
                missing_bullets = "\n".join([f"• {m}" for m in prof_data["missing_sections"]]) if prof_data["missing_sections"] else "• Skills & Technologies"
                reply = (
                    f"Hi **{cand_name}**, you haven't added any skills to your profile yet!\n\n"
                    f"📊 **Profile Strength:** {prof_data['profile_completion']}%\n\n"
                    f"Missing items to complete:\n{missing_bullets}\n\n"
                    f"To help me accurately match and recommend jobs for your career, please complete your profile by adding your skills, programming languages, and experience."
                )
                suggested = ["Complete Profile", "Recommend jobs matching my skills", "Track my applications"]
            else:
                skills_list_str = ", ".join(prof_data["skills"])
                reply = (
                    f"Hi **{cand_name}**, here are your recorded profile details:\n\n"
                    f"🎯 **Skills & Tech Stack:** {skills_list_str}\n"
                    f"📊 **Profile Strength:** {prof_data['profile_completion']}%\n"
                    f"💼 **Total Experience:** {prof_data['experience_total']} year(s)\n\n"
                    f"Would you like me to recommend active jobs matching these skills?"
                )
                suggested = ["Recommend jobs matching my skills", "Complete Profile", "Track my applications"]

            # Enhance with Gemini if available
            if get_gemini_api_key():
                try:
                    llm_prompt = (
                        f"Candidate Name: {cand_name}\n"
                        f"User asked: {user_message}\n"
                        f"Candidate Profile Data:\n"
                        f"- Profile Completion: {prof_data['profile_completion']}%\n"
                        f"- Skills: {', '.join(prof_data['skills']) if prof_data['skills'] else 'No skills added yet'}\n"
                        f"- Total Experience: {prof_data['experience_total']} years\n"
                        f"- Missing sections: {', '.join(prof_data['missing_sections']) if prof_data['missing_sections'] else 'None'}\n\n"
                        f"Answer the user's question directly, accurately, and politely (under 3 sentences). "
                        f"If their profile is incomplete or has no skills, clearly explain that they need to complete their profile (mentioning their current completion %) to unlock accurate job matching."
                    )
                    llm_res = call_gemini(
                        llm_prompt,
                        system_instruction="You are Nexiv, the intelligent AI Career Assistant for TN Jobz. Helpful, polite, and practical assistant for job candidates. You understand English and Tamil."
                    )
                    if llm_res.get("success") and llm_res.get("text"):
                        reply = llm_res["text"].strip()
                except Exception as llm_err:
                    logger.warning(f"Gemini conversational profile reply notice: {llm_err}")

            return Response({
                "reply": reply,
                "suggested_actions": suggested
            })

        # 4. DIRECT ACTION EXECUTION: 'APPLY_JOB' by natural language
        if lower_msg.startswith("apply") or "apply to" in lower_msg or "apply for" in lower_msg:
            exact_m, prof_m, _, _ = get_recommended_jobs(candidate, query_text=lower_msg.replace("apply", "").replace("to", "").replace("for", ""))
            jobs = exact_m if exact_m else prof_m
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

        # 5. Default: Intelligent search & personalized recommendations
        exact_matches, profile_matches, specific_requested, filter_term = get_recommended_jobs(candidate, query_text=user_message)
        prof_data = get_candidate_profile_summary(candidate)
        has_skills = prof_data["has_skills"]
        skills_str = ", ".join(prof_data["skills"][:4]) if has_skills else ""
        candidate_name = prof_data["full_name"]

        if specific_requested:
            filter_title = filter_term.title()
            if exact_matches:
                recommended = exact_matches
                unapplied_count = sum(1 for j in recommended if not j['already_applied'])
                reply = (
                    f"I found **{unapplied_count} active job opening(s)** matching **{filter_title}** for you.\n\n"
                    f"You can click **Apply with Nexiv** on any card below, or simply tell me *'Apply to {recommended[0]['title']}'*."
                )
                llm_prompt = (
                    f"Candidate Name: {candidate_name}\n"
                    f"Candidate Skills: {skills_str if has_skills else 'No skills added yet'}\n"
                    f"Candidate requested: {user_message}\n"
                    f"Status: Found {len(exact_matches)} active job opening(s) specifically matching '{filter_title}':\n"
                    f"{json.dumps([{'title': j['title'], 'company': j['company'], 'location': j['location'], 'salary': j['salary']} for j in recommended[:3]])}\n\n"
                    f"Write a friendly, professional response (under 3 sentences) confirming these matching jobs in {filter_title} and encouraging them to apply."
                )
            else:
                # No active jobs match the requested location/role/skill!
                recommended = profile_matches
                if has_skills:
                    reply = (
                        f"Currently, there are no active job openings matching **{filter_title}** on the platform.\n\n"
                        f"However, I analyzed your profile and skills in **{skills_str}**, and found these top alternative opportunities for you in other locations:"
                    )
                    llm_prompt = (
                        f"Candidate Name: {candidate_name}\n"
                        f"Candidate Skills: {skills_str}\n"
                        f"Candidate requested: {user_message}\n"
                        f"Status: Currently, there are NO active job openings matching '{filter_title}' on the platform.\n"
                        f"Alternative jobs matching candidate profile: {json.dumps([{'title': j['title'], 'company': j['company'], 'location': j['location'], 'salary': j['salary']} for j in recommended[:3]])}\n\n"
                        f"Write a friendly, polite, transparent response (under 3 sentences):\n"
                        f"1. Clearly state that there are currently no active job openings in '{filter_title}'.\n"
                        f"2. Explain that you analyzed their profile and skills ({skills_str}), and found matching alternative opportunities in other locations.\n"
                        f"3. Encourage them to explore or apply for these available opportunities."
                    )
                else:
                    reply = (
                        f"Currently, there are no active job openings matching **{filter_title}** on the platform.\n\n"
                        f"Also, you haven't added your skills to your profile yet (your profile completion is currently **{prof_data['profile_completion']}%**). "
                        f"In the meantime, here are top active openings available across other locations:"
                    )
                    llm_prompt = (
                        f"Candidate Name: {candidate_name}\n"
                        f"Candidate Profile: No skills added yet (Profile Completion: {prof_data['profile_completion']}%)\n"
                        f"Candidate requested: {user_message}\n"
                        f"Status: Currently, there are NO active job openings matching '{filter_title}'.\n"
                        f"Alternative platform jobs: {json.dumps([{'title': j['title'], 'company': j['company'], 'location': j['location'], 'salary': j['salary']} for j in recommended[:3]])}\n\n"
                        f"Write a friendly, transparent response (under 3 sentences):\n"
                        f"1. State that there are currently no active openings in '{filter_title}'.\n"
                        f"2. Note that their profile has no skills added yet (at {prof_data['profile_completion']}% completion) and advise completing their profile for accurate recommendations.\n"
                        f"3. Present the alternative jobs available on the platform."
                    )
        else:
            # General profile recommendations
            recommended = profile_matches
            if not has_skills:
                reply = (
                    f"Hi **{candidate_name}**, you haven't added any skills to your profile yet (your profile completion is at **{prof_data['profile_completion']}%**)!\n\n"
                    f"To get accurate job recommendations tailored to your expertise, please add your skills in your **Profile**.\n\n"
                    f"In the meantime, here are the top active job openings currently available on the platform:"
                )
                llm_prompt = (
                    f"Candidate Name: {candidate_name}\n"
                    f"Candidate Profile: No skills added yet (Profile completion: {prof_data['profile_completion']}%)\n"
                    f"Candidate message: {user_message}\n"
                    f"Available platform jobs: {json.dumps([{'title': j['title'], 'company': j['company'], 'location': j['location'], 'salary': j['salary']} for j in recommended[:3]])}\n\n"
                    f"Write a friendly response (under 3 sentences) explaining that they haven't added skills yet (mentioning {prof_data['profile_completion']}% completion) and advising them to complete their profile for tailored matching, while introducing the active platform openings."
                )
            else:
                unapplied_count = sum(1 for j in recommended if not j['already_applied'])
                reply = (
                    f"Based on your profile, skills in **{skills_str}**, and preferences, I found **{unapplied_count} matching job opening(s)** for you.\n\n"
                    f"You can click **Apply with Nexiv** on any card below, or simply tell me *'Apply to {recommended[0]['title']}'*."
                )
                llm_prompt = (
                    f"Candidate Name: {candidate_name}\n"
                    f"Candidate Skills: {skills_str}\n"
                    f"Candidate message: {user_message}\n"
                    f"Active recommended jobs: {json.dumps([{'title': j['title'], 'company': j['company'], 'location': j['location'], 'salary': j['salary']} for j in recommended[:3]])}\n\n"
                    f"Give a friendly, direct, concise answer (under 3 sentences) highlighting how these jobs match their skills ({skills_str}) and invite them to apply."
                )

        # Enhance reply with Gemini LLM if API key is present
        if llm_prompt and get_gemini_api_key():
            try:
                llm_res = call_gemini(
                    llm_prompt,
                    system_instruction="You are Nexiv, the intelligent AI Career Assistant for TN Jobz. Helpful, polite, and practical assistant for job candidates. You understand English and Tamil."
                )
                if llm_res.get("success") and llm_res.get("text"):
                    reply = llm_res["text"].strip()
            except Exception as llm_err:
                logger.warning(f"Gemini conversational reply notice: {llm_err}")

        suggested = ["Complete Profile", "Track my applications"] if not has_skills else ["Track my applications", "Show my applications"]
        if specific_requested and filter_term != "tamil nadu":
            suggested.insert(0, "Jobs in Tamil Nadu")
        elif not specific_requested and has_skills:
            suggested.insert(0, f"Apply to {recommended[0]['title']}" if recommended else "Jobs in Tamil Nadu")

        return Response({
            "reply": reply,
            "recommended_jobs": recommended,
            "suggested_actions": suggested
        })


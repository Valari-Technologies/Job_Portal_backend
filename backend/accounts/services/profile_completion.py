from ..models import Education, Experience


def calculate_candidate_profile_completion(candidate_profile, user=None):
    """
    Calculate dynamic completion percentage (15% to 100%) based on candidate's real profile data.
    """
    if not candidate_profile:
        return 0
    user = user or candidate_profile.user
    extra_data = candidate_profile.extra_data or {}

    db_educations_count = Education.objects.filter(candidate=candidate_profile).count() or len(extra_data.get('education') or [])
    db_experiences_count = Experience.objects.filter(candidate=candidate_profile).count() or len(extra_data.get('experiences') or [])
    resumes_count = candidate_profile.resumes.count() if hasattr(candidate_profile, 'resumes') else 0
    db_skills_count = candidate_profile.candidate_skills.count() if hasattr(candidate_profile, 'candidate_skills') else 0
    if not db_skills_count:
        db_skills_count = len(extra_data.get('programmingLanguages') or []) + len(extra_data.get('technologies') or [])

    full_name = candidate_profile.full_name or (f"{user.first_name} {user.last_name}".strip() if user else '') or (user.username if user else '')
    avatar_url = bool(user.profile_picture or candidate_profile.profile_photo)
    headline_text = candidate_profile.degree or ''
    location_text = candidate_profile.city or candidate_profile.state or ''
    summary_text = candidate_profile.address or ''
    phone_text = candidate_profile.phone or (user.phone_number if user else '')

    score = 15
    if full_name:
        score += 10
    if phone_text:
        score += 10
    if headline_text:
        score += 10
    if location_text:
        score += 5
    if summary_text:
        score += 10
    if avatar_url:
        score += 10
    if db_experiences_count > 0:
        score += 15
    if db_educations_count > 0:
        score += 10
    if db_skills_count > 0:
        score += 10
    if resumes_count > 0:
        score += 5

    completion_percentage = min(100, max(15, score))
    return completion_percentage

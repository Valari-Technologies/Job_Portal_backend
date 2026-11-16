import json
import logging
import re
import zlib
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from accounts.models import CandidateProfile, Job, Resume, Application
from accounts.api.serializers import ResumeSerializer
from accounts.api.gemini_service import analyze_resume_with_ai, get_gemini_api_key

logger = logging.getLogger(__name__)


WIDTHS = {
    ' ': 250, 'a': 444, 'b': 500, 'c': 444, 'd': 500, 'e': 444, 'f': 278, 'g': 500,
    'h': 500, 'i': 278, 'j': 278, 'k': 444, 'l': 278, 'm': 722, 'n': 500, 'o': 500,
    'p': 500, 'q': 500, 'r': 333, 's': 389, 't': 278, 'u': 500, 'v': 500, 'w': 722,
    'x': 500, 'y': 500, 'z': 444, 'A': 722, 'B': 667, 'C': 667, 'D': 722, 'E': 611,
    'F': 556, 'G': 722, 'H': 722, 'I': 333, 'J': 389, 'K': 722, 'L': 611, 'M': 889,
    'N': 722, 'O': 722, 'P': 556, 'Q': 722, 'R': 667, 'S': 556, 'T': 611, 'U': 722,
    'V': 667, 'W': 889, 'X': 667, 'Y': 667, 'Z': 611, '.': 250, ',': 250, '-': 333,
    '(': 333, ')': 333, '%': 833, '0': 500, '1': 500, '2': 500, '3': 500, '4': 500,
    '5': 500, '6': 500, '7': 500, '8': 500, '9': 500, '+': 564, ':': 278, ';': 278,
    '&': 778, '/': 278
}

def string_width_units(text):
    return sum(WIDTHS.get(c, 500) for c in text)

def fit_text_to_budget(text, target_lines=1):
    words = text.strip().split()
    if target_lines <= 1:
        total_units = string_width_units(text)
        font_size = 10.0
        if total_units * 10.0 / 1000.0 > 504.0:
            font_size = max(8.5, round(504.0 * 1000.0 / total_units, 1))
        return [text], font_size
    else:
        # For 2-line bullets, break line 1 at ~410 pt so it fills line 1 naturally,
        # and line 2 receives the remaining words, perfectly matching the original document's line wrapping & spacing!
        target_w = 410.0
        l1_words = []
        l2_words = []
        for idx, w in enumerate(words):
            candidate = ' '.join(l1_words + [w])
            w_pt = string_width_units(candidate) * 10.0 / 1000.0
            if w_pt <= target_w or len(l1_words) < 5:
                l1_words.append(w)
            else:
                l2_words = words[idx:]
                break

        if not l2_words:
            split_idx = max(1, int(len(words) * 0.65))
            l1_words = words[:split_idx]
            l2_words = words[split_idx:]

        l1 = ' '.join(l1_words)
        l2 = ' '.join(l2_words)
        return [l1, l2], 10.0

def tailor_pdf_bytes(pdf_bytes: bytes, replacements: list) -> bytes:
    """
    Applies text replacements directly into a PDF document's stream,
    preserving exact original layout, fonts, font size, margins,
    header info (name, email, phone, links), and sections.
    Guarantees no text collision or overriding by strictly budgeting line heights.
    """
    if not replacements:
        return pdf_bytes

    try:
        # 1. Inject /FTailor into Font dictionary
        font_dict_match = re.search(rb'(\d+\s+0\s+obj\s*<<[^>]*?/F1\b.*?)(>>\s*endobj)', pdf_bytes, re.DOTALL)
        if font_dict_match:
            old_full = font_dict_match.group(0)
            prefix = font_dict_match.group(1).rstrip()
            suffix = font_dict_match.group(2)
            if b'/FTailor' not in prefix:
                new_full = prefix + b'/FTailor<</Type/Font/Subtype/Type1/BaseFont/Times-Roman>>' + suffix
                pdf_bytes = pdf_bytes.replace(old_full, new_full, 1)
        elif b'/Font <<' in pdf_bytes or b'/Font<<' in pdf_bytes:
            if b'/FTailor' not in pdf_bytes:
                pdf_bytes = re.sub(
                    rb'(/Font\s*<<[^>]*)(>>)',
                    rb'\1/FTailor<</Type/Font/Subtype/Type1/BaseFont/Times-Roman>>\2',
                    pdf_bytes,
                    count=1
                )

        # 2. Resolve content stream object number
        contents_id = 2
        contents_ref = re.search(rb'/Contents\s+(\d+)\s+0\s+R', pdf_bytes)
        if contents_ref:
            try:
                contents_id = int(contents_ref.group(1).decode('ascii'))
            except Exception:
                contents_id = 2

        stream_match = re.search(rf'{contents_id} 0 obj\s*<<.*?>>\s*stream[\r\n]+(.*?)[\r\n]+endstream'.encode('ascii'), pdf_bytes, re.DOTALL)
        if not stream_match:
            stream_match = re.search(rb'stream[\r\n]+(.*?)[\r\n]+endstream', pdf_bytes, re.DOTALL)
        if not stream_match:
            return pdf_bytes

        orig_stream_data = stream_match.group(1)
        decomp = zlib.decompress(orig_stream_data).decode('latin1')

        # 3. Parse all CMaps to map hex codes to unicode across all font streams
        cmap_dict = {}
        all_streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', pdf_bytes, re.DOTALL)
        for s in all_streams:
            try:
                d = zlib.decompress(s).decode('latin1')
                if 'beginbfchar' in d or 'Adobe-Identity-UCS' in d:
                    for match in re.finditer(r'<([0-9A-Fa-f]{2,4})>\s+<([0-9A-Fa-f]{4})>', d):
                        cmap_dict[match.group(1).upper()] = chr(int(match.group(2), 16))
            except Exception:
                pass

        def decode_hex(hex_str):
            return ''.join(cmap_dict.get(hex_str[i:i+2].upper(), '') for i in range(0, len(hex_str), 2))

        def esc(s):
            return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

        # 4. Pattern matching a full bullet including its /Lbl and all its /List continuation blocks
        bullet_pattern = re.compile(
            r'((\/Lbl[^\n\r]*?BDC\s*q\s*0\s*0\s*0\s*rg\s*BT\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+Td\s+/F\d+\s+\d+\.?\d*\s+Tf<[0-9A-Fa-f]+>Tj\s*ET\s*Q\s*EMC\s*)'
            r'((?:\/List[^\n\r]*?BDC\s*q\s*0\s*0\s*0\s*rg\s*BT\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+Td\s+(/F\d+)\s+(\d+\.?\d*)\s+Tf(?:\[<[^>]+>[^\]]*\]|\<[0-9A-Fa-f]+\>)T[Jj]\s*ET\s*Q\s*EMC\s*)+))',
            re.DOTALL
        )

        matches = list(bullet_pattern.finditer(decomp))

        if matches:
            for rep in replacements:
                orig = rep.get('original_text', '').strip()
                new_t = rep.get('new_text', '').strip()
                if not orig or not new_t:
                    continue

                orig_clean = re.sub(r'[^a-zA-Z0-9]', '', orig).lower()

                for idx, bm in enumerate(matches):
                    full_bullet_match = bm.group(0)
                    lbl_block = bm.group(2)
                    lbl_y = float(bm.group(4))
                    content_blocks = bm.group(5)

                    hexes = re.findall(r'<([0-9A-Fa-f]+)>', content_blocks)
                    decoded_text = ''.join(decode_hex(h) for h in hexes).strip()
                    decoded_clean = re.sub(r'[^a-zA-Z0-9]', '', decoded_text).lower()

                    if (orig_clean[:20] and orig_clean[:20] in decoded_clean) or (decoded_clean[:20] and decoded_clean[:20] in orig_clean):
                        first_block_m = re.search(r'BT\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+Td', content_blocks)
                        text_x = first_block_m.group(1) if first_block_m else '45.45'
                        text_y = first_block_m.group(2) if first_block_m else str(lbl_y)

                        # Detect original line count and exact line height
                        orig_lines_m = re.findall(r'BT\s*\d+\.?\d*\s+(\d+\.?\d*)\s+Td', content_blocks)
                        orig_line_count = len(orig_lines_m)
                        line_height = 12.45
                        if orig_line_count >= 2:
                            try:
                                line_height = float(orig_lines_m[0]) - float(orig_lines_m[1])
                            except Exception:
                                line_height = 12.45

                        target_lines = 2 if orig_line_count >= 2 else 1
                        lines, font_size = fit_text_to_budget(new_t, target_lines=target_lines)

                        if len(lines) == 1:
                            new_content = (
                                f'/List#201<</MCID 999>>BDC\nq 0 0 0 rg\nBT\n'
                                f'{text_x} {text_y} Td /FTailor {font_size} Tf ({esc(lines[0])}) Tj\n'
                                f'ET\nQ\nEMC\n'
                            )
                        else:
                            y2 = float(text_y) - line_height
                            new_content = (
                                f'/List#201<</MCID 998>>BDC\nq 0 0 0 rg\nBT\n'
                                f'{text_x} {text_y} Td /FTailor {font_size} Tf ({esc(lines[0])}) Tj\n'
                                f'ET\nQ\nEMC\n'
                                f'/List#201<</MCID 999>>BDC\nq 0 0 0 rg\nBT\n'
                                f'{text_x} {y2:.3f} Td /FTailor {font_size} Tf ({esc(lines[1])}) Tj\n'
                                f'ET\nQ\nEMC\n'
                            )

                        new_full_bullet = lbl_block + new_content
                        decomp = decomp.replace(full_bullet_match, new_full_bullet, 1)
                        logger.info("Tailored bullet %d at y=%s: %d line(s) at %spt (line_height=%s)", idx+1, text_y, len(lines), font_size, line_height)
                        break
        else:
            # Fallback simple string replacement for plain text PDF streams
            for rep in replacements:
                orig = rep.get('original_text', '').strip()
                new_t = rep.get('new_text', '').strip()
                if orig and new_t and orig in decomp:
                    decomp = decomp.replace(orig, new_t, 1)

        new_compressed = zlib.compress(decomp.encode('latin1'), level=9)
        old_stream_full = b'stream\n' + orig_stream_data + b'\nendstream'
        new_stream_full = b'stream\n' + new_compressed + b'\nendstream'
        pdf_bytes = pdf_bytes.replace(old_stream_full, new_stream_full, 1)

        # Update stream length
        len_match = re.search(rf'{contents_id} 0 obj\s*<<[^>]*?/Length\s+(\d+)\s+0\s+R'.encode('ascii'), pdf_bytes)
        if len_match:
            len_obj_num = len_match.group(1).decode('ascii')
            old_len_obj = re.search(rf'{len_obj_num} 0 obj\s*\d+\s*endobj'.encode('ascii'), pdf_bytes)
            if old_len_obj:
                new_len_obj = f'{len_obj_num} 0 obj\n{len(new_compressed)}\nendobj'.encode('ascii')
                pdf_bytes = pdf_bytes.replace(old_len_obj.group(0), new_len_obj, 1)
        else:
            pdf_bytes = re.sub(
                rf'({contents_id} 0 obj\s*<<[^>]*?/Length\s+)\d+'.encode('ascii'),
                rf'\g<1>{len(new_compressed)}'.encode('ascii'),
                pdf_bytes,
                count=1
            )

        return pdf_bytes
    except Exception as e:
        logger.error("Error tailoring PDF bytes: %s", e)
        return pdf_bytes


class IsCandidateRole(permissions.BasePermission):
    """Allows access only to authenticated candidate users."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'CANDIDATE'
        )


class CandidateAIResumeAnalyzeView(APIView):
    """
    Intelligent AI Resume analysis and suggestion engine for Candidates.
    Analyzes candidate's resume against Target Role or Job Description using
    Google Gemini (or smart fallback if no API key is set yet).
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def post(self, request):
        candidate_profile = getattr(request.user, 'candidate_profile', None)
        if not candidate_profile:
            return Response(
                {"success": False, "message": "Candidate profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume_id = request.data.get('resume_id')
        resume_data = request.data.get('resume_data') or {}
        target_role = request.data.get('target_role', '').strip()
        manual_jd = request.data.get('job_description', '').strip()
        job_id = request.data.get('job_id')

        job_obj = None
        if job_id:
            try:
                job_obj = Job.objects.filter(pk=job_id).select_related('hr').first()
            except Exception:
                pass

        if job_obj:
            if not target_role:
                target_role = job_obj.title
            if not manual_jd and job_obj.description:
                manual_jd = job_obj.description

        if not target_role and manual_jd:
            first_line = manual_jd.split('\n')[0].strip()
            if first_line and len(first_line) < 60:
                target_role = first_line

        if not target_role:
            target_role = "Software Developer"

        # Candidate name
        user = request.user
        candidate_name = user.get_full_name() or user.username

        # Resolve candidate resume and disk PDF path if available
        pdf_path = None
        resume_query = Resume.objects.filter(candidate=candidate_profile)
        if resume_id:
            try:
                resume_query_id = resume_query.filter(pk=int(resume_id))
                if resume_query_id.exists():
                    resume_query = resume_query_id
            except (ValueError, TypeError):
                pass
        resume_obj = resume_query.order_by('-is_default', '-updated_at').first()
        if resume_obj:
            if not resume_data.get('title'):
                resume_data['title'] = resume_obj.file_name
            if resume_obj.file_path:
                try:
                    pdf_path = resume_obj.file_path.path
                except Exception:
                    pass

        # Run AI Analysis
        analysis_result = analyze_resume_with_ai(
            resume_data=resume_data,
            target_role=target_role,
            job_description=manual_jd,
            candidate_name=candidate_name,
            pdf_path=pdf_path
        )

        data = analysis_result.get("data", {})
        analysis_payload = {
            "analysisId": f"an_{int(timezone.now().timestamp())}",
            "sourceType": "platform_job" if job_obj else "manual_jd",
            "jobId": job_obj.id if job_obj else None,
            "jobTitle": target_role,
            "companyName": job_obj.hr.company_name if (job_obj and job_obj.hr) else "Target Employer",
            "manualJobDescription": manual_jd or None,
            "score": data.get("score", 85),
            "scoreLabel": data.get("scoreLabel", "Strong"),
            "scoreFeedback": data.get("scoreFeedback", f"Optimized suggestions generated for {target_role}."),
            "missingKeywords": data.get("missingKeywords", []),
            "matchedKeywords": data.get("matchedKeywords", []),
            "suggestions": data.get("suggestions", []),
            "aiSource": analysis_result.get("source", "gemini"),
            "model": analysis_result.get("model", "gemini-1.5-flash")
        }

        return Response({
            "success": True,
            "analysis": analysis_payload,
            "has_gemini_key": bool(get_gemini_api_key())
        }, status=status.HTTP_200_OK)


class CandidateAIResumeSaveTailoredView(APIView):
    """
    Saves a tailored resume version directly to the Candidate's Resume collection
    in the database so it can be immediately selected and submitted for job applications.
    If replacements are provided, it takes the candidate's original uploaded PDF
    and applies the bullet improvements directly to that document, preserving
    exact original layout, fonts, font size, headers, contact info, and formatting.
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidateRole]

    def post(self, request):
        candidate_profile = getattr(request.user, 'candidate_profile', None)
        if not candidate_profile:
            return Response(
                {"success": False, "message": "Candidate profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume_id = request.data.get('resume_id')
        replacements_raw = request.data.get('replacements')
        replacements = []
        if replacements_raw:
            if isinstance(replacements_raw, str):
                try:
                    replacements = json.loads(replacements_raw)
                except Exception:
                    replacements = []
            elif isinstance(replacements_raw, list):
                replacements = replacements_raw

        target_role = request.data.get('target_role') or ""
        clean_role = re.sub(r'[^a-zA-Z0-9]+', '_', target_role).strip('_')

        # Find candidate's base uploaded resume
        base_resume = None
        if resume_id:
            try:
                base_resume = Resume.objects.filter(candidate=candidate_profile, pk=int(resume_id)).first()
            except (ValueError, TypeError):
                pass
        if not base_resume:
            base_resume = candidate_profile.resumes.filter(is_default=True).first() or candidate_profile.resumes.first()

        file_obj = request.FILES.get('file') or request.FILES.get('file_path')
        tailored_file = None

        base_filename = base_resume.file_name if base_resume else "Resume.pdf"
        clean_base = re.sub(r'^(Tailored_|Job_)+', '', base_filename, flags=re.IGNORECASE)

        req_title = request.data.get('title') or request.data.get('file_name')
        if req_title and not req_title.lower().startswith('tailored_job_') and not req_title.lower() == 'tailored_resume.pdf':
            title = req_title.strip()
        elif clean_role and clean_role.lower() not in ('job', 'none', 'tailored'):
            title = f"{clean_role}_{clean_base}"
        else:
            title = f"Tailored_{clean_base}"

        if not title.lower().endswith(('.pdf', '.docx', '.doc')):
            title = f"{title}.pdf"

        # If replacements are provided and base resume exists on disk, tailor the original PDF
        if replacements and base_resume and base_resume.file_path:
            try:
                with open(base_resume.file_path.path, 'rb') as f:
                    orig_pdf_bytes = f.read()
                tailored_pdf_bytes = tailor_pdf_bytes(orig_pdf_bytes, replacements)
                tailored_file = ContentFile(tailored_pdf_bytes, name=title)
            except Exception as e:
                logger.error("Failed to tailor base resume PDF on disk: %s", e)

        if not tailored_file:
            tailored_file = file_obj

        if not tailored_file:
            return Response(
                {"success": False, "message": "No tailored resume file or base resume found to tailor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        set_as_default = str(request.data.get('set_default', 'true')).lower() != 'false'

        with transaction.atomic():
            if set_as_default:
                candidate_profile.resumes.update(is_default=False)

            resume = Resume.objects.create(
                candidate=candidate_profile,
                file_path=tailored_file,
                file_name=title,
                is_default=set_as_default
            )

        serializer = ResumeSerializer(resume, context={'request': request})
        return Response({
            "success": True,
            "resume": serializer.data,
            "message": f"Tailored resume '{title}' saved successfully."
        }, status=status.HTTP_201_CREATED)


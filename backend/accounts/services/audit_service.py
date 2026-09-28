import logging
from accounts.models import AuditEvent

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit_event(
    actor=None,
    action="",
    target_type=None,
    target_id=None,
    target_repr=None,
    outcome="SUCCESS",
    description="",
    request=None,
    actor_email=None
):
    """
    Safely records an audit event in the database.
    Append-only: Never stores or exposes raw passwords, hashes, JWTs, or tokens.
    Guaranteed not to raise an exception if logging fails.
    """
    try:
        ip_address = get_client_ip(request) if request else None

        actor_user = None
        email = actor_email

        if actor and hasattr(actor, 'is_authenticated') and actor.is_authenticated:
            actor_user = actor
            email = getattr(actor, 'email', None) or email
        elif actor and hasattr(actor, 'email'):
            email = getattr(actor, 'email', None) or email

        AuditEvent.objects.create(
            actor=actor_user,
            actor_email=email,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            target_repr=target_repr,
            outcome=outcome,
            description=description,
            ip_address=ip_address
        )
    except Exception as exc:
        logger.error("Failed to write audit log entry: %s", exc)

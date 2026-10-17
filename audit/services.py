from .models import AuditLog


def _client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(user, action, obj=None, detail="", request=None):
    """
    Record one audit entry. Called explicitly from views right after the
    action succeeds, so it always has a concrete user/object rather than
    relying on signals that can fire for unrelated internal saves.
    """
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else "",
        object_id=str(getattr(obj, "pk", "")) if obj is not None else "",
        detail=detail[:255],
        ip_address=_client_ip(request),
    )

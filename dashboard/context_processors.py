from django.conf import settings
from django.db.models import Sum


def storage_summary(request):
    """
    Makes a storage-usage summary available in every template (used by
    the navbar's "Storage: X used / Y" bar from Section 17.1's example
    dashboard layout) without every view having to compute it manually.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    from storage_app.models import FileObject

    used_bytes = (
        FileObject.objects.filter(owner=user, is_deleted=False).aggregate(total=Sum("size_bytes"))["total"] or 0
    )
    quota_bytes = settings.DEFAULT_USER_QUOTA_BYTES
    percent_used = min(100, round((used_bytes / quota_bytes) * 100, 1)) if quota_bytes else 0

    return {
        "storage_summary": {
            "used_bytes": used_bytes,
            "quota_bytes": quota_bytes,
            "percent_used": percent_used,
        }
    }

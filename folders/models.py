from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Folder(models.Model):
    """
    A user-owned folder that can nest inside another folder of the same
    user, per Section 4: "Create, rename, move and delete folders and
    subfolders."
    """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="folders")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    name = models.CharField(max_length=255)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "parent", "name"],
                name="unique_folder_name_per_parent",
            )
        ]
        indexes = [
            models.Index(fields=["owner", "parent"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        # A folder can never become its own ancestor (Section 4 implies
        # folders form a tree; nothing in a tree should cycle back).
        node = self.parent
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError("A folder cannot be moved inside itself or one of its own subfolders.")
            node = node.parent

    def get_absolute_url(self):
        return reverse("folders:detail", args=[self.pk])

    def get_ancestors(self):
        """Return the chain of parent folders, root first, for breadcrumbs."""
        ancestors = []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        return list(reversed(ancestors))

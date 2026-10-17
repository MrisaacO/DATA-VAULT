import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("login", "Logged in"),
                            ("logout", "Logged out"),
                            ("upload", "Uploaded file"),
                            ("download", "Downloaded file"),
                            ("preview", "Previewed file"),
                            ("rename", "Renamed item"),
                            ("move", "Moved item"),
                            ("favourite", "Toggled favourite"),
                            ("soft_delete", "Sent to recycle bin"),
                            ("restore", "Restored from recycle bin"),
                            ("permanent_delete", "Permanently deleted"),
                            ("archive", "Archived"),
                            ("unarchive", "Restored from archive"),
                            ("create_folder", "Created folder"),
                            ("create_note", "Created note"),
                            ("edit_note", "Edited note"),
                            ("search", "Performed search"),
                        ],
                        max_length=30,
                    ),
                ),
                ("object_type", models.CharField(blank=True, max_length=50)),
                ("object_id", models.CharField(blank=True, max_length=50)),
                ("detail", models.CharField(blank=True, max_length=255)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["user", "-created_at"], name="audit_audit_user_id_5e4c34_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["object_type", "object_id"], name="audit_audit_object__f0b3e1_idx"),
        ),
    ]

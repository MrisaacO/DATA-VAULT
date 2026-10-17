import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import storage_app.services


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("folders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FileObject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(max_length=700, upload_to=storage_app.services.storage_key_upload_to)),
                ("original_name", models.CharField(max_length=255)),
                ("storage_key", models.CharField(blank=True, max_length=700, null=True, unique=True)),
                ("mime_type", models.CharField(max_length=150)),
                ("category", models.CharField(blank=True, max_length=30)),
                ("size_bytes", models.BigIntegerField(default=0)),
                ("checksum", models.CharField(blank=True, max_length=128)),
                ("tags", models.CharField(blank=True, help_text="Comma-separated tags", max_length=255)),
                ("is_favourite", models.BooleanField(default=False)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "storage_tier",
                    models.CharField(
                        choices=[("active", "Active"), ("archived", "Archived")],
                        default="active",
                        max_length=30,
                    ),
                ),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("width", models.PositiveIntegerField(blank=True, null=True)),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "folder",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="folders.folder",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["original_name"],
            },
        ),
        migrations.AddIndex(
            model_name="fileobject",
            index=models.Index(fields=["owner", "is_deleted"], name="storage_app_owner_i_d1f1b8_idx"),
        ),
        migrations.AddIndex(
            model_name="fileobject",
            index=models.Index(fields=["owner", "folder"], name="storage_app_owner_i_3a2e77_idx"),
        ),
        migrations.AddIndex(
            model_name="fileobject",
            index=models.Index(fields=["owner", "storage_tier"], name="storage_app_owner_i_9c4f52_idx"),
        ),
        migrations.AddIndex(
            model_name="fileobject",
            index=models.Index(fields=["owner", "is_favourite"], name="storage_app_owner_i_6e1d20_idx"),
        ),
    ]

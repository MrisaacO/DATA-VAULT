import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from folders.models import Folder

from .models import FileObject

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="pdv_test_media_")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FileUploadAndOwnershipTests(TestCase):
    """
    Covers the guide's Definition of Done items: upload validation,
    strict per-owner isolation (Section 25.2), and the recycle bin
    lifecycle (Section 14.1).
    """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")
        self.bob = User.objects.create_user("bob", password="bob-pass-123")
        self.client.login(username="alice", password="alice-pass-123")

    def test_upload_rejects_disallowed_extension(self):
        bad_file = SimpleUploadedFile("virus.exe", b"not really a virus", content_type="application/octet-stream")
        response = self.client.post(reverse("storage_app:upload"), {"files": [bad_file]}, follow=True)
        self.assertEqual(FileObject.objects.count(), 0)
        self.assertContains(response, "not allowed")

    def test_upload_rejects_oversized_file(self):
        from django.conf import settings

        oversized = SimpleUploadedFile(
            "big.txt", b"x" * (settings.MAX_UPLOAD_SIZE_BYTES + 1), content_type="text/plain"
        )
        response = self.client.post(reverse("storage_app:upload"), {"files": [oversized]}, follow=True)
        self.assertEqual(FileObject.objects.count(), 0)
        self.assertContains(response, "upload limit")

    def test_successful_upload_creates_metadata_and_stores_file(self):
        upload = SimpleUploadedFile("notes.txt", b"hello vault", content_type="text/plain")
        self.client.post(reverse("storage_app:upload"), {"files": [upload]}, follow=True)

        self.assertEqual(FileObject.objects.count(), 1)
        file_obj = FileObject.objects.get()
        self.assertEqual(file_obj.owner, self.alice)
        self.assertEqual(file_obj.original_name, "notes.txt")
        self.assertEqual(file_obj.category, "document")
        self.assertTrue(file_obj.checksum)  # SHA-256 was computed

    def test_user_cannot_access_another_users_file(self):
        upload = SimpleUploadedFile("secret.txt", b"alice's secret", content_type="text/plain")
        self.client.post(reverse("storage_app:upload"), {"files": [upload]})
        file_obj = FileObject.objects.get()

        self.client.logout()
        self.client.login(username="bob", password="bob-pass-123")

        response = self.client.get(reverse("storage_app:detail", args=[file_obj.pk]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("storage_app:download", args=[file_obj.pk]))
        self.assertEqual(response.status_code, 404)

    def test_soft_delete_then_restore_round_trip(self):
        upload = SimpleUploadedFile("todo.txt", b"buy milk", content_type="text/plain")
        self.client.post(reverse("storage_app:upload"), {"files": [upload]})
        file_obj = FileObject.objects.get()

        self.client.post(reverse("storage_app:delete", args=[file_obj.pk]))
        file_obj.refresh_from_db()
        self.assertTrue(file_obj.is_deleted)

        # A soft-deleted file is invisible to the normal detail view...
        response = self.client.get(reverse("storage_app:detail", args=[file_obj.pk]))
        self.assertEqual(response.status_code, 404)

        # ...but restorable from the recycle bin.
        self.client.post(reverse("storage_app:restore", args=[file_obj.pk]))
        file_obj.refresh_from_db()
        self.assertFalse(file_obj.is_deleted)
        self.assertIsNone(file_obj.deleted_at)

    def test_permanent_delete_removes_the_database_record(self):
        upload = SimpleUploadedFile("temp.txt", b"scratch", content_type="text/plain")
        self.client.post(reverse("storage_app:upload"), {"files": [upload]})
        file_obj = FileObject.objects.get()
        self.client.post(reverse("storage_app:delete", args=[file_obj.pk]))

        self.client.post(reverse("storage_app:permanent_delete", args=[file_obj.pk]))
        self.assertEqual(FileObject.objects.filter(pk=file_obj.pk).count(), 0)

    def test_upload_into_someone_elses_folder_is_rejected(self):
        bob_folder = Folder.objects.create(owner=self.bob, name="Bob's stuff")
        upload = SimpleUploadedFile("sneaky.txt", b"data", content_type="text/plain")
        response = self.client.post(
            reverse("storage_app:upload_to_folder", args=[bob_folder.pk]), {"files": [upload]}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(FileObject.objects.count(), 0)

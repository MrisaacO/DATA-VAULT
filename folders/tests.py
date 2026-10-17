from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Folder


class FolderModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")

    def test_folder_cannot_be_moved_into_itself(self):
        folder = Folder.objects.create(owner=self.alice, name="Projects")
        folder.parent = folder
        with self.assertRaises(ValidationError):
            folder.clean()

    def test_folder_cannot_be_moved_into_its_own_descendant(self):
        parent = Folder.objects.create(owner=self.alice, name="Parent")
        child = Folder.objects.create(owner=self.alice, name="Child", parent=parent)
        parent.parent = child
        with self.assertRaises(ValidationError):
            parent.clean()

    def test_same_named_folder_allowed_in_different_parents(self):
        parent_a = Folder.objects.create(owner=self.alice, name="A")
        parent_b = Folder.objects.create(owner=self.alice, name="B")
        Folder.objects.create(owner=self.alice, name="Photos", parent=parent_a)
        # Should not raise: same name, different parent.
        Folder.objects.create(owner=self.alice, name="Photos", parent=parent_b)
        self.assertEqual(Folder.objects.filter(name="Photos").count(), 2)


class FolderOwnershipTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")
        self.bob = User.objects.create_user("bob", password="bob-pass-123")
        self.alice_folder = Folder.objects.create(owner=self.alice, name="Alice Folder")

    def test_other_user_cannot_view_folder(self):
        self.client.login(username="bob", password="bob-pass-123")
        response = self.client.get(reverse("folders:detail", args=[self.alice_folder.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_rename_folder(self):
        self.client.login(username="bob", password="bob-pass-123")
        response = self.client.post(
            reverse("folders:rename", args=[self.alice_folder.pk]), {"name": "Hacked"}
        )
        self.assertEqual(response.status_code, 404)
        self.alice_folder.refresh_from_db()
        self.assertEqual(self.alice_folder.name, "Alice Folder")

    def test_owner_can_soft_delete_and_it_leaves_recycle_bin_visible(self):
        self.client.login(username="alice", password="alice-pass-123")
        self.client.post(reverse("folders:delete", args=[self.alice_folder.pk]))
        self.alice_folder.refresh_from_db()
        self.assertTrue(self.alice_folder.is_deleted)

        response = self.client.get(reverse("storage_app:recycle_bin"))
        self.assertContains(response, "Alice Folder")


class FolderFormValidationTests(TestCase):
    """
    Regression coverage for a real bug caught while reviewing this
    scaffold: FolderForm used to call Folder.full_clean() inside save(),
    which raises an uncaught ValidationError (-> 500 response) on a
    duplicate (owner, parent, name). It's now checked up front in
    FolderForm.clean_name() instead, surfacing as a normal form error.
    """

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")
        self.client.login(username="alice", password="alice-pass-123")

    def test_duplicate_top_level_folder_name_is_a_form_error_not_a_crash(self):
        Folder.objects.create(owner=self.alice, name="Photos")

        response = self.client.post(reverse("folders:create"), {"name": "Photos"})

        self.assertEqual(response.status_code, 200)  # re-rendered form, not a redirect
        self.assertContains(response, "already exists")
        self.assertEqual(Folder.objects.filter(owner=self.alice, name="Photos").count(), 1)

    def test_renaming_a_folder_to_its_own_current_name_is_allowed(self):
        folder = Folder.objects.create(owner=self.alice, name="Photos")
        response = self.client.post(reverse("folders:rename", args=[folder.pk]), {"name": "Photos"}, follow=True)
        self.assertEqual(response.status_code, 200)
        folder.refresh_from_db()
        self.assertEqual(folder.name, "Photos")

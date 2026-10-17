from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Note


class NoteCrudAndOwnershipTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")
        self.bob = User.objects.create_user("bob", password="bob-pass-123")
        self.client.login(username="alice", password="alice-pass-123")

    def test_create_note(self):
        response = self.client.post(
            reverse("notes:create"), {"title": "Wifi password", "content": "hunter2", "is_pinned": False}
        )
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.owner, self.alice)
        self.assertRedirects(response, note.get_absolute_url())

    def test_other_user_cannot_read_or_edit_note(self):
        note = Note.objects.create(owner=self.alice, title="Private", content="Shh")
        self.client.logout()
        self.client.login(username="bob", password="bob-pass-123")

        self.assertEqual(self.client.get(reverse("notes:detail", args=[note.pk])).status_code, 404)
        self.assertEqual(
            self.client.post(reverse("notes:edit", args=[note.pk]), {"title": "Hacked", "content": "x"}).status_code,
            404,
        )
        note.refresh_from_db()
        self.assertEqual(note.title, "Private")

    def test_soft_delete_and_restore(self):
        note = Note.objects.create(owner=self.alice, title="Temp", content="x")
        self.client.post(reverse("notes:delete", args=[note.pk]))
        note.refresh_from_db()
        self.assertTrue(note.is_deleted)

        self.client.post(reverse("notes:restore", args=[note.pk]))
        note.refresh_from_db()
        self.assertFalse(note.is_deleted)

    def test_favourite_toggle_requires_post(self):
        note = Note.objects.create(owner=self.alice, title="Star me", content="x")
        # A GET should not mutate state.
        self.client.get(reverse("notes:toggle_favourite", args=[note.pk]))
        note.refresh_from_db()
        self.assertFalse(note.is_favourite)

        self.client.post(reverse("notes:toggle_favourite", args=[note.pk]))
        note.refresh_from_db()
        self.assertTrue(note.is_favourite)

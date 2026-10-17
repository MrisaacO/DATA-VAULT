from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from storage_app.models import FileObject


class SearchScopingTests(TestCase):
    """Search must never surface another user's files or notes (Section 25.2)."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="alice-pass-123")
        self.bob = User.objects.create_user("bob", password="bob-pass-123")

        Note.objects.create(owner=self.alice, title="Alice budget", content="numbers")
        Note.objects.create(owner=self.bob, title="Bob budget", content="numbers")

        FileObject.objects.create(
            owner=self.alice,
            original_name="alice-budget.pdf",
            storage_key="k1",
            mime_type="application/pdf",
            size_bytes=100,
        )
        FileObject.objects.create(
            owner=self.bob,
            original_name="bob-budget.pdf",
            storage_key="k2",
            mime_type="application/pdf",
            size_bytes=100,
        )

        self.client.login(username="alice", password="alice-pass-123")

    def test_search_only_returns_own_items(self):
        response = self.client.get(reverse("search_app:search"), {"q": "budget"})
        self.assertContains(response, "Alice budget")
        self.assertContains(response, "alice-budget.pdf")
        self.assertNotContains(response, "Bob budget")
        self.assertNotContains(response, "bob-budget.pdf")

    def test_empty_search_returns_nothing(self):
        response = self.client.get(reverse("search_app:search"))
        self.assertFalse(response.context["has_search"])

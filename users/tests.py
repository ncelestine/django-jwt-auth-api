# users/tests.py
#
# Test suite:
# - JWT-based user registration & login
# - Book Catalog API with ownership rules
# - Integration test of full flow

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from books.models import Book


class AuthenticationTests(APITestCase):
    """
    Unit tests for user registration and JWT-based login.
    """

    def test_register_user_success(self):
        """
        A user can successfully register with valid data.
        """
        url = reverse("register")
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertNotIn("password", response.data)

    def test_register_user_missing_password_fails(self):
        """
        Registration fails when required fields are missing (e.g., password).
        """
        url = reverse("register")
        payload = {
            "username": "baduser",
            "email": "bad@example.com",
            # no password
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def setUp(self):
        """
        Create a user to test login.
        """
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123",
        )

    def test_login_returns_jwt_tokens_on_valid_credentials(self):
        """
        A user can log in and receive JWT access & refresh tokens.
        """
        url = reverse("login")
        payload = {
            "username": "testuser",
            "password": "TestPass123",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # SimpleJWT returns "access" and "refresh"
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        # We also configured it to return user info
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_login_fails_with_incorrect_credentials(self):
        """
        Login fails with wrong password and returns 401.
        """
        url = reverse("login")
        payload = {
            "username": "testuser",
            "password": "WrongPass",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class BookManagementTests(APITestCase):
    """
    Unit tests for Book Catalog endpoints.
    """

    def setUp(self):
        # Two users: one book owner, one "other" user
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="OwnerPass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="OtherPass123",
        )

    def _get_access_token(self, user):
        """
        Helper to generate a JWT access token for a given user.
        """
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_create_book_fails_when_not_authenticated(self):
        """
        Creating a book should fail if the user is not authenticated.
        """
        url = reverse("book-list-create")
        payload = {
            "title": "Unauth Book",
            "author": "No One",
            "description": "Should not be created",
        }

        response = self.client.post(url, payload, format="json")

        # Unauthenticated user -> 401 (JWT is the first authentication class,
        # so DRF sends a WWW-Authenticate challenge instead of a 403)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_book(self):
        """
        Authenticated user can successfully create a book.
        """
        access = self._get_access_token(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        url = reverse("book-list-create")
        payload = {
            "title": "My Book",
            "author": "Owner User",
            "description": "A test book",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.first()
        self.assertEqual(book.owner, self.owner)
        self.assertEqual(book.title, "My Book")

    def test_book_owner_can_update_and_delete_book(self):
        """
        The book owner can update and delete their own book.
        """
        # Create a book owned by self.owner
        book = Book.objects.create(
            owner=self.owner,
            title="Original Title",
            author="Original Author",
            description="Original description",
        )

        access = self._get_access_token(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        detail_url = reverse("book-detail", args=[book.id])

        # Update (PUT or PATCH)
        update_payload = {
            "title": "Updated Title",
            "author": "Updated Author",
            "description": "Updated description",
        }
        update_resp = self.client.put(detail_url, update_payload, format="json")
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.title, "Updated Title")

        # Delete
        delete_resp = self.client.delete(detail_url, format="json")
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_other_user_cannot_update_or_delete_book(self):
        """
        Any user who is not the owner should be forbidden (403) from
        updating or deleting the book.
        """
        book = Book.objects.create(
            owner=self.owner,
            title="Owner's Book",
            author="Owner Author",
            description="Protected book",
        )

        access = self._get_access_token(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        detail_url = reverse("book-detail", args=[book.id])

        # Attempt to update
        update_payload = {
            "title": "Hacked Title",
            "author": "Hacker",
            "description": "Hacked",
        }
        update_resp = self.client.put(detail_url, update_payload, format="json")
        self.assertEqual(update_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to delete
        delete_resp = self.client.delete(detail_url, format="json")
        self.assertEqual(delete_resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(id=book.id).exists())

    def test_authenticated_user_can_view_all_books(self):
        """
        Any authenticated user can view the full book catalog.
        """
        # Create books with different owners
        Book.objects.create(
            owner=self.owner,
            title="Owner Book",
            author="Owner Author",
            description="Owner's description",
        )
        Book.objects.create(
            owner=self.other_user,
            title="Other Book",
            author="Other Author",
            description="Other's description",
        )

        access = self._get_access_token(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        url = reverse("book-list-create")
        resp = self.client.get(url, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        titles = {b["title"] for b in resp.data}
        self.assertIn("Owner Book", titles)
        self.assertIn("Other Book", titles)


class IntegrationFlowTests(APITestCase):
    """
    Integration test for the full workflow:
      - Register
      - Login (JWT)
      - Create a book
      - Enforce access control
    """

    def test_full_workflow_registration_login_create_book(self):
        # 1) Register a new user
        reg_url = reverse("register")
        reg_payload = {
            "username": "flowuser",
            "email": "flowuser@example.com",
            "password": "FlowPass123",
        }
        reg_resp = self.client.post(reg_url, reg_payload, format="json")
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="flowuser").exists())

        # 2) Login to get JWT tokens
        login_url = reverse("login")
        login_payload = {
            "username": "flowuser",
            "password": "FlowPass123",
        }
        login_resp = self.client.post(login_url, login_payload, format="json")
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        access = login_resp.data["access"]

        # 3) Use access token to create a book
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        books_url = reverse("book-list-create")
        book_payload = {
            "title": "Flow Book",
            "author": "Flow User",
            "description": "Book created in integration test",
        }
        book_resp = self.client.post(books_url, book_payload, format="json")
        self.assertEqual(book_resp.status_code, status.HTTP_201_CREATED)
        book_id = book_resp.data["id"]

        # 4) Confirm that another user cannot delete that book
        other_user = User.objects.create_user(
            username="otherflow",
            email="otherflow@example.com",
            password="OtherFlow123",
        )
        refresh_other = RefreshToken.for_user(other_user)
        other_access = str(refresh_other.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_access}")

        detail_url = reverse("book-detail", args=[book_id])
        delete_resp = self.client.delete(detail_url, format="json")
        self.assertEqual(delete_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Original book should still exist
        self.assertTrue(Book.objects.filter(id=book_id).exists())


class RoleAndLogoutTests(APITestCase):
    """
    Tests for admin-only and group-based (manager) routes, and JWT logout.
    """

    def setUp(self):
        from django.contrib.auth.models import Group

        self.password = "StrongPass123"
        self.user = User.objects.create_user(username="regular", password=self.password)
        self.admin = User.objects.create_user(username="boss", password=self.password, is_staff=True)
        self.manager = User.objects.create_user(username="mgr", password=self.password)
        self.manager.groups.add(Group.objects.create(name="manager"))

    def auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return refresh

    def test_admin_only_route(self):
        self.auth(self.user)
        self.assertEqual(self.client.get(reverse("admin-only")).status_code, status.HTTP_403_FORBIDDEN)
        self.auth(self.admin)
        self.assertEqual(self.client.get(reverse("admin-only")).status_code, status.HTTP_200_OK)

    def test_manager_only_route(self):
        self.auth(self.user)
        self.assertEqual(self.client.get(reverse("manager-only")).status_code, status.HTTP_403_FORBIDDEN)
        self.auth(self.manager)
        self.assertEqual(self.client.get(reverse("manager-only")).status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        refresh = self.auth(self.user)
        response = self.client.post(reverse("logout"), {"refresh": str(refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # The blacklisted refresh token can no longer be used
        self.client.credentials()
        retry = self.client.post("/users/token/refresh/", {"refresh": str(refresh)}, format="json")
        self.assertNotEqual(retry.status_code, status.HTTP_200_OK)

    def test_cannot_log_out_another_user(self):
        other_refresh = RefreshToken.for_user(self.admin)
        self.auth(self.user)
        response = self.client.post(reverse("logout"), {"refresh": str(other_refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

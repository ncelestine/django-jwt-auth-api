# Django JWT Auth API — Authentication, Authorization and Testing

A REST API built with **Django REST Framework** that shows the main patterns for securing an API: user registration, **JWT** login, logout by token blacklisting, admin-only and group-based routes, and **object-level permissions** on a book catalogue. It comes with an automated test suite.

## Features

**Authentication**
- Register with a hashed password; the password is write-only and never returned
- Log in to get JWT **access and refresh tokens**, with extra user details in the response
- Refresh an access token
- **Log out by blacklisting the refresh token**, so it can't be used again; users can only revoke their own tokens

**Authorization**
- `/users/me/` is for logged-in users only
- `/users/admin-only/` is for staff users only (`IsAdminUser`)
- `/users/manager-only/` uses a **custom permission** that checks membership of the `manager` group

**Book catalogue (object-level permissions)**
- Any logged-in user can list and view books
- The person who creates a book is automatically set as its owner
- A custom `IsOwnerOrReadOnly` permission means only the owner can edit or delete a book

## Endpoints

| Method | Endpoint | Access |
|---|---|---|
| POST | `/users/register/` | Public |
| POST | `/users/login/` | Public: returns access and refresh tokens |
| POST | `/users/token/refresh/` | Public: needs a valid refresh token |
| POST | `/users/logout/` | Logged in: body `{"refresh": "<token>"}` |
| GET | `/users/me/` | Logged in |
| GET | `/users/admin-only/` | Staff only |
| GET | `/users/manager-only/` | `manager` group only |
| GET, POST | `/books/` | Logged in |
| GET | `/books/<id>/` | Logged in |
| PUT, PATCH, DELETE | `/books/<id>/` | Owner only |

Send the access token with each request:

```
Authorization: Bearer <access_token>
```

## Tests

The test suite (`users/tests.py`, 14 tests) covers:
- Registration that succeeds, and registration that fails when data is missing
- JWT login with correct and incorrect passwords
- Creating books with and without logging in
- Owners can edit and delete their books; other users get **403 Forbidden**
- Admin-only and manager-only routes reject regular users
- Logout blacklists the refresh token, and one user can't revoke another user's token
- An **end-to-end flow**: register → log in → create a book → another user tries to delete it

```bash
python manage.py test
```

## Running it locally

```bash
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser    # for the admin-only route and /admin/
python manage.py runserver
```

To try the manager route, create a group called `manager` in the Django admin and add a user to it.

For anything other than local development, set `DJANGO_SECRET_KEY` to a long random value and `DJANGO_DEBUG=False`.

## Tech stack

Python · Django · Django REST Framework · SimpleJWT (with token blacklist) · SQLite

# Personal Data Vault — Version 1

A secure, web-based personal data storage, backup and archiving system,
built from the accompanying **Personal Data Vault Complete Development
Guide**. This is Version 1 of the "Final Recommended Build Path"
(guide Section 26): Django + SQLite + the local `media/` folder, with the
production upgrade path (PostgreSQL + private S3-compatible storage)
already wired up as a second settings module.

## What's implemented (guide Appendix B — Definition of Done for Version 1)

- Account registration, login and logout (Django's built-in auth).
- Nested folders: create, rename, move, soft-delete/restore.
- Multi-file upload with server-side type/size validation and a
  drag-and-drop, progress-bar UI.
- File preview (images, audio, video, PDF) and download, both routed
  through an ownership-checked view rather than a raw media URL.
- Rename, move, tag, and favourite files.
- Notes: create, edit, pin, favourite, soft-delete/restore.
- Search across filenames, tags and note text, filterable by file type
  and date range.
- Recycle bin with restore and permanent delete for files, folders and
  notes, plus a configurable retention period.
- Manual per-file archive/unarchive (a synchronous stand-in for the
  background job Section 13.2 describes — see `archive_app/views.py`).
- Storage usage shown per account and broken down by file category.
- A basic audit log (`audit` app) of logins, uploads, downloads, deletes,
  restores, etc.
- Ownership enforced on every lookup (`owner=request.user`), per Section
  25.2 of the guide.

Not implemented yet, on purpose (guide Section 26, steps 5–10): PostgreSQL,
S3, signed URLs, HTTPS/security headers in production, background jobs
(Celery/Redis), automatic lifecycle rules, 2FA, OCR/AI features. The
`config/settings/prod.py` module and `requirements-prod.txt` sketch the
upgrade path for when you get there.

## Project layout

```
personal_data_vault/
├── manage.py
├── requirements.txt         # Version 1: Django + SQLite + Pillow
├── requirements-prod.txt    # adds PostgreSQL + S3 + Gunicorn
├── .env.example
├── config/
│   ├── settings/
│   │   ├── base.py          # shared settings
│   │   ├── dev.py           # SQLite + local media/  (default)
│   │   └── prod.py          # PostgreSQL + private S3
│   ├── urls.py
│   ├── wsgi.py / asgi.py
├── accounts/                # signup / login / logout / profile
├── dashboard/                # "My Storage" home page + storage summary
├── folders/                  # nested folders
├── notes/                    # database-backed notes
├── storage_app/               # file upload/download/preview/recycle bin
├── search_app/                # cross-model search
├── archive_app/                # manual archive / unarchive
├── audit/                     # append-only audit log
├── templates/                 # base layout + shared partials
├── static/                    # Bootstrap-based CSS/JS
└── media/                     # uploaded files (local dev only, gitignored)
```

## Running it locally

This scaffold was generated in a sandbox with no access to PyPI, so the
dependencies have **not** been installed or the test suite run here —
do that as your first step:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set a real SECRET_KEY (any long random string works for dev)

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/accounts/signup/ to create your first
account, or http://127.0.0.1:8000/admin/ to sign in as the superuser.

Run the test suite (ownership isolation, upload validation, recycle bin)
with:

```bash
python manage.py test
```

## Upgrading to production (guide Sections 12 and 20)

1. `pip install -r requirements-prod.txt`
2. Provision PostgreSQL and a private S3-compatible bucket; fill in the
   `DATABASE_URL` / `OBJECT_STORAGE_*` variables in `.env`.
3. `export DJANGO_SETTINGS_MODULE=config.settings.prod`
4. `python manage.py migrate`
5. Serve with Gunicorn behind Nginx/HTTPS:
   `gunicorn config.wsgi:application --bind 0.0.0.0:8000`
6. Test upload/download/preview and a recycle-bin restore against the
   real bucket before storing anything you care about (guide Section 20,
   steps 7–10).

## Notes on decisions made while scaffolding

- **No `django.conf.urls.static` media route.** Per Sections 16.1 and
  25.2 of the guide, files are only ever served through
  `storage_app.views.file_download` / `file_preview`, which check
  ownership first — never through a raw, guessable `/media/<path>` URL.
- **Archiving is synchronous in V1.** The guide's Section 13.2 describes
  a background job; since Celery/Redis are explicitly a "later" addition
  in the recommended stack, `archive_app` just flips a status flag for
  now. The view boundary is kept the same so swapping in a real async
  task later doesn't change the data model or URLs.
- **Favourite toggles are POST-only,** even though many tutorials use a
  plain link for this, to stay consistent with the guide's Section 15
  emphasis on CSRF protection for anything that mutates state.

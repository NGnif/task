# Task Manager (Owner + Workers)

Simple Flask web app for a small shop to manage tasks with two roles: Owner and Workers. First registered user becomes the Owner; after that only the Owner can create new user accounts.

Deploy for free on Vercel:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FYOUR_GITHUB_USERNAME%2FYOUR_REPO_NAME&project-name=task-manager&repository-name=task-manager&env=SECRET_KEY,DATABASE_URL)

Replace YOUR_GITHUB_USERNAME and YOUR_REPO_NAME with your repo path, or follow DEPLOY.md for step-by-step instructions.

## Features

- Users: register (owner first), login, logout
- Roles: owner (manage all), worker (view own tasks only)
- Tasks: owner can create, edit, complete/reopen, assign, delete; workers can only view their own tasks
- Views: list with filters/search; export to CSV
- Storage: SQLite (dev) or Postgres (prod)

## Quickstart (Local)

1. Create and activate a virtualenv (recommended)
2. Install deps: `pip install -r requirements.txt`
3. Run: `python run.py` then open http://localhost:5000
4. Register the first user (becomes Owner), then log in and add workers.

Environment variables (required):

- `DATABASE_URL` (required): pooled Postgres URL, e.g. `postgresql://user:pass@host:5432/db?sslmode=require`
- `SECRET_KEY` (required): any long random string

## Docker

Build and run:

```bash
docker build -t task-manager .
docker run -e SECRET_KEY=change-me -e DATABASE_URL=sqlite:////data/app.db -p 5000:5000 task-manager
```

## Roles and Permissions

- Owner: top-level; manage everything (tasks, approvals), create/delete users
- Admin: manage/approve all tasks, import/export; cannot create/delete users
- Worker: view and manage only own tasks, cannot delete, export only own

## Deploy

- Set `SECRET_KEY` and `DATABASE_URL` env vars (Postgres required; SQLite not supported)
- Run the container with Gunicorn (Dockerfile included) or deploy to Render/Railway/Fly.io
- Vercel (free) instructions: see `DEPLOY.md`

## PWA (Mobile App)

- Installable on Android/iOS as a Progressive Web App.
- Added: `manifest.webmanifest`, `service-worker.js`, and dynamic icons at `/icons/192.png` and `/icons/512.png`.
- On mobile, open the site and use “Add to Home Screen”.
- Offline: core pages are cached; an Offline page is shown when needed.

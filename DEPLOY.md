Deploying (Free) on Vercel + Neon

Overview
- Hosting: Vercel Hobby (free)
- Database: Neon Postgres (free, use a pooled connection)
- Runtime: Python 3.11 serverless function
- Already included in this repo: `api/index.py`, `vercel.json`, `requirements.txt`

1) Push this project to GitHub
- Create a new private/public repo.
- Commit/push all files (including `api/index.py` and `vercel.json`).

2) Create a free Postgres on Neon
- Go to https://neon.tech and create a project (free tier).
- Open “Connection Details” and copy the “Pooled connection string”.
- Make sure it starts with `postgresql://` and includes `sslmode=require`.

3) Deploy to Vercel (free)
- Click this button after you push to GitHub (replace repo in the URL), or use Import Project in Vercel.
- Button: https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FYOUR_GITHUB_USERNAME%2FYOUR_REPO_NAME&project-name=task-manager&repository-name=task-manager&env=SECRET_KEY,DATABASE_URL
- In Vercel → Project Settings → Environment Variables, add:
  - `SECRET_KEY` → any long random string
  - `DATABASE_URL` → your Neon pooled URL
- Deploy.

4) First run
- Visit your Vercel URL.
- Go to `/register` and create the first account (becomes Owner).
- Log in and use the app. Create worker accounts from the navbar (Owner only).

5) Notes for serverless
- Persistence: SQLite does not persist on serverless; Postgres is required.
- Connections: use the pooled connection string for best performance.
- Cold starts: first request after idle can be slightly slower.

6) PWA and cache
- The app ships a service worker. On UI/theme changes, a hard refresh may be required.
- If you don’t see CSS changes, open DevTools → Application → Service Workers → Update, then reload.

7) Optional custom domain
- Add a domain in Vercel → Domains, and assign it to your project.

Troubleshooting
- If you see “No module named flask”: make sure `requirements.txt` is present and Vercel used Python runtime (it will for `api/*.py`).
- If tables do not appear: ensure `DATABASE_URL` is correct (`postgresql://...`) and the Neon role has permission to create tables. The app auto-creates tables at startup.
- If registration is blocked: remember only the first user is Owner; after that, only Owner can register new users.


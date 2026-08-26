# Security Validation Platform

A consumer-friendly compliance scanner. Sign up, get a personal one-line
command for Linux and one for Windows, paste it into a terminal on any
machine you own, and see a detailed security report on your dashboard.

## How it works

1. Create an account on the dashboard (username + password).
2. The dashboard shows you two ready-to-run commands with your personal
   API key already embedded — nothing to type or configure.
3. Paste the Linux command into a terminal, or the Windows command into
   PowerShell. It scans the machine, prints results on screen, and reports
   them to your dashboard. Nothing is installed.
4. The scanned machine shows up on your dashboard with a compliance score
   and a full breakdown of every check, downloadable as a PDF.

Your API key is not your password — it's safe to have it sitting in a
copy-pasted command, and you can regenerate it any time from the dashboard
if you think it's leaked.

## Project layout

```
backend/            FastAPI + SQLAlchemy + Postgres
  main.py           All API routes
  auth.py           Password hashing, JWT sessions, API-key auth
  models.py         User / Server / Scan / Finding tables
  schemas.py        Request/response models
  pdf_generator.py  PDF report generation
  public/           Served at /public - the install scripts live here
    agent-linux.sh
    agent-windows.ps1

frontend/           React + Vite + Tailwind
  src/pages/         Login, Register, Dashboard, ServerReport
  src/components/    CommandBox (copy-to-clipboard install command)
  src/api.js         API client, token storage

render.yaml          Render deployment blueprint (backend + Postgres)
vercel.json          Vercel deployment config (frontend)
```

## Local development

Backend:
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL="sqlite:///./dev.db" SECRET_KEY="dev-secret" uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## Deploying

See the deployment steps in the project notes — Render for the backend
(`render.yaml` provisions the web service and Postgres database together),
Vercel for the frontend (point it at this repo, it reads `vercel.json`
automatically). After the backend is live, set `VITE_API_URL` in Vercel to
your Render URL, and set `BACKEND_URL` in Render to that same Render URL so
the dashboard's install commands point at the right place.

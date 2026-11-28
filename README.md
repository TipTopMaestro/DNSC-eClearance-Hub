# DNSC e-Clearance Hub

An IT312 Integrative Programming and Technologies final project that integrates campus office records into a centralized student clearance system for Davao del Norte State College (DNSC).

The project uses a **monorepo** with a separate FastAPI backend and a vanilla JavaScript frontend. The backend handles authentication, authorization, database operations, data integration, and clearance business rules. The frontend communicates with the backend exclusively through its REST API.


## Technology stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLite (`sqlite3`), Pydantic, HTTPX
- **Security:** PBKDF2-HMAC-SHA256 password hashing, expiring opaque bearer tokens, role-based access control, Fernet encryption
- **Frontend:** Vanilla HTML, CSS, JavaScript (ES modules), Bootstrap 5 or Tailwind CSS (agree on one framework as a team; Bootstrap 5 is recommended)
- **Testing:** pytest and FastAPI TestClient
- **Version control:** Git and GitHub

## Project structure

```text
DNSC-eClearance-Hub/
├── backend/
│   ├── app/                  # FastAPI application and business logic
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── security/
│   │   └── utils/
│   ├── scripts/              # Setup, seed and database utilities
│   ├── tests/                # Automated backend tests
│   ├── data/                 # Local database and private records (ignored)
│   ├── .env                  # Local configuration and secrets (ignored)
│   ├── .env.example          # Configuration template (no real secrets)
│   └── requirements.txt
├── frontend/
│   └── student-hub/
│       ├── assets/
│       │   ├── css/
│       │   └── js/
│       │       ├── config.js
│       │       └── api.js
│       ├── pages/
│       └── integration-test.html  # Temporary development test page
├── docs/                     # Design and API documentation
├── .gitignore
└── README.md
```

The tree shows the intended initial layout. Additional integration modules and frontend pages will be added as development progresses. Ignored files and folders may not appear immediately after cloning.

## 1. Clone the repository (first-time setup)

### Prerequisites

Install Git, Python 3.11 or newer, and a code editor such as VS Code. Check your installations:

```bash
git --version
python --version
```

On macOS/Linux, use `python3` instead of `python` if necessary.

Clone the repository and open it:

```bash
git clone https://github.com/TipTopMaestro/DNSC-eClearance-Hub.git
cd DNSC-eClearance-Hub
code .
```

If `code .` is unavailable, open the folder manually in VS Code. If the repository is private, sign in to GitHub with an account that has been granted access.

## 2. Pull the latest changes (existing contributors)

You only need to clone the repository once. To update an existing local copy, run the following from the repository root:

```bash
git status
git switch main
git pull --ff-only origin main
```

Commit or stash your unfinished work before switching branches or pulling. If `--ff-only` fails, your branch has diverged; ask the project lead before attempting to resolve it. Do not force-push or reset away other people's work.

If backend dependencies changed, reinstall them using `python -m pip install -r requirements.txt` from `backend/` with your virtual environment activated. Keep your own `.env` and local database; Git does not distribute these files.

## 3. Set up the backend (first time only)

All contributors who want to test the Student Hub against a real API should set up their own local backend. You do not need access to anyone else's credentials or database.

### Create and activate a virtual environment

From the repository root:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
cd backend
python -m pip install -r requirements.txt
```

If PowerShell prevents script activation, use Command Prompt (`.venv\Scripts\activate.bat` from the repository root) or invoke the virtual environment's Python directly. Do not disable system-wide security settings.

If the requirements file is not yet present in your checkout, ask the backend developer for the current dependency list before proceeding.

### Configure environment variables

While inside `backend/`, copy the configuration template if it is available:

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Only do this if `.env` does not already exist. If the template is not yet present, create `backend/.env` with the following initial configuration:

```dotenv
APP_NAME=DNSC e-Clearance Hub
DATABASE_PATH=data/clearance.db
REGISTRAR_API_URL=http://127.0.0.1:9000
HOLIDAYS_API_URL=https://date.nager.at/api/v3
CLEARANCE_WORKING_DAYS=10
TOKEN_EXPIRY_MINUTES=30
FRONTEND_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
EXCHANGE_KEY_LIBRARY=
EXCHANGE_KEY_ACCOUNTING=
SLIP_SIGNING_KEY=
FERNET_KEY=
```

Generate your own development keys:

```bash
python -m scripts.generate_keys
```

Copy the generated values into the four corresponding empty key fields in `.env`. Keep them private. Do not regenerate the Fernet key for an existing database containing encrypted records, or those records may become unreadable.

The Registrar and holiday settings are placeholders for upcoming integrations. No external mock Registrar server is required for the initial seeded authentication and student endpoints.

### Seed local development data

Run these commands from `backend/`:

```bash
python -m scripts.seed_students
python -m scripts.seed_users
```

The student seed script creates fictional students, a demonstration clearance period and sample clearance records. Note the clearance period ID printed in the terminal (often `1` on a fresh database).

The user seed script prompts you to create and confirm a password for each account. Use local development passwords of 12–128 characters.

| Username | Role | Assigned office / student |
| --- | --- | --- |
| `student01` | STUDENT | 2023-0104 |
| `library01` | STAFF | Library |
| `accounting01` | STAFF | Accounting |
| `registrar01` | STAFF | Registrar |
| `affairs01` | STAFF | Student Affairs |
| `admin01` | ADMIN | Administration |

For Student Hub development, use `student01` and the password you entered. No shared default password is required.

**Do not reseed every time you start the server.** Student seeding can overwrite demonstration clearance statuses; user seeding skips existing usernames and does not reset passwords.

## 4. Run the backend and frontend

Use two separate terminals in VS Code. Start both from the repository root.

### Terminal 1 — FastAPI backend

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload
```

**macOS / Linux**

```bash
source .venv/bin/activate
cd backend
python -m uvicorn app.main:app --reload
```

The backend automatically initializes missing SQLite tables on startup. Always run Python backend commands from `backend/` because the database path and environment file are relative to this working directory.

### Terminal 2 — Student Hub frontend

From the repository root:

```bash
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Use `python3` on macOS/Linux if needed. Alternatively, use VS Code Live Server configured to serve **only** `frontend/` on port `5500`. Never serve the entire repository, as it contains private backend files.

### Terminal 3 - Register Mock External API

**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn mock_sources.registrar_api:app --port 9000 --reload
```

| Service | Local URL |
| --- | --- |
| FastAPI | http://127.0.0.1:8000/ |
| Health check | http://127.0.0.1:8000/health |
| Swagger API documentation | http://127.0.0.1:8000/docs |
| Student Hub (once index.html exists) | http://127.0.0.1:5500/student-hub/ |
| Temporary integration test (if present) | http://127.0.0.1:5500/student-hub/integration-test.html |

Open the integration test page and sign in using `student01` to verify that the frontend can retrieve the authenticated account and student profile. You can also test these endpoints directly in Swagger UI: log in, copy the `access_token`, click **Authorize**, paste the token, and execute a protected endpoint.

Press `Ctrl+C` in each terminal to stop its server.

## 5. Current API contract

Local base URL: `http://127.0.0.1:8000/api/v1`

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/login` | Public | Create a session |
| GET | `/auth/me` | Authenticated | Get current account and role |
| POST | `/auth/logout` | Authenticated | Revoke current session |
| GET | `/students/me` | STUDENT | Get own student profile |
| GET | `/clearance/me?period_id=1` | STUDENT | Get own clearance summary |

Replace `1` with your actual seeded period ID. The current-period/deadline endpoint is planned but not yet available.

Login accepts a JSON body with `username` and `password`. Successful login returns `access_token`, `token_type`, and `expires_in`. Protected requests require the header `Authorization: Bearer <access_token>`.

Frontend developers should reuse `frontend/student-hub/assets/js/api.js` and `config.js` instead of creating separate API clients per page. The shared API client stores the bearer token in `sessionStorage` and attaches it to authenticated requests.

Example:

```javascript
import { apiRequest } from "./api.js";

const student = await apiRequest("/students/me");
const clearance = await apiRequest("/clearance/me?period_id=1");
```

Adjust the relative import path to match the calling file. Use `overall_status` returned by the backend as the authoritative clearance result. Refer to Swagger UI for the actual request/response schemas. For endpoints still under development, use fictional mock JSON with an agreed response structure.

## 6. Team responsibilities and Git workflow

The backend developer maintains `backend/` and the API contract. The four frontend contributors currently work on `frontend/student-hub/` only. Staff and admin interfaces remain part of the full project scope and will be assigned separately.

| Contributor | Assignment | Suggested feature branch |
| --- | --- | --- |
| Backend developer | API, security, database, integration, tests | `feature/backend-api` |
| Frontend member 1 | Login, authentication and navigation | `feature/student-auth` |
| Frontend member 2 | Dashboard and clearance progress | `feature/student-dashboard` |
| Frontend member 3 | Detailed clearance and student profile | `feature/student-clearance-profile` |
| Frontend member 4 | Clearance slip UI, PWA and frontend QA | `feature/student-slip-pwa` |

### Create your assigned feature branch

From the repository root, after updating `development`:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/student-dashboard
```

Replace the example branch name with your assigned branch. If it already exists locally, use `git switch feature/student-dashboard` instead.

### Commit and push your work

```bash
git status
git add frontend/student-hub/
git diff --cached
git commit -m "feat: implement student dashboard"
git push -u origin feature/student-dashboard
```

Only stage files you intend to contribute. Backend contributors should stage their own changed files under `backend/` instead. After the first push, `git push` is sufficient on that branch.

Open a pull request on GitHub from your feature branch into `main`. The project lead will review changes before merging. Do not push directly to `main` unless the team has agreed to do so.

### Keep your feature branch up to date

With your work committed and your feature branch checked out:

```bash
git fetch origin
git merge origin/main
```

Resolve any conflicts with the relevant file owner, run the application/tests, and push your updated branch. Each member should commit their own code so individual contributions are visible in Git history.

## 7. Backend testing and local database utilities

Run these commands from `backend/` with the virtual environment activated:

```bash
python -m pytest tests/ -v
python -m scripts.check_database
python -m scripts.check_clearance
```

The automated client tests use temporary databases when configured with the tutorial's isolated pytest fixture. They should not require resetting your local development database.

### Reset the development database (optional, destructive)

Only reset if you want to erase all local database records, including accounts and sessions. Stop the backend and any SQLite viewers first. Back up anything you want to retain.

```bash
python -m scripts.reset_db
```

Type `RESET` when prompted. Then recreate the demo records and accounts:

```bash
python -m scripts.seed_students
python -m scripts.seed_users
```

This assumes the reset utility from the previous tutorial is present in your checkout. Never run it against production or real student data. Your `.env` and encryption keys should remain unchanged.

## 8. Security and development guidelines

- Never commit `.env`, secret keys, passwords, tokens, SQLite databases, private imports, reports, or logs.
- Use fictional student records for development and testing.
- The frontend must use the REST API, not direct database access.
- Do not store passwords in browser storage or expose backend secrets in JavaScript.
- Use `textContent` for untrusted values; avoid unsafe HTML injection.
- Frontend route guards improve navigation but are not authorization controls. The backend enforces permissions.
- Do not cache authenticated API responses or private clearance slips in a PWA service worker.
- Use HTTPS in production. The local HTTP servers are for development only.

## 9. Troubleshooting

| Problem | What to check |
| --- | --- |
| `ModuleNotFoundError: app` | Run Python backend commands from `backend/`. |
| Missing package | Activate `.venv` and install backend requirements. |
| Missing environment variable | Check `backend/.env` and generate the required keys. |
| `no such table` / empty database | Check working directory and `DATABASE_PATH`; initialize/seed your local database. |
| `401 Unauthorized` | Log in again; check the token and password. |
| `403 Forbidden` | Check account role; Student Hub requires STUDENT. |
| `422` validation error | Check JSON fields and the positive clearance period ID. |
| `429 Too Many Requests` | Wait for the local login throttle window to expire. |
| CORS error / `Failed to fetch` | Confirm both servers are running, ports are correct, and the frontend origin is allowed. |
| Frontend page not found | Check that the page exists in `frontend/student-hub/` and the static server serves `frontend/`. |
| Git pull conflict or divergence | Preserve your work and coordinate with the project lead. |


## Automated Office Imports

Place complete signed batch folders inside:

`backend/data/drop/`

Each batch must contain one XML or CSV file
and its `manifest.json`.

Run the automation from the backend directory:

```bash
python -m automation.process_drop
```

Successful batches are moved to `data/archive/`.
Invalid batches are moved to `data/rejected/`.

Temporary processing failures remain in the drop folder.

Logs are written to `logs/automation.log`.

Daily HOLD summaries are generated in `data/reports/`.

The script can be scheduled using Windows Task Scheduler.


## Repository

[TipTopMaestro/DNSC-eClearance-Hub](https://github.com/TipTopMaestro/DNSC-eClearance-Hub)

**Course:** IT312 — Integrative Programming and Technologies  
**Project:** DNSC e-Clearance Hub  
**Status:** In active development

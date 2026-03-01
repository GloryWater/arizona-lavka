Act as a Principal DevSecOps Engineer, Staff Platform Engineer, and Autonomous AI Agent. Your objective is to configure an industry-grade `pre-commit` hook system and a robust CI/CD pipeline (GitHub Actions) for the "ArizonaLavka" monorepo.

The repository contains a Python 3.12/FastAPI backend (managed via `uv`), a React 19/TypeScript/Vite frontend (using Feature-Sliced Design), and Docker infrastructure.

Execute this implementation strictly following these three layers:

### LAYER 1: Technical Context & Architecture
- **Target Assets:** `.pre-commit-config.yaml` in the root, and CI/CD workflow files inside `.github/workflows/` (`backend-ci.yaml`, `frontend-ci.yaml`, `docker-ci.yaml`, `cd-deploy.yaml`).
- **Toolchain:** 
  - *Backend:* `uv` (package manager), Ruff (linting/formatting), MyPy (type checking), Bandit (security).
  - *Frontend:* npm, ESLint, Prettier, TypeScript (`tsc`), Vite.
  - *Infrastructure:* Docker Compose, Hadolint.
- **Architectural Pattern (Monorepo):** CI/CD pipelines and pre-commit hooks MUST be strictly isolated by directory. Backend tools must only run on `backend/**` files, and frontend tools must only run on `frontend/**` files.

### LAYER 2: Functional Requirements & Execution Steps
Generate and implement the automation infrastructure step-by-step:

1. **Pre-commit Hooks Configuration (`.pre-commit-config.yaml`):**
   - Create the root configuration file.
   - Add global hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `detect-private-key`.
   - Add Backend hooks (triggering only on `files: ^backend/`): Ruff (linter & formatter), MyPy (strict type checking), and Bandit.
   - Add Frontend hooks (triggering only on `files: ^frontend/`): Configure local hooks utilizing `npm run lint` and `npx prettier --write` to respect the local `node_modules`.
   - Add Docker hook: Hadolint for `Dockerfile` linting.

2. **GitHub Actions CI - Pull Request Validation:**
   - Create `.github/workflows/backend-ci.yaml`: Trigger only on changes in `backend/**`. Use `astral-sh/setup-uv`. Install dependencies via `uv sync`, run Ruff, run MyPy, run Bandit. 
   - Create `.github/workflows/frontend-ci.yaml`: Trigger only on changes in `frontend/**`. Use `actions/setup-node`. Run `npm ci`, `npm run lint`, `npx tsc --noEmit`, and `npm run build` (Vite build test).
   - Create `.github/workflows/docker-ci.yaml`: Trigger on changes to `docker-compose.yml` or `Dockerfile`s. Run a dry-run `docker-compose build` to ensure the infrastructure isn't broken.

3. **GitHub Actions CD - Production Deployment:**
   - Create `.github/workflows/cd-deploy.yaml`: Trigger on `push` to the `main` branch. 
   - Use `appleboy/ssh-action` to SSH into the production server.
   - Execute a safe deployment script: pull latest code, copy `.env` files (if managed via secrets), and run `docker-compose up -d --build`.

### LAYER 3: Integration Details, Reliability & Edge Cases
- **Monorepo Path Filtering (Critical):** You must use `paths` filtering in GitHub Actions (`on: pull_request: paths: ['backend/**']`). Running frontend CI for a backend Python change is a waste of CI minutes and violates best practices.
- **Caching for Speed:** 
  - In the backend CI, heavily utilize `uv`'s native caching mechanisms to make dependency installation instant.
  - In the frontend CI, use `actions/setup-node@v4` with `cache: 'npm'` to cache `node_modules`.
- **FSD Architecture Safety:** Ensure that ESLint and TypeScript checks in the frontend CI run from the `frontend/` working directory (`working-directory: ./frontend`). Otherwise, absolute imports representing Feature-Sliced Design (`@/features`, `@/entities`) will fail to resolve.
- **Fail-Safe CD Deployment:** The `cd-deploy.yaml` MUST include strict checks for required GitHub Secrets (`SERVER_HOST`, `SERVER_USERNAME`, `SERVER_SSH_KEY`). If they are missing, the step should fail gracefully with a clear error message rather than hanging indefinitely.

Output a Markdown summary of the files you will create or modify, and then immediately execute the file creations and modifications autonomously.
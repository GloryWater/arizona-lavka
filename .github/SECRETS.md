# GitHub Secrets Configuration

## Required Secrets for CD Pipeline

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

### Server Connection

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVER_HOST` | Your VPS IP address or domain | `192.168.1.100` or `lavka.glorysyntax.live` |
| `SERVER_USERNAME` | SSH username on your server | `root`, `ubuntu`, `deploy` |
| `SERVER_SSH_KEY` | Private SSH key for server access | (your private key content) |
| `SERVER_PORT` | SSH port (optional, default: 22) | `22` |
| `DEPLOY_PATH` | Path to project on server (optional) | `/opt/arizonalavka` |

### Optional: Environment Variables

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `SERVER_URL` | Public URL of your application | `https://lavka.glorysyntax.live` |

---

## How to Generate SSH Key

### Option 1: Generate New SSH Key

```bash
# Generate new SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "github-actions@arizonalavka" -f ~/.github/id_github_actions

# Copy the private key
cat ~/.github/id_github_actions

# Add public key to your server
ssh-copy-id -i ~/.github/id_github_actions.pub your-user@your-server
```

### Option 2: Use Existing SSH Key

```bash
# Copy your existing public key to server
ssh-copy-id your-user@your-server

# Get private key content for GitHub secret
cat ~/.ssh/id_ed25519  # or id_rsa
```

---

## Server Requirements

Your server must have:

1. **Docker** installed (version 24.0+)
2. **Docker Compose** installed (version 2.20+)
3. Project directory created (e.g., `/opt/arizonalavka`)
4. `.env` file with your configuration

### Server Setup Commands

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose (if not included)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Create project directory
sudo mkdir -p /opt/arizonalavka
cd /opt/arizonalavka

# Create .env file (copy from .env.example and edit)
sudo nano .env
```

---

## Project .env Configuration

Create `/opt/arizonalavka/.env` on your server:

```bash
# Database
POSTGRES_USER=arizonalavka
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=arizonalavka
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# JWT Secrets (GENERATE NEW ONES!)
JWT_SECRET_KEY=your_jwt_secret_key_here_min_32_characters_long
JWT_REFRESH_SECRET_KEY=your_refresh_secret_key_here_min_32_characters_long

# CORS
CORS_ORIGINS=https://lavka.glorysyntax.live,http://lavka.glorysyntax.live

# Application
DEBUG=false
APP_NAME="Arizona Lavka Marketplace"

# Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

### Generate Secure Secrets

```bash
# Generate JWT secret (32+ characters)
openssl rand -hex 32

# Generate password
openssl rand -base64 32
```

---

## Initial Deployment

### 1. Copy docker-compose.yml to Server

```bash
scp docker-compose.yml your-user@your-server:/opt/arizonalavka/
```

### 2. Verify Deployment

After pushing to `main` branch, check:

1. **Actions tab** - CD workflow should run automatically
2. **Server logs** - `docker-compose logs -f`
3. **Health check** - `curl http://your-server:8000/health`
4. **Frontend** - Open `http://your-server:8080` in browser

---

## Troubleshooting

### Deployment Fails with "Permission Denied"

```bash
# On server, add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Docker Pull Fails (Authentication)

```bash
# On server, login to GHCR manually to test
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

### Health Check Fails

```bash
# Check backend logs
docker compose logs backend

# Check if port is accessible
curl -v http://localhost:8000/health

# Check CORS settings in .env
```

### Database Migration Fails

```bash
# Run migrations manually
docker compose run --rm backend alembic upgrade head

# Check current migration
docker compose run --rm backend alembic current
```

---

## Environment-Specific Deployments

The CD workflow supports manual deployment to different environments:

1. Go to **Actions → CD - Deploy to Production**
2. Click **Run workflow**
3. Select environment: `production` or `staging`
4. Click **Run workflow**

---

## Security Best Practices

1. **Never commit secrets** - Always use GitHub Secrets
2. **Rotate secrets regularly** - Update JWT secrets periodically
3. **Use strong passwords** - Minimum 32 characters for secrets
4. **Limit SSH key access** - Use deploy keys with minimal permissions
5. **Enable branch protection** - Require PR reviews for main branch
6. **Review workflow runs** - Monitor Actions for suspicious activity

---

## Verify Deployment

After successful deployment, verify:

```bash
# Backend health
curl http://your-server:8000/health

# Frontend
curl http://your-server:8080

# API docs
curl http://your-server:8000/docs

# Check running containers
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

---

## Rollback

To rollback to a previous version:

```bash
# On server, checkout previous commit
cd /opt/arizonalavka
git checkout <previous-commit-hash>

# Redeploy with specific image tags
# Update docker-compose.yml with specific image tags
docker compose pull
docker compose up -d
```

Or use GitHub Actions:
1. Go to the previous successful deployment in Actions
2. Click "Re-run jobs"

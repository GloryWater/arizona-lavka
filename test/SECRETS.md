# GitHub Secrets Configuration

## Required Secrets for CD Pipeline

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVER_HOST` | Your VPS IP address or domain | `192.168.1.100` or `example.com` |
| `SERVER_USERNAME` | SSH username on your server | `ubuntu`, `deploy`, `root` |
| `SERVER_SSH_KEY` | Private SSH key for server access | (your private key content) |

## How to Generate SSH Key

```bash
# Generate new SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "github-actions" -f ~/.github/id_github_actions

# Copy the private key
cat ~/.github/id_github_actions

# Add public key to your server
ssh-copy-id -i ~/.github/id_github_actions.pub your-user@your-server
```

## Server Requirements

Your server must have:
1. **Docker** installed
2. **Docker Compose** installed
3. Project directory created (e.g., `/opt/url_shortener`)
4. `.env` file with your configuration

## Server Setup Commands

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create project directory
sudo mkdir -p /opt/url_shortener
cd /opt/url_shortener

# Create .env file (copy from .env.example and edit)
sudo nano .env
```

## Verify Deployment

After pushing to main, check:
1. **Actions tab** - CD workflow should run automatically
2. **Server logs** - `docker-compose logs -f`
3. **Health check** - `curl http://your-server:8001/health`

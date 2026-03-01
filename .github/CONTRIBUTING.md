# 🤝 Contributing to Arizona Lavka Marketplace

Thank you for your interest in contributing to Arizona Lavka Marketplace! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Making Changes](#making-changes)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Commit Messages](#commit-messages)

---

## 📜 Code of Conduct

Please be respectful and constructive in your interactions. We're committed to providing a welcoming and inspiring community for all.

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone:
git clone https://github.com/YOUR_USERNAME/arizonalavka.git
cd arizonalavka
```

### 2. Set Up Development Environment

```bash
# Install Python dependencies (backend)
cd backend
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
uv pip install -r requirements.txt

# Install Node.js dependencies (frontend)
cd ../frontend
npm install
```

### 3. Configure Environment

```bash
# Copy environment templates
cp ../.env.example .env
cp ../frontend/.env.example ../frontend/.env.local
```

---

## 🛠️ Development Setup

### Backend Development

```bash
cd backend

# Run database migrations
alembic upgrade head

# Start development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run linting
ruff check .
flake8 .
```

### Frontend Development

```bash
cd frontend

# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
```

### Docker Development

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Run tests
docker-compose exec backend pytest
```

---

## 🏗️ Architecture Overview

### Backend: Domain-Driven Design (DDD)

```
backend/
├── core/           # Enterprise business rules, entities
├── application/    # Use cases, DTOs, interfaces
├── infrastructure/ # Database, external APIs, repositories
├── interfaces/     # HTTP middleware, adapters
├── routes/         # API endpoints (controllers)
└── services/       # Business logic services
```

**Key Principles:**
- Dependencies point inward (core has no dependencies)
- Business logic in `core/` and `application/`
- Infrastructure details in `infrastructure/`

### Frontend: Feature-Sliced Design (FSD)

```
frontend/src/
├── app/            # Application initialization, providers
├── pages/          # Route pages (HomePage, LavkaPage, etc.)
├── widgets/        # Composite blocks (Header, Footer, Layout)
├── features/       # User interactions (auth, search, theme)
├── entities/       # Business entities (user, lavka, offer)
└── shared/         # Reusable code (UI, hooks, lib, api)
```

**Key Principles:**
- Strict layer hierarchy (no upward imports)
- Features depend on entities, not vice versa
- Shared layer has no dependencies on other layers

---

## ✏️ Making Changes

### 1. Create a Branch

```bash
# Always branch from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming:**
- `feature/add-new-feature` - New features
- `fix/bug-fix` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/code-cleanup` - Refactoring
- `test/add-tests` - Tests

### 2. Make Your Changes

- Follow coding standards (see below)
- Write/update tests as needed
- Update documentation if applicable

### 3. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

---

## 📤 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] No new warnings or errors
- [ ] Changes tested locally

### PR Template

When creating a PR, please include:

1. **Description** - What does this PR do?
2. **Type of Change** - Bug fix, feature, refactor, etc.
3. **Testing** - How was it tested?
4. **Screenshots** (if UI changes)
5. **Checklist** - All items from "Before Submitting"

### Review Process

1. **Automated Checks** - CI/CD must pass
2. **Code Review** - At least 1 approval required
3. **Testing** - QA verification if applicable
4. **Merge** - Squash and merge by maintainer

---

## 📝 Coding Standards

### Python (Backend)

```python
# Use type hints
def calculate_price(item_id: int, quantity: int) -> float:
    """Calculate total price for items.
    
    Args:
        item_id: Item identifier
        quantity: Number of items
    
    Returns:
        Total price
    """
    pass

# Follow PEP 8
# Use meaningful variable names
# Keep functions small and focused
```

**Linting:**
```bash
ruff check .
flake8 .
mypy .
```

### TypeScript (Frontend)

```typescript
// Use strict types
interface User {
  id: number;
  username: string;
  email: string;
}

// Use functional components with hooks
const UserProfile: React.FC<UserProps> = ({ user }) => {
  // Component logic
};

// Export components properly
export { UserProfile };
```

**Linting:**
```bash
npm run lint
npm run type-check
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Load Testing

```bash
cd load_tests

# Run Locust tests
locust -f locustfile.py --host http://localhost:8000

# Run k6 tests
k6 run k6_test.js
```

---

## 📝 Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Tests
- `chore:` - Maintenance

**Examples:**
```
feat(auth): add Telegram authentication
fix(api): resolve rate limiting issue
docs(readme): update installation instructions
refactor(database): optimize user queries
test(auth): add login test cases
```

---

## 🎯 Areas Needing Contribution

We especially welcome contributions in:

- 📝 **Documentation** - Improve guides, examples, tutorials
- 🧪 **Testing** - Add unit/integration tests
- 🌐 **Translations** - Add support for new languages
- 🐛 **Bug Fixes** - Fix open issues
- ✨ **Features** - Implement requested features
- 🚀 **Performance** - Optimize slow operations

---

## 📞 Need Help?

- **Discussions** - Ask questions in GitHub Discussions
- **Issues** - Report bugs or request features
- **Email** - contact@lavka.glorysyntax.live

---

**Thank you for contributing to Arizona Lavka Marketplace!** 🎉

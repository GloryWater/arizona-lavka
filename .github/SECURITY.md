# 🔒 Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.0.x   | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

We take the security of Arizona Lavka Marketplace seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

📧 **security@lavka.glorysyntax.live**

### What to Include

Please include the following information in your report:

1. **Description of the vulnerability** - A clear description of the issue
2. **Steps to reproduce** - Detailed steps to reproduce the issue
3. **Affected version(s)** - Which version(s) are affected
4. **Impact** - What an attacker could achieve
5. **Proof of Concept** (optional) - Code or screenshots demonstrating the issue
6. **Suggested fix** (optional) - If you have ideas for how to fix it

### Response Timeline

- **Within 48 hours**: We will acknowledge receipt of your report
- **Within 5 business days**: We will provide an initial assessment
- **Within 30 days**: We will work with you to understand and fix the issue
- **After fix**: We will notify you when the issue is resolved

### Security Best Practices

If you're using Arizona Lavka Marketplace in production, please ensure:

1. ✅ **Change default passwords** - Especially `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`
2. ✅ **Use HTTPS** - Never run in production with HTTP
3. ✅ **Keep dependencies updated** - Regularly update Python and Node.js packages
4. ✅ **Enable rate limiting** - Configure `RATE_LIMIT_PER_MINUTE` appropriately
5. ✅ **Monitor logs** - Watch for suspicious activity in backend logs
6. ✅ **Use environment variables** - Never commit `.env` files
7. ✅ **Restrict database access** - PostgreSQL should only be accessible from backend
8. ✅ **Enable CORS properly** - Only allow trusted origins in `CORS_ORIGINS`

### Security Measures in Place

- 🔐 **Password hashing** - bcrypt with configurable rounds
- 🔐 **JWT authentication** - Secure token-based auth
- 🔐 **Rate limiting** - Protection against brute force
- 🔐 **Input validation** - Pydantic schemas for all inputs
- 🔐 **SQL injection protection** - SQLAlchemy ORM with parameterized queries
- 🔐 **XSS protection** - Content sanitization in frontend
- 🔐 **CORS** - Configurable cross-origin resource sharing

### Bug Bounty Program

Currently, we do not have a formal bug bounty program. However, we deeply appreciate responsible disclosure and will acknowledge your contribution (unless you prefer to remain anonymous).

---

**Thank you for helping keep Arizona Lavka Marketplace secure!** 🙏

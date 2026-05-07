# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| main    | ✅        |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Use GitHub's [private vulnerability reporting](https://github.com/SGM-Studios/MAAPS_Nexus/security/advisories/new) to submit a report. You'll receive a response within 72 hours.

Please include:
- A clear description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- Any suggested mitigations you've identified

We'll acknowledge receipt, work with you on a fix, and credit you in the release notes (unless you prefer to remain anonymous).
| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of the Multi-Agent Audio Processing System seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@maaps.dev** (or open a draft security advisory on GitHub if you have collaborator access).

You should receive a response within 48 hours acknowledging your report. After the initial reply, we will keep you informed of the progress toward a fix and full announcement.

### What to Include

When reporting a vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact
- If possible, suggestions for addressing the issue
- Your contact information for follow-up questions

### Disclosure Policy

We follow a coordinated disclosure process:

1. Reporter submits vulnerability details privately
2. We acknowledge receipt within 48 hours
3. We investigate and validate the report
4. We develop and test a fix
5. We notify the reporter of the timeline
6. We publish the fix and acknowledge the reporter (if desired)

We ask that reporters:
- Give us reasonable time to address the issue before disclosing publicly
- Make a good faith effort to avoid privacy violations and data destruction
- Not interact with user data without explicit permission

## Security Best Practices for Contributors

When contributing to this project, please:

- Never commit secrets, API keys, or credentials
- Keep dependencies up to date
- Follow secure coding practices
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization checks

## Known Limitations

As an audio processing system with AI components, be aware of:

- Model inference may have unexpected behaviors with adversarial inputs
- File upload endpoints have size and type restrictions
- GPU acceleration requires proper sandboxing in multi-tenant environments

Thank you for helping keep MAAPS secure!

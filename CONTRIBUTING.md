# Contributing to MAAPS Nexus

Thank you for your interest in contributing! This document covers the basics of getting started.

## Getting Started

1. Fork the repository and create a branch from `main`.
2. Set up your environment (see [README.md](README.md) or [CLAUDE.md](CLAUDE.md)).
3. Make your changes, add tests where applicable, and ensure CI passes locally.
4. Open a pull request against `main`.

## Development Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-lint.txt
```

## Code Style

- **Formatter**: [Black](https://black.readthedocs.io/) (pinned at `25.11.0`) — run `black .` before committing.
- **Linter**: [Flake8](https://flake8.pycqa.org/) — run `flake8` and resolve any new errors.
- **Types**: [MyPy](https://mypy.readthedocs.io/) — run `mypy src/ --ignore-missing-imports` for type checking.

All three checks run in CI. A pull request must pass the **Code Quality Check** job before it can be merged.

## Running Tests

```bash
pytest tests/
pytest tests/ --cov=src --cov-report=html   # with coverage
```

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR.
- Write a clear description of *what* changed and *why*.
- Reference any related issues with `Closes #<number>`.
- Do not commit secrets, credentials, model weights, or large binary files.

## Reporting Issues

Open a GitHub Issue with:
- A clear title and description
- Steps to reproduce (if a bug)
- Expected vs. actual behavior
- Relevant logs or stack traces

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

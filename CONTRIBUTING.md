# Contributing to Mewtoo

Thank you for your interest in contributing to Mewtoo! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/mewtoo.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
5. Install dependencies: `pip install -r requirements.txt`
6. Create a branch: `git checkout -b feature/your-feature-name`

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Testing
- Write tests for new features
- Ensure all existing tests pass: `pytest`
- Test with both Ollama and Claude providers if applicable

### Documentation
- Update README.md if adding new features
- Update CHANGELOG.md with your changes
- Add docstrings to new functions/classes
- Update relevant docs in `docs/` directory

## Making Changes

### Before You Start
- Check existing issues and PRs to avoid duplicate work
- For large changes, consider opening an issue first to discuss

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (e.g., "Add", "Fix", "Update")
- Reference issue numbers if applicable: "Fix #123: ..."

### Pull Request Process

1. **Update your branch**: Make sure your branch is up to date with main
2. **Test your changes**: Run tests and verify everything works
3. **Check for sensitive data**: Ensure no API keys, ROM files, or secrets are included
4. **Update documentation**: Update relevant docs and CHANGELOG.md
5. **Create PR**: Open a pull request with a clear description

### PR Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No ROM files included
- [ ] No sensitive data included
- [ ] PR description is clear and complete

## Areas for Contribution

- Bug fixes
- Performance improvements
- New features (see TODO.md for ideas)
- Documentation improvements
- Test coverage
- Code refactoring

## Reporting Bugs

Use the bug report template in Issues. Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or screenshots

## Suggesting Features

Use the feature request template in Issues. Include:
- Clear description of the feature
- Motivation and use case
- Proposed solution
- Any alternatives considered

## Questions?

Feel free to open an issue with the "question" label if you need help or clarification.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.


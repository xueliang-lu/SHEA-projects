# Contributing to SheaBot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🎯 How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Node version, browser)

**Example:**
```markdown
**Bug**: Chat messages not loading after refresh

**Steps to Reproduce:**
1. Start a chat conversation
2. Refresh the page
3. Messages don't appear

**Expected:** Messages should load from database
**Actual:** Empty chat screen

**Environment:** macOS 14, Node 20, Chrome 120
```

### Suggesting Features

Feature suggestions are welcome! Please provide:

- **Use case** — Why is this feature needed?
- **Proposed solution** — How should it work?
- **Alternatives considered** — Other approaches you've thought about

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`npm run lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Development Guidelines

### Code Style

- Use **TypeScript** for all new code
- Follow **ESLint** rules (configured in `eslint.config.mjs`)
- Use **Prettier** formatting (if configured)
- Write **meaningful variable/function names**

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add dark mode toggle
fix: resolve MongoDB connection timeout
docs: update README with deployment instructions
refactor: simplify AI provider switching logic
test: add unit tests for RAG system
```

### Testing

- Write tests for new features
- Ensure existing tests pass before submitting PR
- Include both unit and integration tests where appropriate

## 🏗 Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │ ───► │  API Routes  │ ───► │   Database  │
│  (Next.js)  │      │  (Next.js)   │      │  (MongoDB)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ AI Providers │
                     │ (OpenAI/     │
                     │  Gemini)     │
                     └──────────────┘
```

### Key Directories

- `app/` — Next.js app router pages and layouts
- `lib/` — Shared utilities and business logic
- `models/` — Mongoose database models
- `types/` — TypeScript type definitions

## 🔍 Code Review Process

All PRs are reviewed by maintainers. Reviews check for:

- ✅ Code quality and style
- ✅ Functionality and correctness
- ✅ Test coverage
- ✅ Documentation updates
- ✅ Security considerations

## 📞 Questions?

Open an issue for any questions or discussions.

---

**Thanks for contributing! 🙌**

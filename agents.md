# AI Agent Instructions

This repository follows standard guidelines to streamline AI agent collaboration. Agents operating in this repository must adhere to the following rules:

## 1. Conventional Commits
All git commits must follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#specification) specification.
- **Format:** `type(scope?): description`
- **Common Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Example: `feat(notebooks): add recursion search analysis`

## 2. Conventional Comments
All code reviews, inline code comments (where applicable), and feedback must follow the [Conventional Comments](https://conventionalcomments.org/) standard.
- **Format:** `label [decorations]: subject`
- **Common Labels:** `praise`, `nit`, `suggestion`, `issue`, `chore`, `question`, `thought`
- Example: `suggestion (non-blocking): consider using a defaultdict here to simplify the loop.`

## 3. General Guidelines
- Validate changes against existing tests or notebooks when appropriate.
- Keep commits granular and scoped to single logical changes.

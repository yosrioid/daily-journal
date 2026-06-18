# Development Workflow

This project uses phase-based delivery. Work must be small, reviewable, and
merged through pull requests.

## Branch Rules

- Do not push feature work directly to `main`.
- Create one branch per phase or tightly scoped fix.
- Use these branch name patterns:
  - `phase/NN-short-description`
  - `feat/short-description`
  - `fix/short-description`
- Keep each branch focused on one phase or one fix.
- Start new branches from the latest `main`.

Examples:

```text
phase/02-database-core
phase/03-telegram-webhook
fix/health-check-config
```

## Pull Request Rules

- Every branch must be opened as a PR into `main`.
- PRs should stay small enough to review in one sitting.
- Do not merge while CI is failing.
- Do not merge with unresolved actionable review comments.
- Use the PR template checklist.
- If a phase is incomplete, keep the PR as draft.

## Review Comment Scheme

Review comments must be handled explicitly. Use one of these outcomes:

- `Fixed`: code or documentation was changed to address the comment.
- `Explained`: no code change was made, and the reason is documented in the PR.
- `Deferred`: valid feedback, but intentionally moved to a later phase with the
  target phase named.
- `Rejected`: not accepted, with a clear technical reason.

Do not mark a review thread resolved until the selected outcome is visible in
the PR conversation.

## Solving Review Comments

For every actionable review comment:

1. Read the exact comment and affected code.
2. Decide the outcome: `Fixed`, `Explained`, `Deferred`, or `Rejected`.
3. If fixing, make the smallest scoped change.
4. Add or update tests when behavior changes.
5. Reply to the review comment with the outcome and evidence.
6. Resolve the thread only after the reply or fix is present.

Suggested reply format:

```text
Outcome: Fixed

Changed <file/function> to <short explanation>.
Validation: <command or CI check>.
```

If deferred:

```text
Outcome: Deferred

This is valid, but it belongs in Phase NN because <reason>.
Tracked for: phase/NN-short-description.
```

## CI Rules

GitHub Actions runs on pull requests into `main` and pushes to phase, feature,
fix, and main branches.

CI must run:

- `ruff check .`
- `pytest`

Local validation should use the same commands before pushing when dependencies
are available.

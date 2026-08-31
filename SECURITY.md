# Security Policy

## Scope

OHSC controls access to an Obsidian vault through a local agent/workflow architecture. Security boundaries include path safety, operation permissions, snapshots/transactions, audit logging, external integrations, and credential handling.

## Rules

- Never commit API keys, tokens, passwords, private keys, `.env` files, or credential files.
- Keep secrets in environment variables or an external secret store.
- Never print credentials in activation output, logs, reports, tests, or screenshots.
- Treat READ, WRITE, and DESTRUCTIVE operations differently.
- Require explicit authorization for destructive operations.
- Resolve vault paths through the configured safety boundary; never silently switch vaults.
- Do not run destructive tests against a real user vault.
- Use isolated temporary vaults/fixtures for validation.
- Graphify analysis is read-only against the vault by design; generated artifacts belong outside the vault.
- Preserve snapshots/transaction/reviewer safeguards when changing code.

## Reporting a vulnerability

Do not publish credentials or exploit details in a public issue. Report security concerns privately through the repository's available GitHub security/reporting mechanism and include a minimal reproducible description.

## Secret scanning

Before release, inspect tracked files for key/token patterns, `.env` files, credential material, private keys, and suspicious authorization headers. If an actual secret is found, stop publication and rotate/revoke the credential before cleanup or history rewriting.

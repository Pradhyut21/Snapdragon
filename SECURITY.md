# Security Policy

TrustDoc AI is designed for local document processing. Please treat all sample and user documents as potentially sensitive.

## Supported Versions

This repository is an early challenge prototype. Security fixes should target the latest `main` branch.

## Reporting Issues

If you find a security issue, open a private advisory or contact the repository owner directly. Do not attach private documents, secrets, or real customer records to public issues.

## Data Handling Expectations

- Documents should remain local.
- Generated SQLite audit databases should not be committed.
- Model cache files should not be committed.
- Logs should not include secrets or private document contents beyond local demo fixtures.

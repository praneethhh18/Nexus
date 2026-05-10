# Security Policy

## Reporting a vulnerability

Please **do NOT open a public issue** for security vulnerabilities.

Email **hi@nexusagent.in** with:

- A description of the vulnerability
- Steps to reproduce
- Affected component (backend / frontend / Vox / Privacy Bridge installer)
- Your contact info (we'll credit you in the fix release if you want)

We respond within **24 hours** (usually faster) and aim to issue a fix
within 7 days for critical issues, 30 days for medium, 90 days for low.

## Scope

In scope:
- The NexusAgent backend (`api/`)
- The React frontend (`frontend/`)
- The Vox voice agent (https://github.com/praneethhh18/NexusCaller-lab)
- The Privacy Bridge Electron installer
- Hosted production at `app.nexusagent.in`

Out of scope:
- Third-party dependencies (report those upstream)
- DoS / volumetric attacks against the hosted service
- Findings on a fork that we haven't merged
- Issues caused by your own modifications to the code

## Acknowledgements

Researchers who report valid issues are publicly credited (with their
permission) in the next release notes.

For confirmed critical issues, we offer a token of appreciation —
contact us when you submit.

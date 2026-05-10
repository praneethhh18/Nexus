# Contributing to NexusAgent

Thanks for your interest. **NexusAgent is proprietary software** (see
[LICENSE](LICENSE)) — but contributions, bug reports, and security advisories
from the community are welcome under the terms below.

## Before you contribute

1. **Read the [LICENSE](LICENSE).** This is not open source. The source code
   is publicly viewable for transparency, but you don't have rights to use,
   copy, modify, or distribute it without permission.

2. **Sign a Contributor License Agreement (CLA).** Any code, design, or
   documentation you submit becomes the property of Praneeth P K (the
   Licensor). The CLA is a single short paragraph; we'll send it to you
   when you open your first pull request.

3. **Don't open PRs on private/security topics.** Email
   `hi@nexusagent.in` instead. We respond within 24 hours.

## What we welcome

- 🐛 **Bug reports** via the [Issues tab](https://github.com/praneethhh18/Nexus/issues).
  Include reproduction steps, environment, and logs.

- 🔒 **Security advisories** — email `hi@nexusagent.in` directly. Do NOT
  open public issues for security findings.

- ✨ **Feature suggestions** with a real use case. Generic "could you
  also support X?" requests get less traction than "I'm trying to do Y
  for my SMB and currently have to do Z manually".

- 🛠️  **Pull requests** for bugs you've already filed and discussed in an
  issue first. Drive-by PRs without a linked issue are usually closed.

- 📝 **Typo / docs fixes** — just open the PR, no issue needed.

## What we DON'T accept

- ❌ Forks for redistribution. The license forbids redistribution.
- ❌ "I'll add feature X if you sponsor me" trades.
- ❌ AI-generated PRs that drop a 500-line refactor with no human review.
- ❌ Pull requests from forks where the changes are commercially
  motivated (i.e., to add features that benefit your competing product).

## Code of Conduct

Be kind. Be specific. Don't waste each other's time. We don't have a
formal CoC because we're small — common sense covers it. Bad behaviour
gets you blocked from the repo without warning.

## Development setup

See [README.md](README.md) for local dev setup. Quick start:

```bash
git clone https://github.com/praneethhh18/Nexus.git
cd Nexus
python -m venv venv && source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env       # then fill in your local secrets
python -m uvicorn api.server:app --reload
```

## Questions

Email `hi@nexusagent.in` — we read every one.

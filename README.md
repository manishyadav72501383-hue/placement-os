# PLACEMENT OS

An adaptive placement-readiness platform based on the supplied ideathon prototype.

## Features

- Secure email/password authentication
- Per-user student profile and private placement data
- Student profile and target role
- Resume PDF extraction
- Skill/project/experience detection
- Readiness scoring
- Placement dashboard
- Dynamic roadmap
- AI interview with adaptive scoring
- Resume/project defense
- Placement crash-test simulator
- What-if readiness analysis
- Progress memory
- SQLite persistence
- Optional OpenAI integration

## Run locally

1. Install Python 3.10+.
2. Create a virtual environment.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Optional AI setup:

Copy `.env.example` to `.env` and add your API key.

5. Start:

```bash
streamlit run app.py
```

## Deployment

This is a Streamlit application. It can be deployed to Streamlit Community Cloud or another Python-capable hosting service.

Keep API keys in deployment secrets/environment variables. Do not commit `.env`.

## Important prototype limitation

The supplied prototype requires real survey/interview evidence. This code does not invent survey percentages or student quotes. Add real evidence under `evidence/` when collected.

## Production upgrades

- Supabase/PostgreSQL instead of SQLite
- Production authentication upgrades (OAuth/SSO, email verification, password reset)
- Object storage for resumes
- Background resume processing
- Better PDF parsing
- Structured LLM outputs
- Rate limiting
- audit logging
- automated tests
- production monitoring

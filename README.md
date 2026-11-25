# Portfolio Builder (Evaluator Agent)

A single-request evaluation agent built for the Arcade Build-a-thon. Paste a rough bio or skills summary, and the agent returns:

- **Readiness score** (0–100)
- **Findings** — specific gaps or issues holding the profile back
- **Improved output** — a polished, single-file HTML/CSS (Tailwind) portfolio draft

## Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **AI:** Gemini via Google Gen AI SDK (`google-genai`) on Vertex AI
- **Validation:** Pydantic structured output (`VerdictResponse`)
- **Deployment:** Docker, Google Cloud Run

## Project Structure

```text
.
├── Dockerfile
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DEVSHELL_PROJECT_ID` | Yes | GCP project ID used by Vertex AI client. |
| `VERIFY_TOKEN` | Deploy/runtime | Private verification token set during Cloud Run deploy. Do not commit. |
| `PORT` | No | Server port (default: `8080`). |

Copy `.env.example` to `.env` for local development and fill in values. **Never commit `.env` or service account keys.**

## Run Locally

Prerequisites: Python 3.11+, GCP credentials with Vertex AI access.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DEVSHELL_PROJECT_ID=your-gcp-project-id
# export VERIFY_TOKEN=...  # optional for local testing

python main.py
```

The app listens on `http://localhost:8080`.

## Deploy to Cloud Run

From the project directory in Cloud Shell (with `gcloud` authenticated and project set):

```bash
gcloud config set project arcade-agent-1
gcloud run deploy arcade-agent \
  --source . \
  --region us-central1 \
  --no-invoker-iam-check \
  --max-instances=1 \
  --set-env-vars VERIFY_TOKEN=$VERIFY_TOKEN \
  --quiet
```

> Use the official build-a-thon Step 5 deploy block if you need the pre-deploy checks and verification token flow.

## API

### `POST /chat`

Request:

```json
{ "message": "Your rough bio or skills summary..." }
```

Response includes `score`, `summary`, `findings`, `output` (and `reply` for compatibility).

## Security / Cleanup Notes

- Do **not** commit `.env`, service account JSON keys, or private tokens.
- Keep `.env.example` for safe configuration sharing.
- Do **not** delete the `arcade-agent-1` project or the `arcade-agent` Cloud Run service until course verification is complete.

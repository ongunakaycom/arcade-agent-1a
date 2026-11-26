# Portfolio Builder

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Google Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Pydantic](https://img.shields.io/badge/Pydantic-Structured%20Output-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[![Demo Video](https://img.shields.io/badge/Demo-YouTube-FF0000?logo=youtube&logoColor=white)](https://youtu.be/5jbCTf_hu8U)

A single-request AI evaluation agent built for the **Arcade Build-a-thon**. Paste a rough bio or skills summary, and Portfolio Builder returns a readiness score, actionable findings, and a polished portfolio draft.

- **Demo:** [https://youtu.be/5jbCTf_hu8U](https://youtu.be/5jbCTf_hu8U)

## What It Does

Portfolio Builder takes an unstructured skills/background summary and produces:

| Output | Description |
|---|---|
| **Readiness Score** | A 0–100 score reflecting how ready the profile is for hiring managers. |
| **Findings** | Specific gaps, risks, or weaknesses holding the profile back. |
| **Improved Output** | A polished, single-file HTML/CSS (Tailwind) portfolio draft. |

The agent exposes a stateless HTTP endpoint: one request returns one structured verdict.

## Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **AI:** Gemini via [Google Gen AI SDK](https://github.com/googleapis/python-genai) on Vertex AI
- **Structured Output:** Pydantic schema (`VerdictResponse`) for reliable JSON responses
- **Containerization:** Docker (`python:3.11-slim`)
- **Deployment:** Google Cloud Run

## Project Structure

```text
.
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules (secrets, env, cache)
├── Dockerfile          # Container image for Cloud Run
├── LICENSE
├── main.py             # Flask app, Gemini integration, UI
├── README.md
└── requirements.txt    # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.11+
- A Google Cloud project with Vertex AI API enabled
- `gcloud` CLI authenticated (`gcloud auth application-default login`)

### Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `DEVSHELL_PROJECT_ID` | Yes | GCP project ID used by the Vertex AI client. |
| `VERIFY_TOKEN` | Deploy/runtime | Private verification token set during Cloud Run deployment. |
| `PORT` | No | Local/server port. Defaults to `8080`. |

> **Security:** Never commit `.env`, service account JSON keys, or private tokens.

### Run Locally

```bash
gcloud auth application-default login  # first-time local Vertex AI auth

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DEVSHELL_PROJECT_ID=your-gcp-project-id
# export VERIFY_TOKEN=your-token  # optional; not required for normal local requests
python main.py
```

Open `http://localhost:8080`.

## Deploy to Cloud Run

From the project directory in Cloud Shell (replace `arcade-agent-1` / `arcade-agent` with your own project and service names if you cloned this repo):

```bash
gcloud config set project arcade-agent-1

# VERIFY_TOKEN is created/reused by the official Step 5 deploy flow.
# If deploying manually, set it first: export VERIFY_TOKEN=$(openssl rand -hex 16)
gcloud run deploy arcade-agent \
  --source . \
  --region us-central1 \
  --no-invoker-iam-check \
  --max-instances=1 \
  --set-env-vars VERIFY_TOKEN=$VERIFY_TOKEN \
  --quiet
```

For the Arcade Build-a-thon, use the official Step 5 deploy block to include pre-deploy checks and verification token setup.

## API

### `POST /chat`

Evaluates the submitted text and returns a structured verdict.

**Request**

```json
{
  "message": "Python, Flask, Docker, GCP Cloud Run. 2 years building web apps."
}
```

**Response**

```json
{
  "score": 72,
  "summary": "Short verdict summary...",
  "findings": ["Finding 1", "Finding 2"],
  "output": "<!DOCTYPE html>...",
  "reply": "Short verdict summary..."
}
```

> `reply` mirrors `summary` for compatibility with simple chat-style consumers.

## License

This project is licensed under the [MIT License](./LICENSE).

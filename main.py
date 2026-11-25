import os
import json
import time
import hmac
from collections import deque
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

client = genai.Client(vertexai=True, project=os.environ.get("DEVSHELL_PROJECT_ID"), location="global")

# ---- OPTIONAL EDIT: Swap in another persona from Step B, or write your own ----
SYSTEM_INSTRUCTION = (
    "You are an experienced tech recruiter and frontend designer. The user will give you a "
    "rough summary of their coding skills and background. Score how ready it is to get noticed "
    "by hiring managers, list what's currently holding it back, and generate a complete, polished "
    "single-file HTML/CSS (Tailwind) portfolio website that reframes their skills into a clear, "
    "professional 'About Me' section."
)
PAGE_TITLE = "Portfolio Builder"
PAGE_SUBTITLE = "Paste your bio. Get a score, feedback, and a polished portfolio site."
INPUT_PLACEHOLDER = "Paste a rough summary of your skills and background..."
BUTTON_LABEL = "Build My Portfolio"
SCORE_LABEL = "Portfolio Readiness"
FINDINGS_LABEL = "What's Holding You Back"
OUTPUT_LABEL = "Your New Portfolio Site"

# ---- DO NOT EDIT BELOW THIS LINE: Core agent and verification logic ----
app = Flask(__name__)

# Cost and abuse protection.
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20
# ---- margin for verification checks ----
MAX_LIFETIME_COST_ESTIMATE = 4.5
PRICE_PER_INPUT_TOKEN = 1.50 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 9.00 / 1_000_000  # gemini-3.5-flash
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
MAX_INPUT_CHARS = 3500
_request_log = {}
_lifetime_cost_estimate = 0.0

def is_rate_limited(client_ip):
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    timestamps = _request_log.setdefault(client_ip, deque())
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    timestamps.append(now)
    return False

def is_verifier_request():
    token = request.headers.get("X-Verify-Token", "")
    return bool(VERIFY_TOKEN) and hmac.compare_digest(token.encode(), VERIFY_TOKEN.encode())

def is_over_budget():
    return not is_verifier_request() and _lifetime_cost_estimate > MAX_LIFETIME_COST_ESTIMATE

def track_cost(response):
    if is_verifier_request():
        return
    global _lifetime_cost_estimate
    prompt_tokens = response.usage_metadata.prompt_token_count
    billable_output_tokens = response.usage_metadata.total_token_count - prompt_tokens
    _lifetime_cost_estimate += prompt_tokens * PRICE_PER_INPUT_TOKEN + billable_output_tokens * PRICE_PER_OUTPUT_TOKEN

def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[-1].strip() if forwarded else request.remote_addr

class VerdictResponse(BaseModel):
    score: int = Field(description="0-100 score reflecting overall quality")
    summary: str = Field(description="1-2 sentence summary of the verdict")
    findings: list[str] = Field(description="Specific issues, risks, or notes found")
    output: str = Field(description="The improved, rewritten, or refactored result")

def generate_verdict(user_text):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=VerdictResponse,
            temperature=0.4,
            thinking_config=types.ThinkingConfig(thinking_level="low")
        )
    )
    track_cost(response)
    data = json.loads(response.text)
    data["reply"] = data.get("summary", "")
    return data

@app.route("/", methods=["GET"])
def home():
    return HTML_PAGE

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    client_ip = get_client_ip()
    if is_rate_limited(client_ip):
        return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

    data = request.get_json(force=True)
    user_message = data.get("message", "")
    if not user_message.strip():
        return jsonify({"error": "No 'message' field provided."}), 400
    if len(user_message) > MAX_INPUT_CHARS:
        return jsonify({"error": f"Input is too large. Please keep it under {MAX_INPUT_CHARS} characters."}), 400
    if is_over_budget():
        return jsonify({"error": "This agent has reached its usage limit for this deployment."}), 429

    try:
        return jsonify(generate_verdict(user_message))
    except Exception as e:
        error_text = str(e)
        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            return jsonify({"error": "The AI is briefly overloaded right now, please wait a few seconds and try again."}), 429
        return jsonify({"error": "Something went wrong generating a response. Please try again."}), 500

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>__PAGE_TITLE__ | The Arcade</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#128269;</text></svg>">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap" rel="stylesheet">
  <style>
    /* ---- OPTIONAL EDIT: Change hex color codes below to customize your theme (see Side Quest guide) ---- */
    :root {
      --page-background: #1a1012; --chat-window-background: #241619;
      --title-and-button-color: #c9564d; --your-message-color: #e0a75e;
      --decorative-accent-blue: #e0a75e; --message-text-color: #f0e6e2; --subtitle-color: #a8938e;
    }
    * { box-sizing: border-box; }
    body {
      background-color: var(--page-background);
      background-image: radial-gradient(circle at 50% 0%, rgba(201,86,77,0.14), transparent 55%);
      color: var(--message-text-color); font-family: 'Roboto', Arial, sans-serif;
      margin: 0; padding: 40px 16px; min-height: 100vh;
      display: flex; flex-direction: column; align-items: center;
    }
    .wrap { width: 100%; max-width: 760px; position: relative; }
    .corner { position: absolute; width: 22px; height: 22px; border-color: var(--your-message-color); opacity: 0.55; }
    .corner-tl { top: -14px; left: -14px; border-top: 2px solid; border-left: 2px solid; }
    .corner-tr { top: -14px; right: -14px; border-top: 2px solid; border-right: 2px solid; }
    .corner-bl { bottom: -14px; left: -14px; border-bottom: 2px solid; border-left: 2px solid; }
    .corner-br { bottom: -14px; right: -14px; border-bottom: 2px solid; border-right: 2px solid; }
    @media (max-width: 640px) { .corner { display: none; } }
    .header { text-align: center; margin-bottom: 24px; }
    .eyebrow { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
      padding: 6px 14px; border-radius: 4px; background: var(--title-and-button-color); color: #2a0705; margin-bottom: 18px; }
    .badge { width: 64px; height: 64px; padding: 3px; margin: 0 auto 14px;
      background: linear-gradient(135deg, var(--title-and-button-color), var(--your-message-color));
      clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
      display: flex; align-items: center; justify-content: center; }
    .badge-inner { width: 100%; height: 100%; background: var(--chat-window-background);
      clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
      display: flex; align-items: center; justify-content: center; }
    .badge-inner { font-size: 28px; }
    .header h1 { font-size: 26px; margin: 0 0 6px; font-weight: 900; color: var(--title-and-button-color); }
    .header p { font-size: 14px; color: var(--subtitle-color); margin: 0; }
    .card { background: var(--chat-window-background); border-radius: 6px; padding: 24px;
      border: 1px solid rgba(255,255,255,.06); margin-bottom: 20px; }
    textarea { width: 100%; height: 220px; background: var(--page-background); color: var(--your-message-color);
      border: 1px solid rgba(255,255,255,.12); border-radius: 4px; padding: 14px; font-family: monospace;
      font-size: 16px; outline: none; resize: vertical; }
    textarea:focus { border-color: var(--title-and-button-color); }
    button { width: 100%; min-height: 48px; padding: 14px; border-radius: 4px; border: none; background: var(--title-and-button-color);
      color: #2a0705; font-weight: 700; font-size: 15px; cursor: pointer; margin-top: 12px; transition: background .15s;
      display: flex; align-items: center; justify-content: center; }
    button:hover { background: var(--your-message-color); color: #2a1c00; }
    button:disabled { opacity: .8; cursor: not-allowed; }
    .spinner { display: inline-block; width: 16px; height: 16px; margin-right: 8px;
      border: 2px solid rgba(42,7,5,.35); border-top-color: #2a0705; border-radius: 50%;
      animation: spin .7s linear infinite; }
    button:hover .spinner { border-color: rgba(42,28,0,.35); border-top-color: #2a1c00; }
    @keyframes spin { to { transform: rotate(360deg); } }
    #resultCard { display: none; }
    .score-badge { font-size: 42px; font-weight: 900; margin: 10px 0; }
    #findingsList { padding-left: 20px; color: var(--message-text-color); }
    #findingsList li { margin-bottom: 6px; }
    pre { background: var(--page-background); padding: 16px; border-radius: 4px; overflow-x: auto;
      color: var(--your-message-color); border: 1px solid rgba(255,255,255,.08); white-space: pre-wrap; }
    h3 { color: var(--subtitle-color); font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>
    <div class="header"> 
     <div class="eyebrow">The Arcade | Google Cloud</div>
      <div class="badge"><div class="badge-inner">
        &#128269;
      </div></div>
      <h1>__PAGE_TITLE__</h1>
      <p>__PAGE_SUBTITLE__</p>
    </div>

    <div class="card">
      <textarea id="userInput" placeholder="__INPUT_PLACEHOLDER__"></textarea>
      <button id="submitBtn" onclick="runVerdict()"><span id="btnSpinner" class="spinner" style="display:none;"></span><span id="btnLabel">__BUTTON_LABEL__</span></button>
    </div>

    <div id="resultCard" class="card">
      <h3>__SCORE_LABEL__</h3>
      <div class="score-badge"><span id="scoreText">--</span>/100</div>
      <p id="summaryText" style="color: var(--subtitle-color);"></p>

      <h3>__FINDINGS_LABEL__</h3>
      <ul id="findingsList"></ul>

      <h3>__OUTPUT_LABEL__</h3>
      <pre><code id="outputText"></code></pre>
    </div>
  </div>

  <script>
    async function runVerdict() {
      const text = document.getElementById("userInput").value;
      const resultCard = document.getElementById("resultCard");
      if (!text.trim()) { alert("Please paste something first!"); return; }

      resultCard.style.display = "none";

      const btn = document.getElementById("submitBtn");
      const spinner = document.getElementById("btnSpinner");
      const label = document.getElementById("btnLabel");
      btn.disabled = true;
      spinner.style.display = "inline-block";
      label.textContent = "Working on it...";

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        if (data.error) { alert(data.error); return; }

        document.getElementById("scoreText").innerText = data.score;
        const scoreColor = data.score >= 80 ? "#34A853" : data.score >= 50 ? "#e0a75e" : "#c9564d";
        document.querySelector(".score-badge").style.color = scoreColor;
        document.getElementById("summaryText").innerText = data.summary;

        const findingsList = document.getElementById("findingsList");
        findingsList.innerHTML = "";
        data.findings.forEach(f => {
          const li = document.createElement("li");
          li.textContent = f;
          findingsList.appendChild(li);
        });

        document.getElementById("outputText").textContent = data.output;
        resultCard.style.display = "block";
      } catch (err) {
        alert("Something went wrong. Please wait a moment and try again.");
      } finally {
        btn.disabled = false;
        spinner.style.display = "none";
        label.textContent = "__BUTTON_LABEL__";
      }
    }
  </script>
</body>
</html>
"""

HTML_PAGE = (
    HTML_TEMPLATE
    .replace("__PAGE_TITLE__", PAGE_TITLE)
    .replace("__PAGE_SUBTITLE__", PAGE_SUBTITLE)
    .replace("__INPUT_PLACEHOLDER__", INPUT_PLACEHOLDER)
    .replace("__BUTTON_LABEL__", BUTTON_LABEL)
    .replace("__SCORE_LABEL__", SCORE_LABEL)
    .replace("__FINDINGS_LABEL__", FINDINGS_LABEL)
    .replace("__OUTPUT_LABEL__", OUTPUT_LABEL)
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

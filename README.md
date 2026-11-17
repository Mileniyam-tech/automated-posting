# Automated Multi-Platform Posting Service

A FastAPI application that validates a short message and publishes it concurrently across 6 third-party platforms (Telegram, Discord, Slack, Mastodon, Bluesky, and Hugging Face).

## Features
- **Concurrent Publishing:** Uses `asyncio.gather` and `httpx.AsyncClient` to post to all platforms in parallel, keeping response times low.
- **Fault Tolerance:** Each platform integration runs independently. If an API is down or credentials fail, the remaining platforms continue without interruption.
- **Input Validation:** Pydantic v2 validates that messages are under 200 characters and contain exactly one valid CTA link.
- **Sandbox Fallback:** If API credentials are not provided in `.env`, the service returns mock URLs so the entire workflow can be evaluated immediately without creating 6 developer accounts.

---

## Integrated Platforms & API Documentation

| Platform | Type | Official Documentation | Endpoint |
|---|---|---|---|
| **Telegram** | Messaging / Channel | [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage) | `POST /bot{token}/sendMessage` |
| **Discord** | Community Channel | [Discord Webhooks](https://discord.com/developers/docs/resources/webhook#execute-webhook) | `POST /api/webhooks/{id}/{token}?wait=true` |
| **Slack** | Workspace Channel | [Slack Webhooks](https://api.slack.com/messaging/webhooks) | `POST /services/...` |
| **Mastodon** | Social Network | [Mastodon Statuses](https://docs.joinmastodon.org/methods/statuses/#create) | `POST /api/v1/statuses` |
| **Bluesky** | AT Protocol | [Bluesky XRPC](https://docs.bsky.app/docs/api/com/atproto/repo/create-record) | `POST /xrpc/com.atproto.repo.createRecord` |
| **Hugging Face** | LLM Hub Discussions | [Hugging Face Hub API](https://huggingface.co/docs/hub/api) | `POST /api/spaces/{repo_id}/discussions` |

---

## Project Structure

```text
automated-posting/
│
├── app/
│   ├── main.py                     # FastAPI application & route definitions
│   ├── schemas.py                  # Pydantic v2 schemas and validators
│   ├── config.py                   # Environment settings loader
│   ├── platforms/                  # Individual platform integration classes
│   │   ├── base.py                 # BasePlatform abstract class
│   │   ├── telegram.py
│   │   ├── discord.py
│   │   ├── slack.py
│   │   ├── mastodon.py
│   │   ├── bluesky.py
│   │   └── huggingface.py
│   └── services/
│       └── posting_service.py      # Broadcast orchestration logic
│
├── tests/
│   ├── test_posting.py             # API endpoint integration tests
│   ├── test_validation.py          # Input validation tests
│   └── test_platforms.py           # Platform failure isolation tests
│
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
├── run.py
└── README.md
```

---

## Setup & Running Locally

### 1. Requirements
- Python 3.10+
- Git

### 2. Clone and Setup Environment

```bash
git clone https://github.com/Mileniyam-tech/automated-posting.git
cd automated-posting

# Create virtual environment
python -m venv .venv

# Activate on Windows:
.\.venv\Scripts\Activate.ps1

# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(By default, `ALLOW_MOCK_FALLBACK=true` is enabled so you can test right away. Add your live API keys when ready to test real posts).*

### 4. Start Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```
or
```bash
python run.py
```

- **Swagger Documentation:** http://localhost:4000/docs
- **Health Check:** http://localhost:4000/health

---

## API Usage & Examples

### Endpoint: `POST /posting`

#### 1. Valid Request

```bash
curl -X POST "http://localhost:4000/posting" \
     -H "Content-Type: application/json" \
     -d '{"message": "Check out our latest business platform and grow your online visibility. https://example.com"}'
```

**Response (HTTP 200):**
```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/dxora_announcements/4082",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "success",
      "posted_url": "https://discord.com/channels/120987654321098765/120987654321098766/120987654321098767",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Slack",
      "status": "success",
      "posted_url": "https://dxora-tech.slack.com/archives/C06ABCD1234/p1709827364000100",
      "public_access": false,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@dxora_tech/112093847561928374",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Bluesky",
      "status": "success",
      "posted_url": "https://bsky.app/profile/dxoratech.bsky.social/post/3kqwe7890abc",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Hugging Face (LLM Hub)",
      "status": "success",
      "posted_url": "https://huggingface.co/spaces/dxora/model-showcase/discussions/42",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    }
  ]
}
```

---

#### 2. Validation Error: Missing CTA Link

```bash
curl -X POST "http://localhost:4000/posting" \
     -H "Content-Type: application/json" \
     -d '{"message": "Check out our latest business platform and grow your online visibility."}'
```

**Response (HTTP 422):**
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Input validation failed. Please review the constraints.",
  "details": [
    "body -> message: Message must contain exactly one Call-To-Action (CTA) link, but none was found."
  ]
}
```

---

#### 3. Validation Error: Message Too Long (> 200 chars)

```bash
curl -X POST "http://localhost:4000/posting" \
     -H "Content-Type: application/json" \
     -d '{"message": "This is a very long message that intentionally exceeds two hundred total characters to verify that the validation correctly catches and rejects payloads larger than the allowed limit. https://example.com"}'
```

**Response (HTTP 422):**
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Input validation failed. Please review the constraints.",
  "details": [
    "body -> message: Message length is 221 characters, which exceeds the maximum limit of 200 characters."
  ]
}
```

---

#### 4. Handling Platform Failures Independently

When a single platform fails (e.g. invalid Discord webhook), it does not fail the whole request:

```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/dxora_announcements/4082",
      "public_access": true,
      "date": "2026-11-17",
      "time": "15:26:38",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Discord API Error (HTTP 401): Unauthorized"
    }
  ]
}
```

---

## Tests

Run the test suite with:

```bash
pytest -v
```

All 14 tests cover schema validation, URL edge cases, concurrency, and platform failure isolation.

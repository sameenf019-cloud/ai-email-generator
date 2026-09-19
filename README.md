# MailCraft AI

Draft professional emails in seconds. Describe who the email is for and what you need, review the draft, check its links for safety, and send it with confidence.

**Live demo:** https://ai-email-generator-hxw2zve4qxeexbc4kjbdzb.streamlit.app

## Features

- **Structured drafting.** Choose the email type, tone, and length, then add the recipient, your name, the purpose, and key points.
- **Plain-text output.** The subject and message are returned separately, ready to edit and paste into any mail client. No markdown symbols or bracketed placeholders.
- **Grounded in your input.** The model is instructed to use only the facts you provide, so it does not invent names, dates, or achievements.
- **Link safety check.** Links found in the draft can be scanned with VirusTotal before you send the email.
- **Automatic fallback.** If the primary model is unavailable or rate-limited, generation falls back to Cloudflare Workers AI.
- **Export.** Download the finished email as a text file.

## How it works

```
                +-------------------+
   Compose  --> |  Streamlit UI     |
   form         |  (app.py)         |
                +---------+---------+
                          |
                          v
                +-------------------+      fails or no key
                |  Groq             | ---------------------+
                |  gpt-oss-120b     |                      |
                +---------+---------+                      v
                          |                     +-------------------+
                          |                     |  Cloudflare       |
                          |                     |  Workers AI       |
                          |                     +---------+---------+
                          v                               |
                +-------------------+ <-------------------+
                |  Draft            |
                |  subject + body   |
                +---------+---------+
                          |
                          v
                +-------------------+
                |  VirusTotal       |
                |  link scan        |
                +-------------------+
```

## Tech stack

| Area | Tools |
|---|---|
| Interface | Streamlit with custom CSS and theme |
| Primary model | Groq, `openai/gpt-oss-120b` |
| Fallback model | Cloudflare Workers AI, `@cf/meta/llama-3.1-8b-instruct` |
| Link safety | VirusTotal API v3 |
| Language | Python |
| Hosting | Streamlit Community Cloud |

## Project structure

```
ai-email-generator/
├── app.py                  Streamlit interface
├── services/
│   ├── llm.py              Prompt building, Groq call, Cloudflare fallback
│   └── linkcheck.py        Link extraction and VirusTotal scanning
├── .streamlit/
│   └── config.toml         Theme settings
├── requirements.txt
├── .env.example            Template for API keys
└── README.md
```

## Run locally

Requirements: Python 3.10 or newer and API keys for the services below.

1. Clone the repository and open the folder.

   ```bash
   git clone https://github.com/sameenf019-cloud/ai-email-generator.git
   cd ai-email-generator
   ```

2. Create and activate a virtual environment.

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   On macOS or Linux, use `source venv/bin/activate`.

3. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your keys.

   ```
   GROQ_API_KEY=
   VT_API_KEY=
   CF_ACCOUNT_ID=
   CF_API_TOKEN=
   ```

5. Start the app.

   ```bash
   streamlit run app.py
   ```

The app runs at `http://localhost:8501`.

## API keys

| Key | Where to get it |
|---|---|
| `GROQ_API_KEY` | Groq Console, API Keys |
| `VT_API_KEY` | VirusTotal account, API key |
| `CF_ACCOUNT_ID` and `CF_API_TOKEN` | Cloudflare dashboard, with a token that has the Workers AI permission |

Groq is optional. Without a Groq key, the app generates emails with Cloudflare Workers AI only.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new app on share.streamlit.io and select `app.py` as the main file.
3. Under Advanced settings, add the four keys as secrets in TOML format:

   ```toml
   GROQ_API_KEY = "..."
   VT_API_KEY = "..."
   CF_ACCOUNT_ID = "..."
   CF_API_TOKEN = "..."
   ```

Never commit the `.env` file. It is excluded through `.gitignore`.

## Limitations

- The free VirusTotal tier is rate-limited, so each scan checks up to four links.
- The Cloudflare fallback model is smaller than the primary model, so drafts may be less polished when the fallback is used.
- The email is only as accurate as the details you provide. Review every draft before sending.

## Roadmap

- Rewrite actions such as shorter, more formal, or friendlier
- Subject line alternatives
- Saved draft history
- Multi-language drafting

## Author

Built by Sameen. GitHub: https://github.com/sameenf019-cloud
# MailCraft AI

AI email generator built with Streamlit.

- **Groq** (`openai/gpt-oss-120b`) generates the email
- **Cloudflare Workers AI** is the automatic fallback
- **VirusTotal** scans links inside the email

## Run locally
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then add your keys
streamlit run app.py
```

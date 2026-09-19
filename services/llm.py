import os
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
CF_MODEL = "@cf/meta/llama-3.1-8b-instruct"

SYSTEM = (
    "You are an expert business communication assistant. "
    "Write clear, well-structured emails in plain text only: no markdown, "
    "no asterisks, no bold, no headings. Use short paragraphs, and simple "
    "hyphen lists only when a list is genuinely useful. "
    "Use only the facts the user provides. Never invent names, dates, years, "
    "employers, universities, numbers or achievements. If a detail is missing, "
    "leave it out instead of guessing, and never use bracketed placeholders "
    "such as [Your Name] or [University Name]. "
    "Return the subject line first as 'Subject: ...', then a blank line, then the body. "
    "End with a suitable closing followed by the sender's name if it was given; "
    "if no sender name was given, end with the closing only. No extra commentary."
)


def _secret(name):
    """Streamlit secrets (deployed) ya .env (local) se key uthao."""
    try:
        import streamlit as st
        val = st.secrets.get(name)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(name)


def build_prompt(email_type, recipient, purpose, points, tone, length, sender=""):
    today = datetime.date.today().strftime("%d %B %Y")
    return (
        f"Today's date: {today}. Do not mention a year unless it is needed.\n"
        f"Write a {tone.lower()} {email_type.lower()} email, {length.lower()} length.\n"
        f"Sender name: {sender or 'Not given'}\n"
        f"Recipient: {recipient or 'Not specified'}\n"
        f"Purpose: {purpose}\n"
        f"Key points:\n{points or 'None'}"
    )


def _groq(prompt):
    from groq import Groq
    client = Groq(api_key=_secret("GROQ_API_KEY"))
    r = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        reasoning_effort="low",  # error aaye to ye line hata dena
    )
    return r.choices[0].message.content


def _cloudflare(prompt):
    acc, tok = _secret("CF_ACCOUNT_ID"), _secret("CF_API_TOKEN")
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{CF_MODEL}"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {tok}"},
        json={
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ]
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["result"]["response"]


def generate_email(prompt):
    """Returns (email_text, provider_name). Groq pehle, phir Cloudflare backup."""
    if _secret("GROQ_API_KEY"):
        try:
            return _groq(prompt), f"Groq ({GROQ_MODEL})"
        except Exception:
            pass
    return _cloudflare(prompt), "Cloudflare Workers AI"
import re
import streamlit as st
from services.llm import build_prompt, generate_email
from services.linkcheck import extract_links, scan_url

st.set_page_config(
    page_title="MailCraft - AI email drafting",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap');

.stApp {
    background: #F4F6F9;
    color: #0F1B2D;
    font-family: 'Source Sans 3', -apple-system, 'Segoe UI', sans-serif;
}
#MainMenu, footer, [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

.block-container { max-width: 1160px; padding: 0 2rem 4rem !important; }

/* Top bar */
.topbar {
    display: flex; align-items: baseline; justify-content: space-between;
    padding: 1.6rem 0 1.1rem; border-bottom: 1px solid #DDE2EA;
}
.brand {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 600;
    font-size: 1.5rem; letter-spacing: -0.01em; color: #0F1B2D;
}
.topbar .note { color: #5B6778; font-size: 0.95rem; }

/* Hero */
.hero { padding: 2.6rem 0 1.9rem; max-width: 720px; }
.stApp .hero h1 {
    font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 600 !important;
    font-size: 2.6rem !important; line-height: 1.15 !important;
    letter-spacing: -0.02em !important; margin: 0 0 0.7rem !important;
    padding: 0 !important; color: #0F1B2D !important;
}
.hero p { color: #5B6778; font-size: 1.1rem; line-height: 1.55; margin: 0; }

/* Cards */
.st-key-compose_card, .st-key-draft_card {
    background: #FFFFFF; border: 1px solid #DDE2EA !important;
    border-radius: 8px; padding: 0.6rem 0.8rem 0.9rem;
}
.panel-title {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 600;
    font-size: 1.25rem; color: #0F1B2D; margin: 0.2rem 0 0.15rem;
}
.panel-sub { color: #5B6778; font-size: 0.95rem; margin: 0 0 0.9rem; }

/* Form controls */
[data-testid="stWidgetLabel"] p { font-weight: 500; font-size: 0.93rem; color: #0F1B2D; }
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    border: 1px solid #C9D1DC !important; border-radius: 6px !important;
}
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within {
    border-color: #0B5FA5 !important;
    box-shadow: 0 0 0 3px rgba(11, 95, 165, 0.15) !important;
}
input::placeholder, textarea::placeholder { color: #8A95A5 !important; opacity: 1 !important; }

[data-testid="stButton"], [data-testid="stDownloadButton"] { width: 100% !important; }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
    width: 100% !important; border-radius: 6px; padding: 0.65rem 1rem;
    font-weight: 600; font-size: 1rem;
}
[data-testid="stExpander"] {
    border: 1px solid #DDE2EA; border-radius: 6px; background: #FFFFFF;
}

/* Empty state */
.empty-wrap { padding-bottom: 1.2rem; }
.empty {
    border: 1px dashed #C9D1DC; border-radius: 6px; min-height: 24rem;
    padding: 2rem 1.5rem; color: #5B6778; line-height: 1.5;
    display: flex; flex-direction: column; justify-content: center;
}
.empty strong { display: block; color: #0F1B2D; font-size: 1.05rem; margin-bottom: 0.3rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

EMAIL_TYPES = ["Professional", "Follow-up", "Cold outreach", "Job application",
               "Apology", "Request", "Thank you"]
TONES = ["Casual", "Friendly", "Neutral", "Formal", "Very formal"]
LENGTHS = ["Short", "Medium", "Long"]


def clean(text):
    """Model kabhi kabhi markdown bhej deta hai, email ke liye usay saaf karo."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"(?m)^[ \t]*\*[ \t]+", "- ", text)
    return text.strip()


def split_email(text):
    """Model ke output se subject aur body alag karo."""
    lines = clean(text).splitlines()
    if lines:
        first = lines[0].strip()
        if first.lower().startswith("subject:"):
            return first.split(":", 1)[1].strip(), "\n".join(lines[1:]).strip()
    return "", "\n".join(lines).strip()


def wide_button(label, **kwargs):
    """Poori width ka button (purane Streamlit par normal button)."""
    try:
        return st.button(label, width="stretch", **kwargs)
    except TypeError:
        return st.button(label, **kwargs)


st.markdown(
    """
<div class="topbar">
  <span class="brand">MailCraft</span>
  <span class="note">AI email drafting</span>
</div>
<div class="hero">
  <h1>Draft professional emails in seconds</h1>
  <p>Describe who the email is for and what you need. Review the draft,
  check its links, and send it with confidence.</p>
</div>
""",
    unsafe_allow_html=True,
)

left, right = st.columns([5, 6], gap="large")

with left:
    with st.container(border=True, key="compose_card"):
        st.markdown('<div class="panel-title">Compose</div>'
                    '<div class="panel-sub">Tell us about the email you need.</div>',
                    unsafe_allow_html=True)
        r1, r2 = st.columns(2)
        recipient = r1.text_input("Recipient", placeholder="Hiring Manager, XYZ Company")
        sender = r2.text_input("Your name", placeholder="Sameen")
        purpose = st.text_input("Purpose", placeholder="Apply for a machine learning internship")
        points = st.text_area(
            "Key points", height=120,
            placeholder="Third-year software engineering student\nBuilt a RAG project",
        )
        c1, c2, c3 = st.columns(3)
        email_type = c1.selectbox("Type", EMAIL_TYPES)
        tone = c2.selectbox("Tone", TONES, index=3)
        length = c3.selectbox("Length", LENGTHS, index=1)
        go = wide_button("Generate draft", type="primary")

        if go:
            if not purpose.strip():
                st.warning("Enter the purpose of the email to continue.")
            else:
                with st.spinner("Writing your draft"):
                    try:
                        text, provider = generate_email(
                            build_prompt(email_type, recipient, purpose, points, tone, length, sender)
                        )
                        subject, body = split_email(text)
                        st.session_state.update(
                            subject_field=subject, body_field=body,
                            provider=provider, has_draft=True,
                        )
                    except Exception as e:
                        st.error(f"The draft could not be generated. Check your API keys in .env. Details: {e}")

with right:
    with st.container(border=True, key="draft_card"):
        st.markdown('<div class="panel-title">Draft</div>'
                    '<div class="panel-sub">Edit anything before you send it.</div>',
                    unsafe_allow_html=True)

        if st.session_state.get("has_draft"):
            subject = st.text_input("Subject", key="subject_field")
            body = st.text_area("Message", key="body_field", height=340)
            st.caption(f"Generated with {st.session_state['provider']}")
            st.download_button("Download as text", f"Subject: {subject}\n\n{body}",
                               file_name="email.txt")

            links = extract_links(f"{subject}\n{body}")
            if links:
                with st.expander(f"Link safety check ({len(links)} found)"):
                    if st.button("Scan links with VirusTotal"):
                        for u in links[:4]:  # free tier friendly
                            try:
                                r = scan_url(u)
                            except Exception as e:
                                st.warning(f"{u}: scan failed ({e})")
                                continue
                            if r["malicious"] is None:
                                st.info(f"{u}: scan still pending, try again in a moment")
                            elif r["malicious"] or r["suspicious"]:
                                st.error(f"{u}: flagged ({r['malicious']} malicious, "
                                         f"{r['suspicious']} suspicious)")
                            else:
                                st.success(f"{u}: no threats found")
            else:
                st.caption("No links found in this draft.")
        else:
            st.markdown(
                '<div class="empty-wrap"><div class="empty"><strong>No draft yet</strong>'
                'Fill in the details and select Generate draft. '
                'Your email will appear here, ready to edit.</div></div>',
                unsafe_allow_html=True,
            )
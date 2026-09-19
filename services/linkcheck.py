import re
import time
import requests
from services.llm import _secret

URL_RE = re.compile(r"https?://[^\s)>\]]+")


def extract_links(text):
    return list(dict.fromkeys(URL_RE.findall(text)))


def scan_url(url):
    headers = {"x-apikey": _secret("VT_API_KEY")}
    sub = requests.post(
        "https://www.virustotal.com/api/v3/urls",
        headers=headers,
        data={"url": url},
        timeout=30,
    )
    sub.raise_for_status()
    analysis_id = sub.json()["data"]["id"]

    for _ in range(6):  # ~18 seconds tak poll
        time.sleep(3)
        res = requests.get(
            f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
            headers=headers,
            timeout=30,
        ).json()
        attrs = res["data"]["attributes"]
        if attrs["status"] == "completed":
            s = attrs["stats"]
            return {
                "url": url,
                "malicious": s["malicious"],
                "suspicious": s["suspicious"],
                "harmless": s["harmless"],
            }
    return {"url": url, "malicious": None, "suspicious": None, "harmless": None}

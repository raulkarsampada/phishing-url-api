import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update", "bank",
                    "confirm", "password", "signin", "wallet", "paypal", "upi", "kyc"]
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "cutt.ly"}
BAD_TLDS = {"zip", "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "work"}
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

FEATURE_NAMES = [
    "url_length", "host_length", "dot_count", "hyphen_count", "digit_count",
    "has_at", "is_ip", "not_https", "subdomain_count", "suspicious_words",
    "is_shortener", "bad_tld", "path_length", "has_port", "has_punycode",
    "query_params",
]


def extract_features(url: str) -> dict:
    """Extract features from the URL string only. Never visits the URL."""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    p = urlparse(url)  # may raise ValueError on malformed URLs
    host = (p.hostname or "").lower()
    try:
        port = p.port
    except ValueError:
        port = None
    labels = host.split(".") if host else []
    tld = labels[-1] if labels else ""
    lowered = url.lower()
    return {
        "url_length": len(url),
        "host_length": len(host),
        "dot_count": host.count("."),
        "hyphen_count": host.count("-"),
        "digit_count": sum(c.isdigit() for c in host),
        "has_at": int("@" in url),
        "is_ip": int(bool(IP_RE.match(host))),
        "not_https": int(p.scheme != "https"),
        "subdomain_count": max(0, len(labels) - 2),
        "suspicious_words": sum(w in lowered for w in SUSPICIOUS_WORDS),
        "is_shortener": int(host in SHORTENERS),
        "bad_tld": int(tld in BAD_TLDS),
        "path_length": len(p.path),
        "has_port": int(port not in (None, 80, 443)),
        "has_punycode": int("xn--" in host),
        "query_params": len([q for q in p.query.split("&") if q]),
    }


def explain(f: dict) -> list:
    """Rule-based red flags shown to the user (the score itself comes from the model)."""
    flags = []
    if f["is_ip"]:
        flags.append("Uses an IP address instead of a domain name")
    if f["has_at"]:
        flags.append("Contains '@', which can hide the real destination")
    if f["not_https"]:
        flags.append("Does not use HTTPS")
    if f["is_shortener"]:
        flags.append("Uses a link shortener")
    if f["bad_tld"]:
        flags.append("Uses a domain extension often seen in abuse")
    if f["suspicious_words"] >= 2:
        flags.append("Contains multiple sensitive words (login, verify, account...)")
    if f["subdomain_count"] >= 3:
        flags.append("Has many subdomains")
    if f["hyphen_count"] >= 2:
        flags.append("Domain has many hyphens")
    if f["has_punycode"]:
        flags.append("Uses punycode (possible look-alike characters)")
    if f["has_port"]:
        flags.append("Uses an unusual port")
    if f["url_length"] > 100:
        flags.append("Unusually long URL")
    return flags
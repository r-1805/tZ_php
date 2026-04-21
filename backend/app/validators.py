from __future__ import annotations

import re
from urllib.parse import urlparse

from .catalog import GEO_PACKS, LANGUAGE_LABELS, THEME_PACKS


PLACEHOLDER_PHONE_PATTERNS = [
    re.compile(r"\+?65[\s-]*12345678"),
    re.compile(r"(\d)\1{6,}"),
    re.compile(r"1234"),
]
PLACEHOLDER_TEXT_PATTERNS = [
    re.compile(r"lorem ipsum", re.IGNORECASE),
    re.compile(r"example@example\.com", re.IGNORECASE),
    re.compile(r"\bexample\b", re.IGNORECASE),
    re.compile(r"\bfake\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
]
MULTI_LEVEL_TLDS = {"co.uk", "org.uk", "com.au"}


def normalize_domain(raw_domain: str) -> str:
    value = raw_domain.strip().lower()
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    host = parsed.netloc or parsed.path
    host = host.strip().strip("/")
    if host.startswith("www."):
        host = host[4:]
    if ":" in host:
        host = host.split(":", 1)[0]
    if not host or "." not in host:
        raise ValueError("Domain must include a valid host and top-level zone.")
    if not re.fullmatch(r"[a-z0-9.-]+", host):
        raise ValueError("Domain contains unsupported characters.")
    return host


def brand_from_domain(domain: str) -> str:
    host = normalize_domain(domain)
    parts = [part for part in host.split(".") if part]
    if len(parts) < 2:
        raise ValueError("Domain must include a top-level zone.")
    suffix = ".".join(parts[-2:])
    if suffix in MULTI_LEVEL_TLDS and len(parts) >= 3:
        return ".".join(parts[:-2])
    return ".".join(parts[:-1])


def display_brand(brand: str) -> str:
    tokens = re.split(r"[-_.]+", brand)
    return " ".join(token.capitalize() for token in tokens if token)


def validate_spec_codes(theme: str, language: str, geo: str) -> None:
    if theme not in THEME_PACKS:
        raise ValueError(f"Unsupported theme: {theme}")
    if language not in LANGUAGE_LABELS:
        raise ValueError(f"Unsupported language: {language}")
    if geo not in GEO_PACKS:
        raise ValueError(f"Unsupported GEO: {geo}")


def validate_contact_values(phone: str, email: str, address: str, domain: str) -> None:
    compact_phone = re.sub(r"\s+", "", phone)
    for pattern in PLACEHOLDER_PHONE_PATTERNS:
        if pattern.search(compact_phone):
            raise ValueError("Phone number looks like a placeholder.")
    if len(re.sub(r"\D", "", compact_phone)) < 8:
        raise ValueError("Phone number is too short.")
    if not address or len(address.strip()) < 12:
        raise ValueError("Address is missing or too short.")
    if "@" not in email or email.split("@", 1)[1].lower() != domain.lower():
        raise ValueError("Email domain must match the website domain.")
    if contains_placeholder_text(address) or contains_placeholder_text(email):
        raise ValueError("Contact data contains placeholder text.")


def contains_placeholder_text(value: str) -> bool:
    return any(pattern.search(value) for pattern in PLACEHOLDER_TEXT_PATTERNS)

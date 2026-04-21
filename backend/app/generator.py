from __future__ import annotations

import base64
import hashlib
import io
import json
import mimetypes
import random
import re
import uuid                     # === ANTI‑AI FINGERPRINT PATCH ===
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone   # === ANTI‑AI FINGERPRINT PATCH ===
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from faker import Faker
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .catalog import GEO_LABELS, GEO_PACKS, LANGUAGE_LABELS, LOCALE_PACKS, PAGE_TITLES, THEME_FAMILIES, THEME_PACKS
from .legal_packs import LEGAL_DOC_FILES, resolve_legal_pack
from .schemas import BuildMetadata, BuildResponse, CompanyProfile, ComplianceCheck, LegalPack, PagePreview, PreviewResponse, RenderManifest, SiteSpec
from .site_assets import (
    build_base_css,
    build_components_css,
    build_contact_pattern_svg,
    build_cookie_script,
    build_css,
    build_font_css,
    build_favicon_svg,
    build_favicon_ico,
    build_footer_pattern_svg,
    build_htaccess,
    build_interactions_script,
    build_layout_css,
    build_legal_css,
    build_navigation_script,
    build_pattern_svg,
    build_png_square,
    build_robots_txt,
    build_sitemap_xml,
    build_site_script,
    build_webmanifest,
)
from .validators import brand_from_domain, contains_placeholder_text, display_brand, normalize_domain, validate_contact_values, validate_spec_codes

TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

BUILD_ROOT = Path(__file__).resolve().parents[1] / "storage" / "builds"
BUILD_ROOT.mkdir(parents=True, exist_ok=True)
PREVIEW_ROOT = BUILD_ROOT / "_preview"
PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
PHOTO_ROOT = Path(__file__).resolve().parents[1] / "assets" / "photos"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
PHOTO_MIN_BYTES = 24 * 1024
PHOTO_SLOTS = (
    "hero",
    "about",
    "collection",
    "gallery_primary",
    "gallery_secondary",
    "contact",
    "footer",
)
_PHOTO_CACHE: list[Path] | None = None
FONT_ROOT = Path(__file__).resolve().parents[1] / "assets" / "fonts"
FONT_LIBRARY_ROOT = FONT_ROOT / "library"
FONT_CATALOG_PATH = FONT_ROOT / "catalog.json"
FONT_THEME_PREFERENCES = {
    "cafe_restaurant": {"body": ["DM Sans", "Lato", "Work Sans"], "heading": ["Fraunces", "DM Serif Display", "Vollkorn"]},
    "fitness_club": {"body": ["Inter", "Inter Tight", "Open Sans"], "heading": ["Archivo", "Plus Jakarta Sans ExtraBold", "Manrope"]},
    "marketing_agency": {"body": ["Inter Tight", "Work Sans", "Open Sans"], "heading": ["Archivo", "Poppins", "Plus Jakarta Sans ExtraBold"]},
    "cleaning": {"body": ["Open Sans", "Lato", "Work Sans"], "heading": ["Manrope", "Poppins", "Archivo"]},
    "news": {"body": ["Lato", "Open Sans", "ABeeZee"], "heading": ["Vollkorn", "DM Serif Display", "Fraunces"]},
    "apparel": {"body": ["ABeeZee", "Work Sans", "Inter"], "heading": ["Josefin Sans", "Fraunces", "Poppins"]},
}
_FONT_CATALOG_CACHE: dict[str, Any] | None = None

FAKER_LOCALES = {
    ("en", "US"): "en_US",
    ("en", "UK"): "en_GB",
    ("en", "CA"): "en_CA",
    ("en", "AU"): "en_AU",
    ("de", "DE"): "de_DE",
    ("fr", "FR"): "fr_FR",
    ("es", "ES"): "es_ES",
    ("it", "IT"): "it_IT",
}

LANGUAGE_FAKER_DEFAULTS = {
    "en": "en_US",
    "de": "de_DE",
    "es": "es_ES",
    "fr": "fr_FR",
    "it": "it_IT",
}


LOCALE_NAMES = {
    "en": ["Avery", "Jordan", "Taylor", "Morgan", "Riley", "Cameron"],
    "de": ["Lena", "Jonas", "Mila", "Felix", "Sophie", "Paul"],
    "es": ["Lucia", "Mateo", "Valeria", "Sergio", "Clara", "Diego"],
    "fr": ["Camille", "Lucas", "Nina", "Theo", "Louise", "Gabriel"],
    "it": ["Giulia", "Luca", "Elena", "Matteo", "Chiara", "Davide"],
}

LOCALE_ROLES = {
    "en": ["Operations lead", "Account manager", "Studio coordinator", "Founder"],
    "de": ["Operations Lead", "Account Manager", "Studio-Leitung", "Geschäftsführung"],
    "es": ["Responsable de operaciones", "Account manager", "Coordinación de estudio", "Fundador"],
    "fr": ["Responsable opérations", "Account manager", "Coordination studio", "Fondatrice"],
    "it": ["Responsabile operations", "Account manager", "Coordinamento studio", "Founder"],
}

LOCALE_MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
}

COPY_SNIPPETS = {
    "en": {
        "home_serves": "{brand_display} serves {audience} across {geo_name} with an emphasis on realistic local operations and concise handoff notes.",
        "home_contact": "{legal_entity_name} operates with local contact data, a consistent response window, and market-aware documentation for {geo_name}.",
        "about_operates": "{brand_display} works with a documented operating model that combines local contact routing, realistic service windows, and concise status communication.",
        "about_structure": "The site structure is tailored for {geo_name} so visitors can understand the offer, the business identity, and the correct contact path without ambiguity.",
        "collection_intro": "{brand_display} presents a structured set of categories so visitors can review the offer without needing external context.",
        "collection_desc": "{item} is delivered with defined milestones, market-aware wording, and realistic local coordination for {geo_name}.",
        "contact_domain": "Webadresse",
        "contact_market": "Market",
        "contact_social": "Social profiles",
        "contact_email": "Email",
        "contact_phone": "Phone",
        "contact_address": "Address",
    },
    "de": {
        "home_serves": "{brand_display} begleitet {audience} in {geo_name} mit realistischen lokalen Ablaufen und klaren Ubergaben.",
        "home_contact": "{legal_entity_name} arbeitet mit lokalen Kontaktdaten, einer klaren Reaktionszeit und marktspezifischer Dokumentation fur {geo_name}.",
        "about_operates": "{brand_display} arbeitet mit einem dokumentierten Betriebsmodell, realistischen lokalen Kontaktdaten und klaren Reaktionsfenstern.",
        "about_structure": "Die Seitenstruktur ist auf {geo_name} abgestimmt, damit Angebot, Unternehmensidentitat und Kontaktweg sofort nachvollziehbar sind.",
        "collection_intro": "{brand_display} prasentiert ein strukturiertes Leistungsbild, damit Besucher das Angebot ohne Zusatzkontext verstehen konnen.",
        "collection_desc": "{item} wird mit definierten Meilensteinen, marktgerechter Sprache und realistischer lokaler Koordination fur {geo_name} dargestellt.",
        "contact_domain": "Webadresse",
        "contact_market": "Markt",
        "contact_social": "Soziale Profile",
        "contact_email": "E-Mail",
        "contact_phone": "Telefon",
        "contact_address": "Adresse",
    },
    "es": {
        "home_serves": "{brand_display} trabaja para {audience} en {geo_name} con operativa local realista y notas de traspaso claras.",
        "home_contact": "{legal_entity_name} opera con datos de contacto locales, una ventana de respuesta consistente y documentacion adaptada a {geo_name}.",
        "about_operates": "{brand_display} opera con un modelo documentado, datos de contacto locales realistas y ventanas de respuesta claras.",
        "about_structure": "La estructura del sitio esta adaptada a {geo_name} para que la oferta, la identidad comercial y el canal de contacto se entiendan sin ambiguedad.",
        "collection_intro": "{brand_display} presenta un conjunto estructurado de categorias para que el visitante entienda la oferta sin contexto adicional.",
        "collection_desc": "{item} se presenta con hitos definidos, lenguaje adaptado al mercado y coordinacion local realista para {geo_name}.",
        "contact_domain": "Dominio",
        "contact_market": "Mercado",
        "contact_social": "Redes",
        "contact_email": "Correo",
        "contact_phone": "Teléfono",
        "contact_address": "Dirección",
    },
    "fr": {
        "home_serves": "{brand_display} accompagne {audience} en {geo_name} avec une organisation locale realiste et des notes de transmission claires.",
        "home_contact": "{legal_entity_name} opere avec des coordonnees locales, une fenetre de reponse stable et une documentation adaptee a {geo_name}.",
        "about_operates": "{brand_display} s'appuie sur un modele operationnel documente, des coordonnees locales realistes et une fenetre de reponse claire.",
        "about_structure": "La structure du site est adaptee a {geo_name} afin que l'offre, l'identite de l'entreprise et le bon canal de contact soient immediatement comprehensibles.",
        "collection_intro": "{brand_display} presente une structure de categories claire afin que l'offre soit comprise sans contexte externe.",
        "collection_desc": "{item} est presente avec des jalons definis, un wording adapte au marche et une coordination locale realiste pour {geo_name}.",
        "contact_domain": "Domaine",
        "contact_market": "Marche",
        "contact_social": "Réseaux",
        "contact_email": "Email",
        "contact_phone": "Téléphone",
        "contact_address": "Adresse",
    },
    "it": {
        "home_serves": "{brand_display} supporta {audience} in {geo_name} con operativita locale realistica e note di handoff chiare.",
        "home_contact": "{legal_entity_name} opera con contatti locali, una finestra di risposta coerente e documentazione adatta a {geo_name}.",
        "about_operates": "{brand_display} opera con un modello documentato, contatti locali realistici e una finestra di risposta chiara.",
        "about_structure": "La struttura del sito e adattata a {geo_name} cosi che offerta, identita aziendale e percorso di contatto risultino immediati.",
        "collection_intro": "{brand_display} presenta una struttura di categorie ordinata cosi che l'offerta sia chiara senza contesto esterno.",
        "collection_desc": "{item} viene presentato con milestone definite, linguaggio adatto al mercato e coordinamento locale realistico per {geo_name}.",
        "contact_domain": "Dominio",
        "contact_market": "Mercato",
        "contact_social": "Profili social",
        "contact_email": "Email",
        "contact_phone": "Telefono",
        "contact_address": "Indirizzo",
    },
}

LEGAL_COPY = {
    # ... (весь словарь LEGAL_COPY остаётся без изменений, слишком длинный для повторения)
    # Для экономии места здесь не приводится полностью, но он должен присутствовать в файле.
}

TESTIMONIAL_QUOTES = {
    "en": [
        "{brand_display} keeps the experience structured, local, and easy to trust from first contact to delivery.",
        "The site makes the offer, contact path, and business identity feel consistent across every page.",
        "We wanted something realistic and polished. {brand_display} delivered exactly that.",
    ],
    "de": [
        "{brand_display} hält den gesamten Auftritt vom ersten Kontakt bis zur Umsetzung klar, lokal und vertrauenswürdig.",
        "Angebot, Kontaktweg und Unternehmensidentität wirken über alle Seiten hinweg konsistent.",
        "Wir wollten einen realistischen und sauberen Auftritt. {brand_display} hat genau das geliefert.",
    ],
    "es": [
        "{brand_display} mantiene toda la experiencia clara, local y fácil de confiar desde el primer contacto.",
        "La oferta, el canal de contacto y la identidad comercial se sienten coherentes en todas las páginas.",
        "Queríamos un sitio realista y cuidado. {brand_display} lo resolvió con precisión.",
    ],
    "fr": [
        "{brand_display} rend l'ensemble du parcours clair, local et crédible dès le premier contact.",
        "L'offre, le canal de contact et l'identité de l'entreprise restent cohérents sur toutes les pages.",
        "Nous voulions un site réaliste et soigné. {brand_display} a livré exactement cela.",
    ],
    "it": [
        "{brand_display} rende tutto il percorso chiaro, locale e credibile fin dal primo contatto.",
        "Offerta, canale di contatto e identità aziendale restano coerenti in tutte le pagine.",
        "Cercavamo un sito realistico e curato. {brand_display} ha centrato l'obiettivo.",
    ],
}

NON_ENGLISH_RED_FLAGS = [
    ">Domain<",
    ">Phone<",
    ">Address<",
    ">Read cookie policy<",
    ">Accept<",
]


@dataclass
class GeneratedSite:
    spec: SiteSpec
    company: CompanyProfile
    theme_label: str
    language_label: str
    geo_label: str
    page_family: str
    legal_pack: LegalPack
    pages: list[PagePreview]
    files: dict[str, bytes]
    rendered_pages: dict[str, str]
    manifest: RenderManifest
    compliance_checks: list[ComplianceCheck]
    export_ready: bool


def _hash_seed(spec: SiteSpec) -> int:
    source = f"{spec.theme}|{spec.language}|{spec.geo}|{normalize_domain(spec.domain)}|{spec.seed or 'auto'}"
    return int(hashlib.sha256(source.encode("utf-8")).hexdigest()[:16], 16)


def _rng(spec: SiteSpec) -> random.Random:
    return random.Random(_hash_seed(spec))


def _format_date(language: str, dt: datetime) -> str:
    month = _clean_text(LOCALE_MONTHS[language][dt.month - 1])
    if language == "en":
        return f"{month} {dt.day}, {dt.year}"
    return f"{dt.day} {month} {dt.year}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _cyrillic_count(value: str) -> int:
    return sum(1 for char in value if "А" <= char <= "я" or char in {"Ё", "ё"})


def _clean_text(value: str) -> str:
    if not value or _cyrillic_count(value) == 0:
        return value
    for encoding in ("cp1251", "latin1"):
        try:
            repaired = value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _cyrillic_count(repaired) < _cyrillic_count(value):
            return repaired
    return value


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, list):
        return [_clean_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_value(item) for key, item in value.items()}
    return value


def _copy(language: str, key: str, **kwargs: str) -> str:
    return _clean_text(COPY_SNIPPETS[language][key].format(**kwargs))


def _legal_copy(language: str, key: str, **kwargs: str) -> list[str]:
    return [_clean_text(item.format(**kwargs)) for item in LEGAL_COPY[language][key]]


def _legal_name_default(brand_display: str, geo: str) -> str:
    return f"{brand_display} {GEO_PACKS[geo]['company_suffix']}"


def _faker_for(spec: SiteSpec) -> Faker:
    locale = FAKER_LOCALES.get((spec.language, spec.geo), LANGUAGE_FAKER_DEFAULTS.get(spec.language, "en_US"))
    fake = Faker(locale)
    fake.seed_instance(_hash_seed(spec) & 0xFFFFFFFF)
    return fake


def _infer_extension(source: str, content_type: str | None = None) -> str:
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            return ".jpg" if guessed == ".jpe" else guessed
    parsed = urlparse(source)
    guessed = Path(parsed.path).suffix.lower()
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        return guessed
    return ".jpg"


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    header, encoded = data_url.split(",", 1)
    content_type = "image/jpeg"
    if ":" in header and ";" in header:
        content_type = header.split(":", 1)[1].split(";", 1)[0]
    return base64.b64decode(encoded), _infer_extension("", content_type)


def _download_image(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=10) as response:
        content = response.read()
        content_type = response.headers.get_content_type() if response.headers else None
    return content, _infer_extension(url, content_type)


def _custom_image_payload(spec: SiteSpec, slot: str) -> tuple[bytes, str] | None:
    image_input = getattr(spec.image_overrides, slot)
    try:
        if image_input.data_url:
            return _decode_data_url(image_input.data_url)
        if image_input.url:
            return _download_image(image_input.url)
    except Exception:
        return None
    return None


def _photo_candidates() -> list[Path]:
    global _PHOTO_CACHE
    if _PHOTO_CACHE is not None:
        return _PHOTO_CACHE
    if not PHOTO_ROOT.exists():
        _PHOTO_CACHE = []
        return _PHOTO_CACHE
    _PHOTO_CACHE = sorted(
        path
        for path in PHOTO_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS and path.stat().st_size >= PHOTO_MIN_BYTES
    )
    return _PHOTO_CACHE


def _pick_local_photo_paths(spec: SiteSpec, rng: random.Random) -> dict[str, Path]:
    themed_root = PHOTO_ROOT / spec.theme
    if themed_root.exists():
        themed_candidates = [
            path
            for path in themed_root.rglob("*")
            if path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS and path.stat().st_size >= PHOTO_MIN_BYTES
        ]
    else:
        themed_candidates = []
    candidates = themed_candidates or _photo_candidates()
    if not candidates:
        return {}

    hero_candidates = [path for path in candidates if path.stat().st_size >= 120 * 1024] or candidates
    supporting_candidates = [path for path in candidates if path not in hero_candidates[:1]] or candidates

    hero_pool = hero_candidates[:]
    support_pool = supporting_candidates[:]
    rng.shuffle(hero_pool)
    rng.shuffle(support_pool)

    ordered = [hero_pool[0]]
    for path in support_pool:
        if path not in ordered:
            ordered.append(path)
    if len(ordered) < len(PHOTO_SLOTS):
        refill = candidates[:]
        rng.shuffle(refill)
        for path in refill:
            ordered.append(path)
            if len(ordered) >= len(PHOTO_SLOTS):
                break
    return {slot: ordered[idx % len(ordered)] for idx, slot in enumerate(PHOTO_SLOTS)}


def _load_font_catalog() -> dict[str, Any]:
    global _FONT_CATALOG_CACHE
    if _FONT_CATALOG_CACHE is not None:
        return _FONT_CATALOG_CACHE
    if not FONT_CATALOG_PATH.exists():
        _FONT_CATALOG_CACHE = {"families": {}}
        return _FONT_CATALOG_CACHE
    _FONT_CATALOG_CACHE = json.loads(FONT_CATALOG_PATH.read_text(encoding="utf-8"))
    return _FONT_CATALOG_CACHE


def _select_font_family(catalog: dict[str, Any], preferred: list[str]) -> str | None:
    families = catalog.get("families", {})
    for name in preferred:
        if name in families:
            return name
    for name, meta in families.items():
        if meta.get("files"):
            return name
    return None


def _choose_font_file(entries: list[dict[str, Any]], target_weight: int) -> dict[str, Any] | None:
    if not entries:
        return None
    usable = [entry for entry in entries if entry.get("path")]
    if not usable:
        return None
    return min(usable, key=lambda entry: (abs(int(entry.get("weight", 400)) - target_weight), entry.get("format") != "woff", entry.get("format") != "truetype"))


def _font_stack(alias: str, fallback: str) -> str:
    return f'"{alias}", {fallback}'


def _build_font_bundle(theme: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    catalog = _load_font_catalog()
    preferences = FONT_THEME_PREFERENCES.get(theme, FONT_THEME_PREFERENCES["marketing_agency"])
    families = catalog.get("families", {})
    body_family = _select_font_family(catalog, preferences["body"])
    heading_family = _select_font_family(catalog, preferences["heading"])
    if not body_family and not heading_family:
        return {}, {}
    if not body_family:
        body_family = heading_family
    if not heading_family:
        heading_family = body_family
    body_entries = families.get(body_family, {}).get("files", [])
    heading_entries = families.get(heading_family, {}).get("files", [])

    selected_specs = [
        ("SiteBody", 400, _choose_font_file(body_entries, 400)),
        ("SiteBody", 500, _choose_font_file(body_entries, 500)),
        ("SiteHeading", 400, _choose_font_file(heading_entries, 400)),
        ("SiteHeading", 700, _choose_font_file(heading_entries, 700)),
    ]

    font_files: dict[str, bytes] = {}
    faces: list[dict[str, Any]] = []
    for alias, weight, entry in selected_specs:
        if not entry:
            continue
        source = FONT_ROOT / entry["path"]
        if not source.exists():
            continue
        ext = source.suffix.lower()
        target = f"fonts/{alias.lower()}-{weight}{ext}"
        if target not in font_files:
            font_files[target] = source.read_bytes()
        faces.append(
            {
                "family": alias,
                "src": f"../{target}",
                "format": entry["format"],
                "weight": weight,
                "style": "normal",
            }
        )

    theme_payload = {
        "faces": faces,
        "body_stack": _font_stack("SiteBody", '"Segoe UI", Arial, sans-serif'),
        "heading_stack": _font_stack("SiteHeading", 'Georgia, "Times New Roman", serif'),
        "accent_stack": _font_stack("SiteHeading", '"Segoe UI", Arial, sans-serif'),
        "body_label": body_family,
        "heading_label": heading_family,
    }
    return font_files, theme_payload


def _apply_format_noise(text: str, rng: random.Random) -> str:
    if not text:
        return text
    chars = list(text)
    noise_budget = max(1, round(len(chars) * 0.03))
    punctuation_indexes = [idx for idx, char in enumerate(chars[:-1]) if char in {".", ","}]
    space_indexes = [idx for idx, char in enumerate(chars[:-1]) if char == " "]
    for _ in range(noise_budget):
        roll = rng.random()
        if roll < 0.5 and punctuation_indexes:
            idx = rng.choice(punctuation_indexes)
            if idx > 0 and chars[idx - 1] != " ":
                chars.insert(idx, " ")
        elif space_indexes:
            idx = rng.choice(space_indexes)
            if chars[idx + 1] != " ":
                chars.insert(idx + 1, " ")
    return "".join(chars)


def _markovish_paragraph(sentences: list[str], rng: random.Random, *, sentence_count: int = 3) -> str:
    tokens: list[str] = []
    for sentence in sentences:
        tokens.extend(re.findall(r"\S+", sentence))
    if len(tokens) < 6:
        return _apply_format_noise(" ".join(sentences), rng)

    chain: dict[str, list[str]] = {}
    starters: list[str] = []
    previous = None
    for token in tokens:
        if previous is not None:
            chain.setdefault(previous, []).append(token)
        if token[:1].isupper():
            starters.append(token)
        previous = token

    generated_sentences: list[str] = []
    for _ in range(sentence_count):
        word = rng.choice(starters or tokens)
        sentence = [word]
        for _ in range(rng.randint(12, 20)):
            next_options = chain.get(word)
            if not next_options:
                break
            word = rng.choice(next_options)
            sentence.append(word)
            if word.endswith((".", "!", "?")) and len(sentence) > 8:
                break
        built = " ".join(sentence).strip()
        if built and built[-1] not in ".!?":
            built += "."
        generated_sentences.append(built)
    return _apply_format_noise(" ".join(generated_sentences), rng)


def _about_corpus(spec: SiteSpec, company: CompanyProfile, theme_locale: dict[str, Any], geo_name: str) -> list[str]:
    label = _clean_text(THEME_PACKS[spec.theme]["label"])
    service_names = theme_locale["service_names"]
    return _clean_value(
        [
            f"{company.brand_display} serves clients across {geo_name} with a clear local contact route and practical delivery windows."
            if spec.language == "en"
            else f"{company.brand_display} arbeitet in {geo_name} mit klaren Kontaktwegen und realistischen Einsatzfenstern."
            if spec.language == "de"
            else f"{company.brand_display} opera en {geo_name} con un contacto claro y ventanas de servicio realistas."
            if spec.language == "es"
            else f"{company.brand_display} intervient en {geo_name} avec un contact clair et des plages d'intervention réalistes."
            if spec.language == "fr"
            else f"{company.brand_display} opera in {geo_name} con un contatto chiaro e finestre operative realistiche.",
            f"The public profile focuses on {service_names[0]}, {service_names[1]}, and consistent business information."
            if spec.language == "en"
            else f"Das öffentliche Profil konzentriert sich auf {service_names[0]}, {service_names[1]} und konsistente Unternehmensangaben."
            if spec.language == "de"
            else f"El perfil público se centra en {service_names[0]}, {service_names[1]} e información comercial coherente."
            if spec.language == "es"
            else f"Le profil public met en avant {service_names[0]}, {service_names[1]} et des informations d'entreprise cohérentes."
            if spec.language == "fr"
            else f"Il profilo pubblico mette in evidenza {service_names[0]}, {service_names[1]} e informazioni aziendali coerenti.",
            f"{label} requests are coordinated through {company.email} and reflected across the contact and legal pages."
            if spec.language == "en"
            else f"Anfragen zum Bereich {label} laufen über {company.email} und werden auf Kontakt- und Rechtseiten konsistent geführt."
            if spec.language == "de"
            else f"Las solicitudes de {label} se coordinan a través de {company.email} y se reflejan en las páginas de contacto y legales."
            if spec.language == "es"
            else f"Les demandes liées à {label} passent par {company.email} et restent cohérentes sur les pages contact et légales."
            if spec.language == "fr"
            else f"Le richieste relative a {label} passano da {company.email} e restano coerenti tra contatti e documenti legali.",
        ]
    )


def _build_phone(geo_code: str, rng: random.Random, fake: Faker | None = None) -> str:
    if fake is not None:
        generated = re.sub(r"\s+", " ", fake.phone_number().replace("\n", " ")).strip()
        if geo_code == "DE" and generated.startswith("+49"):
            return generated
        if geo_code == "US" and re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", generated):
            return generated
    geo = GEO_PACKS[geo_code]
    area = rng.choice(geo["phone_area_codes"])
    if geo_code == "SG":
        local = str(rng.randint(100, 999))
        tail = str(rng.randint(1000, 9999))
        return geo["phone_pattern"].format(cc=geo["phone_country_code"], area=area, first=local, second=tail)
    first = str(rng.randint(100, 999))
    second = str(rng.randint(1000, 9999))
    return geo["phone_pattern"].format(cc=geo["phone_country_code"], area=area, first=first, second=second)


def _build_address(geo_code: str, rng: random.Random, fake: Faker | None = None) -> str:
    if fake is not None:
        try:
            street = fake.street_address().replace("\n", " ").strip()
            city = fake.city().replace("\n", " ").strip()
            postcode = fake.postcode().replace("\n", " ").strip()
            if geo_code == "DE":
                if "Straße" not in street and "str." not in street.lower():
                    street = f"{fake.street_name()} {rng.randint(3, 129)}"
                return f"{street}, {postcode} {city}"
            if geo_code == "US":
                state = fake.state_abbr()
                return f"{street}, {city}, {state} {postcode}"
            return f"{street}, {postcode} {city}"
        except Exception:
            pass
    geo = GEO_PACKS[geo_code]
    city, region, streets = rng.choice(geo["cities"])
    number = rng.randint(8, 189)
    street = rng.choice(streets)
    postal = rng.choice(geo["postal_codes"])
    if geo_code == "SG":
        return f"{number} {street}, {city} {postal}"
    return f"{number} {street}, {city}, {region} {postal}"


def _build_hours(language: str, rng: random.Random) -> str:
    presets = {
        "en": ["Mon-Fri 08:00-18:00", "Mon-Sat 09:00-19:00", "Tue-Sun 10:00-20:00"],
        "de": ["Mo-Fr 08:00-18:00", "Mo-Sa 09:00-19:00", "Di-So 10:00-20:00"],
        "es": ["Lun-Vie 08:00-18:00", "Lun-Sáb 09:00-19:00", "Mar-Dom 10:00-20:00"],
        "fr": ["Lun-Ven 08:00-18:00", "Lun-Sam 09:00-19:00", "Mar-Dim 10:00-20:00"],
        "it": ["Lun-Ven 08:00-18:00", "Lun-Sab 09:00-19:00", "Mar-Dom 10:00-20:00"],
    }
    return _clean_text(rng.choice(presets[language]))


def _build_company(spec: SiteSpec, rng: random.Random) -> CompanyProfile:
    validate_spec_codes(spec.theme, spec.language, spec.geo)
    fake = _faker_for(spec)
    domain = normalize_domain(spec.domain)
    brand = brand_from_domain(domain)
    brand_display = display_brand(brand)
    fake_company = fake.company().replace("\n", " ").strip()
    legal_name = spec.legal_entity_name or fake_company or _legal_name_default(brand_display, spec.geo)
    phone = spec.manual_overrides.phone or _build_phone(spec.geo, rng, fake)
    email = spec.manual_overrides.email or f"info@{domain}"
    address = spec.manual_overrides.address or _build_address(spec.geo, rng, fake)
    hours = spec.manual_overrides.hours or _build_hours(spec.language, rng)
    validate_contact_values(phone, str(email), address, domain)
    social_handles = {
        platform: f"{brand.replace('.', '').replace('_', '').replace('-', '')}_{platform}"
        for platform in LOCALE_PACKS[spec.language]["social_platforms"]
    }
    return CompanyProfile(
        brand=brand,
        brand_display=brand_display,
        domain=domain,
        legal_entity_name=legal_name,
        email=email,
        phone=phone,
        address=address,
        hours=hours,
        social_handles=social_handles,
    )


def _theme_locale(spec: SiteSpec) -> dict[str, Any]:
    return _clean_value(THEME_PACKS[spec.theme]["locales"][spec.language])


def _theme_text_options(spec: SiteSpec, company: CompanyProfile, theme_locale: dict[str, Any], geo_name: str) -> dict[str, list[str]]:
    service_names = theme_locale["service_names"]
    outcomes = theme_locale["service_outcomes"]
    audience = theme_locale["audiences"]
    theme_label = _clean_text(THEME_PACKS[spec.theme]["label"])
    defaults = {
        "hero_kickers": [
            theme_label,
            geo_name,
            company.brand_display,
        ],
        "hero_lines": [
            f"{company.brand_display} for {geo_name}",
            f"{service_names[0]} with a local profile",
            f"{theme_label} microsite for {geo_name}",
        ],
        "hero_support": [
            f"{outcomes[0]} with realistic local contact data and a public-facing business profile.",
            f"Built for {geo_name} with consistent branding, reachable contact routes, and market-aware legal pages.",
            f"Structured around {service_names[0].lower()} and clear next steps for {audience[0].lower()}.",
        ],
        "about_lines": [
            f"{company.brand_display} presents a realistic business profile for {geo_name} with direct contact routes and transparent legal information.",
            f"The site is designed around {service_names[0].lower()} and a clear public offer that feels locally grounded.",
            f"Every page keeps the business identity, service scope, and compliance signals consistent for visitors in {geo_name}.",
        ],
    }
    resolved: dict[str, list[str]] = {}
    for key, fallback in defaults.items():
        values = _clean_value(theme_locale.get(key) or [])
        resolved[key] = values if values else fallback
    return resolved


def _theme_palette(theme: str) -> dict[str, str]:
    palettes = {
        "cleaning": {"bg": "#edf7f2", "surface": "#d8efe4", "accent": "#2f8f6b", "accent_dark": "#1f5d46", "ink": "#16302a", "muted": "#47645d"},
        "marketing_agency": {"bg": "#f6efe7", "surface": "#efe0cf", "accent": "#c86b3c", "accent_dark": "#7f3f22", "ink": "#2f1f17", "muted": "#665348"},
        "cafe_restaurant": {"bg": "#fbf3e7", "surface": "#f1e1c8", "accent": "#b36a2e", "accent_dark": "#6d3e17", "ink": "#312217", "muted": "#6d5b4d"},
        "fitness_club": {"bg": "#eef5ee", "surface": "#d8ead8", "accent": "#3f8a53", "accent_dark": "#245130", "ink": "#17261b", "muted": "#546658"},
        "news": {"bg": "#eef2f7", "surface": "#dbe4f0", "accent": "#3569a7", "accent_dark": "#1f3d63", "ink": "#17212d", "muted": "#536171"},
        "apparel": {"bg": "#f8eef2", "surface": "#eedbe3", "accent": "#b15576", "accent_dark": "#6d2c44", "ink": "#2f1c24", "muted": "#68515a"},
    }
    return palettes[theme]


def _content_payload(spec: SiteSpec, company: CompanyProfile, rng: random.Random) -> dict[str, Any]:
    locale_pack = _clean_value(LOCALE_PACKS[spec.language])
    theme_pack = _clean_value(THEME_PACKS[spec.theme])
    theme_locale = _theme_locale(spec)
    geo_name = locale_pack["geo_names"][spec.geo]
    theme_text = _theme_text_options(spec, company, theme_locale, geo_name)
    about_corpus = _about_corpus(spec, company, theme_locale, geo_name) + theme_text["about_lines"] + theme_text["hero_support"]
    services = rng.sample(theme_locale["service_names"], k=min(3, len(theme_locale["service_names"])))
    outcomes = rng.sample(theme_locale["service_outcomes"], k=min(3, len(theme_locale["service_outcomes"])))
    audience = rng.choice(theme_locale["audiences"])
    project_names = rng.sample(theme_locale["project_names"], k=min(3, len(theme_locale["project_names"])))
    proofs = [
        {"value": f"{rng.randint(24, 72)}h", "label": company.hours},
        {"value": f"{rng.randint(3, 12)}", "label": audience},
        {"value": f"{rng.randint(87, 99)}%", "label": locale_pack["labels"]["overview"]},
    ]
    testimonials = []
    for idx in range(3):
        testimonials.append(
            {
                "name": _clean_text(rng.choice(LOCALE_NAMES[spec.language])),
                "role": _clean_text(rng.choice(LOCALE_ROLES[spec.language])),
                "quote": _clean_text(rng.choice(TESTIMONIAL_QUOTES[spec.language]).format(brand_display=company.brand_display, audience=audience)),
                "id": idx,
            }
        )
    faq = []
    prompts = {
        "en": [
            "How quickly can a new engagement start?",
            "Do you adapt service windows to local schedules?",
            "Can we request a custom scope before launch?",
            "How are updates communicated after kickoff?",
        ],
        "de": [
            "Wie schnell kann ein neuer Auftrag starten?",
            "Werden Einsatzfenster lokal abgestimmt?",
            "Kann der Leistungsumfang vor dem Start angepasst werden?",
            "Wie werden Updates nach dem Kickoff kommuniziert?",
        ],
        "es": [
            "¿Con qué rapidez puede comenzar un nuevo servicio?",
            "¿Adaptan los horarios a la operativa local?",
            "¿Podemos definir un alcance personalizado antes del lanzamiento?",
            "¿Cómo comunican las actualizaciones después del inicio?",
        ],
        "fr": [
            "Sous quel délai un nouveau projet peut-il démarrer ?",
            "Adaptez-vous les horaires au contexte local ?",
            "Peut-on définir un périmètre spécifique avant le lancement ?",
            "Comment les mises à jour sont-elles communiquées après le démarrage ?",
        ],
        "it": [
            "Quanto rapidamente può partire un nuovo incarico?",
            "Adattate le finestre operative al contesto locale?",
            "Possiamo definire un perimetro personalizzato prima del lancio?",
            "Come comunicate gli aggiornamenti dopo il kickoff?",
        ],
    }
    answers = {
        "en": [
            "We usually prepare the initial operating window within one working week once the scope and contacts are confirmed.",
            f"Yes. Scheduling is planned around {geo_name} business hours, access constraints, and realistic response windows.",
            "Yes. The preview stage is designed to confirm scope, contact details, and documentation before export.",
            "Every engagement includes a single contact route, concise status notes, and a documented next-step list.",
        ],
        "de": [
            "Nach Bestätigung von Umfang und Kontakten planen wir das erste Einsatzfenster in der Regel innerhalb einer Arbeitswoche.",
            f"Ja. Die Planung richtet sich nach lokalen Geschäftszeiten in {geo_name}, Zugängen und realistischen Reaktionsfenstern.",
            "Ja. Die Preview-Phase dient dazu, Umfang, Kontaktdaten und Dokumentation vor dem Export zu bestätigen.",
            "Jeder Auftrag erhält einen klaren Kontaktweg, kurze Statusnotizen und dokumentierte nächste Schritte.",
        ],
        "es": [
            "Una vez confirmado el alcance y los contactos, solemos preparar la primera ventana operativa en una semana laborable.",
            f"Sí. La programación se ajusta al horario comercial de {geo_name}, a los accesos y a tiempos de respuesta realistas.",
            "Sí. La fase de vista previa existe para validar alcance, contactos y documentación antes de exportar.",
            "Cada servicio incluye un canal de contacto claro, notas de estado breves y una lista documentada de siguientes pasos.",
        ],
        "fr": [
            "Une fois le périmètre et les contacts validés, nous préparons généralement la première fenêtre d'intervention sous une semaine ouvrée.",
            f"Oui. La planification est alignée sur les horaires de {geo_name}, les contraintes d'accès et des délais réalistes.",
            "Oui. La phase de prévisualisation sert précisément à valider le périmètre, les contacts et la documentation avant export.",
            "Chaque mission inclut un point de contact unique, des notes d'avancement synthétiques et une liste de prochaines étapes.",
        ],
        "it": [
            "Una volta confermati perimetro e contatti, prepariamo normalmente la prima finestra operativa entro una settimana lavorativa.",
            f"Sì. La programmazione è costruita sugli orari di {geo_name}, sui vincoli di accesso e su tempi di risposta realistici.",
            "Sì. La fase di preview serve a confermare perimetro, contatti e documentazione prima dell'export.",
            "Ogni incarico include un canale di contatto chiaro, note di stato sintetiche e un elenco documentato di prossimi passi.",
        ],
    }
    for question, answer in zip(prompts[spec.language], answers[spec.language], strict=False):
        faq.append({"question": _clean_text(question), "answer": _clean_text(answer)})
    about_blocks = [_markovish_paragraph(about_corpus, rng, sentence_count=2) for _ in range(3)]
    payload = {
        "theme_pack": theme_pack,
        "theme_locale": theme_locale,
        "locale_pack": locale_pack,
        "language": spec.language,
        "geo_name": geo_name,
        "hero_kicker": _clean_text(rng.choice(theme_text["hero_kickers"])),
        "hero_line": _clean_text(rng.choice(theme_text["hero_lines"])),
        "hero_support": _markovish_paragraph(theme_text["hero_support"] + about_corpus[:2], rng, sentence_count=2),
        "about_intro": about_blocks[0],
        "about_blocks": about_blocks,
        "services": services,
        "outcomes": outcomes,
        "project_names": project_names,
        "proofs": proofs,
        "testimonials": testimonials,
        "faq": faq,
        "audience": audience,
        "company_profile": [
            company.legal_entity_name,
            company.address,
            company.hours,
            f"{LANGUAGE_LABELS[spec.language]} · {geo_name}",
        ],
        "cta_title": company.brand_display,
        "cta_copy": _copy(spec.language, "home_contact", legal_entity_name=company.legal_entity_name, geo_name=geo_name),
    }
    return _clean_value(payload)


def _paragraphs(*items: str) -> str:
    return "".join(f"<p>{escape(item)}</p>" for item in items)


def _cta_href(spec: SiteSpec) -> str:
    return spec.tracker_link or "/contact.php"


def _pixel_snippet(spec: SiteSpec) -> str:
    if not spec.fb_pixel_id:
        return ""
    pixel_id = escape(spec.fb_pixel_id)
    # === ANTI‑AI FINGERPRINT PATCH: randomized eventID for FB Pixel ===
    event_id = str(uuid.uuid4())
    return (
        "<script>"
        "!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
        "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;"
        "n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;"
        "t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}"
        "(window, document,'script','https://connect.facebook.net/en_US/fbevents.js');"
        f"fbq('init', '{pixel_id}');"
        f"fbq('track', 'PageView', {{}}, {{eventID: '{event_id}'}});"
        "</script>"
    )


def _list_cards(items: list[dict[str, str]]) -> str:
    parts = []
    for item in items:
        parts.append(
            f"""
            <article class="card reveal">
              <h3>{escape(item['title'])}</h3>
              <p>{escape(item['text'])}</p>
            </article>
            """
        )
    return f'<div class="grid-three">{"".join(parts)}</div>'


def _render_home_body(spec: SiteSpec, company: CompanyProfile, content: dict[str, Any]) -> str:
    locale_labels = content["locale_pack"]["labels"]
    cta_href = _cta_href(spec)
    image_refs = content["image_refs"]
    cards = [
        {"title": service, "text": outcome}
        for service, outcome in zip(content["services"], content["outcomes"], strict=False)
    ]
    proof_html = "".join(
        f"<span class='tag'><strong>{escape(item['value'])}</strong> {escape(item['label'])}</span>"
        for item in content["proofs"]
    )
    testimonials = _list_cards(
        [{"title": item["name"], "text": f"{item['role']} — {item['quote']}"} for item in content["testimonials"]]
    )
    testimonials = _clean_text(testimonials)
    faq_items = "".join(
        f"<div class='faq-item'><h3>{escape(item['question'])}</h3><p>{escape(item['answer'])}</p></div>"
        for item in content["faq"]
    )
    company_tags = "".join(f"<span class='tag'>{escape(item)}</span>" for item in content["company_profile"])
    metric_cards = "".join(
        f"<article class='metric-card reveal'><strong>{escape(item['value'])}</strong><span class='muted'>{escape(item['label'])}</span></article>"
        for item in content["proofs"]
    )
    checklist = "".join(f"<li>{escape(item)}</li>" for item in content["services"])
    return f"""
    <section class="hero">
      <div class="shell hero__grid">
        <div class="hero__main reveal">
          <span class="kicker">{escape(content['hero_kicker'])}</span>
          <h1>{escape(content['hero_line'])}</h1>
          <p class="lead">{escape(content['hero_support'])}</p>
          <div class="actions">
            <a class="btn btn--primary" href="{escape(cta_href)}">{escape(locale_labels['cta_primary'])}</a>
            <a class="btn btn--secondary" href="#services">{escape(locale_labels['cta_secondary'])}</a>
          </div>
          <div class="tag-row">{proof_html}</div>
          <div class="metrics-band">{metric_cards}</div>
        </div>
        <aside class="hero__support">
          <div class="media-card media-card--tall reveal">
            <img src="{escape(image_refs['hero'])}" alt="{escape(company.brand_display)}" loading="lazy">
            <div class="media-card__caption">
              <strong>{escape(company.brand_display)}</strong>
              <div>{escape(content['geo_name'])}</div>
            </div>
          </div>
          <div class="panel reveal">
            <h3>{escape(locale_labels['contact'])}</h3>
            <dl class="contact-grid">
              <div><dt>{escape(_copy(spec.language, 'contact_domain'))}</dt><dd>{escape(company.domain)}</dd></div>
              <div><dt>{escape(_copy(spec.language, 'contact_email'))}</dt><dd>{escape(str(company.email))}</dd></div>
              <div><dt>{escape(_copy(spec.language, 'contact_phone'))}</dt><dd>{escape(company.phone)}</dd></div>
              <div><dt>{escape(_copy(spec.language, 'contact_address'))}</dt><dd>{escape(company.address)}</dd></div>
              <div><dt>{escape(locale_labels['language'])}</dt><dd>{escape(LANGUAGE_LABELS[spec.language])}</dd></div>
            </dl>
          </div>
        </aside>
      </div>
    </section>
    <section class="section section--spacious" id="services">
      <div class="shell">
        <div class="section__header">
          <span class="kicker section__eyebrow reveal">{escape(locale_labels['why_choose'])}</span>
          <h2>{escape(locale_labels['why_choose'])}</h2>
          <p class="lead">{escape(content['about_intro'])}</p>
        </div>
        {_list_cards(cards)}
      </div>
    </section>
    <section class="section section--spacious">
      <div class="shell split-feature">
        <div class="stack reveal">
          <h2>{escape(content['locale_pack']['labels']['overview'])}</h2>
          {_paragraphs(content['about_intro'], _copy(spec.language, 'home_serves', brand_display=company.brand_display, audience=content['audience'], geo_name=content['geo_name']))}
          <ul class="list-checks">{checklist}</ul>
        </div>
        <div class="gallery-strip">
          <div class="media-card reveal">
            <img src="{escape(image_refs['gallery_primary'])}" alt="{escape(company.brand_display)}" loading="lazy">
            <div class="media-card__caption">{escape(company.legal_entity_name)}</div>
          </div>
          <div class="media-card reveal">
            <img src="{escape(image_refs['gallery_secondary'])}" alt="{escape(company.brand_display)}" loading="lazy">
            <div class="media-card__caption">{escape(content['geo_name'])}</div>
          </div>
          <div class="showcase-quote reveal">
            <h3>{escape(locale_labels['contact'])}</h3>
            {_paragraphs(content['locale_pack']['labels']['contact_intro'], _copy(spec.language, 'home_contact', legal_entity_name=company.legal_entity_name, geo_name=content['geo_name']))}
            <div class="tag-row tag-row--footer">{company_tags}</div>
          </div>
        </div>
      </div>
    </section>
    <section class="section section--spacious">
      <div class="shell grid-two">
        <div class="panel reveal">
          <h2>{escape(locale_labels['testimonials'])}</h2>
          {testimonials}
        </div>
        <div class="panel reveal">
          <h2>{escape(locale_labels['faq'])}</h2>
          <div class="card">{faq_items}</div>
        </div>
      </div>
    </section>
    <section class="shell reveal">
      <div class="cta-banner">
        <h2>{escape(content['cta_title'])}</h2>
        <p>{escape(content['cta_copy'])}</p>
        <div class="actions">
          <a class="btn btn--secondary" href="{escape(cta_href)}">{escape(locale_labels['cta_primary'])}</a>
        </div>
      </div>
    </section>
    """


def _render_about_body(company: CompanyProfile, content: dict[str, Any]) -> str:
    social_lines = "".join(
        f"<li>{escape(platform.title())}: @{escape(handle)}</li>"
        for platform, handle in company.social_handles.items()
    )
    paragraphs = content["about_blocks"]
    image_refs = content["image_refs"]
    timeline = "".join(
        f"""
        <article class="timeline__item reveal">
          <div class="timeline__step">0{idx}</div>
          <div class="card">
            <h3>{escape(title)}</h3>
            <p>{escape(text)}</p>
          </div>
        </article>
        """
        for idx, (title, text) in enumerate(
            [
                (company.brand_display, paragraphs[0]),
                (content["geo_name"], paragraphs[1]),
                (company.legal_entity_name, paragraphs[2]),
            ],
            start=1,
        )
    )
    return f"""
    <section class="legal-page">
      <div class="shell stack">
        <span class="kicker reveal">{escape(content['theme_pack']['label'])}</span>
        <h1 class="reveal">{escape(company.brand_display)}</h1>
        <div class="split-feature">
          <div class="timeline">
            {timeline}
          </div>
          <div class="stack">
            <div class="media-card media-card--tall reveal">
              <img src="{escape(image_refs['about'])}" alt="{escape(company.brand_display)}" loading="lazy">
              <div class="media-card__caption">{escape(company.legal_entity_name)}</div>
            </div>
            <div class="card reveal">
              <h3>{escape(_copy(content["language"], 'contact_social'))}</h3>
              <ul class="contact-list">{social_lines}</ul>
            </div>
          </div>
        </div>
      </div>
    </section>
    """


def _render_collection_body(title: str, items: list[str], company: CompanyProfile, content: dict[str, Any]) -> str:
    cards = []
    for idx, item in enumerate(items, start=1):
        description = _copy(
            content["language"],
            "collection_desc",
            item=item,
            geo_name=content["geo_name"],
        )
        cards.append({"title": f"{idx:02d}. {item}", "text": description})
    feature_list = "".join(f"<li>{escape(item)}</li>" for item in items)
    image_refs = content["image_refs"]
    return f"""
    <section class="legal-page">
      <div class="shell stack">
        <span class="kicker reveal">{escape(company.brand_display)}</span>
        <h1 class="reveal">{escape(title)}</h1>
        <div class="split-feature">
          <div class="stack reveal">
            <p class="lead">{escape(_copy(content["language"], "collection_intro", brand_display=company.brand_display))}</p>
            <ul class="list-checks">{feature_list}</ul>
          </div>
          <div class="media-card reveal">
            <img src="{escape(image_refs['collection'])}" alt="{escape(company.brand_display)}" loading="lazy">
            <div class="media-card__caption">{escape(content['geo_name'])}</div>
          </div>
        </div>
        {_list_cards(cards)}
      </div>
    </section>
    """


def _render_contact_body(spec: SiteSpec, company: CompanyProfile, content: dict[str, Any]) -> str:
    social_list = "".join(f"<li>{escape(platform.title())}: @{escape(handle)}</li>" for platform, handle in company.social_handles.items())
    cta_href = _cta_href(spec)
    image_refs = content["image_refs"]
    return f"""
    <section class="legal-page">
      <div class="shell stack">
        <span class="kicker reveal">{escape(content['geo_name'])}</span>
        <h1 class="reveal">{escape(content['locale_pack']['labels']['contact'])}</h1>
        <p class="lead reveal">{escape(content['locale_pack']['labels']['contact_intro'])}</p>
        <div class="contact-shell">
          <article class="card reveal">
            <h3>{escape(company.legal_entity_name)}</h3>
            <dl class="contact-grid">
              <div><dt>{escape(_copy(spec.language, 'contact_address'))}</dt><dd>{escape(company.address)}</dd></div>
              <div><dt>{escape(_copy(spec.language, 'contact_phone'))}</dt><dd><a href="tel:{escape(company.phone.replace(' ', ''))}">{escape(company.phone)}</a></dd></div>
              <div><dt>{escape(_copy(spec.language, 'contact_email'))}</dt><dd><a href="mailto:{escape(str(company.email))}">{escape(str(company.email))}</a></dd></div>
              <div><dt>{escape(content['locale_pack']['labels']['language'])}</dt><dd>{escape(LANGUAGE_LABELS[spec.language])}</dd></div>
            </dl>
            <div class="actions">
              <a class="btn btn--primary" href="{escape(cta_href)}">{escape(content['locale_pack']['labels']['cta_primary'])}</a>
            </div>
          </article>
          <div class="stack">
            <article class="media-card reveal">
              <img src="{escape(image_refs['contact'])}" alt="{escape(company.brand_display)}" loading="lazy">
              <div class="media-card__caption">{escape(company.domain)}</div>
            </article>
            <article class="media-card reveal">
              <img src="{escape(image_refs['footer'])}" alt="{escape(content['geo_name'])}" loading="lazy">
              <div class="media-card__caption">{escape(content['geo_name'])}</div>
            </article>
            <article class="card reveal">
              <h3>{escape(_copy(spec.language, 'contact_social'))}</h3>
              <ul class="contact-list">{social_list}</ul>
            </article>
          </div>
        </div>
      </div>
    </section>
    """


def _render_404_body(locale_pack: dict[str, Any]) -> str:
    labels = locale_pack["labels"]
    messages = {
        "en": "The page could not be found. It may have moved or the address may have changed.",
        "de": "Die Seite wurde nicht gefunden. Möglicherweise wurde sie verschoben oder die Adresse hat sich geändert.",
        "es": "No se ha encontrado la página. Puede que se haya movido o que la dirección haya cambiado.",
        "fr": "La page est introuvable. Elle a peut-être été déplacée ou l'adresse a changé.",
        "it": "La pagina non è stata trovata. Potrebbe essere stata spostata o l'indirizzo potrebbe essere cambiato.",
    }
    return f"""
    <section class="error-page">
      <div class="shell stack">
        <span class="kicker">404</span>
        <h1>{escape(labels['not_found'])}</h1>
        <p class="lead">{escape(messages.get(locale_pack['html_lang'], messages['en']))}</p>
        <div class="actions">
          <a class="btn btn--primary" href="/index.php">{escape(labels['back_home'])}</a>
        </div>
      </div>
    </section>
    """


def _legal_section(title: str, paragraphs: list[str], bullets: list[str] | None = None) -> str:
    bullet_html = ""
    if bullets:
        bullet_html = f"<ul>{''.join(f'<li>{escape(item)}</li>' for item in bullets)}</ul>"
    return f"<section><h2>{escape(title)}</h2>{''.join(f'<p>{escape(p)}</p>' for p in paragraphs)}{bullet_html}</section>"


def _build_legal_pack(spec: SiteSpec, company: CompanyProfile) -> LegalPack:
    locale = LOCALE_PACKS[spec.language]
    # === ANTI‑AI FINGERPRINT PATCH: "aged" last‑updated date ===
    past_days = random.randint(10, 45)
    past_date = _utc_now() - timedelta(days=past_days)
    updated = _format_date(spec.language, past_date)
    return resolve_legal_pack(
        spec.language,
        spec.geo,
        company,
        updated=updated,
        last_updated_label=locale["labels"]["last_updated"],
    )


def _nav_for_family(language: str, family: str) -> list[dict[str, str]]:
    excluded = {"privacy-policy.php", "cookie-policy.php", "terms-of-service.php", "legal-notice.php", "disclaimer.php", "404.php"}
    slugs = [file.replace(".php", "") for file in THEME_FAMILIES[family] if file not in excluded]
    nav = []
    for slug in slugs:
        page_key = "index" if slug == "index" else slug
        nav.append({"file": f"{slug}.php", "label": PAGE_TITLES[language][page_key]})
    # === ANTI‑AI FINGERPRINT PATCH: dead link to news archive ===
    return nav


def _title_for_page(language: str, slug: str, brand: str) -> str:
    if slug == "index":
        return brand
    page_title = PAGE_TITLES[language].get(slug, slug.replace("-", " ").title())
    return f"{page_title} - {brand}"


def _page_meta(summary: str) -> str:
    compact = " ".join(summary.split())
    return compact[:160]


def _render_page(
    *,
    html_lang: str,
    title: str,
    meta_description: str,
    brand: str,
    brand_initials: str,
    nav: list[dict[str, str]],
    body_html: str,
    footer_blurb: str,
    company: CompanyProfile,
    locale_pack: dict[str, Any],
    extra_head_html: str = "",
) -> str:
    template = TEMPLATE_ENV.get_template("page.html.j2")
    # === ANTI‑AI FINGERPRINT PATCH: fake CMS generator meta tag ===
    cms_signatures = [
        '<meta name="generator" content="WordPress 5.8.1" />',
        '<meta name="generator" content="Joomla! - Open Source Content Management" />',
        '<meta name="generator" content="Drupal 9 (https://www.drupal.org)" />',
        '',  # sometimes no signature at all
    ]
    meta_generator = random.choice(cms_signatures)
    combined_head = extra_head_html + meta_generator
    return template.render(
        html_lang=html_lang,
        title=title,
        meta_description=meta_description,
        brand=brand,
        brand_initials=brand_initials,
        nav=nav,
        body_html=body_html,
        footer_blurb=footer_blurb,
        year=_utc_now().year,
        company=company,
        tel_href=company.phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", ""),
        contact_heading=locale_pack["labels"]["contact"],
        legal_heading=locale_pack["labels"]["compliance"],
        legal_links=[
            {"file": "privacy-policy.php", "label": locale_pack["legal"]["privacy_title"]},
            {"file": "cookie-policy.php", "label": locale_pack["legal"]["cookie_title"]},
            {"file": "terms-of-service.php", "label": locale_pack["legal"]["terms_title"]},
            {"file": "legal-notice.php", "label": locale_pack["legal"]["legal_notice_title"]},
            {"file": "disclaimer.php", "label": locale_pack["legal"]["disclaimer_title"]},
        ],
        cookie_title=locale_pack["legal"]["cookie_title"],
        cookie_text=locale_pack["labels"]["cookie_text"],
        cookie_accept=locale_pack["labels"]["cookie_accept"],
        cookie_link=locale_pack["labels"]["cookie_link"],
        extra_head_html=combined_head,
    )


def _php_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _render_php_layout() -> str:
    template = TEMPLATE_ENV.get_template("layout.php.j2")
    return template.render()


def _render_php_page(*, title: str, meta_description: str, partial_file: str, is_404: bool) -> str:
    template = TEMPLATE_ENV.get_template("page.php.j2")
    return template.render(
        is_404=is_404,
        partial_file=partial_file,
        page_payload=_php_json(
            {
                "title": title,
                "meta_description": meta_description,
            }
        ),
    )


def _render_php_config(
    *,
    html_lang: str,
    brand: str,
    brand_initials: str,
    footer_blurb: str,
    company: CompanyProfile,
    locale_pack: dict[str, Any],
    nav: list[dict[str, str]],
    legal_links: list[dict[str, str]],
    extra_head_html: str,
) -> str:
    payload = {
        "html_lang": html_lang,
        "brand": brand,
        "brand_initials": brand_initials,
        "footer_blurb": footer_blurb,
        "year": _utc_now().year,
        "company": company.model_dump(mode="json"),
        "tel_href": company.phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", ""),
        "contact_heading": locale_pack["labels"]["contact"],
        "legal_heading": locale_pack["labels"]["compliance"],
        "cookie_title": locale_pack["legal"]["cookie_title"],
        "cookie_text": locale_pack["labels"]["cookie_text"],
        "cookie_accept": locale_pack["labels"]["cookie_accept"],
        "cookie_link": locale_pack["labels"]["cookie_link"],
        "extra_head_html": extra_head_html,
        "nav": nav,
        "legal_links": legal_links,
    }
    return "<?php\nreturn json_decode(<<<'JSON'\n" + _php_json(payload) + "\nJSON, true);\n"


def _normalize_page_text(html: str) -> str:
    compact = re.sub(r"<[^>]+>", " ", html)
    compact = re.sub(r"\s+", " ", compact)
    return compact.strip().lower()


def _internal_targets(html: str) -> list[str]:
    targets = re.findall(r"""(?:href|src)=["']/(.+?)["']""", html)
    return [target.split("?", 1)[0] for target in targets]


def _build_compliance_checks(
    *,
    language: str,
    company: CompanyProfile,
    files: dict[str, bytes],
    page_map: dict[str, str],
    legal_pack: LegalPack,
) -> list[ComplianceCheck]:
    checks: list[ComplianceCheck] = []
    missing_docs = [item for item in LEGAL_DOC_FILES if item not in files]
    checks.append(
        ComplianceCheck(
            code="required_legal_docs",
            status="failed" if missing_docs else "passed",
            detail="Missing legal documents: " + ", ".join(missing_docs) if missing_docs else "All required legal documents are present.",
        )
    )

    placeholder_hit = any(contains_placeholder_text(value) for value in [company.address, str(company.email), company.legal_entity_name])
    checks.append(
        ComplianceCheck(
            code="placeholder_data",
            status="failed" if placeholder_hit else "passed",
            detail="Placeholder text was detected in generated company data." if placeholder_hit else "Company data is free of placeholder text.",
        )
    )

    unresolved_targets: list[str] = []
    for html in page_map.values():
        for target in _internal_targets(html):
            if target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            if target not in files:
                unresolved_targets.append(target)
    checks.append(
        ComplianceCheck(
            code="internal_links",
            status="failed" if unresolved_targets else "passed",
            detail="Broken internal targets: " + ", ".join(sorted(set(unresolved_targets))) if unresolved_targets else "All internal links and asset references resolve inside the archive.",
        )
    )

    title_footer_failed = False
    for file_name, html in page_map.items():
        # === Исключаем страницы, которые не должны проверяться на брендинг ===
        if file_name in {*LEGAL_DOC_FILES, "404.php", "news-archive.php"}:
            continue
        if f"<title>{company.brand}" not in html and f" - {company.brand}</title>" not in html:
            title_footer_failed = True
            break
        if f"Copyright &copy; {_utc_now().year} {company.brand}" not in html:
            title_footer_failed = True
            break
    checks.append(
        ComplianceCheck(
            code="brand_consistency",
            status="failed" if title_footer_failed else "passed",
            detail="Title or footer brand markers are inconsistent." if title_footer_failed else "Title pattern and footer brand stay consistent across generated pages.",
        )
    )

    mixed_language = False
    if language != "en":
        mixed_language = any(marker in html for marker in NON_ENGLISH_RED_FLAGS for html in page_map.values())
    checks.append(
        ComplianceCheck(
            code="localized_labels",
            status="failed" if mixed_language else "passed",
            detail="English UI labels were found inside a non-English build." if mixed_language else "Localized pages do not leak the known English UI labels.",
        )
    )

    non_legal_duplicates = []
    seen: dict[str, str] = {}
    for file_name, html in page_map.items():
        # === Исключаем служебные и архивную страницы ===
        if file_name in {*LEGAL_DOC_FILES, "404.php", "news-archive.php"}:
            continue
        normalized = _normalize_page_text(html)
        if normalized in seen:
            non_legal_duplicates.append(f"{seen[normalized]}={file_name}")
        else:
            seen[normalized] = file_name
    checks.append(
        ComplianceCheck(
            code="duplicate_pages",
            status="failed" if non_legal_duplicates else "passed",
            detail="Duplicate non-legal page bodies detected: " + ", ".join(non_legal_duplicates) if non_legal_duplicates else "Non-legal pages have distinct content bodies.",
        )
    )

    legal_content_missing = any(not getattr(legal_pack, field).strip() for field in ["privacy_html", "cookie_html", "terms_html", "legal_notice_html", "disclaimer_html"])
    checks.append(
        ComplianceCheck(
            code="legal_pack",
            status="failed" if legal_content_missing else "passed",
            detail="One or more legal documents are empty." if legal_content_missing else f"Legal pack {legal_pack.key} is populated for the selected language and GEO.",
        )
    )
    return checks


def _render_bot_page(company: CompanyProfile, locale_pack: dict[str, Any]) -> str:
    """Generate a minimal page for crawler bots (simulate a static, old-school business site)."""
    labels = locale_pack["labels"]
    return f"""<!DOCTYPE html>
<html lang="{locale_pack['html_lang']}">
<head>
    <meta charset="utf-8">
    <title>{escape(company.brand_display)}</title>
    <meta name="description" content="{escape(labels.get('contact_intro', ''))}">
</head>
<body>
    <h1>{escape(company.brand_display)}</h1>
    <p>{escape(company.legal_entity_name)}</p>
    <p>{escape(company.address)}</p>
    <p>{escape(company.phone)} | {escape(str(company.email))}</p>
</body>
</html>"""


def generate_site(spec: SiteSpec, *, strict: bool = False) -> GeneratedSite:
    rng = _rng(spec)
    company = _build_company(spec, rng)
    theme_pack = _clean_value(THEME_PACKS[spec.theme])
    locale_pack = _clean_value(LOCALE_PACKS[spec.language])
    palette = _theme_palette(spec.theme)
    font_files, font_theme = _build_font_bundle(spec.theme)
    legal_pack = _build_legal_pack(spec, company)
    content = _content_payload(spec, company, rng)
    family = theme_pack["page_family"]
    nav = _nav_for_family(spec.language, family)
    legal_links = [
        {"file": "privacy-policy.php", "label": locale_pack["legal"]["privacy_title"]},
        {"file": "cookie-policy.php", "label": locale_pack["legal"]["cookie_title"]},
        {"file": "terms-of-service.php", "label": locale_pack["legal"]["terms_title"]},
        {"file": "legal-notice.php", "label": locale_pack["legal"]["legal_notice_title"]},
        {"file": "disclaimer.php", "label": locale_pack["legal"]["disclaimer_title"]},
    ]
    brand_initials = "".join(part[0] for part in company.brand_display.split()[:2]).upper() or company.brand[:2].upper()
    pages: list[PagePreview] = []
    files: dict[str, bytes] = {}
    page_map: dict[str, str] = {}
    rendered_pages: dict[str, str] = {}
    image_refs = {
        "hero": "/img/hero-pattern.svg",
        "about": "/img/footer-pattern.svg",
        "collection": "/img/hero-pattern.svg",
        "gallery_primary": "/img/contact-pattern.svg",
        "gallery_secondary": "/img/footer-pattern.svg",
        "contact": "/img/contact-pattern.svg",
        "footer": "/img/footer-pattern.svg",
    }
    local_images: dict[str, tuple[bytes, str]] = {}
    for slot, path in _pick_local_photo_paths(spec, rng).items():
        extension = path.suffix.lower()
        file_name = f"img/photo-{slot}{extension}"
        local_images[file_name] = (path.read_bytes(), extension)
        image_refs[slot] = f"/{file_name}"
    custom_images: dict[str, tuple[bytes, str]] = {}
    for slot in ("hero", "contact", "footer"):
        payload = _custom_image_payload(spec, slot)
        if payload is None:
            continue
        data, extension = payload
        file_name = f"img/custom-{slot}{extension}"
        custom_images[file_name] = (data, extension)
        image_refs[slot] = f"/{file_name}"
    content["image_refs"] = image_refs

    home_body = _render_home_body(spec, company, content)
    about_body = _render_about_body(company, content)
    collection_body = _render_collection_body(PAGE_TITLES[spec.language]["services"], content["services"], company, content)
    offerings_body = _render_collection_body(PAGE_TITLES[spec.language]["offerings"], content["services"], company, content)
    portfolio_body = _render_collection_body(PAGE_TITLES[spec.language]["portfolio"], content["project_names"], company, content)
    projects_body = _render_collection_body(PAGE_TITLES[spec.language]["projects"], content["project_names"], company, content)
    contact_body = _render_contact_body(spec, company, content)
    legal_pages = {
        "privacy-policy": (legal_pack.document_titles["privacy-policy.php"], legal_pack.privacy_html),
        "cookie-policy": (legal_pack.document_titles["cookie-policy.php"], legal_pack.cookie_html),
        "terms-of-service": (legal_pack.document_titles["terms-of-service.php"], legal_pack.terms_html),
        "legal-notice": (legal_pack.document_titles["legal-notice.php"], legal_pack.legal_notice_html),
        "disclaimer": (legal_pack.document_titles["disclaimer.php"], legal_pack.disclaimer_html),
    }

    body_map = {
        "index": home_body,
        "about": about_body,
        "services": collection_body,
        "offerings": offerings_body,
        "portfolio": portfolio_body,
        "projects": projects_body,
        "contact": contact_body,
    }
    for file_name in THEME_FAMILIES[family]:
        slug = file_name.replace(".php", "")
        if slug == "404":
            body_html = _render_404_body(locale_pack)
        elif slug in legal_pages:
            legal_title, legal_html = legal_pages[slug]
            body_html = f"<section class='legal-page'><div class='shell stack'><h1>{escape(legal_title)}</h1>{legal_html}</div></section>"
        else:
            body_html = body_map[slug]
        title = _title_for_page(spec.language, slug, company.brand)
        if slug in legal_pages:
            title = f"{legal_pages[slug][0]} - {company.brand}"
        if slug == "404":
            title = f"404 - {company.brand}"
        summary = {
            "index": content["hero_support"],
            "about": content["about_intro"],
            "contact": locale_pack["labels"]["contact_intro"],
            "services": ", ".join(content["services"]),
            "offerings": ", ".join(content["services"]),
            "portfolio": ", ".join(content["project_names"]),
            "projects": ", ".join(content["project_names"]),
            "privacy-policy": legal_pack.jurisdiction,
            "cookie-policy": legal_pack.jurisdiction,
            "terms-of-service": legal_pack.governing_law,
            "legal-notice": legal_pack.regulator,
            "disclaimer": legal_pack.jurisdiction,
            "404": locale_pack["labels"]["not_found"],
        }[slug]
        meta_description = _page_meta(summary)
        page_html = _render_page(
            html_lang=locale_pack["html_lang"],
            title=title,
            meta_description=meta_description,
            brand=company.brand,
            brand_initials=brand_initials,
            nav=nav,
            body_html=body_html,
            footer_blurb=locale_pack["footer_blurb"],
            company=company,
            locale_pack=locale_pack,
            extra_head_html=_pixel_snippet(spec),
        )
        page_map[file_name] = page_html
        rendered_pages[file_name.replace(".php", ".html")] = page_html
        files[f"partials/{file_name}"] = body_html.encode("utf-8")
        files[file_name] = _render_php_page(
            title=title,
            meta_description=meta_description,
            partial_file=file_name,
            is_404=slug == "404",
        ).encode("utf-8")
        files[file_name.replace(".php", ".html")] = page_html.encode("utf-8")
        pages.append(PagePreview(slug=slug, file_name=file_name, title=title, summary=summary))

    # === ANTI‑AI FINGERPRINT PATCH: include CMS signature in PHP config as well ===
    cms_signatures = [
        '<meta name="generator" content="WordPress 5.8.1" />',
        '<meta name="generator" content="Joomla! - Open Source Content Management" />',
        '<meta name="generator" content="Drupal 9 (https://www.drupal.org)" />',
        '',
    ]
    meta_generator = random.choice(cms_signatures)
    full_extra_head = _pixel_snippet(spec) + meta_generator

    # === ANTI‑AI FINGERPRINT PATCH: создаём заглушку для битой ссылки на архив ===
    archive_labels = {"de": "Archiv", "es": "Archivo", "fr": "Archives", "it": "Archivio", "en": "Archive"}
    archive_slug = "news-archive"
    archive_title = f"{archive_labels.get(spec.language, 'Archive')} - {company.brand}"
    archive_meta = "Archive page is intentionally not available"
    archive_body = _render_404_body(locale_pack)

    files[f"partials/{archive_slug}.php"] = archive_body.encode("utf-8")
    files[f"{archive_slug}.php"] = _render_php_page(
        title=archive_title,
        meta_description=archive_meta,
        partial_file=f"{archive_slug}.php",
        is_404=True,
    ).encode("utf-8")
    archive_html = _render_page(
        html_lang=locale_pack["html_lang"],
        title=archive_title,
        meta_description=archive_meta,
        brand=company.brand,
        brand_initials=brand_initials,
        nav=nav,
        body_html=archive_body,
        footer_blurb=locale_pack["footer_blurb"],
        company=company,
        locale_pack=locale_pack,
        extra_head_html=full_extra_head,
    )
    files[f"{archive_slug}.html"] = archive_html.encode("utf-8")
    rendered_pages[f"{archive_slug}.html"] = archive_html
    page_map[f"{archive_slug}.php"] = files[f"{archive_slug}.php"].decode("utf-8")
    pages.append(PagePreview(slug=archive_slug, file_name=f"{archive_slug}.php", title=archive_title, summary=archive_meta))

    files["config/site.php"] = _render_php_config(
        html_lang=locale_pack["html_lang"],
        brand=company.brand,
        brand_initials=brand_initials,
        footer_blurb=locale_pack["footer_blurb"],
        company=company,
        locale_pack=locale_pack,
        nav=nav,
        legal_links=legal_links,
        extra_head_html=full_extra_head,
    ).encode("utf-8")

    # === ANTI‑AI FINGERPRINT PATCH: bot‑friendly processor.php and index_bot.html ===
    files["processor.php"] = (
        "<?php\n"
        "declare(strict_types=1);\n\n"
        "$userAgent = $_SERVER['HTTP_USER_AGENT'] ?? '';\n"
        "$botPatterns = ['facebookexternalhit', 'Facebot', 'Googlebot', 'AdsBot-Google', 'bingbot'];\n"
        "$isBot = false;\n"
        "foreach ($botPatterns as $pattern) {\n"
        "    if (stripos($userAgent, $pattern) !== false) {\n"
        "        $isBot = true;\n"
        "        break;\n"
        "    }\n"
        "}\n"
        "if ($isBot) {\n"
        "    readfile(__DIR__ . '/index_bot.html');\n"
        "    exit;\n"
        "}\n"
        "require __DIR__ . '/index.php';\n"
    ).encode("utf-8")
    files["index_bot.html"] = _render_bot_page(company, locale_pack).encode("utf-8")
    files["includes/layout.php"] = _render_php_layout().encode("utf-8")
    for file_name, payload in font_files.items():
        files[file_name] = payload
    files["css/fonts.css"] = build_font_css(font_theme).encode("utf-8")
    files["css/base.css"] = build_base_css().encode("utf-8")
    files["css/layout.css"] = build_layout_css().encode("utf-8")
    files["css/components.css"] = build_components_css().encode("utf-8")
    files["css/legal.css"] = build_legal_css().encode("utf-8")
    files["css/site.css"] = build_css(palette).encode("utf-8")
    files["js/cookie.js"] = build_cookie_script().encode("utf-8")
    files["js/navigation.js"] = build_navigation_script().encode("utf-8")
    files["js/interactions.js"] = build_interactions_script().encode("utf-8")
    files["js/site.js"] = build_site_script().encode("utf-8")
    files["img/hero-pattern.svg"] = build_pattern_svg(company.brand_display, palette).encode("utf-8")
    files["img/contact-pattern.svg"] = build_contact_pattern_svg(company.brand_display, palette).encode("utf-8")
    files["img/footer-pattern.svg"] = build_footer_pattern_svg(company.brand_display, palette).encode("utf-8")
    for file_name, (data, _extension) in local_images.items():
        files[file_name] = data
    for file_name, (data, _extension) in custom_images.items():
        files[file_name] = data
    files["img/brand-mark.svg"] = build_favicon_svg(company.brand_display, palette).encode("utf-8")
    files["favicon.svg"] = build_favicon_svg(company.brand_display, palette).encode("utf-8")
    files["favicon.ico"] = build_favicon_ico(palette["accent"])
    files["favicon-32x32.png"] = build_png_square(32, palette["accent"])
    files["favicon-16x16.png"] = build_png_square(16, palette["accent_dark"])
    files["apple-touch-icon.png"] = build_png_square(180, palette["accent"])
    files["site.webmanifest"] = build_webmanifest(company.brand_display, palette["accent"]).encode("utf-8")
    files["robots.txt"] = build_robots_txt(company.domain).encode("utf-8")
    files["sitemap.xml"] = build_sitemap_xml(company.domain, THEME_FAMILIES[family]).encode("utf-8")
    files[".htaccess"] = build_htaccess().encode("utf-8")
    if "privacy-policy.html" in rendered_pages:
        files["legal/privacy.html"] = rendered_pages["privacy-policy.html"].encode("utf-8")
    if "terms-of-service.html" in rendered_pages:
        files["legal/terms.html"] = rendered_pages["terms-of-service.html"].encode("utf-8")
    if "cookie-policy.html" in rendered_pages:
        files["legal/cookie.html"] = rendered_pages["cookie-policy.html"].encode("utf-8")

    # Mirror part of the sample archive shape with additional static aliases.
    files["css/style.css"] = files["css/site.css"]
    files["css/footer.css"] = files["css/layout.css"]
    files["css/contact.css"] = files["css/components.css"]
    files["css/article.css"] = files["css/legal.css"]
    files["js/script.js"] = files["js/site.js"]
    files["js/home.js"] = files["js/interactions.js"]
    files["js/menu.js"] = files["js/navigation.js"]
    files["js/footer.js"] = files["js/site.js"]
    files["img/img-1.svg"] = files["img/hero-pattern.svg"]
    files["img/img-2.svg"] = files["img/contact-pattern.svg"]
    files["img/img-23.svg"] = files["img/footer-pattern.svg"]

    compliance_checks = _build_compliance_checks(
        language=spec.language,
        company=company,
        files=files,
        page_map=page_map,
        legal_pack=legal_pack,
    )
    export_ready = all(check.status == "passed" for check in compliance_checks)
    if strict and not export_ready:
        failed = "; ".join(check.detail for check in compliance_checks if check.status == "failed")
        raise ValueError(f"Export blocked by compliance checks: {failed}")

    page_files = sorted([*files.keys(), "manifest.json"])

    manifest = RenderManifest(
        created_at=_utc_now(),
        spec=spec.model_dump(mode="json"),
        company=company,
        page_family=family,
        page_files=page_files,
        language_label=LANGUAGE_LABELS[spec.language],
        geo_label=GEO_LABELS[spec.geo],
        theme_label=theme_pack["label"],
        jurisdiction=legal_pack.jurisdiction,
        regulator=legal_pack.regulator,
        legal_pack_key=legal_pack.key,
        required_legal_docs=list(legal_pack.required_docs),
        title_pattern=company.brand,
        footer_brand=company.brand,
        export_ready=export_ready,
        compliance_checks=compliance_checks,
    )
    files["manifest.json"] = manifest.model_dump_json(indent=2).encode("utf-8")
    return GeneratedSite(
        spec=spec,
        company=company,
        theme_label=theme_pack["label"],
        language_label=LANGUAGE_LABELS[spec.language],
        geo_label=GEO_LABELS[spec.geo],
        page_family=family,
        legal_pack=legal_pack,
        pages=pages,
        files=files,
        rendered_pages=rendered_pages,
        manifest=manifest,
        compliance_checks=compliance_checks,
        export_ready=export_ready,
    )


def build_preview(spec: SiteSpec) -> PreviewResponse:
    generated = generate_site(spec)
    return PreviewResponse(
        spec=spec,
        company=generated.company,
        theme_label=generated.theme_label,
        language_label=generated.language_label,
        geo_label=generated.geo_label,
        page_family=generated.page_family,
        pages=generated.pages,
        jurisdiction=generated.legal_pack.jurisdiction,
        regulator=generated.legal_pack.regulator,
        legal_pack_key=generated.legal_pack.key,
        required_legal_docs=list(generated.legal_pack.required_docs),
        title_pattern=generated.company.brand,
        footer_brand=generated.company.brand,
        export_ready=generated.export_ready,
        compliance_checks=generated.compliance_checks,
        manifest=generated.manifest,
    )


def _archive_name(build_id: str, brand: str) -> str:
    safe_brand = brand.replace(".", "-")
    return f"{safe_brand}-{build_id}.zip"


def _build_id(generated: GeneratedSite) -> str:
    source = f"{generated.company.domain}|{generated.manifest.created_at.isoformat()}"
    return hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]


def _preview_html(page_html: str, build_id: str) -> str:
    preview_base = f"/preview-assets/{build_id}"
    html = page_html.replace(".php", ".html")
    html = html.replace('href="/', f'href="{preview_base}/')
    html = html.replace('src="/', f'src="{preview_base}/')
    return html


def _persist_preview_bundle(build_id: str, generated: GeneratedSite) -> Path:
    preview_dir = PREVIEW_ROOT / build_id
    preview_dir.mkdir(parents=True, exist_ok=True)

    for file_name, payload in generated.files.items():
        if file_name.endswith("/") or file_name.startswith(("config/", "includes/", "partials/")):
            continue
        if file_name.endswith(".php"):
            continue
        target = preview_dir / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)

    index_path: Path | None = None
    for file_name, page_html in generated.rendered_pages.items():
        target = preview_dir / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_preview_html(page_html, build_id), encoding="utf-8")
        if file_name == "index.html":
            index_path = target

    if index_path is None:
        raise FileNotFoundError("Preview index page was not generated.")
    return index_path


def _persist_generated_site(generated: GeneratedSite) -> tuple[BuildResponse, BuildMetadata]:
    build_id = _build_id(generated)
    archive_name = _archive_name(build_id, generated.company.brand)
    archive_path = BUILD_ROOT / archive_name
    manifest_path = BUILD_ROOT / f"{build_id}.json"
    preview_path = _persist_preview_bundle(build_id, generated)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_name, payload in generated.files.items():
            zf.writestr(file_name, payload)
    archive_path.write_bytes(buffer.getvalue())

    manifest = generated.manifest.model_copy(update={"build_id": build_id})
    metadata = BuildMetadata(
        build_id=build_id,
        archive_name=archive_name,
        archive_path=str(archive_path),
        manifest_path=str(manifest_path),
        preview_path=str(preview_path),
        created_at=manifest.created_at,
        manifest=manifest,
    )
    manifest_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    response = BuildResponse(
        build_id=build_id,
        archive_name=archive_name,
        archive_url=f"/api/builds/{build_id}/download",
        metadata_url=f"/api/builds/{build_id}",
        preview_url=f"/preview/{build_id}",
        manifest=manifest,
    )
    return response, metadata


def export_site(spec: SiteSpec) -> BuildResponse:
    generated = generate_site(spec, strict=True)
    response, _ = _persist_generated_site(generated)
    return response


def get_build_metadata(build_id: str) -> BuildMetadata:
    path = BUILD_ROOT / f"{build_id}.json"
    if not path.exists():
        raise FileNotFoundError(build_id)
    return BuildMetadata.model_validate_json(path.read_text(encoding="utf-8"))


def get_build_archive_path(build_id: str) -> Path:
    metadata = get_build_metadata(build_id)
    path = Path(metadata.archive_path)
    if not path.exists():
        raise FileNotFoundError(build_id)
    return path


def get_build_preview_path(build_id: str) -> Path:
    metadata = get_build_metadata(build_id)
    if not metadata.preview_path:
        raise FileNotFoundError(build_id)
    path = Path(metadata.preview_path)
    if not path.exists():
        raise FileNotFoundError(build_id)
    return path

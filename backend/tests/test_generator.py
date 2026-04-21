from __future__ import annotations

import random

from app.generator import _build_address, _build_phone, generate_site
from app.legal_packs import LEGAL_PACK_REGISTRY
from app.schemas import ManualOverrides, SiteSpec


def make_spec(language: str = "en", geo: str = "US", theme: str = "marketing_agency") -> SiteSpec:
    return SiteSpec(
        theme=theme,
        language=language,
        geo=geo,
        domain="northpeakstudio.com",
        seed="acceptance",
        legal_entity_name=None,
        manual_overrides=ManualOverrides(),
        preview=True,
    )


def test_phone_and_address_generation_are_geo_aware() -> None:
    rng = random.Random(42)
    assert _build_phone("US", rng).startswith("+1")
    assert "Singapore" in _build_address("SG", random.Random(7))


def test_legal_pack_registry_contains_representative_pairs() -> None:
    for key in ["en-US", "en-SG", "de-DE", "fr-FR", "es-ES", "it-IT"]:
        assert key in LEGAL_PACK_REGISTRY


def test_generated_site_contains_required_docs_and_assets() -> None:
    generated = generate_site(make_spec(language="fr", geo="FR", theme="news"))
    names = set(generated.files)
    assert {"privacy-policy.php", "cookie-policy.php", "terms-of-service.php", "legal-notice.php", "disclaimer.php"}.issubset(names)
    assert {"config/site.php", "includes/layout.php", "partials/index.php"}.issubset(names)
    assert {"css/base.css", "css/layout.css", "css/components.css", "css/legal.css", "css/site.css"}.issubset(names)
    assert {"js/cookie.js", "js/navigation.js", "js/interactions.js", "js/site.js"}.issubset(names)
    assert {"img/hero-pattern.svg", "img/contact-pattern.svg", "img/footer-pattern.svg", "fonts/"}.issubset(names)
    assert {"robots.txt", "sitemap.xml", ".htaccess", "favicon.ico"}.issubset(names)
    assert generated.export_ready is True
    assert all(check.status == "passed" for check in generated.compliance_checks)


def test_representative_locales_are_actually_localized() -> None:
    representative = [
        ("en", "US", "Legal Notice"),
        ("en", "SG", "Singapore"),
        ("de", "DE", "Impressum"),
        ("fr", "FR", "Mentions légales"),
        ("es", "ES", "Aviso legal"),
        ("it", "IT", "Nota legale"),
    ]
    for language, geo, expected in representative:
        generated = generate_site(make_spec(language=language, geo=geo))
        legal_notice = generated.files["partials/legal-notice.php"].decode("utf-8")
        assert expected in legal_notice
        index_html = generated.files["partials/index.php"].decode("utf-8")
        assert "lorem ipsum" not in index_html.lower()
        assert "example@example.com" not in index_html.lower()
        assert "Г" not in legal_notice
        if language != "en":
            assert ">Domain<" not in index_html
            assert ">Phone<" not in index_html
            assert ">Address<" not in index_html


def test_title_and_footer_brand_stay_consistent() -> None:
    generated = generate_site(make_spec(language="es", geo="ES", theme="cafe_restaurant"))
    config_php = generated.files["config/site.php"].decode("utf-8")
    layout_php = generated.files["includes/layout.php"].decode("utf-8")
    index_php = generated.files["index.php"].decode("utf-8")
    assert "northpeakstudio" in config_php
    assert "Copyright &copy;" in layout_php
    assert "config/site.php" in index_php
    assert "includes/layout.php" in index_php

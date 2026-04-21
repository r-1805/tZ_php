import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def sample_spec(**overrides):
    payload = {
        "theme": "marketing_agency",
        "language": "en",
        "geo": "US",
        "domain": "northpeakstudio.com",
        "seed": "alpha",
        "legal_entity_name": "",
        "manual_overrides": {"phone": "", "email": "", "address": "", "hours": ""},
        "preview": True,
    }
    payload.update(overrides)
    return payload


def test_catalog_returns_expected_shape() -> None:
    response = client.get("/api/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["themes"]) == 6
    assert "offerings_portfolio" in payload["page_families"]


def test_preview_returns_brand_and_page_family() -> None:
    response = client.post("/api/preview", json=sample_spec())
    assert response.status_code == 200
    payload = response.json()
    assert payload["company"]["brand"] == "northpeakstudio"
    assert payload["page_family"] == "offerings_portfolio"
    assert any(page["file_name"] == "portfolio.php" for page in payload["pages"])
    assert payload["jurisdiction"]
    assert payload["legal_pack_key"] == "en-US"
    assert payload["export_ready"] is True
    assert len(payload["required_legal_docs"]) == 5
    assert all(item["status"] == "passed" for item in payload["compliance_checks"])


def test_export_creates_zip_and_metadata() -> None:
    response = client.post("/api/export", json=sample_spec(theme="news", language="de", geo="DE"))
    assert response.status_code == 200
    payload = response.json()
    build_id = payload["build_id"]

    metadata_response = client.get(f"/api/builds/{build_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["manifest"]["company"]["brand"] == "northpeakstudio"
    assert metadata["manifest"]["page_family"] == "services_projects"

    archive_response = client.get(f"/api/builds/{build_id}/download")
    assert archive_response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        names = set(archive.namelist())
        assert "index.php" in names
        assert "projects.php" in names
        assert "legal-notice.php" in names
        assert "disclaimer.php" in names
        assert "config/site.php" in names
        assert "includes/layout.php" in names
        assert "partials/index.php" in names
        assert "partials/projects.php" in names
        assert "css/base.css" in names
        assert "css/layout.css" in names
        assert "css/components.css" in names
        assert "css/legal.css" in names
        assert "css/site.css" in names
        assert "fonts/" in names
        assert "js/site.js" in names
        assert "js/navigation.js" in names
        assert "js/interactions.js" in names
        assert "js/cookie.js" in names
        assert "img/hero-pattern.svg" in names
        assert "img/contact-pattern.svg" in names
        assert "img/footer-pattern.svg" in names
        assert "manifest.json" in names


def test_preview_supports_all_theme_codes() -> None:
    themes = ["cleaning", "marketing_agency", "cafe_restaurant", "fitness_club", "news", "apparel"]
    for theme in themes:
        response = client.post("/api/preview", json=sample_spec(theme=theme))
        assert response.status_code == 200
        assert response.json()["export_ready"] is True


def test_preview_rejects_mismatched_email_domain() -> None:
    response = client.post(
        "/api/preview",
        json=sample_spec(manual_overrides={"phone": "", "email": "team@wrong-domain.com", "address": "", "hours": ""}),
    )
    assert response.status_code == 422

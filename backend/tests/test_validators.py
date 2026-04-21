from app.validators import brand_from_domain, normalize_domain, validate_contact_values


def test_normalize_domain_and_brand() -> None:
    assert normalize_domain("https://www.northpeakstudio.com/path") == "northpeakstudio.com"
    assert brand_from_domain("https://www.northpeakstudio.com/path") == "northpeakstudio"
    assert brand_from_domain("https://www.northpeakstudio.co.uk/path") == "northpeakstudio"


def test_validate_contact_values_rejects_placeholder_phone() -> None:
    try:
        validate_contact_values("+65 12345678", "contact@example.com", "123 Orchard Road, Singapore 048581", "example.com")
    except ValueError as exc:
        assert "placeholder" in str(exc).lower()
    else:
        raise AssertionError("placeholder phone should fail")


def test_validate_contact_values_reject_placeholder_email_text() -> None:
    try:
        validate_contact_values("+44 20 7123 4567", "example@example.com", "221 Baker Street, London NW1 6XE", "northpeakstudio.com")
    except ValueError as exc:
        assert "placeholder" in str(exc).lower()
    else:
        raise AssertionError("placeholder email should fail")

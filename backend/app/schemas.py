from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


THEME_ALIASES = {
    "cleaning": "cleaning",
    "marketing": "marketing_agency",
    "marketing_agency": "marketing_agency",
    "cafe": "cafe_restaurant",
    "cafe_restaurant": "cafe_restaurant",
    "fitness": "fitness_club",
    "fitness_club": "fitness_club",
    "news": "news",
    "clothes": "apparel",
    "apparel": "apparel",
}


class ManualOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    hours: str | None = None

    @field_validator("phone", "address", "hours", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ImageAssetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str | None = None
    data_url: str | None = None

    @field_validator("url", "data_url", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ImageOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hero: ImageAssetInput = Field(default_factory=ImageAssetInput)
    contact: ImageAssetInput = Field(default_factory=ImageAssetInput)
    footer: ImageAssetInput = Field(default_factory=ImageAssetInput)


class SiteSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str
    language: str
    geo: str
    domain: str
    seed: str | None = None
    legal_entity_name: str | None = None
    tracker_link: str | None = None
    fb_pixel_id: str | None = None
    manual_overrides: ManualOverrides = Field(default_factory=ManualOverrides)
    image_overrides: ImageOverrides = Field(default_factory=ImageOverrides)
    preview: bool = True

    @field_validator("domain")
    @classmethod
    def strip_domain(cls, value: str) -> str:
        return value.strip()

    @field_validator("seed")
    @classmethod
    def normalize_seed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("legal_entity_name")
    @classmethod
    def normalize_legal_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tracker_link")
    @classmethod
    def normalize_tracker_link(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not stripped.startswith(("http://", "https://")):
            raise ValueError("tracker_link must start with http:// or https://")
        return stripped

    @field_validator("fb_pixel_id")
    @classmethod
    def normalize_fb_pixel_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not stripped.isdigit():
            raise ValueError("fb_pixel_id must contain digits only")
        return stripped


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str
    geo: str = "US"
    lang: str = "en"
    domain: str
    tracker_link: str | None = None
    fb_pixel_id: str | None = None

    @field_validator("domain", "geo", "lang", "tracker_link", "fb_pixel_id", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tracker_link")
    @classmethod
    def validate_tracker_link(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("tracker_link must start with http:// or https://")
        return value

    @field_validator("fb_pixel_id")
    @classmethod
    def validate_fb_pixel_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.isdigit():
            raise ValueError("fb_pixel_id must contain digits only")
        return value

    @field_validator("theme")
    @classmethod
    def normalize_theme(cls, value: str) -> str:
        normalized = THEME_ALIASES.get(value.strip().lower())
        if normalized is None:
            supported = ", ".join(sorted(THEME_ALIASES))
            raise ValueError(f"Unsupported theme. Supported values: {supported}")
        return normalized

    def to_site_spec(self) -> "SiteSpec":
        return SiteSpec(
            theme=self.theme,
            language=self.lang,
            geo=self.geo,
            domain=self.domain,
            tracker_link=self.tracker_link,
            fb_pixel_id=self.fb_pixel_id,
        )


class CatalogOption(BaseModel):
    code: str
    label: str


class ThemeCatalogOption(CatalogOption):
    page_family: str


class CatalogResponse(BaseModel):
    themes: list[ThemeCatalogOption]
    languages: list[CatalogOption]
    geos: list[CatalogOption]
    page_families: dict[str, list[str]]


class PagePreview(BaseModel):
    slug: str
    file_name: str
    title: str
    summary: str


class CompanyProfile(BaseModel):
    brand: str
    brand_display: str
    domain: str
    legal_entity_name: str
    email: EmailStr
    phone: str
    address: str
    hours: str
    social_handles: dict[str, str]


class ComplianceCheck(BaseModel):
    code: str
    status: Literal["passed", "failed"]
    detail: str


class LegalPack(BaseModel):
    key: str
    jurisdiction: str
    governing_law: str
    regulator: str
    required_docs: list[str]
    document_titles: dict[str, str]
    privacy_html: str
    cookie_html: str
    terms_html: str
    legal_notice_html: str
    disclaimer_html: str


class RenderManifest(BaseModel):
    build_id: str | None = None
    created_at: datetime
    spec: dict[str, Any]
    company: CompanyProfile
    page_family: str
    page_files: list[str]
    language_label: str
    geo_label: str
    theme_label: str
    jurisdiction: str
    regulator: str
    legal_pack_key: str
    required_legal_docs: list[str]
    title_pattern: str
    footer_brand: str
    export_ready: bool
    compliance_checks: list[ComplianceCheck]


class PreviewResponse(BaseModel):
    spec: SiteSpec
    company: CompanyProfile
    theme_label: str
    language_label: str
    geo_label: str
    page_family: str
    pages: list[PagePreview]
    jurisdiction: str
    regulator: str
    legal_pack_key: str
    required_legal_docs: list[str]
    title_pattern: str
    footer_brand: str
    export_ready: bool
    compliance_checks: list[ComplianceCheck]
    manifest: RenderManifest


class BuildResponse(BaseModel):
    build_id: str
    archive_name: str
    archive_url: str
    metadata_url: str
    preview_url: str | None = None
    manifest: RenderManifest


class BuildMetadata(BaseModel):
    build_id: str
    archive_name: str
    archive_path: str
    manifest_path: str
    preview_path: str | None = None
    created_at: datetime
    manifest: RenderManifest

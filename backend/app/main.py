from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .catalog import GEO_LABELS, GEO_ORDER, LANGUAGE_LABELS, LANGUAGE_ORDER, THEME_FAMILIES, THEME_ORDER, THEME_PACKS
from .generator import PREVIEW_ROOT, build_preview, export_site, get_build_archive_path, get_build_metadata, get_build_preview_path
from .schemas import BuildMetadata, BuildResponse, CatalogOption, CatalogResponse, GenerateRequest, PreviewResponse, SiteSpec, ThemeCatalogOption

app = FastAPI(title="PHP Microsite Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/catalog", response_model=CatalogResponse)
def get_catalog() -> CatalogResponse:
    return CatalogResponse(
        themes=[
            ThemeCatalogOption(code=code, label=THEME_PACKS[code]["label"], page_family=THEME_PACKS[code]["page_family"])
            for code in THEME_ORDER
        ],
        languages=[CatalogOption(code=code, label=LANGUAGE_LABELS[code]) for code in LANGUAGE_ORDER],
        geos=[CatalogOption(code=code, label=GEO_LABELS[code]) for code in GEO_ORDER],
        page_families=THEME_FAMILIES,
    )


@app.post("/api/preview", response_model=PreviewResponse)
def post_preview(spec: SiteSpec) -> PreviewResponse:
    try:
        return build_preview(spec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/export", response_model=BuildResponse)
def post_export(spec: SiteSpec) -> BuildResponse:
    try:
        return export_site(spec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/builds/{build_id}", response_model=BuildMetadata)
def get_build(build_id: str) -> BuildMetadata:
    try:
        return get_build_metadata(build_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Build not found") from exc


@app.get("/api/builds/{build_id}/download")
def download_build(build_id: str) -> FileResponse:
    try:
        archive_path = get_build_archive_path(build_id)
        return FileResponse(archive_path, media_type="application/zip", filename=archive_path.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Build not found") from exc


@app.post("/generate")
def generate_white_page(request: GenerateRequest) -> FileResponse:
    try:
        build = export_site(request.to_site_spec())
        archive_path = get_build_archive_path(build.build_id)
        response = FileResponse(archive_path, media_type="application/zip", filename=archive_path.name)
        response.headers["X-Task-ID"] = build.build_id
        if build.preview_url:
            response.headers["X-Preview-URL"] = build.preview_url
        return response
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/preview/{task_id}")
def preview_generated_site(task_id: str) -> RedirectResponse:
    try:
        get_build_preview_path(task_id)
        return RedirectResponse(url=f"/preview-assets/{task_id}/index.html")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Preview not found") from exc


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
app.mount("/preview-assets", StaticFiles(directory=str(PREVIEW_ROOT), html=True), name="preview-assets")
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

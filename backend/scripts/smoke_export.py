from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.generator import get_build_archive_path, get_build_metadata, export_site  # noqa: E402
from app.schemas import ManualOverrides, SiteSpec  # noqa: E402


REQUIRED_ARCHIVE_ENTRIES = {
    "config/site.php",
    "includes/layout.php",
    "css/base.css",
    "css/layout.css",
    "css/components.css",
    "css/legal.css",
    "css/site.css",
    "js/cookie.js",
    "js/navigation.js",
    "js/interactions.js",
    "js/site.js",
    "img/hero-pattern.svg",
    "img/contact-pattern.svg",
    "img/footer-pattern.svg",
    "favicon.svg",
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "site.webmanifest",
    "robots.txt",
    "sitemap.xml",
    ".htaccess",
    "manifest.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a microsite and run a smoke check against the ZIP archive.")
    parser.add_argument("--theme", default="marketing_agency")
    parser.add_argument("--language", default="en")
    parser.add_argument("--geo", default="US")
    parser.add_argument("--domain", default="northpeakstudio.com")
    parser.add_argument("--seed", default="smoke")
    parser.add_argument("--legal-entity-name", default="")
    parser.add_argument("--php", dest="php_path", default="", help="Optional path to php.exe for `php -l` checks.")
    return parser.parse_args()


def build_spec(args: argparse.Namespace) -> SiteSpec:
    return SiteSpec(
        theme=args.theme,
        language=args.language,
        geo=args.geo,
        domain=args.domain,
        seed=args.seed,
        legal_entity_name=args.legal_entity_name or None,
        manual_overrides=ManualOverrides(),
        preview=True,
    )


def assert_archive_structure(archive: zipfile.ZipFile, metadata_page_files: set[str]) -> None:
    names = set(archive.namelist())
    missing = sorted(REQUIRED_ARCHIVE_ENTRIES - names)
    if missing:
        raise AssertionError(f"Archive is missing required entries: {', '.join(missing)}")

    manifest_payload = json.loads(archive.read("manifest.json").decode("utf-8"))
    manifest_page_files = set(manifest_payload["page_files"])
    if metadata_page_files != manifest_page_files:
        raise AssertionError("Manifest page_files differ between archive and metadata.")

    for page_file in manifest_page_files:
        if page_file.endswith(".php") and page_file not in names:
            raise AssertionError(f"Manifest references missing archive entry: {page_file}")


def lint_php_files(archive: zipfile.ZipFile, php_path: str) -> None:
    if not php_path:
        return
    php_binary = Path(php_path)
    if not php_binary.exists():
        raise FileNotFoundError(f"PHP binary not found: {php_binary}")

    with tempfile.TemporaryDirectory(prefix="php-microsite-smoke-") as temp_dir:
        archive.extractall(temp_dir)
        temp_root = Path(temp_dir)
        for php_file in sorted(temp_root.rglob("*.php")):
            result = subprocess.run(
                [str(php_binary), "-l", str(php_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise AssertionError(f"PHP lint failed for {php_file}:\n{result.stdout}\n{result.stderr}")


def main() -> int:
    args = parse_args()
    spec = build_spec(args)

    build_response = export_site(spec)
    metadata = get_build_metadata(build_response.build_id)
    archive_path = get_build_archive_path(build_response.build_id)

    if metadata.manifest.build_id != build_response.build_id:
        raise AssertionError("Metadata build_id does not match export response.")
    if not metadata.manifest.export_ready:
        raise AssertionError("Exported build is not marked export_ready.")
    if metadata.manifest.company.domain != spec.domain:
        raise AssertionError("Exported manifest domain does not match requested domain.")

    with zipfile.ZipFile(archive_path) as archive:
        assert_archive_structure(archive, set(metadata.manifest.page_files))
        lint_php_files(archive, args.php_path)

    print(f"Smoke check passed for {build_response.archive_name}")
    print(f"Build ID: {build_response.build_id}")
    print(f"Archive: {archive_path}")
    if args.php_path:
        print(f"PHP lint: passed via {args.php_path}")
    else:
        print("PHP lint: skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

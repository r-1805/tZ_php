import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import { exportSite, fetchCatalog, previewSite } from "./api";
import type { BuildResponse, CatalogResponse, ImageOverrides, ManualOverrides, PreviewResponse, SiteSpec } from "./types";

const emptyOverrides: ManualOverrides = {
  phone: "",
  email: "",
  address: "",
  hours: "",
};

const emptyImages: ImageOverrides = {
  hero: { url: "", data_url: "" },
  contact: { url: "", data_url: "" },
  footer: { url: "", data_url: "" },
};

function buildInitialSpec(catalog?: CatalogResponse): SiteSpec {
  return {
    theme: catalog?.themes[0]?.code ?? "cleaning",
    language: catalog?.languages[0]?.code ?? "en",
    geo: catalog?.geos[0]?.code ?? "US",
    domain: "northpeakstudio.com",
    seed: "",
    legal_entity_name: "",
    manual_overrides: emptyOverrides,
    image_overrides: emptyImages,
    preview: true,
  };
}

type UiLanguage = "en" | "ru";

const UI_COPY = {
  en: {
    topbarEyebrow: "Internal panel",
    title: "Localized PHP microsite generator",
    topbarCopy: "Deterministic theme packs, geo-aware contact data, exportable ZIP builds, and localized legal pages.",
    uiLanguage: "Panel language",
    generatorEyebrow: "Generator",
    buildSettings: "Build settings",
    theme: "Theme",
    contentLanguage: "Content language",
    geo: "GEO",
    domain: "Domain",
    seed: "Seed",
    seedPlaceholder: "Optional deterministic seed",
    legalEntity: "Legal entity",
    legalEntityPlaceholder: "Optional company name override",
    manualOverridesEyebrow: "Manual overrides",
    contactValues: "Contact values",
    manualOverridesNote: "Leave fields empty to let the generator produce geo-aware defaults.",
    phone: "Phone",
    email: "Email",
    address: "Address",
    hours: "Hours",
    preview: "Preview",
    generatingPreview: "Generating preview...",
    exportZip: "Export ZIP",
    exportingZip: "Exporting ZIP...",
    buildReady: "Build ready:",
    downloadArchive: "Download archive",
    buildMetadata: "Build metadata",
    previewEyebrow: "Preview",
    generatedProfile: "Generated profile",
    loadingCatalog: "Loading catalog...",
    brand: "Brand",
    exportReady: "Export ready",
    needsFixes: "Needs fixes",
    contact: "Contact",
    compliance: "Compliance",
    jurisdiction: "Jurisdiction",
    regulator: "Regulator",
    legalPack: "Legal pack",
    manifest: "Manifest",
    footerBrand: "Footer brand",
    titlePattern: "Title pattern",
    exportReadiness: "Export readiness",
    passed: "Passed",
    blocked: "Blocked",
    requiredLegalDocs: "Required legal docs",
    complianceSummary: "Compliance summary",
    pages: "Pages",
    manifestExcerpts: "Manifest excerpts",
    emptyState:
      "Configure the generator and run a preview to inspect brand, contact data, page family, and legal jurisdiction before export.",
    previewFailed: "Preview failed",
    exportFailed: "Export failed",
  },
  ru: {
    topbarEyebrow: "Внутренняя панель",
    title: "Генератор локализованных PHP-микросайтов",
    topbarCopy: "Детерминированные theme packs, GEO-aware контакты, ZIP-экспорт и локализованные юр-документы.",
    uiLanguage: "Язык панели",
    generatorEyebrow: "Генератор",
    buildSettings: "Параметры сборки",
    theme: "Тематика",
    contentLanguage: "Язык контента",
    geo: "ГЕО",
    domain: "Домен",
    seed: "Сид",
    seedPlaceholder: "Необязательный детерминированный сид",
    legalEntity: "Юр. лицо",
    legalEntityPlaceholder: "Необязательное имя компании",
    manualOverridesEyebrow: "Ручные значения",
    contactValues: "Контактные данные",
    manualOverridesNote: "Оставь поля пустыми, чтобы генератор сам создал GEO-специфичные значения.",
    phone: "Телефон",
    email: "Email",
    address: "Адрес",
    hours: "Часы работы",
    preview: "Превью",
    generatingPreview: "Генерируем превью...",
    exportZip: "Экспорт ZIP",
    exportingZip: "Экспортируем ZIP...",
    buildReady: "Сборка готова:",
    downloadArchive: "Скачать архив",
    buildMetadata: "Метаданные сборки",
    previewEyebrow: "Превью",
    generatedProfile: "Сгенерированный профиль",
    loadingCatalog: "Загрузка каталога...",
    brand: "Бренд",
    exportReady: "Готово к экспорту",
    needsFixes: "Нужны правки",
    contact: "Контакты",
    compliance: "Комплаенс",
    jurisdiction: "Юрисдикция",
    regulator: "Регулятор",
    legalPack: "Legal pack",
    manifest: "Манифест",
    footerBrand: "Бренд в футере",
    titlePattern: "Паттерн title",
    exportReadiness: "Готовность к экспорту",
    passed: "Пройдено",
    blocked: "Заблокировано",
    requiredLegalDocs: "Обязательные юр-документы",
    complianceSummary: "Сводка проверок",
    pages: "Страницы",
    manifestExcerpts: "Фрагменты manifest",
    emptyState:
      "Настрой генератор и запусти превью, чтобы проверить бренд, контакты, семейство страниц и юрисдикцию до экспорта.",
    previewFailed: "Не удалось построить превью",
    exportFailed: "Не удалось экспортировать ZIP",
  },
} as const;

const OPTION_LABELS = {
  themes: {
    cleaning: { en: "Cleaning", ru: "Клининг" },
    marketing_agency: { en: "Marketing agency", ru: "Маркетинговое агентство" },
    cafe_restaurant: { en: "Cafe / restaurant", ru: "Кафе-ресторан" },
    fitness_club: { en: "Fitness club", ru: "Фитнес-клуб" },
    news: { en: "News", ru: "Новости" },
    apparel: { en: "Apparel", ru: "Одежда" },
  },
  languages: {
    en: { en: "English", ru: "Английский" },
    de: { en: "German", ru: "Немецкий" },
    es: { en: "Spanish", ru: "Испанский" },
    fr: { en: "French", ru: "Французский" },
    it: { en: "Italian", ru: "Итальянский" },
  },
  geos: {
    US: { en: "United States", ru: "США" },
    UK: { en: "United Kingdom", ru: "Великобритания" },
    CA: { en: "Canada", ru: "Канада" },
    AU: { en: "Australia", ru: "Австралия" },
    DE: { en: "Germany", ru: "Германия" },
    FR: { en: "France", ru: "Франция" },
    ES: { en: "Spain", ru: "Испания" },
    IT: { en: "Italy", ru: "Италия" },
    SG: { en: "Singapore", ru: "Сингапур" },
  },
  families: {
    services: { en: "services", ru: "услуги" },
    offerings_portfolio: { en: "offerings / portfolio", ru: "предложения / портфолио" },
    services_projects: { en: "services / projects", ru: "услуги / проекты" },
  },
  docs: {
    "privacy-policy.php": { en: "privacy policy", ru: "политика конфиденциальности" },
    "cookie-policy.php": { en: "cookie policy", ru: "cookie policy" },
    "terms-of-service.php": { en: "terms of service", ru: "условия использования" },
    "legal-notice.php": { en: "legal notice", ru: "legal notice" },
    "disclaimer.php": { en: "disclaimer", ru: "disclaimer" },
  },
  checks: {
    required_legal_docs: { en: "Required legal docs", ru: "Обязательные юр-документы" },
    placeholder_data: { en: "Placeholder data", ru: "Плейсхолдеры в данных" },
    internal_links: { en: "Internal links", ru: "Внутренние ссылки" },
    brand_consistency: { en: "Brand consistency", ru: "Согласованность бренда" },
    localized_labels: { en: "Localized labels", ru: "Локализованные подписи" },
    duplicate_pages: { en: "Duplicate pages", ru: "Дубли страниц" },
    legal_pack: { en: "Legal pack", ru: "Legal pack" },
  },
} as const;

function getInitialUiLanguage(): UiLanguage {
  if (typeof window === "undefined") {
    return "en";
  }
  const stored = window.localStorage.getItem("panel-language");
  if (stored === "en" || stored === "ru") {
    return stored;
  }
  return window.navigator.language.toLowerCase().startsWith("ru") ? "ru" : "en";
}

function humanFamily(family: string, uiLanguage: UiLanguage) {
  return OPTION_LABELS.families[family as keyof typeof OPTION_LABELS.families]?.[uiLanguage] ?? family.split("_").join(" / ");
}

function humanDoc(fileName: string, uiLanguage: UiLanguage) {
  return OPTION_LABELS.docs[fileName as keyof typeof OPTION_LABELS.docs]?.[uiLanguage] ?? fileName.replace(".php", "").split("-").join(" ");
}

function humanCheck(code: string, uiLanguage: UiLanguage) {
  return OPTION_LABELS.checks[code as keyof typeof OPTION_LABELS.checks]?.[uiLanguage] ?? code;
}

function optionLabel(
  group: "themes" | "languages" | "geos",
  code: string,
  uiLanguage: UiLanguage,
  fallback: string,
) {
  const labels = OPTION_LABELS[group] as Record<string, { en: string; ru: string }>;
  return labels[code]?.[uiLanguage] ?? fallback;
}

export default function App() {
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>(getInitialUiLanguage);
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [spec, setSpec] = useState<SiteSpec>(buildInitialSpec());
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [build, setBuild] = useState<BuildResponse | null>(null);
  const [loading, setLoading] = useState<"catalog" | "preview" | "export" | null>("catalog");
  const [error, setError] = useState<string | null>(null);
  const t = UI_COPY[uiLanguage];
  const imageCopy =
    uiLanguage === "ru"
      ? {
          eyebrow: "Изображения",
          title: "Источники изображений",
          note: "Вставь прямую ссылку на картинку или загрузи файл. Загруженный файл заменит SVG-заглушку.",
          hero: "Hero-изображение",
          contact: "Изображение для contact",
          footer: "Footer-изображение",
          upload: "Загрузить файл",
        }
      : {
          eyebrow: "Images",
          title: "Image sources",
          note: "Paste a direct image URL or upload a file. Uploaded files replace the placeholder graphics.",
          hero: "Hero image",
          contact: "Contact image",
          footer: "Footer image",
          upload: "Upload image",
        };

  useEffect(() => {
    window.localStorage.setItem("panel-language", uiLanguage);
  }, [uiLanguage]);

  useEffect(() => {
    fetchCatalog()
      .then((payload) => {
        setCatalog(payload);
        setSpec((current) => ({
          ...buildInitialSpec(payload),
          ...current,
          theme: payload.themes.find((item) => item.code === current.theme)?.code ?? payload.themes[0].code,
          language: payload.languages.find((item) => item.code === current.language)?.code ?? payload.languages[0].code,
          geo: payload.geos.find((item) => item.code === current.geo)?.code ?? payload.geos[0].code,
        }));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(null));
  }, []);

  function updateField<K extends keyof SiteSpec>(key: K, value: SiteSpec[K]) {
    setSpec((current) => ({ ...current, [key]: value }));
  }

  function updateOverride<K extends keyof ManualOverrides>(key: K, value: ManualOverrides[K]) {
    setSpec((current) => ({
      ...current,
      manual_overrides: {
        ...current.manual_overrides,
        [key]: value,
      },
    }));
  }

  function updateImageUrl(key: keyof ImageOverrides, value: string) {
    setSpec((current) => ({
      ...current,
      image_overrides: {
        ...current.image_overrides,
        [key]: {
          ...current.image_overrides[key],
          url: value,
        },
      },
    }));
  }

  async function handleImageUpload(key: keyof ImageOverrides, event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result ?? ""));
      reader.onerror = () => reject(new Error("Failed to read image"));
      reader.readAsDataURL(file);
    });
    setSpec((current) => ({
      ...current,
      image_overrides: {
        ...current.image_overrides,
        [key]: {
          ...current.image_overrides[key],
          data_url: dataUrl,
        },
      },
    }));
    event.target.value = "";
  }

  async function handlePreview(event: FormEvent) {
    event.preventDefault();
    setLoading("preview");
    setError(null);
    setBuild(null);
    try {
      const payload = await previewSite(spec);
      setPreview(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.previewFailed);
    } finally {
      setLoading(null);
    }
  }

  async function handleExport() {
    setLoading("export");
    setError(null);
    try {
      const payload = await exportSite(spec);
      setBuild(payload);
      if (!preview) {
        const latestPreview = await previewSite(spec);
        setPreview(latestPreview);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.exportFailed);
    } finally {
      setLoading(null);
    }
  }

  const selectedTheme = catalog?.themes.find((item) => item.code === spec.theme);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">{t.topbarEyebrow}</p>
          <h1>{t.title}</h1>
        </div>
        <div className="topbar-side">
          <div className="language-switcher" aria-label={t.uiLanguage}>
            <button type="button" className={uiLanguage === "ru" ? "switcher-active" : ""} onClick={() => setUiLanguage("ru")}>
              RU
            </button>
            <button type="button" className={uiLanguage === "en" ? "switcher-active" : ""} onClick={() => setUiLanguage("en")}>
              EN
            </button>
          </div>
          <p className="topbar-copy">{t.topbarCopy}</p>
        </div>
      </header>

      <div className="layout">
        <section className="panel form-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">{t.generatorEyebrow}</p>
              <h2>{t.buildSettings}</h2>
            </div>
            {selectedTheme ? <span className="badge">{humanFamily(selectedTheme.page_family, uiLanguage)}</span> : null}
          </div>

          <form className="generator-form" onSubmit={handlePreview}>
            <div className="grid two">
              <label>
                {t.theme}
                <select value={spec.theme} onChange={(event) => updateField("theme", event.target.value)}>
                  {catalog?.themes.map((item) => (
                    <option key={item.code} value={item.code}>
                      {optionLabel("themes", item.code, uiLanguage, item.label)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t.contentLanguage}
                <select value={spec.language} onChange={(event) => updateField("language", event.target.value)}>
                  {catalog?.languages.map((item) => (
                    <option key={item.code} value={item.code}>
                      {optionLabel("languages", item.code, uiLanguage, item.label)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="grid two">
              <label>
                {t.geo}
                <select value={spec.geo} onChange={(event) => updateField("geo", event.target.value)}>
                  {catalog?.geos.map((item) => (
                    <option key={item.code} value={item.code}>
                      {optionLabel("geos", item.code, uiLanguage, item.label)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t.domain}
                <input value={spec.domain} onChange={(event) => updateField("domain", event.target.value)} placeholder="northpeakstudio.com" />
              </label>
            </div>

            <div className="grid two">
              <label>
                {t.seed}
                <input value={spec.seed} onChange={(event) => updateField("seed", event.target.value)} placeholder={t.seedPlaceholder} />
              </label>
              <label>
                {t.legalEntity}
                <input
                  value={spec.legal_entity_name}
                  onChange={(event) => updateField("legal_entity_name", event.target.value)}
                  placeholder={t.legalEntityPlaceholder}
                />
              </label>
            </div>

            <div className="section-divider">
              <div>
                <p className="eyebrow">{t.manualOverridesEyebrow}</p>
                <h3>{t.contactValues}</h3>
              </div>
              <p>{t.manualOverridesNote}</p>
            </div>

            <div className="grid two">
              <label>
                {t.phone}
                <input value={spec.manual_overrides.phone} onChange={(event) => updateOverride("phone", event.target.value)} />
              </label>
              <label>
                {t.email}
                <input value={spec.manual_overrides.email} onChange={(event) => updateOverride("email", event.target.value)} />
              </label>
            </div>
            <label>
              {t.address}
              <input value={spec.manual_overrides.address} onChange={(event) => updateOverride("address", event.target.value)} />
            </label>
            <label>
              {t.hours}
              <input value={spec.manual_overrides.hours} onChange={(event) => updateOverride("hours", event.target.value)} />
            </label>

            <div className="section-divider">
              <div>
                <p className="eyebrow">{imageCopy.eyebrow}</p>
                <h3>{imageCopy.title}</h3>
              </div>
              <p>{imageCopy.note}</p>
            </div>

            {([
              ["hero", imageCopy.hero],
              ["contact", imageCopy.contact],
              ["footer", imageCopy.footer],
            ] as const).map(([key, label]) => (
              <div key={key} className="image-source-block">
                <label>
                  {label}
                  <input
                    value={spec.image_overrides[key].url}
                    onChange={(event) => updateImageUrl(key, event.target.value)}
                    placeholder="https://example.com/photo.jpg"
                  />
                </label>
                <label>
                  {imageCopy.upload}
                  <input type="file" accept="image/*" onChange={(event) => void handleImageUpload(key, event)} />
                </label>
              </div>
            ))}

            <div className="actions">
              <button type="submit" className="button button-primary" disabled={loading === "preview" || loading === "catalog"}>
                {loading === "preview" ? t.generatingPreview : t.preview}
              </button>
              <button
                type="button"
                className="button button-secondary"
                onClick={handleExport}
                disabled={loading === "export" || loading === "catalog"}
              >
                {loading === "export" ? t.exportingZip : t.exportZip}
              </button>
            </div>
          </form>

          {error ? <div className="alert alert-error">{error}</div> : null}
          {build ? (
            <div className="alert alert-success">
              <strong>{t.buildReady}</strong> {build.archive_name}
              <div className="build-links">
                <a href={build.archive_url}>{t.downloadArchive}</a>
                <a href={build.metadata_url}>{t.buildMetadata}</a>
              </div>
            </div>
          ) : null}
        </section>

        <section className="panel preview-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">{t.previewEyebrow}</p>
              <h2>{t.generatedProfile}</h2>
            </div>
            {preview ? <span className="badge">{optionLabel("themes", spec.theme, uiLanguage, preview.theme_label)}</span> : null}
          </div>

          {loading === "catalog" ? (
            <div className="empty-state">{t.loadingCatalog}</div>
          ) : preview ? (
            <div className="preview-stack">
              <div className="hero-card">
                <div>
                  <p className="eyebrow">{t.brand}</p>
                  <h3>{preview.company.brand}</h3>
                  <p>{preview.company.legal_entity_name}</p>
                </div>
                <div className="hero-meta">
                  <span>{optionLabel("languages", spec.language, uiLanguage, preview.language_label)}</span>
                  <span>{optionLabel("geos", spec.geo, uiLanguage, preview.geo_label)}</span>
                  <span>{humanFamily(preview.page_family, uiLanguage)}</span>
                  <span>{preview.export_ready ? t.exportReady : t.needsFixes}</span>
                </div>
              </div>

              <div className="grid two">
                <article className="subpanel">
                  <h3>{t.contact}</h3>
                  <dl className="definition-list">
                    <div><dt>{t.domain}</dt><dd>{preview.company.domain}</dd></div>
                    <div><dt>{t.email}</dt><dd>{preview.company.email}</dd></div>
                    <div><dt>{t.phone}</dt><dd>{preview.company.phone}</dd></div>
                    <div><dt>{t.address}</dt><dd>{preview.company.address}</dd></div>
                    <div><dt>{t.hours}</dt><dd>{preview.company.hours}</dd></div>
                  </dl>
                </article>

                <article className="subpanel">
                  <h3>{t.compliance}</h3>
                  <dl className="definition-list">
                    <div><dt>{t.jurisdiction}</dt><dd>{preview.jurisdiction}</dd></div>
                    <div><dt>{t.regulator}</dt><dd>{preview.regulator}</dd></div>
                    <div><dt>{t.legalPack}</dt><dd>{preview.legal_pack_key}</dd></div>
                    <div><dt>{t.manifest}</dt><dd>{preview.manifest.page_files.length} files</dd></div>
                    <div><dt>{t.footerBrand}</dt><dd>{preview.footer_brand}</dd></div>
                    <div><dt>{t.titlePattern}</dt><dd>{preview.title_pattern}</dd></div>
                    <div><dt>{t.exportReadiness}</dt><dd>{preview.export_ready ? t.passed : t.blocked}</dd></div>
                  </dl>
                </article>
              </div>

              <article className="subpanel">
                <h3>{t.requiredLegalDocs}</h3>
                <div className="tag-cloud">
                  {preview.required_legal_docs.map((item) => (
                    <span key={item} className="mini-tag">{humanDoc(item, uiLanguage)}</span>
                  ))}
                </div>
              </article>

              <article className="subpanel">
                <h3>{t.complianceSummary}</h3>
                <div className="check-list">
                  {preview.compliance_checks.map((item) => (
                    <div key={item.code} className={`check-item check-item-${item.status}`}>
                      <strong>{humanCheck(item.code, uiLanguage)}</strong>
                      <p>{item.detail}</p>
                    </div>
                  ))}
                </div>
              </article>

              <article className="subpanel">
                <h3>{t.pages}</h3>
                <div className="page-list">
                  {preview.pages.map((page) => (
                    <div key={page.file_name} className="page-item">
                      <div>
                        <strong>{page.file_name}</strong>
                        <p>{page.title}</p>
                      </div>
                      <span>{page.summary}</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="subpanel">
                <h3>{t.manifestExcerpts}</h3>
                <pre>{JSON.stringify(preview.manifest, null, 2)}</pre>
              </article>
            </div>
          ) : (
            <div className="empty-state">{t.emptyState}</div>
          )}
        </section>
      </div>
    </div>
  );
}

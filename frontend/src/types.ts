export type CatalogOption = {
  code: string;
  label: string;
};

export type ThemeCatalogOption = CatalogOption & {
  page_family: string;
};

export type CatalogResponse = {
  themes: ThemeCatalogOption[];
  languages: CatalogOption[];
  geos: CatalogOption[];
  page_families: Record<string, string[]>;
};

export type ManualOverrides = {
  phone: string;
  email: string;
  address: string;
  hours: string;
};

export type ImageAssetInput = {
  url: string;
  data_url: string;
};

export type ImageOverrides = {
  hero: ImageAssetInput;
  contact: ImageAssetInput;
  footer: ImageAssetInput;
};

export type SiteSpec = {
  theme: string;
  language: string;
  geo: string;
  domain: string;
  seed: string;
  legal_entity_name: string;
  manual_overrides: ManualOverrides;
  image_overrides: ImageOverrides;
  preview: boolean;
};

export type PagePreview = {
  slug: string;
  file_name: string;
  title: string;
  summary: string;
};

export type CompanyProfile = {
  brand: string;
  brand_display: string;
  domain: string;
  legal_entity_name: string;
  email: string;
  phone: string;
  address: string;
  hours: string;
  social_handles: Record<string, string>;
};

export type ComplianceCheck = {
  code: string;
  status: "passed" | "failed";
  detail: string;
};

export type RenderManifest = {
  build_id?: string | null;
  created_at: string;
  spec: Record<string, unknown>;
  company: CompanyProfile;
  page_family: string;
  page_files: string[];
  language_label: string;
  geo_label: string;
  theme_label: string;
  jurisdiction: string;
  regulator: string;
  legal_pack_key: string;
  required_legal_docs: string[];
  title_pattern: string;
  footer_brand: string;
  export_ready: boolean;
  compliance_checks: ComplianceCheck[];
};

export type PreviewResponse = {
  spec: SiteSpec;
  company: CompanyProfile;
  theme_label: string;
  language_label: string;
  geo_label: string;
  page_family: string;
  pages: PagePreview[];
  jurisdiction: string;
  regulator: string;
  legal_pack_key: string;
  required_legal_docs: string[];
  title_pattern: string;
  footer_brand: string;
  export_ready: boolean;
  compliance_checks: ComplianceCheck[];
  manifest: RenderManifest;
};

export type BuildResponse = {
  build_id: string;
  archive_name: string;
  archive_url: string;
  metadata_url: string;
  manifest: RenderManifest;
};

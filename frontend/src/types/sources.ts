export type SourceCategory = "geophysics" | "atmosphere" | "space" | "society" | "movement";
export type SourceKind = "geo_event" | "signal";

export interface CredentialField {
  key: string;
  label: string;
  help?: string | null;
  secret: boolean;
  placeholder?: string | null;
}

export interface SourceDescriptor {
  id: string;
  name: string;
  category: SourceCategory;
  kind: SourceKind;
  requires_key: boolean;
  description: string;
  doc_url?: string | null;
  signup_url?: string | null;
  credential_fields: CredentialField[];
  feeds: string[];
}

export interface SourceHealth {
  ok: boolean | null;
  last_fetch?: string | null;
  error?: string | null;
  count?: number | null;
}

export interface SourceStatus {
  descriptor: SourceDescriptor;
  configured: boolean;
  enabled: boolean;
  active: boolean;
  masked_credentials: Record<string, string>;
  health: SourceHealth;
}

export interface SourcesResponse {
  data_mode: string;
  active_count: number;
  total_count: number;
  sources: SourceStatus[];
}

export interface TestResult {
  ok: boolean;
  count: number;
  error?: string | null;
  sample?: string | null;
}

export const CATEGORY_LABELS: Record<SourceCategory, string> = {
  geophysics: "Geophysics & Disasters",
  atmosphere: "Atmosphere & Air Quality",
  space: "Space Weather",
  society: "Society & News",
  movement: "Movement"
};

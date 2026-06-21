// ---------------------------------------------------------------------------
// API client for Engram backend
// ---------------------------------------------------------------------------

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types mirroring the backend models
// ---------------------------------------------------------------------------

export interface Entity {
  id: string;
  entity_type: string;
  title: string;
  content: string | null;
  properties: Record<string, unknown>;
  project: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  importance: number;
  access_count: number;
  last_accessed: string | null;
  decay_factor: number;
  source_event_id: string | null;
  created_by: string | null;
  confidence: number;
  tags: string[];
  files: string[];
}

export interface Relationship {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  properties: Record<string, unknown>;
  weight: number;
  created_at: string;
  source_event_id: string | null;
}

export interface SearchResult {
  entity: Entity;
  score: number;
  relationships: Relationship[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  duration_ms: number;
}

export interface Stats {
  events: number;
  entities: number;
  relationships: number;
  vector_embeddings: number;
}

export interface ProvenanceRecord {
  id: string;
  entity_id: string;
  action: string;
  actor: string;
  timestamp: string;
  source_event_id: string | null;
  related_entity_id: string | null;
  details: Record<string, unknown>;
  confidence_delta: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export function getStats(): Promise<Stats> {
  return request<Stats>("/admin/stats");
}

export function listEntities(params?: {
  entity_type?: string;
  project?: string;
  status?: string;
  min_importance?: number;
  tag?: string;
  limit?: number;
  offset?: number;
}): Promise<Entity[]> {
  const qs = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) qs.set(k, String(v));
    }
  }
  const query = qs.toString();
  return request<Entity[]>(`/entities${query ? `?${query}` : ""}`);
}

export function getEntity(id: string): Promise<Entity> {
  return request<Entity>(`/entities/${encodeURIComponent(id)}`);
}

export function searchEntities(
  query: string,
  opts?: {
    entity_types?: string[];
    project?: string;
    limit?: number;
    min_importance?: number;
    include_relationships?: boolean;
  },
): Promise<SearchResponse> {
  return request<SearchResponse>("/search", {
    method: "POST",
    body: JSON.stringify({ query, ...opts }),
  });
}

export function getRelationships(params?: {
  source_id?: string;
  target_id?: string;
  relation_type?: string;
  limit?: number;
  offset?: number;
}): Promise<Relationship[]> {
  const qs = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) qs.set(k, String(v));
    }
  }
  const query = qs.toString();
  return request<Relationship[]>(`/relationships${query ? `?${query}` : ""}`);
}

export function getEntityProvenance(id: string): Promise<ProvenanceRecord[]> {
  return request<ProvenanceRecord[]>(
    `/entities/${encodeURIComponent(id)}/provenance`,
  );
}

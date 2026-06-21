import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getEntity,
  getEntityProvenance,
  getRelationships,
  type Entity,
  type ProvenanceRecord,
  type Relationship,
} from "../api";
import { entityTypeColor, formatDate } from "../utils";
import { LoadingSpinner, ErrorBanner } from "./DashboardPage";

function EntityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [entity, setEntity] = useState<Entity | null>(null);
  const [provenance, setProvenance] = useState<ProvenanceRecord[]>([]);
  const [related, setRelated] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    async function load() {
      try {
        const [ent, prov, relsOut, relsIn] = await Promise.all([
          getEntity(id!),
          getEntityProvenance(id!),
          getRelationships({ source_id: id, limit: 100 }),
          getRelationships({ target_id: id, limit: 100 }),
        ]);
        if (!cancelled) {
          setEntity(ent);
          setProvenance(prov);
          // Combine outgoing and incoming relationships, dedup by id
          const seen = new Set<string>();
          const all: Relationship[] = [];
          for (const r of [...relsOut, ...relsIn]) {
            if (!seen.has(r.id)) {
              seen.add(r.id);
              all.push(r);
            }
          }
          setRelated(all);
        }
      } catch (err) {
        if (!cancelled) setError(String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!entity) return <ErrorBanner message="Entity not found" />;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link to="/" className="hover:text-gray-300">
          Dashboard
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-300">{entity.title}</span>
      </nav>

      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${entityTypeColor(entity.entity_type)}`}
              >
                {entity.entity_type}
              </span>
              <StatusBadge status={entity.status} />
            </div>
            <h1 className="text-xl font-bold">{entity.title}</h1>
          </div>
          <div className="text-right text-sm text-gray-500 whitespace-nowrap">
            <div>Created {formatDate(entity.created_at)}</div>
            <div>Updated {formatDate(entity.updated_at)}</div>
          </div>
        </div>

        {entity.content && (
          <div className="mt-4 text-gray-300 text-sm whitespace-pre-wrap leading-relaxed border-t border-gray-700 pt-4">
            {entity.content}
          </div>
        )}
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetaCard label="Importance" value={`${(entity.importance * 100).toFixed(0)}%`} />
        <MetaCard label="Confidence" value={`${(entity.confidence * 100).toFixed(0)}%`} />
        <MetaCard label="Access Count" value={String(entity.access_count)} />
        <MetaCard label="Decay Factor" value={entity.decay_factor.toFixed(2)} />
        {entity.project && <MetaCard label="Project" value={entity.project} />}
        {entity.created_by && <MetaCard label="Created By" value={entity.created_by} />}
      </div>

      {/* Tags */}
      {entity.tags.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Tags</h2>
          <div className="flex flex-wrap gap-2">
            {entity.tags.map((tag) => (
              <span
                key={tag}
                className="bg-gray-700 text-gray-300 rounded-full px-3 py-1 text-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Files */}
      {entity.files.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Files</h2>
          <div className="card space-y-1">
            {entity.files.map((file) => (
              <div key={file} className="text-sm font-mono text-gray-400">
                {file}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Properties */}
      {Object.keys(entity.properties).length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Properties</h2>
          <div className="card">
            <pre className="text-sm text-gray-300 overflow-x-auto">
              {JSON.stringify(entity.properties, null, 2)}
            </pre>
          </div>
        </section>
      )}

      {/* Relationships */}
      {related.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">
            Relationships ({related.length})
          </h2>
          <div className="space-y-2">
            {related.map((rel) => {
              const isSource = rel.source_id === id;
              const linkedId = isSource ? rel.target_id : rel.source_id;
              return (
                <Link
                  key={rel.id}
                  to={`/entity/${encodeURIComponent(linkedId)}`}
                  className="card block hover:ring-1 hover:ring-gray-700 transition-all"
                >
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">
                      {isSource ? "this" : linkedId.slice(0, 8)}
                    </span>
                    <span className="text-indigo-400 font-medium">
                      {rel.relation_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-gray-500">
                      {isSource ? linkedId.slice(0, 8) : "this"}
                    </span>
                    <span className="ml-auto text-xs text-gray-600">
                      weight: {rel.weight.toFixed(1)}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Provenance timeline */}
      {provenance.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Provenance</h2>
          <div className="relative pl-6 border-l-2 border-gray-700 space-y-4">
            {provenance.map((rec) => (
              <div key={rec.id} className="relative">
                {/* Timeline dot */}
                <div className="absolute -left-[25px] top-1 w-3 h-3 rounded-full bg-indigo-500 border-2 border-gray-900" />
                <div className="card">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <ProvenanceActionBadge action={rec.action} />
                      <span className="text-sm text-gray-400">by {rec.actor}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatDate(rec.timestamp)}
                    </span>
                  </div>
                  {rec.confidence_delta !== 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      Confidence delta: {rec.confidence_delta > 0 ? "+" : ""}
                      {rec.confidence_delta.toFixed(2)}
                    </div>
                  )}
                  {Object.keys(rec.details).length > 0 && (
                    <pre className="text-xs text-gray-500 mt-2 overflow-x-auto">
                      {JSON.stringify(rec.details, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default EntityDetailPage;

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    active: "bg-emerald-500/20 text-emerald-300",
    superseded: "bg-amber-500/20 text-amber-300",
    archived: "bg-gray-600/20 text-gray-400",
    deleted: "bg-red-500/20 text-red-300",
  };
  const cls = colorMap[status] ?? "bg-gray-600/20 text-gray-400";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function ProvenanceActionBadge({ action }: { action: string }) {
  const colorMap: Record<string, string> = {
    created: "bg-emerald-500/20 text-emerald-300",
    updated: "bg-blue-500/20 text-blue-300",
    referenced: "bg-indigo-500/20 text-indigo-300",
    contradicted: "bg-red-500/20 text-red-300",
    superseded: "bg-amber-500/20 text-amber-300",
    merged: "bg-purple-500/20 text-purple-300",
  };
  const cls = colorMap[action] ?? "bg-gray-600/20 text-gray-400";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {action}
    </span>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listEntities, type Stats, type Entity } from "../api";
import { entityTypeColor, formatDate } from "../utils";

function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<Entity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, r] = await Promise.all([
          getStats(),
          listEntities({ limit: 10 }),
        ]);
        if (!cancelled) {
          setStats(s);
          setRecent(r);
        }
      } catch (err) {
        if (!cancelled) setError(String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Entities" value={stats.entities} color="indigo" />
          <StatCard label="Events" value={stats.events} color="emerald" />
          <StatCard label="Relationships" value={stats.relationships} color="amber" />
          <StatCard label="Embeddings" value={stats.vector_embeddings} color="rose" />
        </div>
      )}

      {/* Recent entities */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Entities</h2>
          <Link to="/search" className="text-sm text-indigo-400 hover:text-indigo-300">
            View all &rarr;
          </Link>
        </div>

        {recent.length === 0 ? (
          <div className="card text-center text-gray-500 py-12">
            No entities yet. Start ingesting data to see them here.
          </div>
        ) : (
          <div className="space-y-3">
            {recent.map((entity) => (
              <Link
                key={entity.id}
                to={`/entity/${encodeURIComponent(entity.id)}`}
                className="card block hover:bg-gray-750 hover:ring-1 hover:ring-gray-700 transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${entityTypeColor(entity.entity_type)}`}
                      >
                        {entity.entity_type}
                      </span>
                      {entity.project && (
                        <span className="text-xs text-gray-500">{entity.project}</span>
                      )}
                    </div>
                    <h3 className="font-medium truncate">{entity.title}</h3>
                    {entity.content && (
                      <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                        {entity.content.slice(0, 200)}
                      </p>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 whitespace-nowrap">
                    {formatDate(entity.created_at)}
                  </div>
                </div>
                {entity.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {entity.tags.map((tag) => (
                      <span key={tag} className="text-xs bg-gray-700 text-gray-300 rounded px-1.5 py-0.5">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    indigo: "text-indigo-400 bg-indigo-400/10",
    emerald: "text-emerald-400 bg-emerald-400/10",
    amber: "text-amber-400 bg-amber-400/10",
    rose: "text-rose-400 bg-rose-400/10",
  };
  const cls = colorMap[color] ?? colorMap.indigo;

  return (
    <div className="card">
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${cls.split(" ")[0]}`}>
        {value.toLocaleString()}
      </p>
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="card border border-red-800 text-red-400">
      <p className="font-medium">Error</p>
      <p className="text-sm mt-1">{message}</p>
    </div>
  );
}

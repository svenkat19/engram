import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { searchEntities, type SearchResult, type SearchResponse } from "../api";
import { entityTypeColor, formatDate, truncate } from "../utils";
import { LoadingSpinner, ErrorBanner } from "./DashboardPage";

function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [meta, setMeta] = useState<{ total: number; duration_ms: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const doSearch = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      const q = query.trim();
      if (!q) return;
      setLoading(true);
      setError(null);
      try {
        const res: SearchResponse = await searchEntities(q, {
          limit: 50,
          include_relationships: true,
        });
        setResults(res.results);
        setMeta({ total: res.total, duration_ms: res.duration_ms });
        setSearched(true);
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    },
    [query],
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Search</h1>

      {/* Search form */}
      <form onSubmit={doSearch} className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search entities..."
          className="input-field flex-1"
          autoFocus
        />
        <button type="submit" disabled={loading} className="btn-primary whitespace-nowrap">
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <ErrorBanner message={error} />}

      {/* Results metadata */}
      {meta && (
        <p className="text-sm text-gray-500">
          {meta.total} result{meta.total !== 1 ? "s" : ""} in {meta.duration_ms.toFixed(1)}ms
        </p>
      )}

      {/* Loading */}
      {loading && <LoadingSpinner />}

      {/* Results */}
      {!loading && searched && results.length === 0 && (
        <div className="card text-center text-gray-500 py-12">
          No results found for &ldquo;{query}&rdquo;.
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          {results.map(({ entity, score }) => (
            <Link
              key={entity.id}
              to={`/entity/${encodeURIComponent(entity.id)}`}
              className="card block hover:ring-1 hover:ring-gray-700 transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${entityTypeColor(entity.entity_type)}`}
                    >
                      {entity.entity_type}
                    </span>
                    <ScoreBadge score={score} />
                    {entity.project && (
                      <span className="text-xs text-gray-500">{entity.project}</span>
                    )}
                  </div>
                  <h3 className="font-medium">{entity.title}</h3>
                  {entity.content && (
                    <p className="text-sm text-gray-400 mt-1">
                      {truncate(entity.content, 300)}
                    </p>
                  )}
                </div>
                <div className="text-right text-xs text-gray-500 whitespace-nowrap">
                  <div>{formatDate(entity.created_at)}</div>
                  <div className="mt-1">imp: {(entity.importance * 100).toFixed(0)}%</div>
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
    </div>
  );
}

export default SearchPage;

function ScoreBadge({ score }: { score: number }) {
  const pct = (score * 100).toFixed(0);
  let cls = "text-gray-400 bg-gray-700/50";
  if (score >= 0.8) cls = "text-emerald-300 bg-emerald-500/20";
  else if (score >= 0.5) cls = "text-amber-300 bg-amber-500/20";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {pct}%
    </span>
  );
}

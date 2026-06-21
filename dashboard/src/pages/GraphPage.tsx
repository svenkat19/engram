import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import * as d3Force from "d3-force";
import * as d3Selection from "d3-selection";
import { listEntities, getRelationships, type Entity, type Relationship } from "../api";
import { entityTypeNodeColor } from "../utils";
import { LoadingSpinner, ErrorBanner } from "./DashboardPage";

// ---------------------------------------------------------------------------
// Types for the D3 simulation
// ---------------------------------------------------------------------------

interface GraphNode extends d3Force.SimulationNodeDatum {
  id: string;
  entity_type: string;
  title: string;
  importance: number;
}

interface GraphLink extends d3Force.SimulationLinkDatum<GraphNode> {
  relation_type: string;
  weight: number;
}

// ---------------------------------------------------------------------------
// GraphPage
// ---------------------------------------------------------------------------

function GraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);

  // Keep a ref to the simulation so we can stop it on unmount
  const simRef = useRef<d3Force.Simulation<GraphNode, GraphLink> | null>(null);

  const buildGraph = useCallback(
    async (width: number, height: number) => {
      if (!svgRef.current) return;

      try {
        const [entities, relationships] = await Promise.all([
          listEntities({ limit: 200 }),
          getRelationships({ limit: 500 }),
        ]);

        const entityMap = new Map<string, Entity>();
        entities.forEach((e) => entityMap.set(e.id, e));

        // Build nodes
        const nodes: GraphNode[] = entities.map((e) => ({
          id: e.id,
          entity_type: e.entity_type,
          title: e.title,
          importance: e.importance,
        }));

        // Build links (only include edges where both endpoints exist)
        const links: GraphLink[] = relationships
          .filter((r) => entityMap.has(r.source_id) && entityMap.has(r.target_id))
          .map((r) => ({
            source: r.source_id,
            target: r.target_id,
            relation_type: r.relation_type,
            weight: r.weight,
          }));

        setNodeCount(nodes.length);
        setEdgeCount(links.length);

        // Clear existing
        const svg = d3Selection.select(svgRef.current);
        svg.selectAll("*").remove();

        // Root group for zoom/pan
        const g = svg.append("g");

        // Zoom behavior
        const zoom = d3Selection
          .select(svgRef.current)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          .call(
            // d3-zoom is not in our deps but we can implement pan/zoom via d3-selection events
            // For simplicity, we skip zoom and just center the graph
            () => {},
          );
        void zoom;

        // Arrow marker for directed edges
        svg
          .append("defs")
          .append("marker")
          .attr("id", "arrowhead")
          .attr("viewBox", "0 -5 10 10")
          .attr("refX", 20)
          .attr("refY", 0)
          .attr("markerWidth", 6)
          .attr("markerHeight", 6)
          .attr("orient", "auto")
          .append("path")
          .attr("d", "M0,-5L10,0L0,5")
          .attr("fill", "#4b5563");

        // Links
        const linkSelection = g
          .append("g")
          .selectAll<SVGLineElement, GraphLink>("line")
          .data(links)
          .join("line")
          .attr("stroke", "#4b5563")
          .attr("stroke-width", (d) => Math.max(0.5, d.weight))
          .attr("stroke-opacity", 0.6)
          .attr("marker-end", "url(#arrowhead)");

        // Link labels
        const linkLabel = g
          .append("g")
          .selectAll<SVGTextElement, GraphLink>("text")
          .data(links)
          .join("text")
          .text((d) => d.relation_type.replace(/_/g, " "))
          .attr("font-size", 8)
          .attr("fill", "#6b7280")
          .attr("text-anchor", "middle")
          .attr("dy", -4);

        // Nodes
        const nodeSelection = g
          .append("g")
          .selectAll<SVGCircleElement, GraphNode>("circle")
          .data(nodes)
          .join("circle")
          .attr("r", (d) => 4 + d.importance * 12)
          .attr("fill", (d) => entityTypeNodeColor(d.entity_type))
          .attr("stroke", "#1f2937")
          .attr("stroke-width", 1.5)
          .attr("cursor", "pointer")
          .on("click", (_event, d) => {
            navigate(`/entity/${encodeURIComponent(d.id)}`);
          });

        // Node labels
        const nodeLabel = g
          .append("g")
          .selectAll<SVGTextElement, GraphNode>("text")
          .data(nodes)
          .join("text")
          .text((d) => d.title.length > 24 ? d.title.slice(0, 22) + "..." : d.title)
          .attr("font-size", 10)
          .attr("fill", "#d1d5db")
          .attr("dx", (d) => 6 + d.importance * 12)
          .attr("dy", 4)
          .attr("pointer-events", "none");

        // Tooltips
        nodeSelection.append("title").text((d) => `${d.title}\nType: ${d.entity_type}\nImportance: ${(d.importance * 100).toFixed(0)}%`);

        // Drag behavior
        function dragStarted(event: d3Force.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
          if (!event.active) sim.alphaTarget(0.3).restart();
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        }
        function dragged(event: d3Force.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        }
        function dragStopped(event: d3Force.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
          if (!event.active) sim.alphaTarget(0);
          event.subject.fx = null;
          event.subject.fy = null;
        }

        // We need d3-drag which is not in our deps, so we'll handle it via
        // mousedown/mousemove/mouseup on the SVG manually instead.
        // For a cleaner solution without adding d3-drag, we skip drag and
        // just let nodes settle.
        void dragStarted;
        void dragged;
        void dragStopped;

        // Simulation
        const sim = d3Force
          .forceSimulation<GraphNode, GraphLink>(nodes)
          .force(
            "link",
            d3Force
              .forceLink<GraphNode, GraphLink>(links)
              .id((d) => d.id)
              .distance(80),
          )
          .force("charge", d3Force.forceManyBody().strength(-200))
          .force("center", d3Force.forceCenter(width / 2, height / 2))
          .force("collision", d3Force.forceCollide<GraphNode>().radius((d) => 8 + d.importance * 12))
          .on("tick", () => {
            linkSelection
              .attr("x1", (d) => (d.source as GraphNode).x ?? 0)
              .attr("y1", (d) => (d.source as GraphNode).y ?? 0)
              .attr("x2", (d) => (d.target as GraphNode).x ?? 0)
              .attr("y2", (d) => (d.target as GraphNode).y ?? 0);

            linkLabel
              .attr("x", (d) =>
                (((d.source as GraphNode).x ?? 0) + ((d.target as GraphNode).x ?? 0)) / 2,
              )
              .attr("y", (d) =>
                (((d.source as GraphNode).y ?? 0) + ((d.target as GraphNode).y ?? 0)) / 2,
              );

            nodeSelection
              .attr("cx", (d) => d.x ?? 0)
              .attr("cy", (d) => d.y ?? 0);

            nodeLabel
              .attr("x", (d) => d.x ?? 0)
              .attr("y", (d) => d.y ?? 0);
          });

        simRef.current = sim;
        setLoading(false);
      } catch (err) {
        setError(String(err));
        setLoading(false);
      }
    },
    [navigate],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    buildGraph(rect.width, rect.height);

    return () => {
      simRef.current?.stop();
    };
  }, [buildGraph]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Knowledge Graph</h1>
        <div className="text-sm text-gray-500">
          {nodeCount} nodes &middot; {edgeCount} edges
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <div ref={containerRef} className="flex-1 card relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        )}
        <svg
          ref={svgRef}
          className="w-full h-full"
          style={{ minHeight: 400 }}
        />
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-400">
        {[
          ["commit", "#3b82f6"],
          ["decision", "#f59e0b"],
          ["conversation", "#14b8a6"],
          ["document", "#10b981"],
          ["person", "#0ea5e9"],
          ["project", "#6366f1"],
          ["concept", "#d946ef"],
          ["issue", "#ef4444"],
        ].map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

export default GraphPage;

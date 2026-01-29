
import React, { useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import * as d3 from 'd3';

interface CodeGraphViewerProps {
    graphData: { nodes: any[], edges?: any[], links?: any[] } | null;
    width?: number;
    height?: number;
}

const CodeGraphViewer: React.FC<CodeGraphViewerProps> = ({ graphData, width = 600, height = 400 }) => {
    const graphRef = useRef<any>();
    const isFirstZoom = useRef(true);

    // Compatibility: map edges to links if needed
    const data = React.useMemo(() => {
        if (!graphData) return { nodes: [], links: [] };
        return {
            nodes: graphData.nodes.map(node => ({ ...node })), // Shallow copy to prevent mutation issues
            links: (graphData.links || graphData.edges || []).map((link: any) => ({ ...link }))
        };
    }, [graphData]);

    useEffect(() => {
        if (graphRef.current) {
            // Enhance forces for card layout
            // Adjusted for Fixed World Size (12px font base)
            graphRef.current.d3Force('charge').strength(-300);
            // Link distance should be > 2x Card Radius (80 * 2 = 160) + extra spacing
            graphRef.current.d3Force('link').distance(250).strength(0.05); // Relaxed stiffness
            // Add collision force with iterations for stability
            graphRef.current.d3Force('collide', d3.forceCollide(85).iterations(3));

            // Reheat simulation
            graphRef.current.d3ReheatSimulation();
        }
    }, [data]);

    if (!data.nodes || data.nodes.length === 0) {
        return (
            <div className="flex items-center justify-center p-8 bg-gray-50 border border-gray-200 rounded-lg" style={{ width, height }}>
                <span className="text-gray-500">Loading Graph...</span>
            </div>
        );
    }

    // Zoom to fit only once when engine stops
    const handleEngineStop = () => {
        if (graphRef.current && isFirstZoom.current) {
            graphRef.current.zoomToFit(400, 20);
            isFirstZoom.current = false;
        }
    };

    const getNodeColor = (type: string) => {
        switch (type) {
            case 'entry_point': return '#10B981'; // Green
            case 'logic': return '#3B82F6'; // Blue
            case 'data': return '#6B7280'; // Grey
            case 'config': return '#F59E0B'; // Orange
            default: return '#9CA3AF';
        }
    };

    // ... (rest of render functions)

    // Custom Node Renderer - Rich Card
    const paintNode = (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
        // ... (keep existing paintNode implementation, just context for match)
        const label = node.name || node.label || node.id;
        const type = node.type ? node.type.toUpperCase() : 'UNKNOWN';

        // Metrics
        const loc = node.val ? `${((node.val || 0) * 10).toFixed(0)} Score` : 'N/A';
        const density = node.density ? `Density: ${(node.density * 100).toFixed(0)}%` : 'Density: 0%';
        const reason = node.reason ? node.reason.replace(/_/g, ' ') : 'Analysis';

        const color = getNodeColor(node.type);

        // FIXED WORLD SIZE - Removed globalScale dependency
        // This ensures visual size matches physics collider size
        const titleFontSize = 12;
        const metaFontSize = 10;
        const reasonFontSize = 8;

        ctx.font = `bold ${titleFontSize}px Sans-Serif`;
        const textWidth = ctx.measureText(label).width;

        // Card Dimensions
        const cardWidth = Math.max(textWidth + 20, 140);
        const cardHeight = titleFontSize * 5.0 + metaFontSize * 3;
        const radius = 6;

        // 1. Draw Shadow
        ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
        ctx.shadowBlur = 6;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;

        // 2. Draw Card Background
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.roundRect(node.x - cardWidth / 2, node.y - cardHeight / 2, cardWidth, cardHeight, radius);
        ctx.fill();

        // Reset Shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;

        // 3. Draw Header Bar (Type Color)
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(node.x - cardWidth / 2, node.y - cardHeight / 2, cardWidth, titleFontSize * 1.5, [radius, radius, 0, 0]);
        ctx.fill();

        // 4. Draw Type Label (in Header)
        ctx.font = `bold ${metaFontSize}px Sans-Serif`;
        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(type, node.x - cardWidth / 2 + 6, node.y - cardHeight / 2 + titleFontSize * 0.75);

        // 5. Draw File Name (Body)
        ctx.font = `bold ${titleFontSize}px Sans-Serif`;
        ctx.fillStyle = '#1F2937'; // Gray 800
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, node.x, node.y - cardHeight / 2 + titleFontSize * 2.5);

        // 6. Draw Metrics (Footer area)
        ctx.font = `${metaFontSize}px Sans-Serif`;
        ctx.fillStyle = '#6B7280'; // Gray 500
        ctx.textAlign = 'center';
        const metricsY = node.y + cardHeight / 2 - metaFontSize * 2.2;
        ctx.fillText(`${loc} • ${density}`, node.x, metricsY);

        // 7. Reason (Why Selected)
        ctx.font = `italic ${reasonFontSize}px Sans-Serif`;
        ctx.fillStyle = '#9CA3AF'; // Lighter gray
        ctx.fillText(`Why: ${reason}`, node.x, node.y + cardHeight / 2 - reasonFontSize * 0.8);

        // 8. Border (Visual definition)
        ctx.strokeStyle = color;
        ctx.lineWidth = 1; // Fixed width
        ctx.beginPath();
        ctx.roundRect(node.x - cardWidth / 2, node.y - cardHeight / 2, cardWidth, cardHeight, radius);
        ctx.stroke();

        // Interaction area
        node.__bckgDimensions = [cardWidth + 10, cardHeight + 10]; // Padding for easier grabbing
    };

    // Custom Link Renderer (Edge Labels)
    const paintLink = (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
        const start = link.source;
        const end = link.target;

        // Ignore if positions aren't calculated yet
        if (typeof start !== 'object' || typeof end !== 'object' || !start.x || !end.x) return;

        // Draw Line
        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.strokeStyle = '#94A3B8'; // Slate 400
        ctx.lineWidth = 1.5; // Fixed width
        ctx.stroke();

        // Draw Arrow (Manual calculation since we override rendering)
        // ... Or simpler: use default link rendering but add a Label using linkCanvasObject?
        // Actually, linkCanvasObject REPLACES default rendering. So we must draw line + arrow + label.

        // Calculate mid point
        const midX = start.x + (end.x - start.x) * 0.5;
        const midY = start.y + (end.y - start.y) * 0.5;

        // Draw Label "imports" - ONLY SHOW IF ZOOM LEVEL IS SUFFICIENT
        // Or keep it fixed size. Fixed size labels can clutter. 
        // Let's keep labels fixed size for consistency but small.

        const labelText = "imports";
        const fontSize = 8; // Fixed
        ctx.font = `${fontSize}px Sans-Serif`;
        const textWidth = ctx.measureText(labelText).width;

        // Label Background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(midX - textWidth / 2 - 2, midY - fontSize / 2 - 2, textWidth + 4, fontSize + 4);

        // Label Text
        ctx.fillStyle = '#64748B'; // Slate 500
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labelText, midX, midY);

        // We can skip manual arrow drawing if we rely on linkDirectionalArrow... 
        // BUT force-graph says: "if linkCanvasObject is defined, it takes precedence". 
        // So we lose built-in arrows if we use this.
        // Strategy: Don't use linkCanvasObject for *lines*, use `linkCanvasObjectMode` to draw *on top*?
        // No, `linkCanvasObjectMode` options are 'replace', 'before', 'after'.
        // Perfect! We can use 'after' to draw the label ON TOP of the default line/arrow.
    };

    return (
        <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50 shadow-sm">
            <ForceGraph2D
                ref={graphRef}
                width={width}
                height={height}
                graphData={data}

                // Custom Node Rendering
                nodeCanvasObject={paintNode}
                nodeCanvasObjectMode={() => 'replace'}

                // Link Styling (Default Line + Arrow)
                linkColor={() => '#94A3B8'}
                linkWidth={1.5}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={0.5} // Arrow in middle
                linkCurvature={0.2}

                // Custom Link Label (Draw AFTER default link)
                linkCanvasObject={paintLink}
                linkCanvasObjectMode={() => 'after'}

                // Interaction
                onNodeDragEnd={node => {
                    node.fx = node.x;
                    node.fy = node.y;
                }}
                cooldownTicks={100}
                onEngineStop={handleEngineStop}

                backgroundColor="#F8FAFC"
            />
        </div>
    );
};

export default CodeGraphViewer;

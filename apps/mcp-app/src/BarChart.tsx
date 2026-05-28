import type { TrendPoint } from "./types";

type Props = {
  points: TrendPoint[];
  width?: number;
  height?: number;
};

export function BarChart({ points, width = 320, height = 140 }: Props) {
  if (points.length === 0) {
    return (
      <div className="chart-empty" style={{ width, height }}>
        No trend data yet.
      </div>
    );
  }

  const max = Math.max(...points.map((p) => p.value), 1);

  const padX = 8;
  const padY = 8;
  const labelArea = 14;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2 - labelArea;

  const gap = 6;
  const barW = Math.max(
    1,
    (innerW - gap * (points.length - 1)) / points.length,
  );

  return (
    <svg
      className="chart"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Dashboard trend bar chart"
    >
      <rect x={0} y={0} width={width} height={height} className="chart-bg" />
      {points.map((p, i) => {
        const x = padX + i * (barW + gap);
        const barH = (p.value / max) * innerH;
        const y = padY + innerH - barH;
        return (
          <g key={`${p.label}-${i}`}>
            <rect
              x={x}
              y={y}
              width={barW}
              height={barH}
              className="chart-bar"
              rx={2}
            />
            <text
              x={x + barW / 2}
              y={height - 2}
              className="chart-label"
              textAnchor="middle"
            >
              {p.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

import type { HistoryPoint } from "./App";

type Props = {
  history: HistoryPoint[];
  width?: number;
  height?: number;
};

export function Chart({ history, width = 320, height = 120 }: Props) {
  if (history.length === 0) {
    return (
      <div className="chart-empty" style={{ width, height }}>
        No data yet — click +1 to start.
      </div>
    );
  }

  const values = history.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const padX = 8;
  const padY = 8;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;

  const points = history
    .map((p, i) => {
      const x = padX + (history.length === 1 ? innerW / 2 : (i / (history.length - 1)) * innerW);
      const y = padY + innerH - ((p.value - min) / range) * innerH;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg
      className="chart"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Counter history line chart"
    >
      <rect x={0} y={0} width={width} height={height} className="chart-bg" />
      <polyline points={points} className="chart-line" fill="none" />
      {history.map((p, i) => {
        const x = padX + (history.length === 1 ? innerW / 2 : (i / (history.length - 1)) * innerW);
        const y = padY + innerH - ((p.value - min) / range) * innerH;
        return <circle key={`${p.ts}-${i}`} cx={x} cy={y} r={2.5} className="chart-dot" />;
      })}
    </svg>
  );
}

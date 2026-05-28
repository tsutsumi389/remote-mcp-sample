import { useState, type FormEvent } from "react";

import type { YoutubeSearchResults, YoutubeVideo } from "./types";

type Props = {
  data: YoutubeSearchResults;
  isConnected: boolean;
  busy: boolean;
  error: string | null;
  callTool: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
  applyResult: (structuredContent: unknown) => void;
};

const SEARCH_LIMIT = 12;

function formatViews(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M views`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(0)}K views`;
  return `${count} views`;
}

function formatPublished(epochSeconds: number): string {
  // Server stores seconds; Date wants milliseconds.
  return new Date(epochSeconds * 1000).toLocaleDateString();
}

// Deterministic placeholder thumbnail derived from the video's hue. Keeps the
// bundle self-contained (no outbound image fetch) while still looking distinct
// per video — a soft diagonal gradient plus a centered play glyph.
function Thumbnail({ hue, title }: { hue: number; title: string }) {
  const from = `hsl(${hue}, 55%, 52%)`;
  const to = `hsl(${(hue + 40) % 360}, 60%, 38%)`;
  const gradientId = `yt-grad-${hue}`;
  return (
    <svg
      className="youtube-thumb"
      viewBox="0 0 320 180"
      role="img"
      aria-label={`Thumbnail for ${title}`}
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={from} />
          <stop offset="100%" stopColor={to} />
        </linearGradient>
      </defs>
      <rect width="320" height="180" fill={`url(#${gradientId})`} />
      <circle cx="160" cy="90" r="34" fill="rgba(0, 0, 0, 0.35)" />
      <path d="M150 73 L150 107 L178 90 Z" fill="#ffffff" />
    </svg>
  );
}

function VideoCard({ video }: { video: YoutubeVideo }) {
  return (
    <article className="youtube-card">
      <Thumbnail hue={video.thumbnail_hue} title={video.title} />
      <div className="youtube-card-body">
        <h2 className="youtube-card-title">{video.title}</h2>
        <p className="youtube-card-channel">{video.channel}</p>
        <p className="youtube-card-meta">
          {formatViews(video.view_count)} · {formatPublished(video.published_at)}
        </p>
      </div>
    </article>
  );
}

export function YoutubeScreen({
  data,
  isConnected,
  busy,
  error,
  callTool,
  applyResult,
}: Props) {
  const [draft, setDraft] = useState(data.query ?? "");
  const disabled = busy || !isConnected;

  const run = async (name: string, args?: Record<string, unknown>) => {
    applyResult(await callTool(name, args));
  };

  const onSearch = async (event: FormEvent) => {
    event.preventDefault();
    await run("search_youtube", { query: draft.trim(), limit: SEARCH_LIMIT });
  };

  return (
    <main className="main main-wide">
      <header className="header">
        <h1 className="heading">YouTube Search</h1>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>

      <form className="task-form" onSubmit={onSearch}>
        <input
          className="task-input"
          type="text"
          placeholder="Search videos… (e.g. python, music, ramen)"
          value={draft}
          disabled={disabled}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" className="btn" disabled={disabled}>
          Search
        </button>
      </form>

      <p className="muted">
        {data.total_count === 0
          ? "No results"
          : `${data.results.length} of ${data.total_count} result${
              data.total_count === 1 ? "" : "s"
            }`}
        {data.query ? ` for “${data.query}”` : ""}
      </p>

      {data.results.length === 0 ? (
        <section className="value-card">
          <p className="muted">No videos match — try another keyword.</p>
        </section>
      ) : (
        <section className="youtube-grid">
          {data.results.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </section>
      )}

      {error && <p className="error">{error}</p>}
    </main>
  );
}

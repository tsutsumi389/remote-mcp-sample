import type { ArticleDetail } from "./types";

type Props = {
  data: ArticleDetail;
  isConnected: boolean;
  busy: boolean;
  error: string | null;
  callTool: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
  applyResult: (structuredContent: unknown) => void;
};

function formatPublished(epochSeconds: number): string {
  // Server stores seconds; Date wants milliseconds.
  return new Date(epochSeconds * 1000).toLocaleDateString();
}

export function ArticleDetailScreen({
  data,
  isConnected,
  busy,
  error,
  callTool,
  applyResult,
}: Props) {
  const disabled = busy || !isConnected;

  const run = async (name: string, args?: Record<string, unknown>) => {
    applyResult(await callTool(name, args));
  };

  // Split the body into paragraphs on blank lines so the server can ship plain
  // text and the UI still renders readable blocks.
  const paragraphs = data.body.split(/\n{2,}/).filter((p) => p.trim().length > 0);

  return (
    <main className="main main-wide">
      <header className="header">
        <button
          type="button"
          className="btn btn-ghost btn-small"
          disabled={disabled}
          onClick={() => run("list_articles")}
        >
          ← Back to list
        </button>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>

      <article className="article-detail">
        <h1 className="article-detail-title">{data.title}</h1>
        <p className="article-card-meta">
          {data.author} · {formatPublished(data.published_at)}
        </p>
        {data.tags.length > 0 && (
          <ul className="article-tags">
            {data.tags.map((tag) => (
              <li key={tag} className="article-tag">
                {tag}
              </li>
            ))}
          </ul>
        )}
        <div className="article-body">
          {paragraphs.map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      </article>

      {error && <p className="error">{error}</p>}
    </main>
  );
}

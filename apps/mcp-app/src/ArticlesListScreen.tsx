import type { ArticleList, ArticleSummary } from "./types";

type Props = {
  data: ArticleList;
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

function ArticleCard({
  article,
  disabled,
  onOpen,
}: {
  article: ArticleSummary;
  disabled: boolean;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      className="article-card"
      disabled={disabled}
      onClick={onOpen}
    >
      <h2 className="article-card-title">{article.title}</h2>
      <p className="article-card-meta">
        {article.author} · {formatPublished(article.published_at)}
      </p>
      {article.tags.length > 0 && (
        <ul className="article-tags">
          {article.tags.map((tag) => (
            <li key={tag} className="article-tag">
              {tag}
            </li>
          ))}
        </ul>
      )}
    </button>
  );
}

export function ArticlesListScreen({
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

  return (
    <main className="main main-wide">
      <header className="header">
        <h1 className="heading">Articles</h1>
        <span className="muted">{isConnected ? "connected" : "connecting…"}</span>
      </header>

      <p className="muted">
        {data.articles.length} article{data.articles.length === 1 ? "" : "s"} —
        select one to read.
      </p>

      {data.articles.length === 0 ? (
        <section className="value-card">
          <p className="muted">No articles available.</p>
        </section>
      ) : (
        <section className="article-list">
          {data.articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              disabled={disabled}
              onOpen={() => run("get_article_detail", { article_id: article.id })}
            />
          ))}
        </section>
      )}

      {error && <p className="error">{error}</p>}
    </main>
  );
}

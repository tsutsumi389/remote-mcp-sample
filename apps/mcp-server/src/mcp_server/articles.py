"""Articles sample: tools + UI resource for the list → detail MCP App screens.

This is the fifth sample alongside Counter / Tasks / Dashboard / YouTube. It is
the first one to demonstrate **screen navigation** (a list view drilling into a
detail view) inside a single MCP App. The mechanism reuses the existing routing
design unchanged: the React App picks a screen by the *shape* of the structured
content it receives, so two tools that return two differently-shaped payloads
naturally drive two screens.

- ``list_articles`` returns an ``ArticleList`` (rows without a ``body``) → the
  React App renders the list screen.
- ``get_article_detail`` returns an ``ArticleDetail`` (one article *with* a
  ``body``) → the React App renders the detail screen.

Clicking a card on the list calls ``get_article_detail``; the detail screen's
"back" button calls ``list_articles``. Both tools carry
``_meta["ui/resourceUri"] = "ui://articles"`` and the ``ui://articles`` resource
reuses the *same* single-file bundle as the other screens
(``resources.read_bundle()``).

Data is a read-only, in-memory mock (no external access). Publish dates are
fixed epoch seconds so the catalog is deterministic across restarts.
"""

from __future__ import annotations

import threading

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from mcp_server.resources import UI_RESOURCE_MIME, read_bundle

UI_ARTICLES_RESOURCE_URI = "ui://articles"
ARTICLES_UI_META: dict = {"ui/resourceUri": UI_ARTICLES_RESOURCE_URI}


class ArticleSummary(BaseModel):
    """A row in the list view — intentionally has no ``body``.

    The absence of ``body`` is what lets the React type guard tell an
    ``ArticleList`` apart from an ``ArticleDetail``.
    """

    id: str
    title: str
    author: str
    published_at: float  # seconds since epoch, like HistoryPoint.ts
    tags: list[str] = Field(default_factory=list)


class ArticleDetail(ArticleSummary):
    """A single article with its full ``body`` — backs the detail view."""

    body: str


class ArticleList(BaseModel):
    articles: list[ArticleSummary] = Field(default_factory=list)


# Read-only mock catalog. Each entry is a full ArticleDetail; the list view
# projects these down to ArticleSummary (dropping `body`). Publish dates are
# fixed epoch seconds (UTC) so the sample is deterministic.
_SEED_ARTICLES: tuple[ArticleDetail, ...] = (
    ArticleDetail(
        id="mcp-apps-intro",
        title="MCP Apps 入門：ツール結果を画面に映す",
        author="Aoi Tanaka",
        published_at=1704067200.0,  # 2024-01-01
        tags=["mcp", "tutorial"],
        body=(
            "MCP Apps は、MCP ツールの実行結果を専用の UI として表示する仕組みです。\n\n"
            "サーバーはツールの戻り値を構造化データ（structuredContent）として返し、"
            "ホストはそれを iframe に読み込んだ単一ファイル HTML へ渡します。\n\n"
            "この記事ではカウンターの例を題材に、ツールと UI リソースを結びつける"
            "最小構成を確認します。"
        ),
    ),
    ArticleDetail(
        id="single-bundle-routing",
        title="1 つのバンドルで複数画面を出し分ける",
        author="Ken Sato",
        published_at=1706745600.0,  # 2024-02-01
        tags=["architecture", "react"],
        body=(
            "本サンプルでは Counter / Tasks / Dashboard / YouTube / Articles の"
            "すべてが同じ単一ファイルバンドルを共有しています。\n\n"
            "ontoolresult 通知は解決済みリソース URI を確実には含まないため、"
            "React 側は受け取った structuredContent の『形』を型ガードで判定し、"
            "表示する画面を切り替えます。\n\n"
            "この設計は画面遷移（一覧→詳細）にもそのまま使えます。"
        ),
    ),
    ArticleDetail(
        id="list-to-detail",
        title="一覧から詳細へ：画面遷移パターン",
        author="Mio Kobayashi",
        published_at=1709251200.0,  # 2024-03-01
        tags=["mcp", "ux"],
        body=(
            "一覧画面でカードをクリックすると get_article_detail を呼び、"
            "サーバーが本文付きの ArticleDetail を返します。\n\n"
            "一覧の ArticleList とは形が異なるため、フロントは自動的に詳細画面へ"
            "切り替わります。戻るボタンは list_articles を呼ぶだけです。\n\n"
            "新しいツールを 1 つ足すだけでナビゲーションが成立する点が要点です。"
        ),
    ),
    ArticleDetail(
        id="structured-content",
        title="Pydantic モデルと structuredContent",
        author="Aoi Tanaka",
        published_at=1711929600.0,  # 2024-04-01
        tags=["python", "fastmcp"],
        body=(
            "FastMCP はツールの戻り値型（Pydantic モデル）から JSON 出力スキーマを"
            "生成し、CallToolResult.structuredContent を自動で埋めます。\n\n"
            "サーバー側でモデルを定義しておけば、フロントは型安全にデータを"
            "受け取れます。\n\n"
            "ArticleSummary と ArticleDetail のように、継承でフィールドを足すだけで"
            "一覧用と詳細用のスキーマを使い分けられます。"
        ),
    ),
    ArticleDetail(
        id="theme-following",
        title="ホストのテーマに追従する UI",
        author="Ken Sato",
        published_at=1714521600.0,  # 2024-05-01
        tags=["css", "react"],
        body=(
            "ホストは onhostcontextchanged でテーマ（light/dark）やセーフエリアを"
            "通知します。\n\n"
            "App はそれを document.documentElement.dataset.theme に反映し、"
            "CSS 変数で配色を切り替えます。\n\n"
            "単一ファイルバンドルでも、ホストの見た目に自然になじむ UI を"
            "作れます。"
        ),
    ),
    ArticleDetail(
        id="local-dev-loop",
        title="ローカル開発ループ：build と preview",
        author="Mio Kobayashi",
        published_at=1717200000.0,  # 2024-06-01
        tags=["vite", "workflow"],
        body=(
            "mcp-app は vite-plugin-singlefile で単一ファイルにビルドされ、"
            "vite preview で配信されます。\n\n"
            "MCP サーバーは resources/read のたびにその HTML を HTTP で取得して"
            "インラインで返すため、build --watch の変更がそのまま反映されます。\n\n"
            "make serve-app と make serve-server を並べて起動すれば、保存するだけで"
            "画面に反映される開発ループが得られます。"
        ),
    ),
)


class ArticleStore:
    """Thread-safe, read-only article catalog.

    ``list()`` returns ``ArticleSummary`` rows (no ``body``); ``get()`` returns
    the full ``ArticleDetail``. Snapshots are fresh copies so callers can never
    mutate the seed data.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._articles: tuple[ArticleDetail, ...] = ()
        self._seed()

    def _seed(self) -> None:
        with self._lock:
            self._articles = tuple(a.model_copy(deep=True) for a in _SEED_ARTICLES)

    def list(self) -> ArticleList:
        with self._lock:
            summaries = [
                ArticleSummary(
                    id=a.id,
                    title=a.title,
                    author=a.author,
                    published_at=a.published_at,
                    tags=list(a.tags),
                )
                for a in self._articles
            ]
        return ArticleList(articles=summaries)

    def get(self, article_id: str) -> ArticleDetail:
        with self._lock:
            for article in self._articles:
                if article.id == article_id:
                    return article.model_copy(deep=True)
        raise ValueError(f"Unknown article id: {article_id!r}")

    def reset(self) -> None:
        self._seed()


article_store = ArticleStore()


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="list_articles",
        description=(
            "Return the article list (summaries without body). Backs the list "
            "screen; the UI calls this again to navigate back from a detail."
        ),
        meta=ARTICLES_UI_META,
    )
    def list_articles() -> ArticleList:
        return article_store.list()

    @mcp.tool(
        name="get_article_detail",
        description=(
            "Return the full article (with body) for the given `article_id`. "
            "Backs the detail screen. Unknown ids raise an error."
        ),
        meta=ARTICLES_UI_META,
    )
    def get_article_detail(article_id: str) -> ArticleDetail:
        return article_store.get(article_id)

    @mcp.resource(
        UI_ARTICLES_RESOURCE_URI,
        name="Articles App UI",
        description="Single-file HTML bundle for the Articles MCP App (shared bundle).",
        mime_type=UI_RESOURCE_MIME,
    )
    def articles_ui() -> str:
        return read_bundle()

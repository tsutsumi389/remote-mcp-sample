# Remote MCP Sample — Python FastAPI + FastMCP + React MCP App

リモート MCP サーバー（FastAPI 上に FastMCP の Streamable HTTP をマウント）と、その上で動く **MCP App**（ホスト内 iframe で動くインタラクティブ UI）を一つにまとめた最小モノレポサンプルです。サーバーは FastAPI ベースなので、MCP の `POST /mcp` に加えて通常の HTTP リクエスト（`GET /health` など）も受け付けます。

本サンプルには **3 つの画面** が含まれ、いずれも「サーバーの構造化データ（`structuredContent`）を MCP App 画面に連携して表示する」パターンを示します。3 画面は **同一の単一ファイルバンドル** を共有し、受信データの形に応じて React 側が画面を切り替えます。

### 1. カウンター + 履歴チャート（`ui://counter`）

- モデル（LLM）が `increment_counter` ツールを呼ぶ → 値が増え、UI iframe が描画される
- ユーザーが UI 上のボタンを押す → `callServerTool` 経由でサーバーの `increment_counter` / `reset_counter` を呼ぶ
- 双方向通信、ホストテーマ追従、`_meta.ui.resourceUri` リンクが一通り見られます

### 2. タスク一覧テーブル（`ui://tasks`）

- `list_tasks` がサーバーの `TaskList`（行データ）を返す → 画面がテーブルとして表示
- UI のフォームから `add_task`、チェックボックスから `toggle_task` を呼び、返ってきた `TaskList` で再描画
- 「サーバー → 画面のデータ連携」を表形式で分かりやすく示す追加サンプルです

### 3. ダッシュボード（KPI + トレンド + アクティビティ）（`ui://dashboard`）

- `get_dashboard` がサーバーの `Dashboard`（KPIカード × 4 + 7 バケットのトレンド + アクティビティ一覧）を返す → 画面が複合ウィジェットとして表示
- 「Refresh」ボタンから `refresh_dashboard` を呼ぶと、KPI 値とトレンドが決定論的に更新されて再描画
- アクティビティ行の「Ack」ボタンから `acknowledge_alert` を呼ぶと該当行が消える（未知 ID は no-op）
- 「1 回のツール呼び出しで複合 UI を駆動する」集約スナップショット型のパターンを示します

### 4. YouTube 検索（`ui://youtube`）

- 画面の検索ボックスに入力 → `search_youtube` を呼ぶ → サーバーが（モックの）動画カタログをキーワードで絞り込み、再生回数順に並べた `YoutubeSearchResults` を返す → 画面がサムネイル付きの動画カード一覧として表示
- データは API キー不要のインメモリ・モックです（実際の YouTube へはアクセスしません）。空クエリは全件を返します
- サムネイルは外部画像取得を避けるため、各動画の `thumbnail_hue` から決定論的に生成するインライン SVG プレースホルダです
- 「ユーザー入力 → ツール呼び出し → 構造化データ受信 → 一覧描画」という検索 UI 型のパターンを示します

## アーキテクチャ

```
MCP Host (basic-host / Claude Desktop / etc.)
  └─ iframe: React MCP App (single-file HTML bundle / srcdoc 描画)
        │ callServerTool / tool result
        ▼
HTTP  http://localhost:3001
  └─ Python Server (FastAPI + uvicorn)
        ├─ GET  /health           → {"status":"ok"}（通常の HTTP リクエスト）
        ├─ GET  /docs, /openapi.json → FastAPI 自動ドキュメント
        └─ POST /mcp (Streamable HTTP) → FastMCP をマウント
              ├─ tools: increment_counter / reset_counter / get_counter
              │   ※ 各ツールに _meta["ui/resourceUri"] = "ui://counter"
              ├─ tools: list_tasks / add_task / toggle_task
              │   ※ 各ツールに _meta["ui/resourceUri"] = "ui://tasks"
              ├─ tools: get_dashboard / refresh_dashboard / acknowledge_alert
              │   ※ 各ツールに _meta["ui/resourceUri"] = "ui://dashboard"
              ├─ tools: search_youtube
              │   ※ ツールに _meta["ui/resourceUri"] = "ui://youtube"
              ├─ resource: ui://counter   (text/html;profile=mcp-app)
              ├─ resource: ui://tasks     (text/html;profile=mcp-app)
              ├─ resource: ui://dashboard (text/html;profile=mcp-app)
              └─ resource: ui://youtube   (text/html;profile=mcp-app)
                    │ resources/read のたびに HTTP で取得して中継（インライン返却）
                    ▼
HTTP  http://mcp-app:4173/ (host: http://localhost:4173/)
  └─ MCP App 配信サーバ (vite preview)
        └─ apps/mcp-app/dist/index.html を配信
              ※ ui://counter / ui://tasks / ui://dashboard / ui://youtube は同じ単一ファイルを返す
```

HTML の**配信責務は mcp-app 側**（`vite preview`）にあります。MCP Apps SDK はインライン HTML のみ対応（ホストは `resource.contents[0].text` を iframe `srcdoc` で描画し、アプリの URL から直接ロードできない）ため、Python サーバはその HTML を HTTP で取得してインラインで**中継**します。

## リポジトリ構成

```
.
├── apps/
│   ├── mcp-server/   # Python: FastAPI + FastMCP (Streamable HTTP)
│   └── mcp-app/      # React: MCP Apps SDK (@modelcontextprotocol/ext-apps)
├── docker-compose.yml
├── Makefile
├── pnpm-workspace.yaml
├── package.json
└── pyproject.toml    # uv workspace
```

## 前提

- Docker / Docker Compose
- （ホスト直接ビルド用）Node.js 22+ + [pnpm](https://pnpm.io/) / Python 3.12+ + [uv](https://docs.astral.sh/uv/)

## クイックスタート (Docker)

```bash
make dev
```

- `mcp-app` コンテナが `pnpm serve`（初回ビルド → `vite build --watch` + `vite preview`）で `dist/index.html` を `http://mcp-app:4173/` に配信。ホストからは `http://localhost:4173/`（ループバック公開）で閲覧可
- `mcp-server` コンテナ（FastAPI + uvicorn）が `--reload` で起動。リソース取得時に `MCP_APP_BUNDLE_URL`（既定 `http://mcp-app:4173/`）から HTML を中継。MCP は `http://localhost:3001/mcp`、ヘルスチェックは `http://localhost:3001/health` で待ち受け

MCP ホストの設定で、Streamable HTTP の URL に `http://localhost:3001/mcp` を追加してください。

### ホスト直接ビルド

```bash
make install    # pnpm install + uv sync
make build      # apps/mcp-app/dist/index.html 生成
make test       # Python ユニットテスト
```

Docker を使わず 2 ターミナルで動かす場合（中継方式）:

```bash
# ターミナル1: MCP App を :4173 で配信（初回ビルド → watch + preview）
make serve-app

# ターミナル2: MCP サーバを起動（:4173 から HTML を中継）
make serve-server   # MCP_APP_BUNDLE_URL=http://localhost:4173/ を自動設定
```

## 動作確認

### 0. ヘルスチェック (curl)

FastAPI の通常エンドポイント。MCP ハンドシェイク不要で叩けます:

```bash
curl -s http://localhost:3001/health
# => {"status":"ok"}
```

FastAPI の自動ドキュメントは `http://localhost:3001/docs`（Swagger UI）で確認できます。

### 1. ツール一覧を確認 (curl)

`tools/list` で `_meta.ui.resourceUri` が含まれていることをチェック:

```bash
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### 2. UI リソースを確認

```bash
# Counter 画面のバンドル
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"ui://counter"}}'

# Tasks 画面のバンドル（同じ HTML が返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"ui://tasks"}}'

# Dashboard 画面のバンドル（同じ HTML が返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"ui://dashboard"}}'

# YouTube 検索画面のバンドル（同じ HTML が返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":5,"method":"resources/read","params":{"uri":"ui://youtube"}}'
```

レスポンスの `contents[0].text` が `<!doctype html>` で始まる単一ファイル HTML になっていれば OK です。`ui://counter` / `ui://tasks` / `ui://dashboard` / `ui://youtube` は同一バンドルを返します（画面の出し分けは React 側がデータ形で判定）。

### 2-1. タスク一覧のデータ連携を確認

```bash
# 一覧取得（シード済みタスクが返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"list_tasks","arguments":{}}}'

# 追加 → 返却された structuredContent.tasks に行が増える
#   {"name":"add_task","arguments":{"title":"Buy milk"}}
# 完了トグル（一覧の id を指定）
#   {"name":"toggle_task","arguments":{"id":1}}
```

### 2-2. ダッシュボードのデータ連携を確認

```bash
# 集約スナップショット取得（KPI 4 件 + 7 バケットトレンド + アクティビティ 3 件）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"get_dashboard","arguments":{}}}'

# Refresh → KPI 値とトレンド末尾が決定論的に更新される
#   {"name":"refresh_dashboard","arguments":{}}
# 個別アラート既読化（structuredContent.activity の id を指定）
#   {"name":"acknowledge_alert","arguments":{"alert_id":"act-1"}}
```

### 2-3. YouTube 検索のデータ連携を確認

```bash
# キーワード検索（structuredContent.results が再生回数順で返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"search_youtube","arguments":{"query":"python"}}}'

# 空クエリ → 全件返却（limit で件数を制限）
#   {"name":"search_youtube","arguments":{"query":"","limit":5}}
```

> 注: 素の curl での `tools/call` は Streamable HTTP セッションの初期化が必要な場合があります。確実に往復を確認したいときは `make test`（pytest, インプロセス実行）か basic-host を使ってください。

### 3. MCP ホストから接続

#### basic-host で確認する場合

[`modelcontextprotocol/ext-apps`](https://github.com/modelcontextprotocol/ext-apps) リポジトリに含まれる `examples/basic-host` を使うと、ブラウザ上で MCP App を試せます。

```bash
# 別ディレクトリで
git clone --depth 1 https://github.com/modelcontextprotocol/ext-apps.git
cd ext-apps/examples/basic-host
npm install
SERVERS='["http://localhost:3001/mcp"]' npm run start
# http://localhost:8080 を開く
```

#### Claude Desktop など他ホストで確認する場合

各ホストの設定 UI から Streamable HTTP MCP サーバーとして `http://localhost:3001/mcp` を登録してください。

## ホットリロード

| 変更 | 反映方法 |
|------|---------|
| Python ファイル | `uvicorn --reload` が自動再起動 |
| React (`apps/mcp-app/src/**`) | `vite build --watch` が `dist/index.html` を更新 → `vite preview` が配信 → サーバーが再フェッチして反映。ホストでツール再呼び出し（or リソース再フェッチ）すれば反映され、両サービスの再起動は不要 |

## 設計上の注意

- **状態は in-memory のみ**: マルチプロセス・再起動で値が消えます。永続化は学習の発展課題として残しています。
- **認証なし**: ローカル開発専用。リモート公開時は OAuth2.1 等を別途追加してください。
- **MCP Apps `_meta`**: ツール定義の `_meta["ui/resourceUri"]` がリソースに対応する HTML を指定します（キーは `@modelcontextprotocol/ext-apps` の `RESOURCE_URI_META_KEY` 定数と同一）。本サンプルでは `FastMCP.tool(..., meta={"ui/resourceUri": "ui://counter"})` / `"ui://tasks"` / `"ui://dashboard"` / `"ui://youtube"` を利用しています。
- **リソース MIME**: `text/html;profile=mcp-app`（同パッケージの `RESOURCE_MIME_TYPE` 定数）。
- **配信は mcp-app 側 / サーバは中継**: HTML を配信するのは mcp-app の `vite preview`（`MCP_APP_BUNDLE_URL`）です。Python サーバは `resources/read` のたびに HTTP で取得してインライン返却します（接続不可・タイムアウト・非200・サイズ超過時は安全なプレースホルダ HTML にフォールバック）。
- **単一ファイルが必須な理由**: `@modelcontextprotocol/ext-apps` はインライン HTML のみ対応で、ホストは `resource.contents[0].text` を iframe `srcdoc` で描画します。外部 URL からの読み込みができないため、サーバが返す HTML は自己完結している必要があり、ビルドは単一ファイル（`vite-plugin-singlefile`）のままにしています。
- **1 バンドル × 複数画面**: Counter / Tasks / Dashboard / YouTube は同じ単一ファイルバンドルを共有します。`ontoolresult` 通知は解決済みリソース URI を確実には含まないため、React 側（`App.tsx`）は受信した `structuredContent` の形（型ガード `isCounterData` / `isTaskList` / `isDashboard` / `isYoutubeSearchResults`）で表示画面を切り替えます。最初のツール結果が来るまでは中立な「読み込み中」画面を表示します。
- **データ連携の要点**: ツールは Pydantic モデル（`CounterSnapshot` / `TaskList` / `Dashboard` / `YoutubeSearchResults`）を返し、FastMCP が `CallToolResult.structuredContent` を自動生成。React 側は `ontoolresult` / `callServerTool` の `structuredContent` を読んで描画します。サーバー実装は `apps/mcp-server/src/mcp_server/tasks.py` / `dashboard.py` / `youtube.py` を参照。

## 拡張ヒント

- 複数 MCP App: `ui://other` リソースを増やし、別ツール群に `_meta.ui.resourceUri` を設定（Tasks / Dashboard / YouTube 画面が実例。`apps/mcp-server/src/mcp_server/tasks.py` / `dashboard.py` / `youtube.py` + `apps/mcp-app/src/TasksScreen.tsx` / `DashboardScreen.tsx` / `YoutubeScreen.tsx`）
- 永続化: `state.py` を SQLite / Redis 接続に差し替え
- 認証: FastAPI のミドルウェア / 依存（`Depends`）を MCP マウント（`app.mount("/", ...)`）の前段に挟む。`/health` など公開ルートだけ認証から除外する構成も可能
- 通常の REST API 追加: `server.py` の FastAPI `app` に `@app.get(...)` / `APIRouter` を足すだけ（MCP は `POST /mcp` のまま共存）
- ストリーミング入力: 大きな入力を扱うツールに `ontoolinputpartial` ハンドラを追加（[shadertoy 例](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/shadertoy-server) 参照）

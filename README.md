# Remote MCP Sample — Python FastAPI + FastMCP + React MCP App

リモート MCP サーバー（FastAPI 上に FastMCP の Streamable HTTP をマウント）と、その上で動く **MCP App**（ホスト内 iframe で動くインタラクティブ UI）を一つにまとめた最小モノレポサンプルです。サーバーは FastAPI ベースなので、MCP の `POST /mcp` に加えて通常の HTTP リクエスト（`GET /health` など）も受け付けます。

本サンプルには **2 つの画面** が含まれ、どちらも「サーバーの構造化データ（`structuredContent`）を MCP App 画面に連携して表示する」パターンを示します。両画面は **同一の単一ファイルバンドル** を共有し、受信データの形に応じて React 側が画面を切り替えます。

### 1. カウンター + 履歴チャート（`ui://counter`）

- モデル（LLM）が `increment_counter` ツールを呼ぶ → 値が増え、UI iframe が描画される
- ユーザーが UI 上のボタンを押す → `callServerTool` 経由でサーバーの `increment_counter` / `reset_counter` を呼ぶ
- 双方向通信、ホストテーマ追従、`_meta.ui.resourceUri` リンクが一通り見られます

### 2. タスク一覧テーブル（`ui://tasks`）

- `list_tasks` がサーバーの `TaskList`（行データ）を返す → 画面がテーブルとして表示
- UI のフォームから `add_task`、チェックボックスから `toggle_task` を呼び、返ってきた `TaskList` で再描画
- 「サーバー → 画面のデータ連携」を表形式で分かりやすく示す追加サンプルです

## アーキテクチャ

```
MCP Host (basic-host / Claude Desktop / etc.)
  └─ iframe: React MCP App (single-file HTML bundle)
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
              ├─ resource: ui://counter (text/html;profile=mcp-app)
              └─ resource: ui://tasks   (text/html;profile=mcp-app)
                    ※ どちらも同じ apps/mcp-app/dist/index.html を返す
```

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

- `mcp-app` コンテナが `pnpm build:watch` で `dist/index.html` を継続生成
- `mcp-server` コンテナ（FastAPI + uvicorn）が `--reload` で起動。MCP は `http://localhost:3001/mcp`、ヘルスチェックは `http://localhost:3001/health` で待ち受け

MCP ホストの設定で、Streamable HTTP の URL に `http://localhost:3001/mcp` を追加してください。

### ホスト直接ビルド

```bash
make install    # pnpm install + uv sync
make build      # apps/mcp-app/dist/index.html 生成
make test       # Python ユニットテスト
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
```

レスポンスの `contents[0].text` が `<!doctype html>` で始まる単一ファイル HTML になっていれば OK です。`ui://counter` と `ui://tasks` は同一バンドルを返します（画面の出し分けは React 側がデータ形で判定）。

### 2-1. タスク一覧のデータ連携を確認

```bash
# 一覧取得（シード済みタスクが返る）
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_tasks","arguments":{}}}'

# 追加 → 返却された structuredContent.tasks に行が増える
#   {"name":"add_task","arguments":{"title":"Buy milk"}}
# 完了トグル（一覧の id を指定）
#   {"name":"toggle_task","arguments":{"id":1}}
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
| React (`apps/mcp-app/src/**`) | `vite build --watch` が `dist/index.html` を更新。ホストでツールを再呼び出し（or リソースを再フェッチ）すると反映 |

## 設計上の注意

- **状態は in-memory のみ**: マルチプロセス・再起動で値が消えます。永続化は学習の発展課題として残しています。
- **認証なし**: ローカル開発専用。リモート公開時は OAuth2.1 等を別途追加してください。
- **MCP Apps `_meta`**: ツール定義の `_meta["ui/resourceUri"]` がリソースに対応する HTML を指定します（キーは `@modelcontextprotocol/ext-apps` の `RESOURCE_URI_META_KEY` 定数と同一）。本サンプルでは `FastMCP.tool(..., meta={"ui/resourceUri": "ui://counter"})` / `"ui://tasks"` を利用しています。
- **リソース MIME**: `text/html;profile=mcp-app`（同パッケージの `RESOURCE_MIME_TYPE` 定数）。
- **1 バンドル × 複数画面**: Counter / Tasks は同じ単一ファイルバンドルを共有します。`ontoolresult` 通知は解決済みリソース URI を確実には含まないため、React 側（`App.tsx`）は受信した `structuredContent` の形（型ガード `isCounterData` / `isTaskList`）で表示画面を切り替えます。最初のツール結果が来るまでは中立な「読み込み中」画面を表示します。
- **データ連携の要点**: ツールは Pydantic モデル（`CounterSnapshot` / `TaskList`）を返し、FastMCP が `CallToolResult.structuredContent` を自動生成。React 側は `ontoolresult` / `callServerTool` の `structuredContent` を読んで描画します。サーバー実装は `apps/mcp-server/src/mcp_server/tasks.py` を参照。

## 拡張ヒント

- 複数 MCP App: `ui://other` リソースを増やし、別ツール群に `_meta.ui.resourceUri` を設定（Tasks 画面が実例。`apps/mcp-server/src/mcp_server/tasks.py` + `apps/mcp-app/src/TasksScreen.tsx`）
- 永続化: `state.py` を SQLite / Redis 接続に差し替え
- 認証: FastAPI のミドルウェア / 依存（`Depends`）を MCP マウント（`app.mount("/", ...)`）の前段に挟む。`/health` など公開ルートだけ認証から除外する構成も可能
- 通常の REST API 追加: `server.py` の FastAPI `app` に `@app.get(...)` / `APIRouter` を足すだけ（MCP は `POST /mcp` のまま共存）
- ストリーミング入力: 大きな入力を扱うツールに `ontoolinputpartial` ハンドラを追加（[shadertoy 例](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/shadertoy-server) 参照）

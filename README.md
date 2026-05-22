# Remote MCP Sample — Python FastMCP + React MCP App

リモート MCP サーバー（Streamable HTTP）と、その上で動く **MCP App**（ホスト内 iframe で動くインタラクティブ UI）を一つにまとめた最小モノレポサンプルです。

題材は **カウンター + 履歴チャート**:

- モデル（LLM）が `increment_counter` ツールを呼ぶ → 値が増え、UI iframe が描画される
- ユーザーが UI 上のボタンを押す → `callServerTool` 経由でサーバーの `increment_counter` / `reset_counter` を呼ぶ
- 双方向通信、ホストテーマ追従、`_meta.ui.resourceUri` リンクが一通り見られます

## アーキテクチャ

```
MCP Host (basic-host / Claude Desktop / etc.)
  └─ iframe: React MCP App (single-file HTML bundle)
        │ callServerTool / tool result
        ▼
Streamable HTTP  http://localhost:3001/mcp
  └─ Python MCP Server (FastMCP + uvicorn)
        ├─ tools: increment_counter / reset_counter / get_counter
        │   ※ 各ツールに _meta["ui/resourceUri"] = "ui://counter"
        └─ resource: ui://counter (text/html;profile=mcp-app)
              → apps/mcp-app/dist/index.html を返す
```

## リポジトリ構成

```
.
├── apps/
│   ├── mcp-server/   # Python: FastMCP + Streamable HTTP
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
- `mcp-server` コンテナが `uvicorn ... --reload` で起動し、`http://localhost:3001/mcp` で待ち受け

MCP ホストの設定で、Streamable HTTP の URL に `http://localhost:3001/mcp` を追加してください。

### ホスト直接ビルド

```bash
make install    # pnpm install + uv sync
make build      # apps/mcp-app/dist/index.html 生成
make test       # Python ユニットテスト
```

## 動作確認

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
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"ui://counter"}}'
```

レスポンスの `contents[0].text` が `<!doctype html>` で始まる単一ファイル HTML になっていれば OK です。

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
- **MCP Apps `_meta`**: ツール定義の `_meta["ui/resourceUri"]` がリソースに対応する HTML を指定します（キーは `@modelcontextprotocol/ext-apps` の `RESOURCE_URI_META_KEY` 定数と同一）。本サンプルでは `FastMCP.tool(..., meta={"ui/resourceUri": "ui://counter"})` を利用しています。
- **リソース MIME**: `text/html;profile=mcp-app`（同パッケージの `RESOURCE_MIME_TYPE` 定数）。

## 拡張ヒント

- 複数 MCP App: `ui://other` リソースを増やし、別ツール群に `_meta.ui.resourceUri` を設定
- 永続化: `state.py` を SQLite / Redis 接続に差し替え
- 認証: `Starlette` ミドルウェアを `streamable_http_app()` の前段に挟む
- ストリーミング入力: 大きな入力を扱うツールに `ontoolinputpartial` ハンドラを追加（[shadertoy 例](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/shadertoy-server) 参照）

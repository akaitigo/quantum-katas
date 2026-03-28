# quantum-katas — CLAUDE.md

## プロジェクト概要

量子コンピューティングの基礎をカタ形式で学べるWebアプリ。
モノレポ構成: `backend/` (Python/FastAPI/Cirq) + `frontend/` (TypeScript/React/Monaco Editor)

## コマンド

```bash
# Backend
cd backend && ruff check src/ tests/           # lint
cd backend && ruff format src/ tests/           # format
cd backend && pytest                             # test
cd backend && pytest tests/test_foo.py -k name   # 単一テスト

# Frontend
cd frontend && npx biome check src/             # lint
cd frontend && npx biome format --write src/    # format
cd frontend && npm test                          # test
```

## コーディング規約

### Python (backend/)
- **Ruff** でlint + format。pyproject.toml に全設定あり
- 型ヒント必須（`-> None` 含む）
- `Any` 型は避け、`Unknown` パターンまたはジェネリクスを使う
- テストは `tests/` 配下、pytest を使用
- Cirq の量子回路コードは型安全に書く

### TypeScript (frontend/)
- **Biome** でlint + format
- `any` 型禁止 → `unknown` + 型ガードまたはジェネリクス
- `as` 型アサーション最小限
- React コンポーネントは関数コンポーネント + hooks
- パスエイリアス: `@/*` → `./src/*`

## セキュリティ注意事項

- ユーザー入力のPythonコードは **サンドボックス内で実行** すること
- 実行時間制限（タイムアウト）を必ず設定
- ファイルシステムアクセス・ネットワークアクセスを制限
- `.env` ファイルをコミットしない

# quantum-katas — アーキテクチャ概要

## システム構成

```
[Browser]
   |
   | HTTP (REST API)
   |
[Frontend: React + Monaco Editor]  -- port 5173
   |
   | POST /api/execute
   | POST /api/katas/{id}/check
   | GET  /api/katas
   |
[Backend: FastAPI]  -- port 8000
   |
   | Python in-process
   |
[Cirq Simulator]  -- 量子回路シミュレーション
```

## バックエンド設計 (backend/)

### モジュール構成
```
src/quantum_katas/
├── __init__.py
├── main.py              # FastAPI app, CORS, ルーター登録
├── routers/
│   ├── katas.py         # GET /katas, GET /katas/{id}
│   └── execute.py       # POST /execute
├── models/
│   ├── kata.py          # Kata, KataStep, Hint データモデル
│   └── execution.py     # ExecutionRequest, ExecutionResult
├── services/
│   ├── executor.py      # サンドボックスコード実行
│   └── judge.py         # 正解判定ロジック
└── data/
    └── katas/           # カタ定義 (YAML or JSON)
        ├── 01_hello_qubit.yaml
        ├── 02_not_gate.yaml
        └── ...
```

### API エンドポイント
| Method | Path | 説明 |
|--------|------|------|
| GET | /api/katas | カタ一覧取得 |
| GET | /api/katas/{id} | カタ詳細取得 |
| POST | /api/execute | Pythonコード実行 |
| POST | /api/katas/{id}/check | 正解判定 |

### セキュリティ: コード実行サンドボックス
- `subprocess` + タイムアウト（15秒 — Cirq import に ~8s かかるため）
- `import` ホワイトリスト: cirq, numpy, math のみ（AST検査 + ラ��タイムガード）
- ダンダー属性アクセスブロック（`__class__`, `__bases__`, `__globals__` 等 — オブジェクトグラフ脱出防止）
- ファイルI/O・ネットワーク禁止
- メモリ制限: RLIMIT_AS 1GB
- 同時実行制限: セマフォ（最大3プロセス）
- validation_code はユーザーコ��ドと同一名前空間で���行（共有変数で正確な採点）
- validation_code は API レスポンスから除外

## フロントエンド設計 (frontend/)

### コンポーネント構成
```
src/
├── components/
│   ├── KataList.tsx        # カタ一覧
│   ├── KataDetail.tsx      # カタ詳細（説明 + エディタ + 結果）
│   ├── CodeEditor.tsx      # Monaco Editor ラッパー
│   ├── ResultDisplay.tsx   # 実行結果表示（ヒストグラム等）
│   ├── HintPanel.tsx       # ヒント表示パネル
│   └── ProgressBar.tsx     # 進捗バー
├── hooks/
│   ├── useKatas.ts         # カタデータ取得
│   ├── useExecution.ts     # コード実行
│   └── useProgress.ts     # 進捗管理（localStorage）
├── lib/
│   ├── api.ts              # APIクライアント
│   └── constants.ts        # 定数
└── types/
    ├── kata.ts             # カタ関連型
    └── execution.ts        # 実行関連型
```

### 状態管理
- React hooks + Context（軽量、Zustand不要の規模）
- 進捗データは localStorage に永続化

## データフロー

1. ユーザーがカタを選択 → `GET /api/katas/{id}` でカタデータ取得
2. 穴埋めテンプレートをMonaco Editorに表示
3. ユーザーがコードを編集 → 「実行」ボタン押下
4. `POST /api/execute` でバックエンドにコード送信
5. Cirqシミュレーター実行 → 測定結果を返却
6. フロントエンドでヒストグラム表示
7. `POST /api/katas/{id}/check` で正解判定
8. 正解なら進捗更新（localStorage）

## 決定事項

- Cirq を選択（Google製、Pythonネイティブ、シミュレーター内蔵）
- Qiskit は将来的な拡張候補だがMVPでは対象外
- コード実行はバックエンド側（ブラウザ内Python実行は信頼性の問題）

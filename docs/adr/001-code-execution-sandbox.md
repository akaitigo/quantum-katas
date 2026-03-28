# ADR-001: コード実行サンドボックスの設計判断

## ステータス

Accepted

## コンテキスト

quantum-katas はユーザーが入力した Python (Cirq) コードをサーバーサイドで実行する必要がある。任意コード実行はセキュリティ上の最大リスクであり、適切なサンドボックス設計が不可欠である。

以下の選択肢を検討した:

| 手法 | メリット | デメリット |
|------|---------|-----------|
| A: subprocess + import ホワイトリスト | シンプル、依存なし、デバッグ容易 | OS レベル隔離なし |
| B: Docker コンテナ | 完全な OS レベル隔離 | オーバーヘッド大、Cold start 問題 |
| C: WebAssembly (Pyodide) | クライアントサイド実行、サーバー不要 | Cirq 非対応、パッケージ制約 |
| D: gVisor / Firecracker | 強力なサンドボックス | インフラ複雑性、運用コスト |

## 決定

**手法 A: subprocess + 多層防御** を採用する。

### 防御レイヤー

1. **AST レベル import 検証**: `ast.walk()` でインポート文を解析し、ホワイトリスト (`cirq`, `numpy`, `math`) 以外を拒否
2. **危険な組み込み関数の無効化**: `open`, `exec`, `eval`, `compile`, `__import__` 等をサンドボックス builtins から除外
3. **ガード付き `__import__`**: ランタイムの `import` もホワイトリストで制限
4. **subprocess 隔離**: `subprocess.run()` で子プロセスとして実行。`shell=False` でシェルインジェクション防止
5. **タイムアウト制御**: 5 秒の実行時間制限で無限ループ・リソース枯渇を防止

### 制限されるもの

- ファイル I/O (`open` 無効化)
- ネットワークアクセス (`socket`, `urllib` 等のインポート不可)
- OS コマンド実行 (`os`, `subprocess` のインポート不可)
- 動的コード生成 (`exec`, `eval`, `compile` 無効化)

## 結果

### ポジティブ

- 追加インフラ不要で MVP に適切なセキュリティレベルを確保
- レスポンスタイム良好 (Docker の Cold start 問題なし)
- テスト・デバッグが容易 (通常の pytest で検証可能)
- 76 テスト中 5 件がサンドボックスセキュリティ専用テスト

### リスク・将来の改善

- **P1**: 本番環境では Docker コンテナ or gVisor による OS レベル隔離の追加を検討
- **P2**: メモリ制限 (`ulimit`) の導入
- **P2**: ネットワーク名前空間隔離の追加
- **P3**: CPU 使用率制限 (cgroups)

### 関連コード

- `backend/src/quantum_katas/services/executor.py` — サンドボックス実行エンジン
- `backend/tests/test_executor.py` — 実行エンジンテスト
- `backend/tests/test_judge.py::TestSandboxSecurity` — セキュリティテスト

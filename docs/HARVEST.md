# Harvest: quantum-katas

> 日付: 2026-03-28
> パイプライン: Launch → Scaffold → Build → Harden → Ship → **Harvest**

## テンプレートの実戦評価

### 使えたもの
- [x] Makefile (backend-check/frontend-check/check) — 毎PRで使用、CI と同等チェック
- [x] CI YAML (.github/workflows/ci.yml) — 全PR+pushで自動実行、**CI失敗0回**
- [x] CLAUDE.md — ルール・コマンド定義が効果的。Python+TS双方のコマンドを一覧化
- [x] ADR テンプレート — 001 (コード実行サンドボックス) でセキュリティ判断を記録
- [x] biome.json (Layer-1 TypeScript) — lint/format 統合、テンプレートから適用
- [x] Ruff 設定 (pyproject.toml) — Layer-1 Python として初適用。セキュリティルール(S)含む厳格設定
- [x] startup.sh — 配置済み。Python/TS/lefthook の自動検出・インストール機能あり
- [x] **PostToolUse Hooks (settings.json)** — **初めて設定・動作した**。Edit/Write 時に ruff 自動lint
- [x] **settings.json 自動生成** — **初めて適用**。hooks 設定が scaffold 時に配置された
- [x] 品質チェックリスト — CI全グリーン + テスト130件で実質達成

### 使えなかったもの
| ファイル | 理由 |
|---------|------|
| lefthook | lefthook 未インストール（startup.sh 未実行のため） |
| startup.sh | 配置したが実行しなかった。3PJ連続の構造的問題 |
| session-end.sh | 未配置。不要と判断された |
| CONTEXT.json | 生成せず。git log で代替（3PJ連続で不使用） |
| progress.json | 生成せず。同上 |
| quality-override.md | 未配置。quality-checklist.md + CI で十分 |

## 今回初めて適用された改善の評価

### 1. PostToolUse Hooks 自動注入 — 効果あり

| 項目 | 評価 |
|------|------|
| 設定 | `.claude/settings.json` に hooks 定義が配置された |
| 動作 | Edit/Write 実行時に `post-lint.sh` が自動実行 |
| 効果 | Python ファイル編集時に ruff が自動で lint+fix を実行 |
| 結論 | **3PJ目で初めて Hooks が機能した。テンプレート改善の効果を実証** |

Guardian/Podflow では `settings.json` が未配置で hooks が動かなかった。今回は scaffold 時に自動生成されたことで、手動設定なしに hooks が機能した。

### 2. settings.json 自動生成 — 効果あり

Scaffold 時に `.claude/settings.json` が自動配置され、hooks の「設定する動機がない」問題を解決した。これが Hooks 動作の前提条件であり、最も効果的な改善だった。

### 3. startup.sh コピー — 効果なし（3PJ連続で未実行）

配置はされたが実行されなかった。ツールの自動インストール（ruff, lefthook 等）が行われず、lefthook が動かない原因になった。ただし、ruff は dev 依存として pip install 時にインストールされるため、Python PJ では影響が小さかった。

**結論**: startup.sh は「配置するだけ」では不十分。idea-work スキルの Step 3 冒頭にハードコードするか、Hooks で初回自動実行する仕組みが必要。

### 4. CONTEXT.json — 不要と確定

3PJ連続で不使用。git log + GitHub Issues で十分な状態管理ができている。テンプレートから削除を推奨。

## Python テンプレート（Layer-1）の実戦評価

| 項目 | 評価 |
|------|------|
| Ruff 設定 | 非常に良好。pyproject.toml に lint/format/pytest/coverage を統合 |
| ルール選択 | 厳格だが実用的。セキュリティ(S), 型注釈(ANN), 複雑度(C90) を含む |
| per-file-ignores | テストファイルで assert/型注釈を緩和。実用的な設定 |
| coverage | 80% 閾値を設定。レビュー修正後 96% を達成 |
| 全体評価 | **Go テンプレートと同等以上の品質**。Python PJ の標準として十分 |

## コード実行サンドボックスのセキュリティ設計評価

| 防御レイヤー | 実装 | テスト | 評価 |
|-------------|------|--------|------|
| AST import 検証 | ホワイトリスト方式 | あり | MVP として適切 |
| 組み込み関数無効化 | open/exec/eval 等を除外 | あり | 基本的な防御 |
| ガード付き __import__ | ランタイム import 制限 | あり | 二重防御として有効 |
| subprocess 隔離 | shell=False | あり | シェルインジェクション防止 |
| タイムアウト | 5秒制限 | あり | DoS 防止 |

**ADR-001 に明記されたリスク**: 本番環境では Docker/gVisor による OS レベル隔離が必要（P1）。MVP としては適切な判断。

## Guardian / Podflow との比較（3PJ共通の問題）

| 問題 | Guardian | Podflow | Quantum-Katas | 結論 |
|------|----------|---------|---------------|------|
| Hooks 設定 | ❌ 未設定 | ❌ 未設定 | ✅ **初めて動作** | settings.json 自動生成が解決策 |
| startup.sh 実行 | ❌ | ❌ | ❌ | **3PJ連続で未実行。構造的問題** |
| CONTEXT.json | ❌ 不使用 | ❌ 不使用 | ❌ 不使用 | **削除確定** |
| テンプレート実装率 | ~70% | ~80% | ~85% | **改善の効果で着実に向上** |
| CI 失敗 | 1回 (sudo) | 0回 | 0回 | CI品質は安定 |
| テスト数 | ~20件 | 69件 | 130件 | PJ規模に応じて増加 |
| ADR | 1件 | 2件 | 1件 | セキュリティ判断を適切に記録 |

### Quantum-Katas 固有の発見

| 発見 | 内容 | 対応 |
|------|------|------|
| **Python Layer-1 初検証** | Ruff 設定が効果的に機能。Go/TS と同等の品質 | テンプレートとして採用確定 |
| **Hooks 初動作** | settings.json 自動配置で 3PJ目にして初めて機能 | テンプレート改善の最重要成果 |
| **サンドボックス設計** | ADR+テスト駆動で適切なセキュリティ判断 | 学習App固有だがADR駆動設計の好例 |
| **モノレポCI** | Python+TS の2ジョブ並列。Podflow (3ジョブ) と同パターン | モノレポ CI テンプレート化を推奨 |
| **カバレッジ 96%** | 80% 閾値を達成。レビュー修正で全カタのテスト追加 | セキュリティテスト・ソリューション検証テストで網羅率向上 |

## テンプレートへの改善提案

| 提案 | 対象 | 内容 |
|------|------|------|
| CONTEXT.json 削除 | layer-0-universal | 3PJ全てで不使用。git log で代替確定 |
| progress.json 削除 | layer-0-universal | 同上 |
| session-end.sh 削除 | layer-0-universal | 同上 |
| startup.sh 自動実行 | idea-work スキル | 配置だけでは実行されない。仕組みの変更が必要 |
| モノレポ CI テンプレート | layer-2-product | Python+TS / TS+Kotlin の並列ジョブパターン |
| カバレッジ閾値の段階化 | layer-1-language | MVP=50%, Harden=80% の2段階を推奨 |

## 数値サマリ

| 指標 | 値 |
|------|-----|
| コミット数 | 7 (scaffold含む) |
| PR数 | 5 (全マージ、CI全グリーン) |
| Issue数 | 5 (全クローズ) |
| ADR | 1件 (サンドボックス設計) |
| テスト (Backend) | 76件 (pytest) |
| テスト (Frontend) | 54件 (Vitest) |
| テスト合計 | 130件 |
| CI失敗 | 0回 |
| CI実行 | 11回 (PR 5 + push 6) |
| テンプレート実装率 | ~85% |
| 品質チェックリスト | 5/5 (実質) |
| カバレッジ (Backend) | 96% (80%閾値達成) |

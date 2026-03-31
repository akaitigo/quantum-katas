# Changelog

## v1.0.0 (2026-04-01)

### Initial Release

- chore: upgrade all frontend dependencies (#33)
- fix: update stale test counts in README and add CI permissions (#32)
- chore: ruff lint/format修正 — import位置とリスト内包表記 (#31)
- fix: カタ遷移時にエディタ内容・ヒント表示数をリセット (#30)
- fix: セキュリティ脆弱性修正 — stdin経由コード実行・NPROC制限・CORS環境変数化 (#29)
- fix: 3モデルレビュー指摘対応 — 採点ロジック・サンドボックス・API漏洩修正 (#27)
- chore(deps): bump actions/checkout from 4 to 6
- chore(deps): bump actions/setup-node from 4 to 6
- chore(deps): bump pnpm/action-setup from 4 to 5
- chore(deps): bump actions/setup-python from 5 to 6
- build(deps-dev): bump jsdom from 25.0.1 to 29.0.1 in /frontend (#20)
- ci: add Dependabot auto-merge workflow
- fix: address review v2 findings
- docs: add Harvest report for quantum-katas
- docs: add real screenshots + fix mock fallback detection
- feat: ヒントシステム + 進捗トラッカー UI + テスト + ドキュメント仕上げ (#10)
- feat: Monaco Editor 統合 + コード実行・結果可視化 (#4) (#9)
- feat: React frontend foundation with kata list and detail views (#8)
- feat: add kata data model, 10-stage curriculum, and kata API endpoints (#7)
- feat: FastAPI backend foundation with sandboxed code execution engine (#6)
- Initial project scaffold for quantum-katas
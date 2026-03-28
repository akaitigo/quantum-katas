# ユースケースフロー

## UC-1: カタを選んで学習する [実装済み]

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API
    participant Sim as Cirq Simulator

    User->>FE: トップページにアクセス
    FE->>API: GET /api/katas
    API-->>FE: カタ一覧 (10件)
    FE-->>User: カタ一覧表示 (進捗バー + 完了/ロック/未完了アイコン)
    User->>FE: カタ #3 "Superposition" を選択
    FE->>API: GET /api/katas/3
    API-->>FE: カタ詳細 (解説, テンプレートコード, ヒント)
    FE-->>User: 解説 + 穴埋めエディタ表示
```

## UC-2: コードを編集して実行する [実装済み]

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API
    participant Sim as Cirq Simulator

    User->>FE: 穴埋め部分にコード入力 (Monaco Editor)
    User->>FE: 「実行」ボタン押下 or Ctrl+Enter
    FE->>API: POST /api/execute {code: "..."}
    API->>Sim: Cirq回路を構築・シミュレート
    Sim-->>API: 測定結果 {counts: {"00": 50, "11": 50}}
    API-->>FE: 実行結果 (stdout, stderr, success)
    FE-->>User: 結果表示 (回路図 + 出力)
```

## UC-3: 正解判定を受ける [実装済み]

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API

    User->>FE: 「提出」ボタン押下
    FE->>API: POST /api/katas/3/validate {code: "..."}
    API->>API: ユーザーコード実行 + 検証コード実行
    alt 正解
        API-->>FE: {passed: true, message: "Correct!"}
        FE-->>User: 正解表示 + 進捗更新
        FE->>FE: localStorage に進捗保存
        FE-->>User: 「次のカタへ」ボタン表示
    else 不正解
        API-->>FE: {passed: false, message: "..."}
        FE-->>User: 不正解表示 + エラー詳細
    end
```

## UC-4: ヒントを使う [実装済み]

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend

    User->>FE: 「Hint 1 を表示」ボタン押下
    FE->>FE: localStorage にヒント表示状態を保存
    FE-->>User: 💡 Hint 1: "アダマールゲートを使ってみましょう"
    User->>FE: ヒント1をクリック (折りたたみ/展開)
    FE-->>User: ヒント1が折りたたまれる
    User->>FE: 「Hint 2 を表示」ボタン押下
    FE-->>User: 💡 Hint 2: "cirq.H を量子ビットに適用します"
    User->>FE: 「Hint 3 を表示」ボタン押下
    FE-->>User: 💡 Hint 3: "circuit.append(cirq.H(qubit))"
    Note over FE: ヒント表示状態はページリロード後も保持される
```

## UC-5: 進捗を確認する [実装済み]

```mermaid
flowchart LR
    A[トップページ] --> B{進捗バー}
    B --> C[3/10 完了]
    C --> D[未完了カタは白丸アイコン]
    C --> E[完了カタは緑チェック]
    C --> F[前提未完了カタは南京錠アイコン]
```

## UC-6: 全クリアを達成する [実装済み]

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend

    User->>FE: 最後のカタを正解
    FE->>FE: 10/10 完了を検知
    FE-->>User: 祝福バナー "All Clear!" 表示
    User->>FE: カタ一覧に戻る
    FE-->>User: カタ一覧にも祝福バナー表示
```

## ユースケース一覧

| ID | ユースケース名 | アクター | 優先度 | ステータス |
|----|--------------|---------|--------|-----------|
| UC-1 | カタを選んで学習する | 学習者 | P0 | 実装済み |
| UC-2 | コードを編集して実行する | 学習者 | P0 | 実装済み |
| UC-3 | 正解判定を受ける | 学習者 | P0 | 実装済み |
| UC-4 | ヒントを使う | 学習者 | P1 | 実装済み |
| UC-5 | 進捗を確認する | 学習者 | P1 | 実装済み |
| UC-6 | 全クリアを達成する | 学習者 | P2 | 実装済み |

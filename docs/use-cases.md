# ユースケースフロー

## UC-1: カタを選んで学習する

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API
    participant Sim as Cirq Simulator

    User->>FE: トップページにアクセス
    FE->>API: GET /api/katas
    API-->>FE: カタ一覧 (10件)
    FE-->>User: カタ一覧表示 (進捗バー付き)
    User->>FE: カタ #3 "Superposition" を選択
    FE->>API: GET /api/katas/3
    API-->>FE: カタ詳細 (解説, テンプレートコード, ヒント)
    FE-->>User: 解説 + 穴埋めエディタ表示
```

## UC-2: コードを編集して実行する

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API
    participant Sim as Cirq Simulator

    User->>FE: 穴埋め部分にコード入力
    User->>FE: 「実行」ボタン押下
    FE->>API: POST /api/execute {code: "..."}
    API->>Sim: Cirq回路を構築・シミュレート
    Sim-->>API: 測定結果 {counts: {"00": 50, "11": 50}}
    API-->>FE: 実行結果 (ヒストグラムデータ + 状態ベクトル)
    FE-->>User: ヒストグラム表示
```

## UC-3: 正解判定を受ける

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend
    participant API as Backend API

    User->>FE: 「提出」ボタン押下
    FE->>API: POST /api/katas/3/check {code: "..."}
    API->>API: 期待出力と比較
    alt 正解
        API-->>FE: {correct: true, message: "正解!"}
        FE-->>User: 正解表示 + 進捗更新
        FE->>FE: localStorage に進捗保存
    else 不正解
        API-->>FE: {correct: false, message: "もう一度..."}
        FE-->>User: 不正解表示
    end
```

## UC-4: ヒントを使う

```mermaid
sequenceDiagram
    actor User as 学習者
    participant FE as Frontend

    User->>FE: 「ヒント」ボタン押下
    FE-->>User: ヒント1: "アダマールゲートを使ってみましょう"
    User->>FE: 「もう1つヒント」ボタン押下
    FE-->>User: ヒント2: "cirq.H を量子ビットに適用します"
    User->>FE: 「もう1つヒント」ボタン押下
    FE-->>User: ヒント3: "circuit.append(cirq.H(qubit))"
```

## UC-5: 進捗を確認する

```mermaid
flowchart LR
    A[トップページ] --> B{進捗バー}
    B --> C[3/10 完了]
    C --> D[未完了カタは灰色アイコン]
    C --> E[完了カタは緑チェック]
    C --> F[現在のカタはハイライト]
```

## ユースケース一覧

| ID | ユースケース名 | アクター | 優先度 |
|----|--------------|---------|--------|
| UC-1 | カタを選んで学習する | 学習者 | P0 |
| UC-2 | コードを編集して実行する | 学習者 | P0 |
| UC-3 | 正解判定を受ける | 学習者 | P0 |
| UC-4 | ヒントを使う | 学習者 | P1 |
| UC-5 | 進捗を確認する | 学習者 | P1 |

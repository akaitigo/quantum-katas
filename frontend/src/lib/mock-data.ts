import type { ExecutionResult } from "@/types/execution";
import type { KataDetail, KataSummary, ValidateResponse } from "@/types/kata";

export const MOCK_KATA_SUMMARIES: readonly KataSummary[] = [
  {
    id: "01-single-qubit",
    title: "量子ビットの基礎",
    difficulty: 1,
    category: "basics",
    prerequisites: [],
  },
  {
    id: "02-pauli-x-gate",
    title: "Pauli-X ゲート (NOT)",
    difficulty: 2,
    category: "basics",
    prerequisites: ["01-single-qubit"],
  },
  {
    id: "03-hadamard-gate",
    title: "アダマールゲート (H)",
    difficulty: 3,
    category: "basics",
    prerequisites: ["01-single-qubit"],
  },
  {
    id: "04-measurement-statistics",
    title: "測定と確率",
    difficulty: 4,
    category: "basics",
    prerequisites: ["03-hadamard-gate"],
  },
  {
    id: "05-pauli-z-gate",
    title: "Pauli-Z ゲート (位相反転)",
    difficulty: 5,
    category: "basics",
    prerequisites: ["03-hadamard-gate"],
  },
  {
    id: "06-multi-qubit",
    title: "複数量子ビット",
    difficulty: 6,
    category: "entanglement",
    prerequisites: ["04-measurement-statistics"],
  },
  {
    id: "07-cnot-gate",
    title: "CNOT ゲート",
    difficulty: 7,
    category: "entanglement",
    prerequisites: ["06-multi-qubit"],
  },
  {
    id: "08-bell-state",
    title: "ベル状態",
    difficulty: 8,
    category: "entanglement",
    prerequisites: ["07-cnot-gate"],
  },
  {
    id: "09-quantum-teleportation",
    title: "量子テレポーテーション",
    difficulty: 9,
    category: "algorithms",
    prerequisites: ["08-bell-state"],
  },
  {
    id: "10-deutsch-jozsa",
    title: "Deutsch-Jozsa アルゴリズム",
    difficulty: 10,
    category: "algorithms",
    prerequisites: ["08-bell-state"],
  },
];

const MOCK_KATA_DETAILS: Record<string, KataDetail> = {
  "01-single-qubit": {
    id: "01-single-qubit",
    title: "量子ビットの基礎",
    description:
      "Cirqを使って1量子ビットを作成し、測定する基本的な量子回路を構築します。\n量子コンピューティングの最も基本的な操作を学びましょう。",
    difficulty: 1,
    category: "basics",
    template_code: `import cirq

# 量子ビットを1つ作成してください
# YOUR CODE HERE

# 量子ビットを測定する回路を作成してください
# YOUR CODE HERE

# シミュレーターで回路を実行し、結果を表示してください
sim = cirq.Simulator()
# YOUR CODE HERE`,

    hints: [
      "cirq.LineQubit(0) で量子ビットを作成できます",
      "cirq.Circuit([cirq.measure(q, key='result')]) で測定回路を作成します",
      "sim.run(circuit, repetitions=10) でシミュレーションを実行し、print(result) で結果を表示します",
    ],
    prerequisites: [],
    explanation: `## 量子ビット (Qubit)

量子ビットは量子コンピューティングの基本単位です。
古典的なビット (0 or 1) と異なり、量子ビットは **重ね合わせ状態** を取ることができます。

Cirqでは \`cirq.LineQubit(0)\` で量子ビットを作成します。
初期状態は |0> であり、何もゲートを適用せずに測定すると常に 0 が返ります。`,
  },
  "02-pauli-x-gate": {
    id: "02-pauli-x-gate",
    title: "Pauli-X ゲート (NOT)",
    description:
      "Pauli-X ゲートは量子ビットの状態を反転させます。古典的な NOT ゲートの量子版です。",
    difficulty: 2,
    category: "basics",
    template_code: `import cirq

q = cirq.LineQubit(0)

# Pauli-X ゲートを適用して |0> を |1> に反転してください
circuit = cirq.Circuit([
    # YOUR CODE HERE
    cirq.measure(q, key='result'),
])

sim = cirq.Simulator()
result = sim.run(circuit, repetitions=10)
print(result)`,

    hints: [
      "cirq.X(q) で Pauli-X ゲートを適用できます",
      "X ゲートは |0> を |1> に、|1> を |0> に反転します",
      "cirq.X(q) を cirq.measure の前に追加してください",
    ],
    prerequisites: ["01-single-qubit"],
    explanation:
      "## Pauli-X ゲート\n\nPauli-X ゲートは量子ビットの NOT 操作です。",
  },
};

export function getMockKataDetail(kataId: string): KataDetail | undefined {
  const detail = MOCK_KATA_DETAILS[kataId];
  if (detail) {
    return detail;
  }

  // Generate a fallback detail from summary data
  const summary = MOCK_KATA_SUMMARIES.find((k) => k.id === kataId);
  if (!summary) {
    return undefined;
  }
  return {
    id: summary.id,
    title: summary.title,
    description: `${summary.title}に関する練習問題です。`,
    difficulty: summary.difficulty,
    category: summary.category,
    template_code: "import cirq\n\n# YOUR CODE HERE\n",

    hints: [
      "Cirq のドキュメントを参照してください",
      "量子回路の基本的なパターンを思い出してください",
      "前提カタの内容を復習してみましょう",
    ],
    prerequisites: [...summary.prerequisites],
    explanation: `## ${summary.title}\n\nこのカタの詳細な解説はバックエンド接続後に表示されます。`,
  };
}

export function getMockValidateResponse(
  _kataId: string,
  _code: string,
): ValidateResponse {
  return {
    passed: false,
    message:
      "モックモード: バックエンドに接続されていないため、コード検証は利用できません。",
    stdout: "",
    stderr: "",
  };
}

export function getMockExecuteResponse(_code: string): ExecutionResult {
  return {
    stdout:
      "モックモード: バックエンドに接続されていないため、コード実行は利用できません。",
    stderr: "",
    success: false,
    error:
      "モックモード: バックエンドに接続されていないため、コード実行は利用できません。",
  };
}

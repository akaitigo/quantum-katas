import Editor, { type OnMount } from "@monaco-editor/react";
import { useCallback, useRef } from "react";

interface CodeEditorProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly onExecute?: () => void;
}

export function CodeEditor({
  value,
  onChange,
  onExecute,
}: CodeEditorProps): React.JSX.Element {
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const handleEditorDidMount: OnMount = useCallback(
    (editor, monaco) => {
      editorRef.current = editor;

      // Keyboard shortcut: Ctrl+Enter / Cmd+Enter to execute
      if (onExecute) {
        editor.addAction({
          id: "execute-code",
          label: "Execute Code",
          keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
          run: () => {
            onExecute();
          },
        });
      }
    },
    [onExecute],
  );

  const handleChange = useCallback(
    (newValue: string | undefined) => {
      onChange(newValue ?? "");
    },
    [onChange],
  );

  return (
    <div className="code-editor-wrapper" data-testid="code-editor">
      <div className="code-editor-header">
        <span className="code-editor-label">Python (Cirq)</span>
        <span className="code-editor-shortcut">Ctrl+Enter で実行</span>
      </div>
      <Editor
        height="400px"
        language="python"
        theme="vs-dark"
        value={value}
        onChange={handleChange}
        onMount={handleEditorDidMount}
        options={{
          fontSize: 14,
          fontFamily:
            "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
          lineNumbers: "on",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
          tabSize: 4,
          automaticLayout: true,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "line",
          suggestOnTriggerCharacters: true,
          quickSuggestions: true,
        }}
      />
    </div>
  );
}

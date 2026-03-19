/**
 * TinyTalk language definition for Monaco Editor.
 * Monarch tokenizer — maps directly to the lexer.py token types.
 */

/* exported tinytalkLanguageDef, tinytalkThemeDark, tinytalkThemeLight */
/* global window */

window.tinytalkLanguageDef = {
  defaultToken: '',
  ignoreCase: false,

  keywords: [
    // Modern
    'let', 'const', 'fn', 'return', 'if', 'else', 'elif',
    'for', 'while', 'in', 'break', 'continue', 'match',
    'struct', 'enum', 'import', 'from', 'use', 'as',
    'try', 'catch', 'throw',
    // Classic (Smalltalk-inspired)
    'when', 'fin', 'blueprint', 'law', 'field', 'forge',
    'reply', 'do', 'end', 'self',
  ],

  typeKeywords: [
    'int', 'float', 'str', 'string', 'bool', 'boolean',
    'list', 'map', 'any', 'void', 'null', 'num', 'number',
  ],

  operators: [
    'and', 'or', 'not',
    'is', 'isnt', 'has', 'hasnt', 'isin', 'islike',
  ],

  builtins: [
    'show', 'print', 'len', 'range', 'abs', 'round', 'floor', 'ceil',
    'sqrt', 'pow', 'min', 'max', 'sum', 'sin', 'cos', 'tan', 'log', 'exp',
    'append', 'push', 'pop', 'sort', 'reverse', 'contains', 'slice',
    'keys', 'values', 'zip', 'enumerate',
    'split', 'join', 'replace', 'trim', 'upcase', 'downcase',
    'startswith', 'endswith',
    'type', 'assert', 'assert_equal', 'assert_true', 'assert_false',
    'read_csv', 'write_csv', 'read_json', 'write_json',
    'parse_json', 'to_json', 'http_get', 'http_post',
    'date_now', 'date_parse', 'date_format', 'date_floor',
    'date_add', 'date_diff',
    // Extended stdlib
    'regex_match', 'regex_find', 'regex_replace', 'regex_split',
    'file_read', 'file_write', 'file_exists', 'file_list',
    'env', 'args', 'format', 'hash', 'md5', 'sha256',
    'DataFrame',
  ],

  constants: ['true', 'false', 'null', 'nil', 'PI', 'E', 'TAU', 'INF'],

  stepChains: [
    '_filter', '_sort', '_map', '_take', '_drop', '_first', '_last',
    '_reverse', '_unique', '_count', '_sum', '_avg', '_min', '_max',
    '_group', '_flatten', '_zip', '_chunk', '_reduce', '_sortBy',
    '_join', '_mapValues', '_each', '_select', '_mutate', '_summarize',
    '_rename', '_arrange', '_distinct', '_slice', '_pull', '_groupBy',
    '_leftJoin', '_pivot', '_unpivot', '_window',
  ],

  symbols: /[=><!~?:&|+\-*\/\^%]+/,

  tokenizer: {
    root: [
      // Comments
      [/\/\/.*$/, 'comment'],

      // Step chains (must come before identifiers)
      [/_[a-zA-Z]\w*/, {
        cases: {
          '@stepChains': 'keyword.step',
          '@default': 'identifier',
        }
      }],

      // Identifiers and keywords
      [/[a-zA-Z_]\w*/, {
        cases: {
          '@keywords': 'keyword',
          '@typeKeywords': 'type',
          '@operators': 'keyword.operator',
          '@builtins': 'predefined',
          '@constants': 'constant',
          '@default': 'identifier',
        }
      }],

      // Whitespace
      [/[ \t\r\n]+/, 'white'],

      // Strings with interpolation
      [/"/, 'string', '@string'],

      // Single-quoted strings (no interpolation)
      [/'[^']*'/, 'string'],

      // Numbers
      [/0[xX][0-9a-fA-F]+/, 'number.hex'],
      [/0[oO][0-7]+/, 'number.octal'],
      [/0[bB][01]+/, 'number.binary'],
      [/\d+\.\d*([eE][-+]?\d+)?/, 'number.float'],
      [/\d+([eE][-+]?\d+)?/, 'number'],

      // Pipe operators
      [/\|>/, 'operator.pipe'],
      [/%>%/, 'operator.pipe'],

      // Fat arrow
      [/=>/, 'operator'],

      // Comparison operators (multi-char first)
      [/[<>]=?/, 'operator'],
      [/[!=]=/, 'operator'],

      // Assignment operators
      [/[+\-*\/%]=/, 'operator'],
      [/:=/, 'operator'],

      // Arithmetic
      [/\*\*/, 'operator'],
      [/\/\//, 'operator'],
      [/[+\-*\/%]/, 'operator'],

      // Delimiters
      [/[{}()\[\]]/, '@brackets'],
      [/[;,.]/, 'delimiter'],
      [/[?:]/, 'delimiter'],
      [/->/, 'operator'],
      [/=/, 'operator'],
    ],

    // String state with interpolation support
    string: [
      [/\{/, { token: 'string.interpolation', next: '@interpolation', bracket: '@open' }],
      [/\\[ntr\\"{]/, 'string.escape'],
      [/[^"\\{]+/, 'string'],
      [/"/, 'string', '@pop'],
    ],

    interpolation: [
      [/\}/, { token: 'string.interpolation', next: '@pop', bracket: '@close' }],
      // Allow nested expressions inside interpolation
      [/[a-zA-Z_]\w*/, {
        cases: {
          '@keywords': 'keyword',
          '@builtins': 'predefined',
          '@constants': 'constant',
          '@default': 'identifier',
        }
      }],
      [/\d+(\.\d+)?/, 'number'],
      [/[+\-*\/%<>=!]+/, 'operator'],
      [/[()\[\]]/, '@brackets'],
      [/[ \t]+/, 'white'],
      [/[,.]/, 'delimiter'],
    ],
  },
};

/**
 * TinyTalk dark theme for Monaco — designed to complement the IDE.
 */
window.tinytalkThemeDark = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'keyword',           foreground: 'C586C0' },
    { token: 'keyword.step',      foreground: '4EC9B0', fontStyle: 'bold' },
    { token: 'keyword.operator',  foreground: 'C586C0' },
    { token: 'type',              foreground: '4EC9B0' },
    { token: 'predefined',        foreground: 'DCDCAA' },
    { token: 'constant',          foreground: '569CD6' },
    { token: 'identifier',        foreground: '9CDCFE' },
    { token: 'number',            foreground: 'B5CEA8' },
    { token: 'number.hex',        foreground: 'B5CEA8' },
    { token: 'number.octal',      foreground: 'B5CEA8' },
    { token: 'number.binary',     foreground: 'B5CEA8' },
    { token: 'number.float',      foreground: 'B5CEA8' },
    { token: 'string',            foreground: 'CE9178' },
    { token: 'string.escape',     foreground: 'D7BA7D' },
    { token: 'string.interpolation', foreground: 'C586C0' },
    { token: 'comment',           foreground: '6A9955', fontStyle: 'italic' },
    { token: 'operator',          foreground: 'D4D4D4' },
    { token: 'operator.pipe',     foreground: '4EC9B0', fontStyle: 'bold' },
    { token: 'delimiter',         foreground: 'D4D4D4' },
    { token: '@brackets',         foreground: 'FFD700' },
  ],
  colors: {
    'editor.background':                '#1E1E2E',
    'editor.foreground':                '#CDD6F4',
    'editorCursor.foreground':          '#F5E0DC',
    'editor.lineHighlightBackground':   '#2A2A3C',
    'editor.selectionBackground':       '#45475A',
    'editorLineNumber.foreground':      '#6C7086',
    'editorLineNumber.activeForeground':'#CDD6F4',
    'editor.inactiveSelectionBackground':'#313244',
  },
};

/**
 * TinyTalk light theme for Monaco.
 */
window.tinytalkThemeLight = {
  base: 'vs',
  inherit: true,
  rules: [
    { token: 'keyword',           foreground: '7C3AED' },
    { token: 'keyword.step',      foreground: '0D9488', fontStyle: 'bold' },
    { token: 'keyword.operator',  foreground: '7C3AED' },
    { token: 'type',              foreground: '0D9488' },
    { token: 'predefined',        foreground: 'B45309' },
    { token: 'constant',          foreground: '2563EB' },
    { token: 'identifier',        foreground: '1E293B' },
    { token: 'number',            foreground: '16A34A' },
    { token: 'number.hex',        foreground: '16A34A' },
    { token: 'number.octal',      foreground: '16A34A' },
    { token: 'number.binary',     foreground: '16A34A' },
    { token: 'number.float',      foreground: '16A34A' },
    { token: 'string',            foreground: 'C2410C' },
    { token: 'string.escape',     foreground: 'A16207' },
    { token: 'string.interpolation', foreground: '7C3AED' },
    { token: 'comment',           foreground: '6B7280', fontStyle: 'italic' },
    { token: 'operator',          foreground: '475569' },
    { token: 'operator.pipe',     foreground: '0D9488', fontStyle: 'bold' },
    { token: 'delimiter',         foreground: '475569' },
    { token: '@brackets',         foreground: 'B45309' },
  ],
  colors: {
    'editor.background':                '#FAFAFA',
    'editor.foreground':                '#1E293B',
    'editorCursor.foreground':          '#7C3AED',
    'editor.lineHighlightBackground':   '#F1F5F9',
    'editor.selectionBackground':       '#BFDBFE',
    'editorLineNumber.foreground':      '#94A3B8',
    'editorLineNumber.activeForeground':'#475569',
    'editor.inactiveSelectionBackground':'#E2E8F0',
  },
};

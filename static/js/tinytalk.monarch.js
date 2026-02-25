/**
 * TinyTalk language definition for Monaco Editor.
 * Monarch tokenizer — maps directly to the lexer.py token types.
 */

/* exported tinytalkLanguageDef, tinytalkTheme */
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
    'file_read', 'file_write', 'file_append', 'file_exists',
    'file_delete', 'file_list', 'file_mkdir',
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
window.tinytalkTheme = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'keyword',           foreground: 'C586C0' },       // purple — control flow
    { token: 'keyword.step',      foreground: '4EC9B0', fontStyle: 'bold' },  // teal — step chains
    { token: 'keyword.operator',  foreground: 'C586C0' },       // purple — is/has/and/or
    { token: 'type',              foreground: '4EC9B0' },       // teal — type keywords
    { token: 'predefined',        foreground: 'DCDCAA' },       // yellow — builtin functions
    { token: 'constant',          foreground: '569CD6' },       // blue — true/false/PI
    { token: 'identifier',        foreground: '9CDCFE' },       // light blue — variables
    { token: 'number',            foreground: 'B5CEA8' },       // green — numbers
    { token: 'number.hex',        foreground: 'B5CEA8' },
    { token: 'number.octal',      foreground: 'B5CEA8' },
    { token: 'number.binary',     foreground: 'B5CEA8' },
    { token: 'number.float',      foreground: 'B5CEA8' },
    { token: 'string',            foreground: 'CE9178' },       // orange — strings
    { token: 'string.escape',     foreground: 'D7BA7D' },       // gold — escape sequences
    { token: 'string.interpolation', foreground: 'C586C0' },    // purple — { } in strings
    { token: 'comment',           foreground: '6A9955', fontStyle: 'italic' },
    { token: 'operator',          foreground: 'D4D4D4' },
    { token: 'operator.pipe',     foreground: '4EC9B0', fontStyle: 'bold' },  // teal — pipe ops
    { token: 'delimiter',         foreground: 'D4D4D4' },
    { token: '@brackets',         foreground: 'FFD700' },       // gold — brackets
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

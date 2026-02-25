/**
 * TinyTalk IDE — main application logic.
 * Connects Monaco editor to the TinyTalk backend API.
 */

/* global require, monaco, tinytalkLanguageDef, tinytalkTheme, tinytalkCompletionProvider */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────

  var editor;
  var currentMarkers = [];
  var checkTimeout = null;

  var DEFAULT_CODE = [
    '// Welcome to TinyTalk!',
    '// Press Ctrl+Enter (or click Run) to execute.',
    '',
    'let name = "World"',
    'show("Hello, {name}!")',
    '',
    '// Step chains — TinyTalk\'s superpower',
    'let data = [42, 17, 93, 5, 68, 31, 84]',
    'let top3 = data _sort _reverse _take(3)',
    'show("Top 3:" top3)',
    '',
    '// Functions',
    'fn factorial(n) {',
    '    if n <= 1 { return 1 }',
    '    return n * factorial(n - 1)',
    '}',
    'show("10! = {factorial(10)}")',
    '',
  ].join('\n');

  // ── Monaco setup ───────────────────────────────────────────────────

  require.config({
    paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }
  });

  require(['vs/editor/editor.main'], function () {
    // Register language
    monaco.languages.register({ id: 'tinytalk', extensions: ['.tt'] });
    monaco.languages.setMonarchTokensProvider('tinytalk', tinytalkLanguageDef);
    monaco.languages.registerCompletionItemProvider('tinytalk', tinytalkCompletionProvider);

    // Language config: brackets, auto-closing, comments
    monaco.languages.setLanguageConfiguration('tinytalk', {
      comments: { lineComment: '//' },
      brackets: [['{', '}'], ['[', ']'], ['(', ')']],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"', notIn: ['string'] },
        { open: "'", close: "'", notIn: ['string'] },
      ],
      surroundingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
      ],
      indentationRules: {
        increaseIndentPattern: /\{[^}]*$/,
        decreaseIndentPattern: /^\s*\}/,
      },
    });

    // Register theme
    monaco.editor.defineTheme('tinytalk-dark', tinytalkTheme);

    // Create editor
    editor = monaco.editor.create(document.getElementById('editor'), {
      value: DEFAULT_CODE,
      language: 'tinytalk',
      theme: 'tinytalk-dark',
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
      minimap: { enabled: false },
      lineNumbers: 'on',
      roundedSelection: true,
      scrollBeyondLastLine: false,
      padding: { top: 12, bottom: 12 },
      tabSize: 4,
      insertSpaces: true,
      automaticLayout: true,
      wordWrap: 'on',
      suggestOnTriggerCharacters: true,
      quickSuggestions: true,
    });

    // Keybindings
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, runCode);
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, function () {
      transpileCode('python');
    });

    // Live error checking (debounced)
    editor.onDidChangeModelContent(function () {
      clearTimeout(checkTimeout);
      checkTimeout = setTimeout(checkCode, 600);
    });

    // Load examples
    loadExamples();

    // Initial focus
    editor.focus();
  });

  // ── Resize handle ──────────────────────────────────────────────────

  (function () {
    var handle = document.getElementById('resize-handle');
    var editorPane = document.getElementById('editor-pane');
    var dragging = false;

    handle.addEventListener('mousedown', function (e) {
      dragging = true;
      e.preventDefault();
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      var main = document.getElementById('main');
      var rect = main.getBoundingClientRect();
      var pct = ((e.clientX - rect.left) / rect.width) * 100;
      pct = Math.max(20, Math.min(80, pct));
      editorPane.style.flexBasis = pct + '%';
    });

    document.addEventListener('mouseup', function () {
      if (dragging) {
        dragging = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        if (editor) editor.layout();
      }
    });
  })();

  // ── Tab switching ──────────────────────────────────────────────────

  document.querySelectorAll('#output-tabs .tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      document.querySelectorAll('#output-tabs .tab').forEach(function (t) { t.classList.remove('active'); });
      document.querySelectorAll('#output-panels .panel').forEach(function (p) { p.classList.remove('active'); });
      tab.classList.add('active');
      document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    });
  });

  // ── Button handlers ────────────────────────────────────────────────

  document.getElementById('btn-run').addEventListener('click', runCode);

  document.getElementById('btn-transpile-py').addEventListener('click', function () {
    transpileCode('python');
  });

  document.getElementById('btn-transpile-sql').addEventListener('click', function () {
    transpileCode('sql');
  });

  document.getElementById('btn-transpile-js').addEventListener('click', function () {
    transpileCode('js');
  });

  document.getElementById('btn-clear').addEventListener('click', function () {
    document.getElementById('panel-output').textContent = '';
    document.getElementById('panel-python').textContent = '';
    document.getElementById('panel-sql').textContent = '';
    document.getElementById('panel-js').textContent = '';
    setStatus('Cleared', '');
  });

  document.getElementById('sel-examples').addEventListener('change', function () {
    if (this.value) {
      editor.setValue(this.value);
      this.selectedIndex = 0;
      editor.focus();
    }
  });

  // ── API calls ──────────────────────────────────────────────────────

  function runCode() {
    var code = editor.getValue();
    if (!code.trim()) return;

    setStatus('Running...', '');
    var outputEl = document.getElementById('panel-output');
    outputEl.textContent = '';
    outputEl.classList.remove('error');

    // Switch to output tab
    switchTab('output');

    fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        outputEl.textContent = data.output || '(no output)';
        setStatus('Done', data.elapsed_ms + 'ms | ' + data.op_count + ' ops');
      } else {
        outputEl.textContent = 'Error: ' + data.error;
        outputEl.classList.add('error');
        setStatus('Error', data.elapsed_ms + 'ms');
        highlightError(data.error);
      }
    })
    .catch(function (err) {
      outputEl.textContent = 'Network error: ' + err.message;
      outputEl.classList.add('error');
      setStatus('Error', '');
    });
  }

  function checkCode() {
    var code = editor.getValue();
    if (!code.trim()) {
      clearMarkers();
      return;
    }

    fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      clearMarkers();
      if (data.errors && data.errors.length > 0) {
        var markers = data.errors.map(function (e) {
          return {
            severity: monaco.MarkerSeverity.Error,
            message: e.message,
            startLineNumber: e.line || 1,
            startColumn: e.column || 1,
            endLineNumber: e.line || 1,
            endColumn: (e.column || 1) + 10,
          };
        });
        monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', markers);
        currentMarkers = markers;
      }
    })
    .catch(function () {
      // Silently ignore check errors
    });
  }

  function transpileCode(target) {
    var code = editor.getValue();
    if (!code.trim()) return;

    var endpoint = target === 'sql' ? '/api/transpile-sql' : target === 'js' ? '/api/transpile-js' : '/api/transpile';
    var panelId = target === 'sql' ? 'panel-sql' : target === 'js' ? 'panel-js' : 'panel-python';
    var tabName = target === 'sql' ? 'sql' : target === 'js' ? 'js' : 'python';

    setStatus('Transpiling to ' + target + '...', '');

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var panel = document.getElementById(panelId);
      panel.classList.remove('error');
      if (data.success) {
        panel.textContent = data.output;
        setStatus('Transpiled to ' + target, '');
      } else {
        panel.textContent = 'Error: ' + data.error;
        panel.classList.add('error');
        setStatus('Transpile error', '');
      }
      switchTab(tabName);
    })
    .catch(function (err) {
      var panel = document.getElementById(panelId);
      panel.textContent = 'Network error: ' + err.message;
      panel.classList.add('error');
      setStatus('Error', '');
      switchTab(tabName);
    });
  }

  function loadExamples() {
    fetch('/api/examples')
      .then(function (r) { return r.json(); })
      .then(function (examples) {
        var sel = document.getElementById('sel-examples');
        examples.forEach(function (ex) {
          var opt = document.createElement('option');
          opt.value = ex.code;
          opt.textContent = ex.name;
          sel.appendChild(opt);
        });
      })
      .catch(function () {
        // Silently ignore — examples are optional
      });
  }

  // ── Helpers ────────────────────────────────────────────────────────

  function setStatus(msg, stats) {
    document.getElementById('status-msg').textContent = msg;
    document.getElementById('status-stats').textContent = stats || '';
  }

  function switchTab(name) {
    document.querySelectorAll('#output-tabs .tab').forEach(function (t) { t.classList.remove('active'); });
    document.querySelectorAll('#output-panels .panel').forEach(function (p) { p.classList.remove('active'); });
    var tab = document.querySelector('#output-tabs .tab[data-tab="' + name + '"]');
    if (tab) tab.classList.add('active');
    var panel = document.getElementById('panel-' + name);
    if (panel) panel.classList.add('active');
  }

  function clearMarkers() {
    if (editor) {
      monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', []);
    }
    currentMarkers = [];
  }

  function highlightError(errorMsg) {
    // Try to extract line number from error message like "Line 3: ..."
    var match = errorMsg.match(/[Ll]ine\s+(\d+)/);
    if (match && editor) {
      var line = parseInt(match[1], 10);
      var markers = [{
        severity: monaco.MarkerSeverity.Error,
        message: errorMsg,
        startLineNumber: line,
        startColumn: 1,
        endLineNumber: line,
        endColumn: editor.getModel().getLineMaxColumn(line),
      }];
      monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', markers);
      currentMarkers = markers;
    }
  }

  // Suppress unused variable warning
  void currentMarkers;

})();

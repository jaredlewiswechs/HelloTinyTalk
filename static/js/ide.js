/**
 * TinyTalk IDE — main application logic.
 * Connects Monaco editor to the TinyTalk backend API.
 *
 * Features:
 *   - Run & transpile TinyTalk code
 *   - REPL mode with persistent state
 *   - Step-through chain debugger
 *   - Shareable playground links (URL-encoded programs)
 *   - Live syntax checking with error recovery
 */

/* global require, monaco, tinytalkLanguageDef, tinytalkTheme, tinytalkCompletionProvider */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────

  var editor;
  var currentMarkers = [];
  var checkTimeout = null;
  var replSession = '';
  var replHistory = [];
  var isReplMode = false;

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

  // ── Shareable links: load code from URL ────────────────────────────

  function getCodeFromURL() {
    var params = new URLSearchParams(window.location.search);
    var encoded = params.get('code');
    if (encoded) {
      try {
        return decodeURIComponent(atob(encoded));
      } catch (e) {
        // Try URI-decoded version
        try { return decodeURIComponent(encoded); } catch (e2) { /* ignore */ }
      }
    }
    // Also check hash fragment
    if (window.location.hash && window.location.hash.length > 1) {
      try {
        return decodeURIComponent(atob(window.location.hash.substring(1)));
      } catch (e) { /* ignore */ }
    }
    return null;
  }

  function generateShareURL() {
    var code = editor.getValue();
    var encoded = btoa(encodeURIComponent(code));
    var url = window.location.origin + window.location.pathname + '?code=' + encoded;
    return url;
  }

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

    // Check for shared code in URL
    var initialCode = getCodeFromURL() || DEFAULT_CODE;

    // Create editor
    editor = monaco.editor.create(document.getElementById('editor'), {
      value: initialCode,
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
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, function () {
      if (isReplMode) { replEval(); } else { runCode(); }
    });
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

    // If code was loaded from URL, show a hint
    if (getCodeFromURL()) {
      setStatus('Loaded shared program', 'Press Ctrl+Enter to run');
    }

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

  document.getElementById('btn-run').addEventListener('click', function () {
    if (isReplMode) { replEval(); } else { runCode(); }
  });

  document.getElementById('btn-debug').addEventListener('click', runDebug);

  document.getElementById('btn-share').addEventListener('click', function () {
    var url = generateShareURL();
    // Copy to clipboard
    navigator.clipboard.writeText(url).then(function () {
      setStatus('Link copied to clipboard!', url.length + ' chars');
    }).catch(function () {
      // Fallback: show URL in output
      var panel = document.getElementById('panel-output');
      panel.textContent = 'Share this link:\n\n' + url;
      switchTab('output');
      setStatus('Share link generated', '');
    });
  });

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
    document.getElementById('panel-debug').innerHTML = '';
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

  // ── Mode switching (Program / REPL) ────────────────────────────────

  document.getElementById('sel-mode').addEventListener('change', function () {
    isReplMode = this.value === 'repl';
    if (isReplMode) {
      replSession = '';
      replHistory = [];
      document.getElementById('panel-output').textContent = 'REPL mode active. Type code and press Ctrl+Enter.\nState persists between executions.\n\n';
      setStatus('REPL mode', 'State persists across runs');
    } else {
      setStatus('Program mode', '');
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

  function runDebug() {
    var code = editor.getValue();
    if (!code.trim()) return;

    setStatus('Debugging...', '');
    var outputEl = document.getElementById('panel-output');
    outputEl.textContent = '';
    outputEl.classList.remove('error');

    fetch('/api/run-debug', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        outputEl.textContent = data.output || '(no output)';
        renderDebugTraces(data.chain_traces || []);
        setStatus('Done (debug)', data.elapsed_ms + 'ms | ' + data.op_count + ' ops');
        if (data.chain_traces && data.chain_traces.length > 0) {
          switchTab('debug');
        }
      } else {
        outputEl.textContent = 'Error: ' + data.error;
        outputEl.classList.add('error');
        setStatus('Error', data.elapsed_ms + 'ms');
        highlightError(data.error);
        switchTab('output');
      }
    })
    .catch(function (err) {
      outputEl.textContent = 'Network error: ' + err.message;
      outputEl.classList.add('error');
      setStatus('Error', '');
    });
  }

  function renderDebugTraces(traces) {
    var panel = document.getElementById('panel-debug');
    if (!traces || traces.length === 0) {
      panel.innerHTML = '<div style="color: var(--text-muted); padding: 12px;">No step chains found in this program.<br>Add step chains like: data _filter(...) _sort _take(3)</div>';
      return;
    }

    var html = '';
    traces.forEach(function (trace, ti) {
      html += '<div class="debug-chain">';
      html += '<div class="debug-header">Chain #' + (ti + 1) + '</div>';
      html += '<div class="debug-step debug-source">';
      html += '<span class="debug-label">source</span>';
      html += '<span class="debug-preview">' + escapeHtml(trace.source) + '</span>';
      if (trace.source_count !== null) {
        html += '<span class="debug-count">' + trace.source_count + ' items</span>';
      }
      html += '</div>';

      trace.steps.forEach(function (step) {
        html += '<div class="debug-step">';
        html += '<span class="debug-arrow">  \u2193</span>';
        html += '<span class="debug-step-name">' + escapeHtml(step.step) + '</span>';
        if (step.args) {
          html += '<span class="debug-args">(' + escapeHtml(step.args) + ')</span>';
        }
        html += '<div class="debug-result">';
        html += '<span class="debug-preview">' + escapeHtml(step.preview) + '</span>';
        if (step.count !== null) {
          html += '<span class="debug-count">' + step.count + ' items</span>';
        }
        html += '</div>';
        html += '</div>';
      });

      html += '</div>';
    });

    panel.innerHTML = html;
  }

  function replEval() {
    var code = editor.getValue();
    if (!code.trim()) return;

    setStatus('Evaluating...', '');
    var outputEl = document.getElementById('panel-output');

    switchTab('output');

    fetch('/api/repl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, session: replSession }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      replSession = data.session || replSession;
      replHistory.push(code);

      // Append to output (don't clear — REPL accumulates)
      var existing = outputEl.textContent;
      var prefix = '>> ' + code.split('\n')[0];
      if (code.split('\n').length > 1) prefix += ' ...';
      prefix += '\n';

      if (data.success) {
        outputEl.textContent = existing + prefix + (data.output || '') + '\n';
        outputEl.classList.remove('error');
        setStatus('REPL', data.elapsed_ms + 'ms');
      } else {
        outputEl.textContent = existing + prefix + 'Error: ' + data.error + '\n';
        setStatus('REPL error', data.elapsed_ms + 'ms');
      }

      // Scroll to bottom
      outputEl.scrollTop = outputEl.scrollHeight;
    })
    .catch(function (err) {
      outputEl.textContent += 'Network error: ' + err.message + '\n';
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

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Suppress unused variable warning
  void currentMarkers;

})();

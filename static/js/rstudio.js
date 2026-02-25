/**
 * TinyTalk Studio — RStudio-style 4-pane IDE
 *
 * Layout:
 *   ┌──────────┬──────────────┐
 *   │ Source    │ Environment  │
 *   │ (Monaco)  │ / History    │
 *   ├──────────┼──────────────┤
 *   │ Console   │ Output/Plots │
 *   │ (REPL)    │ /Help/Data   │
 *   └──────────┴──────────────┘
 *
 * Features:
 *   - Run All / Run Selection / Run Line
 *   - Live REPL console with history
 *   - Environment inspector (auto-refreshes after each eval)
 *   - Data viewer (spreadsheet view of list-of-maps)
 *   - Help pane with search
 *   - Plot pane with chart history
 *   - Debug traces for step chains
 *   - Transpiler view (Python / SQL / JS)
 */

/* global require, monaco, tinytalkLanguageDef, tinytalkTheme, tinytalkCompletionProvider, Chart */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────

  var editor;
  var replSession = '';
  var commandHistory = [];
  var historyIndex = -1;
  var checkTimeout = null;
  var activeCharts = [];
  var currentTranspileLang = 'python';

  var CHART_COLORS = [
    '#89B4FA', '#A6E3A1', '#F38BA8', '#F9E2AF', '#94E2D5',
    '#CBA6F7', '#FAB387', '#89DCEB', '#F5C2E7', '#B4BEFE',
  ];

  var DEFAULT_CODE = [
    '// Welcome to TinyTalk Studio!',
    '// This is a 4-pane IDE inspired by RStudio.',
    '//',
    '// Top-left: Source editor (Ctrl+Enter to run)',
    '// Bottom-left: Console (REPL with persistent state)',
    '// Top-right: Environment (see your variables)',
    '// Bottom-right: Output, Plots, Data viewer, Help',
    '',
    '// --- Try running this code! ---',
    '',
    'let scores = [85, 92, 78, 95, 88, 76, 91, 83, 79, 94]',
    '',
    '// Statistics (R-style functions)',
    'show("Mean:" mean(scores))',
    'show("Median:" median(scores))',
    'show("Std Dev:" sd(scores))',
    'show("Summary:" summary(scores))',
    '',
    '// Step chains — TinyTalk\'s superpower',
    'let top5 = scores _sort _reverse _take(5)',
    'show("Top 5:" top5)',
    '',
    '// Visualize',
    'chart_histogram(scores, 8, "Score Distribution")',
    '',
  ].join('\n');

  // ── Shared code from URL ───────────────────────────────────────

  function getCodeFromURL() {
    var params = new URLSearchParams(window.location.search);
    var encoded = params.get('code');
    if (encoded) {
      try { return decodeURIComponent(atob(encoded)); } catch (e) {
        try { return decodeURIComponent(encoded); } catch (e2) { /* ignore */ }
      }
    }
    if (window.location.hash && window.location.hash.length > 1) {
      try { return decodeURIComponent(atob(window.location.hash.substring(1))); } catch (e) { /* ignore */ }
    }
    return null;
  }

  // ── Monaco setup ───────────────────────────────────────────────

  require.config({
    paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }
  });

  require(['vs/editor/editor.main'], function () {
    monaco.languages.register({ id: 'tinytalk', extensions: ['.tt'] });
    monaco.languages.setMonarchTokensProvider('tinytalk', tinytalkLanguageDef);
    monaco.languages.registerCompletionItemProvider('tinytalk', tinytalkCompletionProvider);

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
      indentationRules: {
        increaseIndentPattern: /\{[^}]*$/,
        decreaseIndentPattern: /^\s*\}/,
      },
    });

    monaco.editor.defineTheme('tinytalk-dark', tinytalkTheme);

    var initialCode = getCodeFromURL() || DEFAULT_CODE;

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
      padding: { top: 8, bottom: 8 },
      tabSize: 4,
      insertSpaces: true,
      automaticLayout: true,
      wordWrap: 'on',
      suggestOnTriggerCharacters: true,
      quickSuggestions: true,
    });

    // ── Keybindings ──────────────────────────────────────────────

    // Ctrl+Enter: Run all code in source
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, function () {
      runSourceCode();
    });

    // Ctrl+Shift+Enter: Run selection or current line
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, function () {
      runSelection();
    });

    // Live error checking
    editor.onDidChangeModelContent(function () {
      clearTimeout(checkTimeout);
      checkTimeout = setTimeout(checkSyntax, 600);
    });

    // Cursor position in status bar
    editor.onDidChangeCursorPosition(function (e) {
      document.getElementById('status-cursor').textContent =
        'Ln ' + e.position.lineNumber + ', Col ' + e.position.column;
    });

    loadExamples();
    loadHelpIndex();
    editor.focus();

    if (getCodeFromURL()) {
      setStatus('Loaded shared program');
    }
  });

  // ══════════════════════════════════════════════════════════════════
  // RESIZE (drag the gap borders between panes)
  // ══════════════════════════════════════════════════════════════════

  (function () {
    var grid = document.getElementById('pane-grid');
    var dragging = null; // 'col' or 'row'

    grid.addEventListener('mousedown', function (e) {
      // Detect clicks near the gap borders (within 6px)
      var rect = grid.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      var midX = rect.width / 2;
      var midY = rect.height / 2;

      if (Math.abs(x - midX) < 6) {
        dragging = 'col';
        e.preventDefault();
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
      } else if (Math.abs(y - midY) < 6) {
        dragging = 'row';
        e.preventDefault();
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
      }
    });

    document.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      var rect = grid.getBoundingClientRect();
      if (dragging === 'col') {
        var pct = ((e.clientX - rect.left) / rect.width) * 100;
        pct = Math.max(20, Math.min(80, pct));
        grid.style.gridTemplateColumns = pct + '% ' + (100 - pct) + '%';
      } else if (dragging === 'row') {
        var pct2 = ((e.clientY - rect.top) / rect.height) * 100;
        pct2 = Math.max(15, Math.min(85, pct2));
        grid.style.gridTemplateRows = pct2 + '% ' + (100 - pct2) + '%';
      }
      if (editor) editor.layout();
    });

    document.addEventListener('mouseup', function () {
      if (dragging) {
        dragging = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        if (editor) editor.layout();
      }
    });
  })();

  // ══════════════════════════════════════════════════════════════════
  // TAB SWITCHING
  // ══════════════════════════════════════════════════════════════════

  document.querySelectorAll('.ptab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      var pane = tab.dataset.pane;
      var target = tab.dataset.target;
      // Deactivate siblings
      document.querySelectorAll('.ptab[data-pane="' + pane + '"]').forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');
      // Show target body
      var parent = document.getElementById(target).parentElement;
      parent.querySelectorAll('.pane-body').forEach(function (b) { b.classList.remove('active'); });
      document.getElementById(target).classList.add('active');
    });
  });

  // Transpile sub-tabs
  document.querySelectorAll('.ttab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      document.querySelectorAll('.ttab').forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');
      currentTranspileLang = tab.dataset.lang;
      transpileCode(currentTranspileLang);
    });
  });

  // ══════════════════════════════════════════════════════════════════
  // BUTTON HANDLERS
  // ══════════════════════════════════════════════════════════════════

  document.getElementById('btn-run').addEventListener('click', runSourceCode);
  document.getElementById('btn-run-selection').addEventListener('click', runSelection);
  document.getElementById('btn-debug').addEventListener('click', runDebug);

  document.getElementById('btn-share').addEventListener('click', function () {
    var code = editor.getValue();
    var encoded = btoa(encodeURIComponent(code));
    var url = window.location.origin + window.location.pathname + '?code=' + encoded;
    navigator.clipboard.writeText(url).then(function () {
      setStatus('Link copied to clipboard!');
    }).catch(function () {
      consolePrint('Share link: ' + url, 'system');
    });
  });

  document.getElementById('btn-transpile-py').addEventListener('click', function () { transpileCode('python'); showOutputTab('out-transpiled'); });
  document.getElementById('btn-transpile-sql').addEventListener('click', function () { transpileCode('sql'); showOutputTab('out-transpiled'); });
  document.getElementById('btn-transpile-js').addEventListener('click', function () { transpileCode('js'); showOutputTab('out-transpiled'); });

  document.getElementById('sel-examples').addEventListener('change', function () {
    if (this.value) {
      editor.setValue(this.value);
      this.selectedIndex = 0;
      editor.focus();
    }
  });

  // Import
  document.getElementById('btn-import').addEventListener('click', function () {
    document.getElementById('file-import').click();
  });

  document.getElementById('file-import').addEventListener('change', function () {
    var file = this.files[0];
    if (!file) return;
    var formData = new FormData();
    formData.append('file', file);
    setStatus('Importing ' + file.name + '...');
    fetch('/api/upload', { method: 'POST', body: formData })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          var fn = file.name.toLowerCase().endsWith('.json') ? 'read_json' : 'read_csv';
          var code = 'let data = ' + fn + '("' + data.filename + '")';
          replEval(code);
          setStatus('Imported ' + data.filename);
        } else {
          consolePrint('Import failed: ' + data.error, 'error');
        }
      })
      .catch(function (err) { consolePrint('Import error: ' + err.message, 'error'); });
    this.value = '';
  });

  // Console clear
  document.getElementById('console-clear').addEventListener('click', function () {
    document.getElementById('console-output').innerHTML = '';
  });

  // Env controls
  document.getElementById('env-refresh').addEventListener('click', refreshEnvironment);
  document.getElementById('env-clear').addEventListener('click', function () {
    replEval(':reset');
  });
  document.getElementById('env-filter').addEventListener('input', filterEnvironment);

  // ══════════════════════════════════════════════════════════════════
  // CONSOLE (REPL)
  // ══════════════════════════════════════════════════════════════════

  var consoleInput = document.getElementById('console-input');

  consoleInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      var code = consoleInput.value.trim();
      if (!code) return;
      consoleInput.value = '';
      commandHistory.push(code);
      historyIndex = commandHistory.length;
      replEval(code);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex > 0) {
        historyIndex--;
        consoleInput.value = commandHistory[historyIndex];
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        consoleInput.value = commandHistory[historyIndex];
      } else {
        historyIndex = commandHistory.length;
        consoleInput.value = '';
      }
    }
  });

  function consolePrint(text, cls) {
    var el = document.getElementById('console-output');
    var line = document.createElement('div');
    line.className = 'console-line ' + (cls || 'output');
    line.textContent = text;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  function replEval(code) {
    consolePrint('>> ' + code, 'input');
    setStatus('Evaluating...');

    fetch('/api/repl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, session: replSession }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      replSession = data.session || replSession;
      if (data.success) {
        if (data.output && data.output.trim()) {
          consolePrint(data.output.trimEnd(), 'output');
        }
        setStatus('Done', data.elapsed_ms + 'ms');
        // Handle charts
        if (data.charts && data.charts.length > 0) {
          renderCharts(data.charts);
          showOutputTab('out-plots');
        }
      } else {
        consolePrint('Error: ' + data.error, 'error');
        setStatus('Error');
      }
      // Always refresh environment after REPL eval
      refreshEnvironment();
      updateHistory();
    })
    .catch(function (err) {
      consolePrint('Network error: ' + err.message, 'error');
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // SOURCE EXECUTION
  // ══════════════════════════════════════════════════════════════════

  function runSourceCode() {
    var code = editor.getValue();
    if (!code.trim()) return;

    // Run each statement through REPL for persistent state
    setStatus('Running...');
    var outputEl = document.getElementById('output-text');
    outputEl.textContent = '';
    outputEl.classList.remove('error');
    showOutputTab('out-output');

    fetch('/api/repl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, session: replSession }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      replSession = data.session || replSession;
      if (data.success) {
        outputEl.textContent = data.output || '(no output)';
        consolePrint('[Source] ran successfully', 'system');
        if (data.output && data.output.trim()) {
          consolePrint(data.output.trimEnd(), 'output');
        }
        setStatus('Done', data.elapsed_ms + 'ms');
        if (data.charts && data.charts.length > 0) {
          renderCharts(data.charts);
          showOutputTab('out-plots');
        }
      } else {
        outputEl.textContent = 'Error: ' + data.error;
        outputEl.classList.add('error');
        consolePrint('Error: ' + data.error, 'error');
        setStatus('Error');
        highlightError(data.error);
      }
      refreshEnvironment();
      updateHistory();
    })
    .catch(function (err) {
      outputEl.textContent = 'Network error: ' + err.message;
      outputEl.classList.add('error');
    });
  }

  function runSelection() {
    var selection = editor.getModel().getValueInRange(editor.getSelection());
    if (!selection.trim()) {
      // No selection — run current line
      var line = editor.getPosition().lineNumber;
      selection = editor.getModel().getLineContent(line);
      // Move cursor to next line
      if (line < editor.getModel().getLineCount()) {
        editor.setPosition({ lineNumber: line + 1, column: 1 });
      }
    }
    if (!selection.trim()) return;
    replEval(selection.trim());
  }

  function runDebug() {
    var code = editor.getValue();
    if (!code.trim()) return;
    setStatus('Debugging...');

    fetch('/api/run-debug', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.success) {
        var outputEl = document.getElementById('output-text');
        outputEl.textContent = data.output || '(no output)';
        renderDebugTraces(data.chain_traces || []);
        setStatus('Debug done', data.elapsed_ms + 'ms');
        if (data.chain_traces && data.chain_traces.length > 0) {
          showOutputTab('out-debug');
        }
        if (data.charts && data.charts.length > 0) {
          renderCharts(data.charts);
        }
      } else {
        consolePrint('Debug error: ' + data.error, 'error');
        setStatus('Error');
      }
    })
    .catch(function (err) {
      consolePrint('Network error: ' + err.message, 'error');
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // ENVIRONMENT INSPECTOR
  // ══════════════════════════════════════════════════════════════════

  function refreshEnvironment() {
    if (!replSession) return;

    fetch('/api/repl/env', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session: replSession }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      renderEnvironment(data.variables || []);
    })
    .catch(function () { /* silently ignore */ });
  }

  function renderEnvironment(vars) {
    var list = document.getElementById('env-list');
    var dataSelect = document.getElementById('data-var-select');

    if (!vars || vars.length === 0) {
      list.innerHTML = '<div class="env-empty">No user-defined variables yet.<br>Run some code to populate the environment.</div>';
      dataSelect.innerHTML = '<option value="">No data variables</option>';
      return;
    }

    var html = '';
    var dataVars = [];

    vars.forEach(function (v) {
      html += '<div class="env-item" data-name="' + escapeHtml(v.name) + '" data-type="' + v.type + '">';
      html += '<div class="env-name">' + escapeHtml(v.name);
      html += '<span class="env-type">' + v.type + '</span>';
      if (v.is_const) html += '<span class="env-const">const</span>';
      if (v.is_data) {
        html += '<span class="env-data-badge" data-var="' + escapeHtml(v.name) + '" title="View as table">View</span>';
        dataVars.push(v);
      }
      html += '</div>';
      html += '<div class="env-preview" title="' + escapeHtml(v.preview) + '">' + escapeHtml(v.preview) + '</div>';
      html += '</div>';
    });

    list.innerHTML = html;

    // Update data variable select
    dataSelect.innerHTML = '<option value="">Select variable...</option>';
    dataVars.forEach(function (v) {
      var opt = document.createElement('option');
      opt.value = v.name;
      opt.textContent = v.name + ' (' + v.size + ')';
      dataSelect.appendChild(opt);
    });

    // Click to insert variable name in console
    list.querySelectorAll('.env-item').forEach(function (item) {
      item.addEventListener('click', function (e) {
        // If clicking the View badge, open data viewer instead
        if (e.target.classList.contains('env-data-badge')) {
          var varName = e.target.dataset.var;
          openDataViewer(varName);
          return;
        }
        var name = item.dataset.name;
        consoleInput.value = name;
        consoleInput.focus();
      });
    });

    // Filter
    filterEnvironment();
  }

  function filterEnvironment() {
    var query = document.getElementById('env-filter').value.toLowerCase();
    document.querySelectorAll('#env-list .env-item').forEach(function (item) {
      var name = item.dataset.name.toLowerCase();
      item.style.display = (!query || name.indexOf(query) !== -1) ? '' : 'none';
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // HISTORY
  // ══════════════════════════════════════════════════════════════════

  function updateHistory() {
    var list = document.getElementById('history-list');
    if (commandHistory.length === 0) {
      list.innerHTML = '<div class="env-empty">Command history will appear here.</div>';
      return;
    }
    var html = '';
    for (var i = commandHistory.length - 1; i >= 0; i--) {
      html += '<div class="history-item" data-code="' + escapeHtml(commandHistory[i]) + '">';
      html += '<span class="history-num">' + (i + 1) + '</span>';
      html += escapeHtml(commandHistory[i].split('\n')[0]);
      if (commandHistory[i].indexOf('\n') !== -1) html += ' ...';
      html += '</div>';
    }
    list.innerHTML = html;

    list.querySelectorAll('.history-item').forEach(function (item) {
      item.addEventListener('click', function () {
        consoleInput.value = item.dataset.code;
        consoleInput.focus();
      });
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // DATA VIEWER
  // ══════════════════════════════════════════════════════════════════

  var dataCurrentVar = '';
  var dataCurrentPage = 0;

  document.getElementById('data-var-select').addEventListener('change', function () {
    if (this.value) {
      openDataViewer(this.value);
    }
  });

  document.getElementById('data-prev').addEventListener('click', function () {
    if (dataCurrentPage > 0) {
      dataCurrentPage--;
      loadDataPage();
    }
  });

  document.getElementById('data-next').addEventListener('click', function () {
    dataCurrentPage++;
    loadDataPage();
  });

  function openDataViewer(varName) {
    dataCurrentVar = varName;
    dataCurrentPage = 0;
    document.getElementById('data-var-select').value = varName;
    showOutputTab('out-data');
    loadDataPage();
  }

  function loadDataPage() {
    if (!replSession || !dataCurrentVar) return;

    fetch('/api/repl/data-view', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session: replSession,
        variable: dataCurrentVar,
        page: dataCurrentPage,
        page_size: 50,
      }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!data.success) {
        document.getElementById('data-table-wrap').innerHTML =
          '<div class="env-empty">Error: ' + escapeHtml(data.error) + '</div>';
        return;
      }
      renderDataTable(data);
    })
    .catch(function (err) {
      document.getElementById('data-table-wrap').innerHTML =
        '<div class="env-empty">Error loading data: ' + escapeHtml(err.message) + '</div>';
    });
  }

  function renderDataTable(data) {
    var wrap = document.getElementById('data-table-wrap');
    var info = document.getElementById('data-info');
    var prevBtn = document.getElementById('data-prev');
    var nextBtn = document.getElementById('data-next');
    var pageInfo = document.getElementById('data-page-info');

    info.textContent = data.total + ' rows x ' + data.columns.length + ' cols';
    pageInfo.textContent = 'Page ' + (data.page + 1) + ' of ' + data.total_pages;
    prevBtn.disabled = data.page <= 0;
    nextBtn.disabled = data.page >= data.total_pages - 1;

    var html = '<table class="data-table"><thead><tr>';
    html += '<th class="row-num-header">#</th>';
    data.columns.forEach(function (col) {
      html += '<th>' + escapeHtml(col) + '</th>';
    });
    html += '</tr></thead><tbody>';

    data.rows.forEach(function (row, i) {
      html += '<tr>';
      html += '<td class="row-num">' + (data.page * data.page_size + i + 1) + '</td>';
      data.columns.forEach(function (col) {
        var val = row[col] !== undefined ? row[col] : '';
        html += '<td title="' + escapeHtml(String(val)) + '">' + escapeHtml(String(val)) + '</td>';
      });
      html += '</tr>';
    });

    html += '</tbody></table>';
    wrap.innerHTML = html;
  }

  // ══════════════════════════════════════════════════════════════════
  // HELP SYSTEM
  // ══════════════════════════════════════════════════════════════════

  var helpSearchTimeout;

  document.getElementById('help-search').addEventListener('input', function () {
    clearTimeout(helpSearchTimeout);
    var query = this.value.trim();
    helpSearchTimeout = setTimeout(function () {
      if (query.length === 0) {
        document.getElementById('help-results').innerHTML = '';
        document.getElementById('help-categories').style.display = '';
      } else {
        searchHelp(query);
      }
    }, 300);
  });

  function loadHelpIndex() {
    fetch('/api/help')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderHelpCategories(data.functions || {});
      })
      .catch(function () { /* silently ignore */ });
  }

  function renderHelpCategories(byCategory) {
    var el = document.getElementById('help-categories');
    var html = '';
    var cats = Object.keys(byCategory).sort();

    cats.forEach(function (cat) {
      html += '<div class="help-category-header">' + escapeHtml(cat) + '</div>';
      byCategory[cat].forEach(function (fn) {
        html += renderHelpEntry(fn);
      });
    });

    el.innerHTML = html;

    el.querySelectorAll('.help-entry').forEach(function (entry) {
      entry.addEventListener('click', function () {
        var name = entry.dataset.name;
        consoleInput.value = name + '(';
        consoleInput.focus();
      });
    });
  }

  function searchHelp(query) {
    fetch('/api/help/search?q=' + encodeURIComponent(query))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var el = document.getElementById('help-results');
        if (!data.results || data.results.length === 0) {
          el.innerHTML = '<div class="env-empty">No results for "' + escapeHtml(query) + '"</div>';
        } else {
          var html = '';
          data.results.forEach(function (entry) {
            html += renderHelpEntry(entry);
          });
          el.innerHTML = html;
        }
        document.getElementById('help-categories').style.display = 'none';
      })
      .catch(function () { /* silently ignore */ });
  }

  function renderHelpEntry(entry) {
    var html = '<div class="help-entry" data-name="' + escapeHtml(entry.name) + '">';
    html += '<div class="help-name">' + escapeHtml(entry.name) + '</div>';
    if (entry.signature) {
      html += '<div class="help-sig">' + escapeHtml(entry.signature) + '</div>';
    }
    if (entry.description) {
      html += '<div class="help-desc">' + escapeHtml(entry.description) + '</div>';
    }
    if (entry.examples && entry.examples.length > 0) {
      html += '<div class="help-examples">' + entry.examples.map(escapeHtml).join('\n') + '</div>';
    }
    html += '</div>';
    return html;
  }

  // ══════════════════════════════════════════════════════════════════
  // CHARTS / PLOTS
  // ══════════════════════════════════════════════════════════════════

  function renderCharts(charts) {
    var panel = document.getElementById('plots-container');
    // Destroy existing charts
    activeCharts.forEach(function (c) { c.destroy(); });
    activeCharts = [];
    panel.innerHTML = '';

    if (!charts || charts.length === 0) {
      panel.innerHTML = '<div class="chart-empty">No plots to display.<br>Use <code>chart_bar()</code>, <code>chart_line()</code>, <code>chart_pie()</code>, <code>chart_scatter()</code>, or <code>chart_histogram()</code></div>';
      return;
    }

    charts.forEach(function (spec, idx) {
      var wrapper = document.createElement('div');
      wrapper.className = 'chart-wrapper';
      var canvas = document.createElement('canvas');
      canvas.id = 'chart-' + idx;
      canvas.style.maxHeight = '300px';
      wrapper.appendChild(canvas);
      panel.appendChild(wrapper);

      var config = buildChartConfig(spec);
      var chart = new Chart(canvas.getContext('2d'), config);
      activeCharts.push(chart);
    });
  }

  function buildChartConfig(spec) {
    var defaults = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#CDD6F4', font: { family: "'JetBrains Mono', monospace", size: 11 } } },
        title: {
          display: !!spec.title,
          text: spec.title || '',
          color: '#CDD6F4',
          font: { family: "'JetBrains Mono', monospace", size: 14, weight: '600' },
        },
      },
      scales: {},
    };
    var axisDefaults = {
      grid: { color: 'rgba(69, 71, 90, 0.6)' },
      ticks: { color: '#A6ADC8', font: { family: "'JetBrains Mono', monospace", size: 10 } },
    };

    if (spec.type === 'bar') {
      defaults.scales = { x: axisDefaults, y: axisDefaults };
      return {
        type: 'bar',
        data: {
          labels: spec.labels,
          datasets: [{ label: spec.title || 'Values', data: spec.values, backgroundColor: spec.values.map(function (_, i) { return CHART_COLORS[i % CHART_COLORS.length] + 'CC'; }), borderColor: spec.values.map(function (_, i) { return CHART_COLORS[i % CHART_COLORS.length]; }), borderWidth: 1, borderRadius: 4 }],
        },
        options: defaults,
      };
    }
    if (spec.type === 'line') {
      defaults.scales = { x: axisDefaults, y: axisDefaults };
      return {
        type: 'line',
        data: {
          labels: spec.labels,
          datasets: [{ label: spec.title || 'Values', data: spec.values, borderColor: CHART_COLORS[0], backgroundColor: CHART_COLORS[0] + '33', fill: true, tension: 0.3, pointRadius: 4 }],
        },
        options: defaults,
      };
    }
    if (spec.type === 'pie') {
      delete defaults.scales;
      return {
        type: 'pie',
        data: {
          labels: spec.labels,
          datasets: [{ data: spec.values, backgroundColor: spec.values.map(function (_, i) { return CHART_COLORS[i % CHART_COLORS.length] + 'CC'; }), borderColor: '#1E1E2E', borderWidth: 2 }],
        },
        options: defaults,
      };
    }
    if (spec.type === 'scatter') {
      defaults.scales = { x: axisDefaults, y: axisDefaults };
      var points = spec.x.map(function (xv, i) { return { x: xv, y: spec.y[i] }; });
      return {
        type: 'scatter',
        data: { datasets: [{ label: spec.title || 'Data', data: points, backgroundColor: CHART_COLORS[0] + 'CC', borderColor: CHART_COLORS[0], pointRadius: 5 }] },
        options: defaults,
      };
    }
    if (spec.type === 'multi') {
      defaults.scales = { x: axisDefaults, y: axisDefaults };
      var datasets = [];
      var names = Object.keys(spec.series);
      names.forEach(function (name, i) {
        datasets.push({ label: name, data: spec.series[name], borderColor: CHART_COLORS[i % CHART_COLORS.length], fill: false, tension: 0.3 });
      });
      return { type: 'line', data: { labels: spec.labels, datasets: datasets }, options: defaults };
    }
    // Fallback
    defaults.scales = { x: axisDefaults, y: axisDefaults };
    return {
      type: 'bar',
      data: { labels: spec.labels || [], datasets: [{ label: spec.title || 'Values', data: spec.values || [], backgroundColor: CHART_COLORS[0] + 'CC' }] },
      options: defaults,
    };
  }

  // ══════════════════════════════════════════════════════════════════
  // DEBUG TRACES
  // ══════════════════════════════════════════════════════════════════

  function renderDebugTraces(traces) {
    var panel = document.getElementById('debug-traces');
    if (!traces || traces.length === 0) {
      panel.innerHTML = '<div class="env-empty">No step chains found.<br>Add chains like: data _filter(...) _sort _take(3)</div>';
      return;
    }
    var html = '';
    traces.forEach(function (trace, ti) {
      html += '<div class="debug-chain">';
      html += '<div class="debug-header">Chain #' + (ti + 1) + '</div>';
      html += '<div class="debug-step debug-source">';
      html += '<span class="debug-label">source</span>';
      html += '<span class="debug-preview">' + escapeHtml(trace.source) + '</span>';
      if (trace.source_count !== null) html += '<span class="debug-count">' + trace.source_count + ' items</span>';
      html += '</div>';
      trace.steps.forEach(function (step) {
        html += '<div class="debug-step">';
        html += '<span class="debug-arrow">  \u2193</span>';
        html += '<span class="debug-step-name">' + escapeHtml(step.step) + '</span>';
        if (step.args) html += '<span class="debug-args">(' + escapeHtml(step.args) + ')</span>';
        html += '<div class="debug-result">';
        html += '<span class="debug-preview">' + escapeHtml(step.preview) + '</span>';
        if (step.count !== null) html += '<span class="debug-count">' + step.count + ' items</span>';
        html += '</div></div>';
      });
      html += '</div>';
    });
    panel.innerHTML = html;
  }

  // ══════════════════════════════════════════════════════════════════
  // TRANSPILER
  // ══════════════════════════════════════════════════════════════════

  function transpileCode(lang) {
    var code = editor.getValue();
    if (!code.trim()) return;
    var endpoint = lang === 'sql' ? '/api/transpile-sql' : lang === 'js' ? '/api/transpile-js' : '/api/transpile';
    setStatus('Transpiling to ' + lang + '...');

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var el = document.getElementById('transpiled-code');
      if (data.success) {
        el.textContent = data.output;
        setStatus('Transpiled to ' + lang);
      } else {
        el.textContent = 'Error: ' + data.error;
      }
      // Activate correct sub-tab
      document.querySelectorAll('.ttab').forEach(function (t) {
        t.classList.toggle('active', t.dataset.lang === lang);
      });
    })
    .catch(function (err) {
      document.getElementById('transpiled-code').textContent = 'Error: ' + err.message;
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // SYNTAX CHECKING
  // ══════════════════════════════════════════════════════════════════

  function checkSyntax() {
    var code = editor.getValue();
    if (!code.trim()) {
      monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', []);
      return;
    }
    fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var markers = (data.errors || []).map(function (e) {
        return {
          severity: monaco.MarkerSeverity.Error,
          message: e.message,
          startLineNumber: e.line || 1, startColumn: e.column || 1,
          endLineNumber: e.line || 1, endColumn: (e.column || 1) + 10,
        };
      });
      monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', markers);
    })
    .catch(function () { /* ignore */ });
  }

  function highlightError(errorMsg) {
    var match = errorMsg.match(/[Ll]ine\s+(\d+)/);
    if (match && editor) {
      var line = parseInt(match[1], 10);
      monaco.editor.setModelMarkers(editor.getModel(), 'tinytalk', [{
        severity: monaco.MarkerSeverity.Error,
        message: errorMsg,
        startLineNumber: line, startColumn: 1,
        endLineNumber: line, endColumn: editor.getModel().getLineMaxColumn(line),
      }]);
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // EXAMPLES
  // ══════════════════════════════════════════════════════════════════

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
      .catch(function () { /* ignore */ });
  }

  // ══════════════════════════════════════════════════════════════════
  // HELPERS
  // ══════════════════════════════════════════════════════════════════

  function setStatus(msg, stats) {
    document.getElementById('status-msg').textContent = msg;
    document.getElementById('status-stats').textContent = stats || '';
  }

  function showOutputTab(targetId) {
    document.querySelectorAll('.ptab[data-pane="output"]').forEach(function (t) {
      t.classList.toggle('active', t.dataset.target === targetId);
    });
    var parent = document.getElementById(targetId).parentElement;
    parent.querySelectorAll('.pane-body').forEach(function (b) { b.classList.remove('active'); });
    document.getElementById(targetId).classList.add('active');
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

})();

/**
 * TinyTalk autocomplete provider for Monaco Editor.
 * Context-aware: step chains after _, properties after ., keywords elsewhere.
 */

/* exported tinytalkCompletionProvider */
/* global window, monaco */

window.tinytalkCompletionProvider = {
  triggerCharacters: ['_', '.', ' '],

  provideCompletionItems: function (model, position) {
    var word = model.getWordUntilPosition(position);
    var range = {
      startLineNumber: position.lineNumber,
      endLineNumber: position.lineNumber,
      startColumn: word.startColumn,
      endColumn: word.endColumn,
    };

    // Check what character precedes the current word
    var lineContent = model.getLineContent(position.lineNumber);
    var textBefore = lineContent.substring(0, position.column - 1);

    // After underscore — suggest step chains
    if (textBefore.endsWith('_') || /\s_$/.test(textBefore)) {
      return { suggestions: stepChainSuggestions(range) };
    }

    // After dot — suggest property conversions
    if (textBefore.endsWith('.') || /\w\.$/.test(textBefore)) {
      return { suggestions: propertySuggestions(range) };
    }

    // Default: keywords + builtins + snippets
    var suggestions = [].concat(
      keywordSuggestions(range),
      builtinSuggestions(range),
      snippetSuggestions(range)
    );
    return { suggestions: suggestions };
  }
};

function stepChainSuggestions(range) {
  var Kind = monaco.languages.CompletionItemKind;
  var chains = [
    // Filtering & slicing
    ['_filter((x) => x)', 'Filter items by predicate', '_filter'],
    ['_take(${1:n})', 'Take first n items', '_take'],
    ['_drop(${1:n})', 'Drop first n items', '_drop'],
    ['_first', 'Get the first item', '_first'],
    ['_last', 'Get the last item', '_last'],
    ['_slice(${1:start}, ${2:count})', 'Slice by position', '_slice'],
    // Ordering
    ['_sort', 'Sort ascending', '_sort'],
    ['_reverse', 'Reverse the order', '_reverse'],
    ['_sortBy((x) => x)', 'Sort by key function', '_sortBy'],
    ['_arrange((r) => r["${1:col}"])', 'Sort rows by column', '_arrange'],
    // Transforming
    ['_map((x) => x)', 'Transform each item', '_map'],
    ['_mutate((r) => {"${1:col}": ${2:expr}})', 'Add/modify columns', '_mutate'],
    ['_select(["${1:col1}", "${2:col2}"])', 'Pick columns', '_select'],
    ['_rename({"${1:old}": "${2:new}"})', 'Rename columns', '_rename'],
    ['_pull("${1:col}")', 'Extract a single column', '_pull'],
    // Aggregating
    ['_count', 'Count items', '_count'],
    ['_sum', 'Sum of items', '_sum'],
    ['_avg', 'Average of items', '_avg'],
    ['_min', 'Minimum value', '_min'],
    ['_max', 'Maximum value', '_max'],
    ['_reduce((acc, x) => acc + x, ${1:0})', 'Reduce to single value', '_reduce'],
    ['_summarize({"${1:col}": (rows) => rows _count})', 'Aggregate dataset', '_summarize'],
    // Grouping & deduplication
    ['_group((x) => x)', 'Group by key', '_group'],
    ['_groupBy((r) => r["${1:col}"])', 'Group rows by column', '_groupBy'],
    ['_unique', 'Remove duplicates', '_unique'],
    ['_distinct', 'Remove duplicates (dplyr-style)', '_distinct'],
    // Restructuring
    ['_flatten', 'Flatten nested lists', '_flatten'],
    ['_chunk(${1:n})', 'Split into chunks of size n', '_chunk'],
    ['_zip(${1:otherList})', 'Pair up two lists', '_zip'],
    ['_join(${1:right}, (r) => r["${2:key}"])', 'Inner join two datasets', '_join'],
    ['_leftJoin(${1:right}, (r) => r["${2:key}"])', 'Left join two datasets', '_leftJoin'],
    ['_pivot((r) => r["${1:row}"], (r) => r["${2:col}"], (r) => r["${3:val}"])', 'Pivot long to wide', '_pivot'],
    ['_unpivot(["${1:id_col}"])', 'Unpivot wide to long', '_unpivot'],
    ['_window(${1:3}, (w) => w _avg)', 'Sliding window function', '_window'],
    // Side effects
    ['_each((x) => show(x))', 'Run function on each item (returns original)', '_each'],
    ['_mapValues((v) => v)', 'Transform map values', '_mapValues'],
  ];

  return chains.map(function (c, i) {
    return {
      label: c[2],
      kind: Kind.Method,
      insertText: c[0],
      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
      detail: c[1],
      documentation: c[1],
      range: range,
      sortText: String(i).padStart(3, '0'),
    };
  });
}

function propertySuggestions(range) {
  var Kind = monaco.languages.CompletionItemKind;
  var props = [
    ['str', 'Convert to string', 'Property'],
    ['int', 'Convert to integer', 'Property'],
    ['float', 'Convert to float', 'Property'],
    ['bool', 'Convert to boolean', 'Property'],
    ['type', 'Get type name', 'Property'],
    ['len', 'Get length', 'Property'],
    ['upcase', 'Uppercase (string)', 'Property'],
    ['downcase', 'Lowercase (string)', 'Property'],
    ['trim', 'Strip whitespace (string)', 'Property'],
    ['reversed', 'Reverse (string)', 'Property'],
    ['chars', 'Split into characters (string)', 'Property'],
    ['words', 'Split into words (string)', 'Property'],
  ];

  return props.map(function (p) {
    return {
      label: p[0],
      kind: Kind.Property,
      insertText: p[0],
      detail: p[1],
      documentation: p[2] + ': ' + p[1],
      range: range,
    };
  });
}

function keywordSuggestions(range) {
  var Kind = monaco.languages.CompletionItemKind;
  var kws = [
    'let', 'const', 'fn', 'return', 'if', 'else', 'elif',
    'for', 'while', 'in', 'break', 'continue', 'match',
    'struct', 'import', 'from', 'use', 'as',
    'try', 'catch', 'throw',
    'when', 'blueprint', 'law', 'forge', 'reply', 'end', 'field',
    'and', 'or', 'not', 'is', 'isnt', 'has', 'hasnt', 'isin', 'islike',
    'true', 'false', 'null',
  ];

  return kws.map(function (kw) {
    return {
      label: kw,
      kind: Kind.Keyword,
      insertText: kw,
      range: range,
    };
  });
}

function builtinSuggestions(range) {
  var Kind = monaco.languages.CompletionItemKind;
  var fns = [
    ['show(${1:value})', 'Print with newline'],
    ['print(${1:value})', 'Print without newline'],
    ['len(${1:x})', 'Get length'],
    ['range(${1:n})', 'Generate number sequence'],
    ['abs(${1:n})', 'Absolute value'],
    ['round(${1:n}, ${2:decimals})', 'Round number'],
    ['floor(${1:n})', 'Round down'],
    ['ceil(${1:n})', 'Round up'],
    ['sqrt(${1:n})', 'Square root'],
    ['pow(${1:base}, ${2:exp})', 'Power'],
    ['min(${1:a}, ${2:b})', 'Minimum'],
    ['max(${1:a}, ${2:b})', 'Maximum'],
    ['sum(${1:list})', 'Sum of list'],
    ['append(${1:list}, ${2:val})', 'Append to list'],
    ['pop(${1:list})', 'Remove and return last'],
    ['sort(${1:list})', 'Sort list'],
    ['reverse(${1:x})', 'Reverse list or string'],
    ['contains(${1:list}, ${2:val})', 'Check membership'],
    ['slice(${1:x}, ${2:start}, ${3:end})', 'Slice'],
    ['keys(${1:map})', 'Get map keys'],
    ['values(${1:map})', 'Get map values'],
    ['zip(${1:a}, ${2:b})', 'Pair up elements'],
    ['enumerate(${1:list})', 'Index-value pairs'],
    ['split(${1:str}, ${2:delim})', 'Split string'],
    ['join(${1:list}, ${2:delim})', 'Join to string'],
    ['replace(${1:str}, ${2:old}, ${3:new})', 'Replace in string'],
    ['trim(${1:str})', 'Strip whitespace'],
    ['upcase(${1:str})', 'Uppercase'],
    ['downcase(${1:str})', 'Lowercase'],
    ['startswith(${1:str}, ${2:prefix})', 'Check start'],
    ['endswith(${1:str}, ${2:suffix})', 'Check end'],
    ['type(${1:x})', 'Get type name'],
    ['str(${1:x})', 'Convert to string'],
    ['int(${1:x})', 'Convert to integer'],
    ['float(${1:x})', 'Convert to float'],
    ['bool(${1:x})', 'Convert to boolean'],
    ['read_csv("${1:file.csv}")', 'Read CSV file'],
    ['write_csv(${1:data}, "${2:file.csv}")', 'Write CSV file'],
    ['read_json("${1:file.json}")', 'Read JSON file'],
    ['write_json(${1:data}, "${2:file.json}")', 'Write JSON file'],
    ['parse_json(${1:str})', 'Parse JSON string'],
    ['to_json(${1:value})', 'Convert to JSON string'],
    ['date_now()', 'Current date-time'],
    ['date_parse("${1:date}")', 'Parse date string'],
    ['date_add("${1:date}", ${2:n}, "${3:days}")', 'Add time to date'],
    ['date_diff("${1:date1}", "${2:date2}", "${3:days}")', 'Date difference'],
    ['date_floor("${1:date}", "${2:month}")', 'Truncate date'],
    ['date_format("${1:date}", "${2:%Y-%m-%d}")', 'Format date'],
    ['assert(${1:cond}, "${2:message}")', 'Assert condition'],
    ['assert_equal(${1:a}, ${2:b}, "${3:message}")', 'Assert equality'],
  ];

  return fns.map(function (f) {
    return {
      label: f[0].replace(/\$\{\d+:?([^}]*)}/g, '$1'),  // strip snippet markers for label
      kind: Kind.Function,
      insertText: f[0],
      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
      detail: f[1],
      documentation: f[1],
      range: range,
    };
  });
}

function snippetSuggestions(range) {
  var Kind = monaco.languages.CompletionItemKind;
  var snippets = [
    {
      label: 'fn (function)',
      insertText: 'fn ${1:name}(${2:params}) {\n\t${3:// body}\n\treturn ${4:result}\n}',
      detail: 'Define a function',
    },
    {
      label: 'for (loop)',
      insertText: 'for ${1:item} in ${2:list} {\n\t${3:// body}\n}',
      detail: 'For loop over a collection',
    },
    {
      label: 'while (loop)',
      insertText: 'while ${1:condition} {\n\t${2:// body}\n}',
      detail: 'While loop',
    },
    {
      label: 'if/else',
      insertText: 'if ${1:condition} {\n\t${2:// then}\n} else {\n\t${3:// else}\n}',
      detail: 'If/else block',
    },
    {
      label: 'match',
      insertText: 'match ${1:value} {\n\t${2:1} => ${3:result},\n\t_ => ${4:default},\n}',
      detail: 'Pattern matching',
    },
    {
      label: 'try/catch',
      insertText: 'try {\n\t${1:// code}\n} catch(${2:e}) {\n\tshow("Error: " + ${2:e})\n}',
      detail: 'Error handling',
    },
    {
      label: 'struct',
      insertText: 'struct ${1:Name} {\n\t${2:field}: ${3:int},\n}',
      detail: 'Define a struct',
    },
    {
      label: 'blueprint',
      insertText: 'blueprint ${1:Name}\n\tfield ${2:value} = ${3:0}\n\n\tforge ${4:method}()\n\t\t${5:// body}\n\t\treply self.${2:value}\n\tend\nend',
      detail: 'Define a class (blueprint)',
    },
    {
      label: 'law (classic function)',
      insertText: 'law ${1:name}(${2:params})\n\treply ${3:result}\nend',
      detail: 'Classic-style function',
    },
    {
      label: 'pipeline',
      insertText: 'let ${1:result} = ${2:data}\n\t_filter((r) => ${3:r > 0})\n\t_sort\n\t_take(${4:10})',
      detail: 'Data pipeline template',
    },
  ];

  return snippets.map(function (s) {
    return {
      label: s.label,
      kind: Kind.Snippet,
      insertText: s.insertText,
      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
      detail: s.detail,
      documentation: s.detail,
      range: range,
    };
  });
}

/**
 * tree-sitter grammar for TinyTalk
 *
 * Provides structural parsing for:
 *   - GitHub syntax highlighting (.tt files)
 *   - Neovim / Helix / Zed editor integration
 *   - Code navigation and folding
 *
 * Install: npm install tree-sitter-tinytalk
 * GitHub linguist: add to languages.yml for .tt file recognition
 */

module.exports = grammar({
  name: 'tinytalk',

  extras: $ => [/\s/, $.comment],

  rules: {
    source_file: $ => repeat($._statement),

    _statement: $ => choice(
      $.let_statement,
      $.const_statement,
      $.function_declaration,
      $.if_statement,
      $.for_statement,
      $.while_statement,
      $.return_statement,
      $.break_statement,
      $.continue_statement,
      $.struct_declaration,
      $.enum_declaration,
      $.import_statement,
      $.match_statement,
      $.try_statement,
      $.throw_statement,
      $.expression_statement,
      // Classic syntax
      $.when_declaration,
      $.law_declaration,
      $.blueprint_declaration,
    ),

    // --- Statements ---

    let_statement: $ => seq('let', $.identifier, optional(seq(':', $._type)), optional(seq('=', $._expression))),
    const_statement: $ => seq('const', $.identifier, '=', $._expression),

    function_declaration: $ => seq('fn', $.identifier, '(', optional($.parameter_list), ')', optional(seq('->', $._type)), $.block),
    parameter_list: $ => seq($.parameter, repeat(seq(',', $.parameter))),
    parameter: $ => seq($.identifier, optional(seq(':', $._type)), optional(seq('=', $._expression))),

    if_statement: $ => seq('if', $._expression, $.block, repeat(seq('elif', $._expression, $.block)), optional(seq('else', $.block))),
    for_statement: $ => seq('for', $.identifier, 'in', $._expression, $.block),
    while_statement: $ => seq('while', $._expression, $.block),

    return_statement: $ => seq('return', optional($._expression)),
    break_statement: $ => 'break',
    continue_statement: $ => 'continue',

    struct_declaration: $ => seq('struct', $.identifier, '{', repeat($.field_declaration), '}'),
    field_declaration: $ => seq($.identifier, ':', $._type, optional(seq('=', $._expression)), optional(',')),

    enum_declaration: $ => seq('enum', $.identifier, '{', repeat(seq($.identifier, optional(seq('=', $._expression)), optional(','))), '}'),

    import_statement: $ => choice(
      seq('import', $.string, optional(seq('as', $.identifier))),
      seq('from', $.string, 'use', choice(
        seq('{', commaSep($.identifier), '}'),
        commaSep1($.identifier),
      )),
    ),

    match_statement: $ => seq('match', $._expression, '{', repeat(seq($._expression, '=>', $._expression, optional(','))), '}'),
    try_statement: $ => seq('try', $.block, optional(seq('catch', optional(seq('(', $.identifier, ')')), $.block))),
    throw_statement: $ => seq('throw', $._expression),

    expression_statement: $ => $._expression,

    // Classic syntax
    when_declaration: $ => choice(
      seq('when', $.identifier, '=', $._expression),
      seq('when', $.identifier, '(', optional($.parameter_list), ')', repeat($._statement), choice('fin', 'end')),
    ),
    law_declaration: $ => seq('law', $.identifier, '(', optional($.parameter_list), ')', repeat($._statement), 'end'),
    blueprint_declaration: $ => seq('blueprint', $.identifier, repeat(choice($.field_line, $.method_declaration)), 'end'),
    field_line: $ => seq('field', $.identifier, optional(seq('=', $._expression))),
    method_declaration: $ => seq(choice('forge', 'law'), $.identifier, '(', optional($.parameter_list), ')', repeat($._statement), 'end'),

    block: $ => seq('{', repeat($._statement), '}'),

    // --- Expressions ---

    _expression: $ => choice(
      $.binary_expression,
      $.unary_expression,
      $.call_expression,
      $.index_expression,
      $.member_expression,
      $.step_chain,
      $.lambda,
      $.ternary_expression,
      $.pipe_expression,
      $.parenthesized_expression,
      $.array,
      $.map_literal,
      $.string,
      $.number,
      $.boolean,
      $.null,
      $.identifier,
    ),

    binary_expression: $ => choice(
      ...[['+', 6], ['-', 6], ['*', 7], ['/', 7], ['%', 7], ['**', 8],
        ['==', 4], ['!=', 4], ['<', 5], ['>', 5], ['<=', 5], ['>=', 5],
        ['and', 2], ['or', 1],
        ['is', 4], ['isnt', 4], ['has', 4], ['hasnt', 4], ['isin', 4], ['islike', 4],
      ].map(([op, prec]) =>
        prec_left(prec, seq($._expression, op, $._expression))
      ),
    ),

    unary_expression: $ => choice(
      seq('-', $._expression),
      seq('not', $._expression),
      seq('!', $._expression),
    ),

    call_expression: $ => seq($._expression, '(', optional(commaSep($._expression)), ')'),
    index_expression: $ => seq($._expression, '[', $._expression, ']'),
    member_expression: $ => seq($._expression, '.', $.identifier),

    step_chain: $ => seq($._expression, repeat1($.step)),
    step: $ => seq($.step_name, optional(seq('(', optional(commaSep($._expression)), ')'))),
    step_name: $ => token(seq('_', /[a-zA-Z]\w*/)),

    lambda: $ => choice(
      seq('(', optional(commaSep($.identifier)), ')', '=>', $._expression),
      seq('|', optional(commaSep($.identifier)), '|', $._expression),
    ),

    ternary_expression: $ => prec_right(seq($._expression, '?', $._expression, ':', $._expression)),
    pipe_expression: $ => prec_left(seq($._expression, choice('|>', '%>%'), $._expression)),

    parenthesized_expression: $ => seq('(', $._expression, ')'),
    array: $ => seq('[', optional(commaSep($._expression)), ']'),
    map_literal: $ => seq('{', optional(commaSep(seq($._expression, ':', $._expression))), '}'),

    // --- Types ---

    _type: $ => choice(
      $.identifier,
      seq($.identifier, '[', commaSep($._type), ']'),
      seq('?', $._type),
    ),

    // --- Literals ---

    string: $ => choice(
      seq('"', repeat(choice(/[^"\\{]+/, $.escape_sequence, $.interpolation)), '"'),
      seq("'", /[^']*/, "'"),
    ),
    escape_sequence: $ => token(seq('\\', /[ntr\\\"\'{}]/)),
    interpolation: $ => seq('{', $._expression, '}'),

    number: $ => choice(
      /0[xX][0-9a-fA-F_]+/,
      /0[oO][0-7_]+/,
      /0[bB][01_]+/,
      /\d+\.\d*([eE][-+]?\d+)?/,
      /\d+([eE][-+]?\d+)?/,
    ),

    boolean: $ => choice('true', 'false'),
    null: $ => choice('null', 'nil'),
    identifier: $ => /[a-zA-Z_]\w*/,

    comment: $ => choice(
      seq('//', /.*$/),
      seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/'),
      seq('#', /.*$/),
    ),
  },
});

function commaSep(rule) {
  return optional(commaSep1(rule));
}

function commaSep1(rule) {
  return seq(rule, repeat(seq(',', rule)));
}

function prec_left(prec, rule) {
  if (typeof prec === 'number') {
    return { type: 'PREC_LEFT', value: prec, content: rule };
  }
  return { type: 'PREC_LEFT', value: 0, content: prec };
}

function prec_right(rule) {
  return { type: 'PREC_RIGHT', value: 0, content: rule };
}

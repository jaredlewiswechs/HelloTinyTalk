"""
TinyTalk Help System
Inline documentation for functions, operators, and language features.

Powers the Help pane in the RStudio-style IDE.
"""

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Function documentation entries
# ---------------------------------------------------------------------------

FUNCTION_DOCS: Dict[str, dict] = {
    # --- Output ---
    "show": {
        "signature": "show(value1, value2, ...)",
        "description": "Print values to output, separated by spaces, followed by a newline.",
        "category": "Output",
        "examples": ['show("Hello, world!")', 'show("Score:" score)'],
    },
    "print": {
        "signature": "print(value1, value2, ...)",
        "description": "Print values without a trailing newline.",
        "category": "Output",
        "examples": ['print("Loading...")'],
    },
    # --- Math ---
    "abs": {
        "signature": "abs(n)",
        "description": "Absolute value of a number.",
        "category": "Math",
        "examples": ["abs(-5)  // 5"],
    },
    "round": {
        "signature": "round(n [, decimals])",
        "description": "Round a number. Optional decimal places (default 0).",
        "category": "Math",
        "examples": ["round(3.14159, 2)  // 3.14"],
    },
    "sqrt": {
        "signature": "sqrt(n)",
        "description": "Square root.",
        "category": "Math",
        "examples": ["sqrt(16)  // 4.0"],
    },
    "floor": {
        "signature": "floor(n)",
        "description": "Round down to nearest integer.",
        "category": "Math",
        "examples": ["floor(3.7)  // 3"],
    },
    "ceil": {
        "signature": "ceil(n)",
        "description": "Round up to nearest integer.",
        "category": "Math",
        "examples": ["ceil(3.2)  // 4"],
    },
    "log": {
        "signature": "log(n)",
        "description": "Natural logarithm (base e).",
        "category": "Math",
        "examples": ["log(E)  // 1.0"],
    },
    "exp": {
        "signature": "exp(n)",
        "description": "e raised to the power n.",
        "category": "Math",
        "examples": ["exp(1)  // 2.718..."],
    },
    "pow": {
        "signature": "pow(base, exponent)",
        "description": "Raise base to the power of exponent.",
        "category": "Math",
        "examples": ["pow(2, 10)  // 1024"],
    },
    "sin": {"signature": "sin(radians)", "description": "Sine function.", "category": "Math", "examples": ["sin(PI / 2)  // 1.0"]},
    "cos": {"signature": "cos(radians)", "description": "Cosine function.", "category": "Math", "examples": ["cos(0)  // 1.0"]},
    "tan": {"signature": "tan(radians)", "description": "Tangent function.", "category": "Math", "examples": ["tan(PI / 4)  // 1.0"]},
    "sum": {"signature": "sum(list)", "description": "Sum all numbers in a list.", "category": "Math", "examples": ["sum([1, 2, 3])  // 6"]},
    "min": {"signature": "min(a, b) or min(list)", "description": "Minimum of two values or a list.", "category": "Math", "examples": ["min(3, 7)  // 3"]},
    "max": {"signature": "max(a, b) or max(list)", "description": "Maximum of two values or a list.", "category": "Math", "examples": ["max(3, 7)  // 7"]},

    # --- Statistics ---
    "mean": {
        "signature": "mean(list)",
        "description": "Arithmetic mean (average) of a list of numbers.",
        "category": "Statistics",
        "examples": ["mean([1, 2, 3, 4, 5])  // 3.0"],
    },
    "median": {
        "signature": "median(list)",
        "description": "Middle value of a sorted list. For even-length lists, returns the average of the two middle values.",
        "category": "Statistics",
        "examples": ["median([1, 3, 5, 7, 9])  // 5.0", "median([1, 2, 3, 4])  // 2.5"],
    },
    "sd": {
        "signature": "sd(list)",
        "description": "Sample standard deviation (n-1 denominator, R-compatible).",
        "category": "Statistics",
        "examples": ["sd([2, 4, 4, 4, 5, 5, 7, 9])  // 2.138..."],
    },
    "variance": {
        "signature": "variance(list)",
        "description": "Sample variance (n-1 denominator).",
        "category": "Statistics",
        "examples": ["variance([2, 4, 4, 4, 5, 5, 7, 9])  // 4.571..."],
    },
    "cor": {
        "signature": "cor(x, y)",
        "description": "Pearson correlation coefficient between two numeric lists. Returns a value between -1 and 1.",
        "category": "Statistics",
        "examples": ["cor([1, 2, 3], [2, 4, 6])  // 1.0"],
    },
    "cov": {
        "signature": "cov(x, y)",
        "description": "Sample covariance between two numeric lists.",
        "category": "Statistics",
        "examples": ["cov([1, 2, 3], [2, 4, 6])  // 2.0"],
    },
    "lm": {
        "signature": "lm(y, x)",
        "description": "Simple linear regression. Like R's lm(y ~ x). Returns {slope, intercept, r_squared, se, t, n, residuals}.",
        "category": "Statistics",
        "examples": [
            'let model = lm([2, 4, 6], [1, 2, 3])',
            'show(model["slope"])       // 2.0',
            'show(model["r_squared"])   // 1.0',
        ],
    },
    "t_test": {
        "signature": "t_test(x, y)",
        "description": "Two-sample Welch's t-test. Like R's t.test(x, y). Returns {t, df, p, mean_x, mean_y, diff, ci_lower, ci_upper}.",
        "category": "Statistics",
        "examples": [
            'let result = t_test([5, 6, 7, 8], [3, 4, 5, 6])',
            'show("p-value:" result["p"])',
        ],
    },
    "summary": {
        "signature": "summary(list)",
        "description": "R-style 6-number summary: {min, q1, median, mean, q3, max, n}.",
        "category": "Statistics",
        "examples": ["summary([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])"],
    },
    "quantile": {
        "signature": "quantile(list, p)",
        "description": "Compute the p-th quantile (0 to 1) using linear interpolation.",
        "category": "Statistics",
        "examples": ["quantile([1, 2, 3, 4, 5], 0.25)  // 2.0"],
    },
    "iqr": {
        "signature": "iqr(list)",
        "description": "Interquartile range (Q3 - Q1).",
        "category": "Statistics",
        "examples": ["iqr([1, 2, 3, 4, 5, 6, 7, 8])"],
    },
    "scale": {
        "signature": "scale(list)",
        "description": "Standardize values to z-scores (mean=0, sd=1). Like R's scale().",
        "category": "Statistics",
        "examples": ["scale([2, 4, 4, 4, 5, 5, 7, 9])"],
    },
    "cumsum": {
        "signature": "cumsum(list)",
        "description": "Cumulative sum. Like R's cumsum().",
        "category": "Statistics",
        "examples": ["cumsum([1, 2, 3, 4])  // [1, 3, 6, 10]"],
    },
    "diff": {
        "signature": "diff(list)",
        "description": "Successive differences. Like R's diff().",
        "category": "Statistics",
        "examples": ["diff([1, 3, 6, 10])  // [2, 3, 4]"],
    },
    "table": {
        "signature": "table(list)",
        "description": "Frequency table. Like R's table(). Returns a map of {value: count}.",
        "category": "Statistics",
        "examples": ['table(["a", "b", "a", "c", "b", "a"])  // {"a": 3, "b": 2, "c": 1}'],
    },

    # --- Distributions ---
    "dnorm": {
        "signature": "dnorm(x [, mean, sd])",
        "description": "Normal probability density function. Default: mean=0, sd=1.",
        "category": "Distributions",
        "examples": ["dnorm(0)  // 0.3989..."],
    },
    "pnorm": {
        "signature": "pnorm(x [, mean, sd])",
        "description": "Normal cumulative distribution function. P(X <= x).",
        "category": "Distributions",
        "examples": ["pnorm(1.96)  // 0.975..."],
    },
    "qnorm": {
        "signature": "qnorm(p [, mean, sd])",
        "description": "Normal quantile function (inverse CDF). What value gives probability p?",
        "category": "Distributions",
        "examples": ["qnorm(0.975)  // 1.96..."],
    },
    "rnorm": {
        "signature": "rnorm(n [, mean, sd])",
        "description": "Generate n random values from a normal distribution.",
        "category": "Distributions",
        "examples": ["rnorm(100, 50, 10)  // 100 values with mean=50, sd=10"],
    },
    "runif": {
        "signature": "runif(n [, min, max])",
        "description": "Generate n random uniform values between min and max.",
        "category": "Distributions",
        "examples": ["runif(10, 0, 100)  // 10 random values 0-100"],
    },
    "rbinom": {
        "signature": "rbinom(n, size, prob)",
        "description": "Generate n random binomial values.",
        "category": "Distributions",
        "examples": ["rbinom(10, 1, 0.5)  // 10 coin flips"],
    },

    # --- Random / Sampling ---
    "sample": {
        "signature": "sample(list, n [, replace])",
        "description": "Random sample of n items. Default: without replacement. Like R's sample().",
        "category": "Sampling",
        "examples": [
            'sample([1, 2, 3, 4, 5], 3)           // 3 random items',
            'sample(["a", "b", "c"], 5, true)      // 5 items with replacement',
        ],
    },
    "set_seed": {
        "signature": "set_seed(n)",
        "description": "Set random seed for reproducibility. Like R's set.seed().",
        "category": "Sampling",
        "examples": ["set_seed(42)"],
    },
    "shuffle": {
        "signature": "shuffle(list)",
        "description": "Return a randomly shuffled copy of the list.",
        "category": "Sampling",
        "examples": ["shuffle([1, 2, 3, 4, 5])"],
    },
    "seq": {
        "signature": "seq(from, to [, by])",
        "description": "Generate a numeric sequence. Like R's seq().",
        "category": "Sampling",
        "examples": ["seq(1, 10, 2)  // [1, 3, 5, 7, 9]"],
    },
    "rep": {
        "signature": "rep(value, n)",
        "description": "Repeat a value n times. Like R's rep().",
        "category": "Sampling",
        "examples": ["rep(0, 5)  // [0, 0, 0, 0, 0]"],
    },

    # --- NA Handling ---
    "is_na": {
        "signature": "is_na(value)",
        "description": "Check if a value is null/NA. Works on single values or lists. Like R's is.na().",
        "category": "NA Handling",
        "examples": ["is_na(null)  // true", "is_na([1, null, 3])  // [false, true, false]"],
    },
    "na_rm": {
        "signature": "na_rm(list)",
        "description": "Remove null/NA values from a list.",
        "category": "NA Handling",
        "examples": ["na_rm([1, null, 3, null, 5])  // [1, 3, 5]"],
    },
    "complete_cases": {
        "signature": "complete_cases(data)",
        "description": "Filter rows that have no null values. Like R's complete.cases().",
        "category": "NA Handling",
        "examples": ["complete_cases(data)"],
    },
    "which_min": {
        "signature": "which_min(list)",
        "description": "Index of the minimum value. Like R's which.min().",
        "category": "NA Handling",
        "examples": ["which_min([5, 2, 8, 1, 4])  // 3"],
    },
    "which_max": {
        "signature": "which_max(list)",
        "description": "Index of the maximum value. Like R's which.max().",
        "category": "NA Handling",
        "examples": ["which_max([5, 2, 8, 1, 4])  // 2"],
    },

    # --- Collections ---
    "len": {"signature": "len(value)", "description": "Length of a string, list, or map.", "category": "Collections", "examples": ["len([1, 2, 3])  // 3"]},
    "range": {"signature": "range(n) or range(start, end [, step])", "description": "Generate a list of integers.", "category": "Collections", "examples": ["range(5)  // [0, 1, 2, 3, 4]"]},
    "append": {"signature": "append(list, item)", "description": "Append an item to a list (mutates).", "category": "Collections", "examples": ["append(myList, 42)"]},
    "keys": {"signature": "keys(map)", "description": "Get all keys of a map as a list.", "category": "Collections", "examples": ['keys({"a": 1, "b": 2})  // ["a", "b"]']},
    "values": {"signature": "values(map)", "description": "Get all values of a map as a list.", "category": "Collections", "examples": ['values({"a": 1, "b": 2})  // [1, 2]']},
    "contains": {"signature": "contains(collection, item)", "description": "Check if a list contains an item or a map contains a key.", "category": "Collections", "examples": ["contains([1, 2, 3], 2)  // true"]},
    "sort": {"signature": "sort(list)", "description": "Sort a list in ascending order.", "category": "Collections", "examples": ["sort([3, 1, 2])  // [1, 2, 3]"]},
    "reverse": {"signature": "reverse(list)", "description": "Reverse a list.", "category": "Collections", "examples": ["reverse([1, 2, 3])  // [3, 2, 1]"]},
    "zip": {"signature": "zip(list1, list2)", "description": "Pair up elements from two lists.", "category": "Collections", "examples": ["zip([1, 2], [\"a\", \"b\"])  // [[1, \"a\"], [2, \"b\"]]"]},

    # --- Strings ---
    "split": {"signature": "split(str, delimiter)", "description": "Split a string by delimiter.", "category": "Strings", "examples": ['split("a,b,c", ",")  // ["a", "b", "c"]']},
    "join": {"signature": "join(list, separator)", "description": "Join list items into a string.", "category": "Strings", "examples": ['join(["a", "b", "c"], ", ")  // "a, b, c"']},
    "replace": {"signature": "replace(str, old, new)", "description": "Replace occurrences in a string.", "category": "Strings", "examples": ['replace("hello", "l", "r")  // "herro"']},
    "trim": {"signature": "trim(str)", "description": "Remove leading and trailing whitespace.", "category": "Strings", "examples": ['trim("  hello  ")  // "hello"']},
    "upcase": {"signature": "upcase(str)", "description": "Convert to uppercase.", "category": "Strings", "examples": ['upcase("hello")  // "HELLO"']},
    "downcase": {"signature": "downcase(str)", "description": "Convert to lowercase.", "category": "Strings", "examples": ['downcase("HELLO")  // "hello"']},

    # --- Type Conversion ---
    "str": {"signature": "str(value)", "description": "Convert any value to a string.", "category": "Types", "examples": ["str(42)  // \"42\""]},
    "int": {"signature": "int(value)", "description": "Convert to integer.", "category": "Types", "examples": ['int("42")  // 42']},
    "float": {"signature": "float(value)", "description": "Convert to float.", "category": "Types", "examples": ['float("3.14")  // 3.14']},
    "bool": {"signature": "bool(value)", "description": "Convert to boolean.", "category": "Types", "examples": ["bool(0)  // false"]},
    "type": {"signature": "type(value)", "description": "Get the type name as a string.", "category": "Types", "examples": ['type(42)  // "int"']},
    "DataFrame": {
        "signature": "DataFrame(list_of_maps)",
        "description": "Create a columnar DataFrame from a list of maps. Supports the same step chain syntax as lists. Access .columns, .shape, .nrows properties.",
        "category": "Types",
        "examples": [
            'let df = DataFrame(data)',
            'df.columns  // ["name", "age"]',
            'df.shape    // [100, 3]',
            'df _filter((r) => r["age"] > 30)  // returns DataFrame',
        ],
    },

    # --- I/O ---
    "read_csv": {"signature": 'read_csv("file.csv")', "description": "Read a CSV file into a list of maps (one map per row).", "category": "Data I/O", "examples": ['let data = read_csv("sales.csv")']},
    "write_csv": {"signature": 'write_csv(data, "file.csv")', "description": "Write a list of maps to a CSV file.", "category": "Data I/O", "examples": ['write_csv(results, "output.csv")']},
    "read_json": {"signature": 'read_json("file.json")', "description": "Read and parse a JSON file.", "category": "Data I/O", "examples": ['let config = read_json("config.json")']},
    "parse_json": {"signature": "parse_json(str)", "description": "Parse a JSON string into a TinyTalk value.", "category": "Data I/O", "examples": ['parse_json(\'{"key": "value"}\')']},
    "to_json": {"signature": "to_json(value)", "description": "Convert a TinyTalk value to a JSON string.", "category": "Data I/O", "examples": ['to_json({"key": "value"})']},

    # --- Charts ---
    "chart_bar": {"signature": "chart_bar(labels, values [, title])", "description": "Render a bar chart.", "category": "Visualization", "examples": ['chart_bar(["A", "B", "C"], [10, 20, 30], "Sales")']},
    "chart_line": {"signature": "chart_line(labels, values [, title])", "description": "Render a line chart.", "category": "Visualization", "examples": ['chart_line(["Jan", "Feb", "Mar"], [100, 150, 120], "Revenue")']},
    "chart_pie": {"signature": "chart_pie(labels, values [, title])", "description": "Render a pie chart.", "category": "Visualization", "examples": ['chart_pie(["A", "B", "C"], [40, 35, 25], "Market Share")']},
    "chart_scatter": {"signature": "chart_scatter(x, y [, title])", "description": "Render a scatter plot.", "category": "Visualization", "examples": ['chart_scatter(x_values, y_values, "Correlation")']},
    "chart_histogram": {"signature": "chart_histogram(data [, bins] [, title])", "description": "Render a histogram.", "category": "Visualization", "examples": ['chart_histogram(scores, 10, "Score Distribution")']},
    "chart_multi": {"signature": "chart_multi(labels, series_map [, title])", "description": "Multi-series line chart.", "category": "Visualization", "examples": ['chart_multi(months, {"Sales": s, "Costs": c}, "Comparison")']},

    # --- Date/Time ---
    "date_now": {"signature": "date_now()", "description": "Current date/time as ISO string.", "category": "Date/Time", "examples": ["date_now()"]},
    "date_parse": {"signature": 'date_parse(str [, format])', "description": "Parse a date string.", "category": "Date/Time", "examples": ['date_parse("2024-01-15")']},
    "date_format": {"signature": 'date_format(date, format)', "description": "Format a date string.", "category": "Date/Time", "examples": ['date_format(date_now(), "%Y-%m-%d")']},
    "date_diff": {"signature": "date_diff(date1, date2, unit)", "description": "Difference between two dates.", "category": "Date/Time", "examples": ['date_diff(start, end, "days")']},
    "date_add": {"signature": "date_add(date, amount, unit)", "description": "Add time to a date.", "category": "Date/Time", "examples": ['date_add(date_now(), 7, "days")']},

    # --- Regex ---
    "regex_match": {"signature": "regex_match(str, pattern)", "description": "Test if string matches pattern.", "category": "Regex", "examples": ['regex_match("hello123", "\\\\d+")']},
    "regex_find": {"signature": "regex_find(str, pattern)", "description": "Find all matches of pattern in string.", "category": "Regex", "examples": ['regex_find("a1b2c3", "\\\\d+")  // ["1", "2", "3"]']},
    "regex_replace": {"signature": "regex_replace(str, pattern, replacement)", "description": "Replace pattern matches.", "category": "Regex", "examples": ['regex_replace("hello world", "\\\\s+", "_")']},

    # --- HTTP ---
    "http_get": {"signature": "http_get(url)", "description": "Make an HTTP GET request. Returns parsed JSON or string.", "category": "HTTP", "examples": ['let data = http_get("https://api.example.com/data")']},
    "http_post": {"signature": "http_post(url, data)", "description": "Make an HTTP POST request with JSON body.", "category": "HTTP", "examples": ['http_post("https://api.example.com/submit", payload)']},

    # --- File System ---
    "file_read": {"signature": "file_read(path)", "description": "Read a file's contents as a string.", "category": "File System", "examples": ['let text = file_read("notes.txt")']},
    "file_write": {"signature": "file_write(path, content)", "description": "Write a string to a file.", "category": "File System", "examples": ['file_write("output.txt", result)']},
    "file_exists": {"signature": "file_exists(path)", "description": "Check if a file exists.", "category": "File System", "examples": ['file_exists("data.csv")  // true']},
    "file_list": {"signature": "file_list(directory)", "description": "List files in a directory.", "category": "File System", "examples": ['file_list("./data")']},
}


# ---------------------------------------------------------------------------
# Step chain documentation
# ---------------------------------------------------------------------------

STEP_DOCS: Dict[str, dict] = {
    "_filter": {
        "signature": "data _filter(predicate)",
        "description": "Keep only items where predicate returns true. Like R's filter() or dplyr::filter().",
        "examples": ['data _filter((r) => r["age"] > 30)'],
    },
    "_map": {
        "signature": "data _map(fn)",
        "description": "Transform each item. Like R's sapply() or purrr::map().",
        "examples": ['[1, 2, 3] _map((x) => x * 2)  // [2, 4, 6]'],
    },
    "_sort": {
        "signature": "data _sort or data _sort(fn)",
        "description": "Sort in ascending order. Optionally accepts a key function.",
        "examples": [
            "[3, 1, 2] _sort  // [1, 2, 3]",
            'people _sort((r) => r["age"])  // sort by key',
        ],
    },
    "_sortBy": {
        "signature": "data _sortBy(fn)",
        "description": "Sort by a computed key.",
        "examples": ['data _sortBy((r) => r["name"])'],
    },
    "_reverse": {"signature": "data _reverse", "description": "Reverse order.", "examples": ["[1, 2, 3] _reverse  // [3, 2, 1]"]},
    "_take": {"signature": "data _take(n)", "description": "First n items. Like R's head().", "examples": ["[1, 2, 3, 4, 5] _take(3)  // [1, 2, 3]"]},
    "_drop": {"signature": "data _drop(n)", "description": "Skip first n items. Like R's tail(-n).", "examples": ["[1, 2, 3, 4, 5] _drop(2)  // [3, 4, 5]"]},
    "_first": {"signature": "data _first", "description": "Get the first item.", "examples": ["[1, 2, 3] _first  // 1"]},
    "_last": {"signature": "data _last", "description": "Get the last item.", "examples": ["[1, 2, 3] _last  // 3"]},
    "_count": {"signature": "data _count", "description": "Count items. Like R's length() or nrow().", "examples": ["[1, 2, 3] _count  // 3"]},
    "_sum": {"signature": "data _sum", "description": "Sum all values.", "examples": ["[1, 2, 3] _sum  // 6"]},
    "_avg": {"signature": "data _avg", "description": "Average of all values. Like R's mean().", "examples": ["[1, 2, 3, 4, 5] _avg  // 3.0"]},
    "_min": {"signature": "data _min", "description": "Minimum value.", "examples": ["[3, 1, 2] _min  // 1"]},
    "_max": {"signature": "data _max", "description": "Maximum value.", "examples": ["[3, 1, 2] _max  // 3"]},
    "_unique": {"signature": "data _unique", "description": "Remove duplicates. Like R's unique().", "examples": ["[1, 2, 2, 3, 1] _unique  // [1, 2, 3]"]},
    "_flatten": {"signature": "data _flatten", "description": "Flatten nested lists. Like R's unlist().", "examples": ["[[1, 2], [3, 4]] _flatten  // [1, 2, 3, 4]"]},
    "_group": {"signature": "data _group(fn)", "description": "Group items by key. Like R's split() or dplyr::group_by().", "examples": ['data _group((r) => r["category"])']},
    "_reduce": {"signature": "data _reduce(fn, initial)", "description": "Reduce to a single value. Like R's Reduce().", "examples": ["[1, 2, 3, 4] _reduce((acc, x) => acc + x, 0)  // 10"]},
    "_select": {"signature": 'data _select("col1", "col2")', "description": "Select columns from tabular data. Like dplyr::select().", "examples": ['data _select("name", "age")']},
    "_mutate": {"signature": "data _mutate(fn)", "description": "Add or modify columns. Like dplyr::mutate().", "examples": ['data _mutate((r) => {"total": r["price"] * r["qty"]})']},
    "_summarize": {"signature": "grouped _summarize(aggs)", "description": "Aggregate groups. Like dplyr::summarize().", "examples": ['grouped _summarize({"total": (g) => g _map(...) _sum})']},
    "_rename": {"signature": 'data _rename({"old": "new"})', "description": "Rename columns. Like dplyr::rename().", "examples": ['data _rename({"nm": "name"})']},
    "_arrange": {"signature": 'data _arrange(fn, "desc")', "description": "Sort rows. Like dplyr::arrange().", "examples": ['data _arrange((r) => r["score"], "desc")']},
    "_distinct": {"signature": "data _distinct(fn)", "description": "Unique rows by key. Like dplyr::distinct().", "examples": ['data _distinct((r) => r["id"])']},
    "_pull": {"signature": 'data _pull("column")', "description": "Extract a single column as a list. Like dplyr::pull().", "examples": ['data _pull("name")  // ["Alice", "Bob", ...]']},
    "_leftJoin": {"signature": "data _leftJoin(other, fn)", "description": "Left join two datasets. Like dplyr::left_join().", "examples": ['data _leftJoin(lookup, (a, b) => a["id"] == b["id"])']},
    "_pivot": {"signature": "data _pivot(row_fn, col_fn, val_fn)", "description": "Reshape long to wide. Like tidyr::pivot_wider().", "examples": ['data _pivot((r) => r["year"], (r) => r["metric"], (r) => r["value"])']},
    "_unpivot": {"signature": 'data _unpivot("id_col")', "description": "Reshape wide to long. Like tidyr::pivot_longer().", "examples": ['data _unpivot("name")']},
    "_window": {"signature": "data _window(n, fn)", "description": "Rolling window aggregation.", "examples": ["data _window(3, (w) => w _avg)  // 3-period moving average"]},
    "_chunk": {"signature": "data _chunk(n)", "description": "Split into chunks of size n.", "examples": ["[1, 2, 3, 4, 5, 6] _chunk(2)  // [[1, 2], [3, 4], [5, 6]]"]},
    "_zip": {"signature": "data _zip(other)", "description": "Pair elements from two lists.", "examples": ['[1, 2, 3] _zip(["a", "b", "c"])']},
    "_each": {"signature": "data _each(fn)", "description": "Execute fn for each item (side effects).", "examples": ["data _each((item) => show(item))"]},
    "_groupBy": {"signature": "data _groupBy(fn)", "description": "Alias for _group.", "examples": ['data _groupBy((r) => r["dept"])']},
}


# ---------------------------------------------------------------------------
# Language feature documentation
# ---------------------------------------------------------------------------

LANGUAGE_DOCS: Dict[str, dict] = {
    "let": {"description": "Declare a variable.", "examples": ['let name = "Alice"', "let score = 95"]},
    "const": {"description": "Declare a constant (cannot be reassigned).", "examples": ["const PI = 3.14159"]},
    "fn": {"description": "Define a function.", "examples": ["fn add(a, b) {\n    return a + b\n}"]},
    "if": {"description": "Conditional execution.", "examples": ["if score > 90 {\n    show(\"A\")\n} else {\n    show(\"B\")\n}"]},
    "for": {"description": "Loop over a range or list.", "examples": ["for i in range(10) {\n    show(i)\n}", "for item in data {\n    show(item)\n}"]},
    "while": {"description": "Loop while condition is true.", "examples": ["while count > 0 {\n    count = count - 1\n}"]},
    "match": {"description": "Pattern matching (like switch).", "examples": ['match grade {\n    "A" => show("Excellent")\n    "B" => show("Good")\n    _ => show("Other")\n}']},
    "struct": {"description": "Define a custom data structure.", "examples": ["struct Point {\n    x: int\n    y: int\n}"]},
    "enum": {"description": "Define an enumeration.", "examples": ["enum Color {\n    Red\n    Green\n    Blue\n}"]},
    "try": {"description": "Error handling.", "examples": ['try {\n    risky_operation()\n} catch e {\n    show("Error:" e)\n}']},
    "import": {"description": "Import from another module.", "examples": ['import "utils.tt"', 'from python use math']},
    "step_chains": {
        "description": "TinyTalk's signature feature: chain operations with underscore-prefixed steps. Like R's pipe operator (|>) or dplyr chains.",
        "examples": [
            'let top = data\n    _filter((r) => r["score"] > 80)\n    _sortBy((r) => r["score"])\n    _reverse\n    _take(5)',
            "[1, 2, 3, 4, 5] _filter((x) => x > 2) _map((x) => x * 10) _sum",
        ],
    },
}


# ---------------------------------------------------------------------------
# Search / Lookup
# ---------------------------------------------------------------------------

def get_categories() -> List[str]:
    """Return all unique function categories."""
    cats = set()
    for doc in FUNCTION_DOCS.values():
        cats.add(doc.get("category", "Other"))
    return sorted(cats)


def search_help(query: str) -> List[dict]:
    """Search help entries by name or description."""
    query = query.lower()
    results = []

    for name, doc in FUNCTION_DOCS.items():
        if query in name.lower() or query in doc.get("description", "").lower():
            results.append({"type": "function", "name": name, **doc})

    for name, doc in STEP_DOCS.items():
        if query in name.lower() or query in doc.get("description", "").lower():
            results.append({"type": "step", "name": name, **doc})

    for name, doc in LANGUAGE_DOCS.items():
        if query in name.lower() or query in doc.get("description", "").lower():
            results.append({"type": "keyword", "name": name, **doc})

    return results


def get_help(name: str) -> Optional[dict]:
    """Get help for a specific function, step, or keyword."""
    if name in FUNCTION_DOCS:
        return {"type": "function", "name": name, **FUNCTION_DOCS[name]}
    if name in STEP_DOCS:
        return {"type": "step", "name": name, **STEP_DOCS[name]}
    if name in LANGUAGE_DOCS:
        return {"type": "keyword", "name": name, **LANGUAGE_DOCS[name]}
    # Try with underscore prefix for steps
    if "_" + name in STEP_DOCS:
        return {"type": "step", "name": "_" + name, **STEP_DOCS["_" + name]}
    return None


def get_all_functions_by_category() -> Dict[str, List[dict]]:
    """Return all functions grouped by category."""
    by_cat: Dict[str, List[dict]] = {}
    for name, doc in FUNCTION_DOCS.items():
        cat = doc.get("category", "Other")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append({"name": name, **doc})
    # Sort each category by name
    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: x["name"])
    return by_cat

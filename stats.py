"""
TinyTalk Statistics Library
R-level statistical computing for TinyTalk.

Provides: descriptive stats, correlation, regression, t-tests,
probability distributions, random sampling, and summary tables.

Usage in TinyTalk:
    let scores = [85, 92, 78, 95, 88, 76, 91, 83, 79, 94]
    show(median(scores))       // 86.5
    show(sd(scores))           // 6.96
    show(quantile(scores, 0.25))  // 79.0
    show(summary(scores))      // {min: 76, q1: 79, median: 86.5, ...}
    show(cor(x, y))            // 0.87
    show(t_test(a, b))         // {t: 2.31, p: 0.034, ...}
    let model = lm(y, x)      // {slope: 1.5, intercept: 3.2, r_squared: 0.76}
"""

from typing import List
import math
import random as _random

from .tt_types import Value, ValueType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_numbers(val: Value) -> List[float]:
    """Extract a list of floats from a TinyTalk list Value."""
    if val.type != ValueType.LIST:
        raise ValueError("Expected a list of numbers")
    nums = []
    for v in val.data:
        if v.type in (ValueType.INT, ValueType.FLOAT):
            nums.append(float(v.data))
        elif v.type == ValueType.NULL:
            continue  # skip NA/null values
        else:
            raise ValueError(f"Expected number, got {v.type.value}")
    return nums


def _extract_numbers_with_na(val: Value) -> List[float | None]:
    """Extract numbers, preserving nulls as None (NA)."""
    if val.type != ValueType.LIST:
        raise ValueError("Expected a list of numbers")
    result = []
    for v in val.data:
        if v.type in (ValueType.INT, ValueType.FLOAT):
            result.append(float(v.data))
        elif v.type == ValueType.NULL:
            result.append(None)
        else:
            raise ValueError(f"Expected number or null, got {v.type.value}")
    return result


def _na_rm(nums: List[float | None]) -> List[float]:
    """Remove NA (None) values."""
    return [x for x in nums if x is not None]


# ---------------------------------------------------------------------------
# Descriptive Statistics
# ---------------------------------------------------------------------------

def builtin_median(args: List[Value]) -> Value:
    """median(list) — middle value of a sorted list."""
    if not args:
        raise ValueError("median expects a list of numbers")
    nums = sorted(_extract_numbers(args[0]))
    if not nums:
        return Value.null_val()
    n = len(nums)
    mid = n // 2
    if n % 2 == 0:
        return Value.float_val((nums[mid - 1] + nums[mid]) / 2)
    return Value.float_val(nums[mid])


def builtin_mean(args: List[Value]) -> Value:
    """mean(list) — arithmetic mean."""
    if not args:
        raise ValueError("mean expects a list of numbers")
    nums = _extract_numbers(args[0])
    if not nums:
        return Value.null_val()
    return Value.float_val(sum(nums) / len(nums))


def builtin_sd(args: List[Value]) -> Value:
    """sd(list) — sample standard deviation (R-compatible: n-1 denominator)."""
    if not args:
        raise ValueError("sd expects a list of numbers")
    nums = _extract_numbers(args[0])
    if len(nums) < 2:
        return Value.null_val()
    m = sum(nums) / len(nums)
    variance = sum((x - m) ** 2 for x in nums) / (len(nums) - 1)
    return Value.float_val(math.sqrt(variance))


def builtin_variance(args: List[Value]) -> Value:
    """variance(list) — sample variance (n-1 denominator)."""
    if not args:
        raise ValueError("variance expects a list of numbers")
    nums = _extract_numbers(args[0])
    if len(nums) < 2:
        return Value.null_val()
    m = sum(nums) / len(nums)
    return Value.float_val(sum((x - m) ** 2 for x in nums) / (len(nums) - 1))


def builtin_quantile(args: List[Value]) -> Value:
    """quantile(list, p) — p-th quantile (0 to 1). Uses linear interpolation."""
    if len(args) < 2:
        raise ValueError("quantile expects (list, p)")
    nums = sorted(_extract_numbers(args[0]))
    if not nums:
        return Value.null_val()
    p = float(args[1].data)
    if p < 0 or p > 1:
        raise ValueError("Quantile p must be between 0 and 1")
    if p == 0:
        return Value.float_val(nums[0])
    if p == 1:
        return Value.float_val(nums[-1])
    idx = p * (len(nums) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    frac = idx - lo
    return Value.float_val(nums[lo] * (1 - frac) + nums[hi] * frac)


def builtin_iqr(args: List[Value]) -> Value:
    """iqr(list) — interquartile range (Q3 - Q1)."""
    q1 = builtin_quantile([args[0], Value.float_val(0.25)])
    q3 = builtin_quantile([args[0], Value.float_val(0.75)])
    if q1.type == ValueType.NULL or q3.type == ValueType.NULL:
        return Value.null_val()
    return Value.float_val(q3.data - q1.data)


def builtin_summary(args: List[Value]) -> Value:
    """summary(list) — R-style 6-number summary: min, q1, median, mean, q3, max."""
    if not args:
        raise ValueError("summary expects a list of numbers")
    nums = sorted(_extract_numbers(args[0]))
    if not nums:
        return Value.null_val()
    n = len(nums)
    m = sum(nums) / n

    def _q(p):
        return builtin_quantile([args[0], Value.float_val(p)]).data

    return Value.map_val({
        "min": Value.float_val(nums[0]),
        "q1": Value.float_val(_q(0.25)),
        "median": Value.float_val(_q(0.5)),
        "mean": Value.float_val(m),
        "q3": Value.float_val(_q(0.75)),
        "max": Value.float_val(nums[-1]),
        "n": Value.int_val(n),
    })


# ---------------------------------------------------------------------------
# Correlation & Covariance
# ---------------------------------------------------------------------------

def builtin_cor(args: List[Value]) -> Value:
    """cor(x, y) — Pearson correlation coefficient."""
    if len(args) < 2:
        raise ValueError("cor expects (x_list, y_list)")
    x = _extract_numbers(args[0])
    y = _extract_numbers(args[1])
    if len(x) != len(y):
        raise ValueError(f"cor: x and y must have the same length ({len(x)} vs {len(y)})")
    n = len(x)
    if n < 2:
        return Value.null_val()
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / (n - 1))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / (n - 1))
    if sx == 0 or sy == 0:
        return Value.null_val()
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1)
    return Value.float_val(cov / (sx * sy))


def builtin_cov(args: List[Value]) -> Value:
    """cov(x, y) — sample covariance."""
    if len(args) < 2:
        raise ValueError("cov expects (x_list, y_list)")
    x = _extract_numbers(args[0])
    y = _extract_numbers(args[1])
    if len(x) != len(y):
        raise ValueError(f"cov: x and y must have the same length ({len(x)} vs {len(y)})")
    n = len(x)
    if n < 2:
        return Value.null_val()
    mx, my = sum(x) / n, sum(y) / n
    return Value.float_val(sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1))


# ---------------------------------------------------------------------------
# Linear Regression
# ---------------------------------------------------------------------------

def builtin_lm(args: List[Value]) -> Value:
    """lm(y, x) — simple linear regression. Returns {slope, intercept, r_squared, residuals}.

    Like R's lm(y ~ x) but with positional args.
    """
    if len(args) < 2:
        raise ValueError("lm expects (y_list, x_list)")
    y = _extract_numbers(args[0])
    x = _extract_numbers(args[1])
    if len(x) != len(y):
        raise ValueError(f"lm: x and y must have the same length ({len(x)} vs {len(y)})")
    n = len(x)
    if n < 2:
        raise ValueError("lm: need at least 2 data points")
    mx, my = sum(x) / n, sum(y) / n
    ss_xx = sum((xi - mx) ** 2 for xi in x)
    ss_xy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    if ss_xx == 0:
        raise ValueError("lm: all x values are identical")
    slope = ss_xy / ss_xx
    intercept = my - slope * mx
    # R-squared
    y_pred = [slope * xi + intercept for xi in x]
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    ss_tot = sum((yi - my) ** 2 for yi in y)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    # Residuals
    residuals = [yi - yp for yi, yp in zip(y, y_pred)]
    # Standard error of slope
    if n > 2 and ss_xx > 0:
        se = math.sqrt(ss_res / (n - 2)) / math.sqrt(ss_xx)
        t_stat = slope / se if se > 0 else float('inf')
    else:
        se = 0
        t_stat = float('inf')

    return Value.map_val({
        "slope": Value.float_val(slope),
        "intercept": Value.float_val(intercept),
        "r_squared": Value.float_val(r_squared),
        "se": Value.float_val(se),
        "t": Value.float_val(t_stat),
        "n": Value.int_val(n),
        "residuals": Value.list_val([Value.float_val(r) for r in residuals]),
    })


# ---------------------------------------------------------------------------
# T-Test
# ---------------------------------------------------------------------------

def _t_cdf(t, df):
    """Approximate two-tailed p-value for Student's t-distribution.

    Uses the regularized incomplete beta function relationship.
    For large df, this is very accurate; for small df it's a good approximation.
    """
    x = df / (df + t * t)
    # Use the regularized incomplete beta function via math.gamma
    # P(T > |t|) = I_x(df/2, 1/2)
    # We use a simple continued-fraction approximation
    a, b = df / 2.0, 0.5
    # For the beta regularized incomplete function, use a series expansion
    if x >= (a + 1) / (a + b + 2):
        p = 1.0 - _beta_inc(b, a, 1.0 - x)
    else:
        p = _beta_inc(a, b, x)
    return p  # This is already two-tailed since we use t^2


def _beta_inc(a, b, x):
    """Regularized incomplete beta function I_x(a, b) via continued fraction."""
    if x < 0 or x > 1:
        return 0.0
    if x == 0 or x == 1:
        return x
    # Use the log-beta for the prefactor
    try:
        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        prefix = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) / a
    except (ValueError, OverflowError):
        return 0.5

    # Lentz's continued fraction
    # I_x(a, b) = (x^a * (1-x)^b) / (a * B(a,b)) * CF
    # Using the continued fraction expansion
    f = 1.0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    f = d

    for m in range(1, 200):
        # Even step
        numerator = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        d = 1.0 + numerator * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + numerator / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        f *= c * d

        # Odd step
        numerator = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + numerator * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + numerator / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = c * d
        f *= delta

        if abs(delta - 1.0) < 1e-10:
            break

    return prefix * f


def builtin_t_test(args: List[Value]) -> Value:
    """t_test(x, y) — two-sample Welch's t-test. Returns {t, df, p, mean_x, mean_y, ci_lower, ci_upper}.

    Like R's t.test(x, y).
    """
    if len(args) < 2:
        raise ValueError("t_test expects (x_list, y_list)")
    x = _extract_numbers(args[0])
    y = _extract_numbers(args[1])
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        raise ValueError("t_test: each group needs at least 2 observations")
    mx, my = sum(x) / nx, sum(y) / ny
    vx = sum((xi - mx) ** 2 for xi in x) / (nx - 1)
    vy = sum((yi - my) ** 2 for yi in y) / (ny - 1)
    se = math.sqrt(vx / nx + vy / ny)
    if se == 0:
        return Value.map_val({
            "t": Value.float_val(0),
            "df": Value.float_val(nx + ny - 2),
            "p": Value.float_val(1.0),
            "mean_x": Value.float_val(mx),
            "mean_y": Value.float_val(my),
        })
    t_stat = (mx - my) / se
    # Welch-Satterthwaite degrees of freedom
    num = (vx / nx + vy / ny) ** 2
    denom = (vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1)
    df = num / denom if denom > 0 else nx + ny - 2
    # Two-tailed p-value
    p = _t_cdf(t_stat, df)
    # 95% CI for difference in means
    # t_crit for 95% CI (approximate: 1.96 for large df)
    t_crit = 1.96 if df > 30 else 2.0 + 3.0 / df  # rough approximation
    ci_lower = (mx - my) - t_crit * se
    ci_upper = (mx - my) + t_crit * se

    return Value.map_val({
        "t": Value.float_val(round(t_stat, 6)),
        "df": Value.float_val(round(df, 2)),
        "p": Value.float_val(round(p, 6)),
        "mean_x": Value.float_val(mx),
        "mean_y": Value.float_val(my),
        "diff": Value.float_val(mx - my),
        "ci_lower": Value.float_val(round(ci_lower, 6)),
        "ci_upper": Value.float_val(round(ci_upper, 6)),
    })


# ---------------------------------------------------------------------------
# Probability Distributions (like R's dnorm, pnorm, qnorm, rnorm)
# ---------------------------------------------------------------------------

def _phi(x):
    """Standard normal CDF (cumulative distribution function)."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _phi_inv(p):
    """Inverse standard normal CDF (quantile function). Rational approximation."""
    if p <= 0:
        return float('-inf')
    if p >= 1:
        return float('inf')
    if p == 0.5:
        return 0.0
    # Rational approximation (Abramowitz and Stegun)
    if p < 0.5:
        t = math.sqrt(-2 * math.log(p))
    else:
        t = math.sqrt(-2 * math.log(1 - p))
    # Coefficients for rational approximation
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    result = t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)
    return result if p >= 0.5 else -result


def builtin_dnorm(args: List[Value]) -> Value:
    """dnorm(x [, mean, sd]) — normal probability density function."""
    if not args:
        raise ValueError("dnorm expects (x [, mean, sd])")
    x = float(args[0].data)
    mu = float(args[1].data) if len(args) > 1 else 0.0
    sigma = float(args[2].data) if len(args) > 2 else 1.0
    if sigma <= 0:
        raise ValueError("sd must be positive")
    z = (x - mu) / sigma
    density = math.exp(-0.5 * z * z) / (sigma * math.sqrt(2 * math.pi))
    return Value.float_val(density)


def builtin_pnorm(args: List[Value]) -> Value:
    """pnorm(x [, mean, sd]) — normal cumulative distribution function."""
    if not args:
        raise ValueError("pnorm expects (x [, mean, sd])")
    x = float(args[0].data)
    mu = float(args[1].data) if len(args) > 1 else 0.0
    sigma = float(args[2].data) if len(args) > 2 else 1.0
    if sigma <= 0:
        raise ValueError("sd must be positive")
    z = (x - mu) / sigma
    return Value.float_val(_phi(z))


def builtin_qnorm(args: List[Value]) -> Value:
    """qnorm(p [, mean, sd]) — normal quantile function (inverse CDF)."""
    if not args:
        raise ValueError("qnorm expects (p [, mean, sd])")
    p = float(args[0].data)
    mu = float(args[1].data) if len(args) > 1 else 0.0
    sigma = float(args[2].data) if len(args) > 2 else 1.0
    if sigma <= 0:
        raise ValueError("sd must be positive")
    if p < 0 or p > 1:
        raise ValueError("p must be between 0 and 1")
    return Value.float_val(mu + sigma * _phi_inv(p))


def builtin_rnorm(args: List[Value]) -> Value:
    """rnorm(n [, mean, sd]) — generate n random normal values."""
    if not args:
        raise ValueError("rnorm expects (n [, mean, sd])")
    n = int(args[0].data)
    mu = float(args[1].data) if len(args) > 1 else 0.0
    sigma = float(args[2].data) if len(args) > 2 else 1.0
    values = [Value.float_val(_random.gauss(mu, sigma)) for _ in range(n)]
    return Value.list_val(values)


def builtin_runif(args: List[Value]) -> Value:
    """runif(n [, min, max]) — generate n random uniform values."""
    if not args:
        raise ValueError("runif expects (n [, min, max])")
    n = int(args[0].data)
    lo = float(args[1].data) if len(args) > 1 else 0.0
    hi = float(args[2].data) if len(args) > 2 else 1.0
    values = [Value.float_val(_random.uniform(lo, hi)) for _ in range(n)]
    return Value.list_val(values)


def builtin_rbinom(args: List[Value]) -> Value:
    """rbinom(n, size, prob) — generate n random binomial values."""
    if len(args) < 3:
        raise ValueError("rbinom expects (n, size, prob)")
    n = int(args[0].data)
    size = int(args[1].data)
    prob = float(args[2].data)
    values = []
    for _ in range(n):
        successes = sum(1 for _ in range(size) if _random.random() < prob)
        values.append(Value.int_val(successes))
    return Value.list_val(values)


# ---------------------------------------------------------------------------
# Random Sampling (like R's sample, set.seed)
# ---------------------------------------------------------------------------

def builtin_sample(args: List[Value]) -> Value:
    """sample(list, n [, replace]) — random sample of n items from list.

    Like R's sample(). Default: without replacement.
    """
    if len(args) < 2:
        raise ValueError("sample expects (list, n [, replace])")
    if args[0].type != ValueType.LIST:
        raise ValueError("sample: first argument must be a list")
    items = args[0].data
    n = int(args[1].data)
    replace = args[2].is_truthy() if len(args) > 2 else False

    if not replace and n > len(items):
        raise ValueError(f"sample: cannot take {n} samples from {len(items)} items without replacement")

    if replace:
        sampled = [_random.choice(items) for _ in range(n)]
    else:
        sampled = list(_random.sample(items, n))
    return Value.list_val(sampled)


def builtin_set_seed(args: List[Value]) -> Value:
    """set_seed(n) — set random seed for reproducibility. Like R's set.seed()."""
    if not args:
        raise ValueError("set_seed expects a number")
    _random.seed(int(args[0].data))
    return Value.null_val()


def builtin_shuffle(args: List[Value]) -> Value:
    """shuffle(list) — return a randomly shuffled copy of the list."""
    if not args or args[0].type != ValueType.LIST:
        raise ValueError("shuffle expects a list")
    items = list(args[0].data)
    _random.shuffle(items)
    return Value.list_val(items)


# ---------------------------------------------------------------------------
# Additional Statistical Functions
# ---------------------------------------------------------------------------

def builtin_cumsum(args: List[Value]) -> Value:
    """cumsum(list) — cumulative sum. Like R's cumsum()."""
    if not args:
        raise ValueError("cumsum expects a list of numbers")
    nums = _extract_numbers(args[0])
    result = []
    total = 0.0
    for x in nums:
        total += x
        result.append(Value.float_val(total))
    return Value.list_val(result)


def builtin_diff(args: List[Value]) -> Value:
    """diff(list) — successive differences. Like R's diff()."""
    if not args:
        raise ValueError("diff expects a list of numbers")
    nums = _extract_numbers(args[0])
    if len(nums) < 2:
        return Value.list_val([])
    result = [Value.float_val(nums[i + 1] - nums[i]) for i in range(len(nums) - 1)]
    return Value.list_val(result)


def builtin_scale(args: List[Value]) -> Value:
    """scale(list) — standardize (z-scores). Like R's scale()."""
    if not args:
        raise ValueError("scale expects a list of numbers")
    nums = _extract_numbers(args[0])
    if len(nums) < 2:
        return Value.list_val([Value.float_val(0)] * len(nums))
    m = sum(nums) / len(nums)
    s = math.sqrt(sum((x - m) ** 2 for x in nums) / (len(nums) - 1))
    if s == 0:
        return Value.list_val([Value.float_val(0)] * len(nums))
    return Value.list_val([Value.float_val((x - m) / s) for x in nums])


def builtin_which_min(args: List[Value]) -> Value:
    """which_min(list) — index of the minimum value. Like R's which.min()."""
    if not args:
        raise ValueError("which_min expects a list of numbers")
    nums = _extract_numbers(args[0])
    if not nums:
        return Value.null_val()
    return Value.int_val(nums.index(min(nums)))


def builtin_which_max(args: List[Value]) -> Value:
    """which_max(list) — index of the maximum value. Like R's which.max()."""
    if not args:
        raise ValueError("which_max expects a list of numbers")
    nums = _extract_numbers(args[0])
    if not nums:
        return Value.null_val()
    return Value.int_val(nums.index(max(nums)))


def builtin_table(args: List[Value]) -> Value:
    """table(list) — frequency table. Like R's table().

    Returns a map of {value: count}.
    """
    if not args or args[0].type != ValueType.LIST:
        raise ValueError("table expects a list")
    counts: dict = {}
    for item in args[0].data:
        key = item.data if item.type == ValueType.STRING else str(item.data)
        if key in counts:
            counts[key] = Value.int_val(counts[key].data + 1)
        else:
            counts[key] = Value.int_val(1)
    return Value.map_val(counts)


def builtin_seq(args: List[Value]) -> Value:
    """seq(from, to [, by]) — generate a sequence. Like R's seq()."""
    if len(args) < 2:
        raise ValueError("seq expects (from, to [, by])")
    start = float(args[0].data)
    end = float(args[1].data)
    step = float(args[2].data) if len(args) > 2 else 1.0
    if step == 0:
        raise ValueError("seq: step cannot be zero")
    if (end - start) / step < 0:
        return Value.list_val([])
    result = []
    current = start
    if step > 0:
        while current <= end + 1e-10:
            result.append(Value.float_val(current))
            current += step
    else:
        while current >= end - 1e-10:
            result.append(Value.float_val(current))
            current += step
    return Value.list_val(result)


def builtin_rep(args: List[Value]) -> Value:
    """rep(value, n) — repeat a value n times. Like R's rep()."""
    if len(args) < 2:
        raise ValueError("rep expects (value, n)")
    n = int(args[1].data)
    return Value.list_val([args[0]] * n)


def builtin_na_rm(args: List[Value]) -> Value:
    """na_rm(list) — remove null/NA values from a list. Like R's na.rm behavior."""
    if not args or args[0].type != ValueType.LIST:
        raise ValueError("na_rm expects a list")
    return Value.list_val([v for v in args[0].data if v.type != ValueType.NULL])


def builtin_is_na(args: List[Value]) -> Value:
    """is_na(value) — check if a value is null/NA. Like R's is.na()."""
    if not args:
        raise ValueError("is_na expects a value")
    if args[0].type == ValueType.LIST:
        return Value.list_val([Value.bool_val(v.type == ValueType.NULL) for v in args[0].data])
    return Value.bool_val(args[0].type == ValueType.NULL)


def builtin_complete_cases(args: List[Value]) -> Value:
    """complete_cases(list_of_maps) — filter rows with no null values. Like R's complete.cases()."""
    if not args or args[0].type != ValueType.LIST:
        raise ValueError("complete_cases expects a list of maps")
    result = []
    for item in args[0].data:
        if item.type == ValueType.MAP:
            has_na = any(v.type == ValueType.NULL for v in item.data.values())
            if not has_na:
                result.append(item)
        elif item.type != ValueType.NULL:
            result.append(item)
    return Value.list_val(result)


# ---------------------------------------------------------------------------
# Registry — all stats functions
# ---------------------------------------------------------------------------

STATS_FUNCTIONS = {
    # Descriptive
    "mean": builtin_mean,
    "median": builtin_median,
    "sd": builtin_sd,
    "variance": builtin_variance,
    "quantile": builtin_quantile,
    "iqr": builtin_iqr,
    "summary": builtin_summary,
    # Correlation & regression
    "cor": builtin_cor,
    "cov": builtin_cov,
    "lm": builtin_lm,
    # Hypothesis testing
    "t_test": builtin_t_test,
    # Distributions
    "dnorm": builtin_dnorm,
    "pnorm": builtin_pnorm,
    "qnorm": builtin_qnorm,
    "rnorm": builtin_rnorm,
    "runif": builtin_runif,
    "rbinom": builtin_rbinom,
    # Sampling
    "sample": builtin_sample,
    "set_seed": builtin_set_seed,
    "shuffle": builtin_shuffle,
    # Cumulative & transforms
    "cumsum": builtin_cumsum,
    "diff": builtin_diff,
    "scale": builtin_scale,
    # Which
    "which_min": builtin_which_min,
    "which_max": builtin_which_max,
    # Tables & sequences
    "table": builtin_table,
    "seq": builtin_seq,
    "rep": builtin_rep,
    # NA handling
    "na_rm": builtin_na_rm,
    "is_na": builtin_is_na,
    "complete_cases": builtin_complete_cases,
}

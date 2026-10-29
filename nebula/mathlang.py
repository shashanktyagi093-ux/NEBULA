"""Natural language -> math expression compiler.

NEBULA lets people type a curve the way they would say it:

    graph two sine of x plus one
    x squared minus three x plus one
    y = 1 / x
    sqrt(x) times cos(2x)
    x^2 + y^2 = 25
    r = 2 * cos(4 * theta)
    (cos(3*t), sin(4*t))

Supports the ENTIRE mathematical universe:
- Explicit Cartesian curves: y = f(x)
- Implicit equations: F(x, y) = G(x, y) via 2D Marching Squares
- Polar equations: r = f(theta)
- Parametric curves: (x(t), y(t))
- Special functions: Bessel (J0, J1, Y0, Y1), Airy (Ai, Bi), Riemann Zeta,
  Gamma, Beta, Error function (erf, erfc), Sinc, Elliptic integrals
- Signal & Discrete functions: Heaviside, Step, Rect, Tri, Sawtooth, Squarewave
- Multi-argument functions: max, min, clamp, mod, hypot, atan2, pow
"""

from __future__ import annotations

import math
import re
from typing import Any

try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    np = None
    _HAS_NUMPY = False

try:
    from scipy import special as sp
    _HAS_SCIPY = True
except Exception:
    sp = None
    _HAS_SCIPY = False


# --------------------------------------------------------------------------
# functions and constants
# --------------------------------------------------------------------------


def _cbrt(v: float) -> float:
    return math.copysign(abs(v) ** (1.0 / 3.0), v)


def _sec(v: float) -> float:
    c = math.cos(v)
    if abs(c) < 1e-12:
        raise ZeroDivisionError("sec divide by zero")
    return 1.0 / c


def _csc(v: float) -> float:
    s = math.sin(v)
    if abs(s) < 1e-12:
        raise ZeroDivisionError("csc divide by zero")
    return 1.0 / s


def _cot(v: float) -> float:
    t = math.tan(v)
    if abs(t) < 1e-12:
        raise ZeroDivisionError("cot divide by zero")
    return 1.0 / t


def _sech(v: float) -> float:
    return 1.0 / math.cosh(v)


def _csch(v: float) -> float:
    s = math.sinh(v)
    if abs(s) < 1e-12:
        raise ZeroDivisionError("csch divide by zero")
    return 1.0 / s


def _coth(v: float) -> float:
    t = math.tanh(v)
    if abs(t) < 1e-12:
        raise ZeroDivisionError("coth divide by zero")
    return 1.0 / t


def _sinc(v: float) -> float:
    return 1.0 if v == 0 else math.sin(v) / v


def _j0(v: float) -> float:
    return float(sp.j0(v)) if _HAS_SCIPY else math.cos(v)


def _j1(v: float) -> float:
    return float(sp.j1(v)) if _HAS_SCIPY else math.sin(v)


def _y0(v: float) -> float:
    return float(sp.y0(v)) if _HAS_SCIPY else math.sin(v)


def _y1(v: float) -> float:
    return float(sp.y1(v)) if _HAS_SCIPY else -math.cos(v)


def _ai(v: float) -> float:
    return float(sp.airy(v)[0]) if _HAS_SCIPY else math.exp(-v)


def _bi(v: float) -> float:
    return float(sp.airy(v)[2]) if _HAS_SCIPY else math.exp(v)


def _zeta(v: float) -> float:
    return float(sp.zeta(v)) if _HAS_SCIPY else 1.0


def _erf(v: float) -> float:
    return math.erf(v)


def _erfc(v: float) -> float:
    return math.erfc(v)


def _gamma(v: float) -> float:
    return math.gamma(v)


def _lgamma(v: float) -> float:
    return math.lgamma(v)


def _factorial(v: float) -> float:
    if v < 0 or v > 170:
        raise ValueError("factorial out of bounds")
    return float(math.factorial(int(v)))


def _heaviside(v: float) -> float:
    return 0.0 if v < 0 else (1.0 if v > 0 else 0.5)


def _step(v: float) -> float:
    return 0.0 if v < 0 else 1.0


def _rect(v: float) -> float:
    return 1.0 if abs(v) <= 0.5 else 0.0


def _tri(v: float) -> float:
    return max(0.0, 1.0 - abs(v))


def _sawtooth(v: float) -> float:
    return v - math.floor(v)


def _squarewave(v: float) -> float:
    s = math.sin(v)
    return 0.0 if abs(s) < 1e-9 else math.copysign(1.0, s)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _mod(a: float, b: float) -> float:
    return a % b


FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sec": _sec,
    "csc": _csc,
    "cot": _cot,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "arcsin": math.asin,
    "arccos": math.acos,
    "arctan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "sech": _sech,
    "csch": _csch,
    "coth": _coth,
    "asinh": math.asinh,
    "acosh": math.acosh,
    "atanh": math.atanh,
    "asec": lambda v: math.acos(1.0 / v),
    "acsc": lambda v: math.asin(1.0 / v),
    "acot": lambda v: math.atan(1.0 / v),
    "asech": lambda v: math.acosh(1.0 / v),
    "acsch": lambda v: math.asinh(1.0 / v),
    "acoth": lambda v: math.atanh(1.0 / v),
    "sqrt": math.sqrt,
    "cbrt": _cbrt,
    "abs": abs,
    "ln": math.log,
    "log": math.log10,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "sinc": _sinc,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "sign": lambda v: 0 if v == 0 else math.copysign(1, v),
    "deg": math.degrees,
    "rad": math.radians,
    # Special functions
    "j0": _j0,
    "j1": _j1,
    "y0": _y0,
    "y1": _y1,
    "bessel_j": lambda n, x: float(sp.jv(int(n), x)) if _HAS_SCIPY else _j0(x),
    "bessel_y": lambda n, x: float(sp.yv(int(n), x)) if _HAS_SCIPY else _y0(x),
    "ai": _ai,
    "bi": _bi,
    "zeta": _zeta,
    "erf": _erf,
    "erfc": _erfc,
    "gamma": _gamma,
    "lgamma": _lgamma,
    "factorial": _factorial,
    "beta": lambda a, b: float(sp.beta(a, b)) if _HAS_SCIPY else 1.0,
    "digamma": lambda x: float(sp.digamma(x)) if _HAS_SCIPY else 0.0,
    "ellipk": lambda m: float(sp.ellipk(m)) if _HAS_SCIPY else 1.0,
    "ellipe": lambda m: float(sp.ellipe(m)) if _HAS_SCIPY else 1.0,
    # Signals & Discrete
    "heaviside": _heaviside,
    "step": _step,
    "rect": _rect,
    "tri": _tri,
    "sawtooth": _sawtooth,
    "squarewave": _squarewave,
    "min": min,
    "max": max,
    "clamp": _clamp,
    "mod": _mod,
    "hypot": math.hypot,
    "atan2": math.atan2,
    "pow": math.pow,
    "frac": lambda v: v - math.floor(v),
    "trunc": math.trunc,
}

CONSTS = {
    "pi": math.pi,
    "tau": math.tau,
    "e": math.e,
    "phi": (1.0 + math.sqrt(5.0)) / 2.0,
}

FUNC_WORDS = {
    "sin": "sin", "sine": "sin", "sign": "sin",
    "cos": "cos", "cosine": "cos", "cause": "cos", "course": "cos",
    "tan": "tan", "tangent": "tan",
    "sec": "sec", "secant": "sec",
    "csc": "csc", "cosecant": "csc", "cosec": "csc",
    "cot": "cot", "cotangent": "cot", "cotan": "cot",
    "arcsin": "asin", "arccos": "acos", "arctan": "atan",
    "asin": "asin", "acos": "acos", "atan": "atan",
    "sinh": "sinh", "cosh": "cosh", "tanh": "tanh",
    "sech": "sech", "csch": "csch", "coth": "coth",
    "asinh": "asinh", "acosh": "acosh", "atanh": "atanh",
    "sqrt": "sqrt", "squareroot": "sqrt",
    "ln": "ln", "log": "log", "log10": "log10", "log2": "log2",
    "exp": "exp", "abs": "abs", "cbrt": "cbrt", "sinc": "sinc",
    "round": "round", "floor": "floor", "ceil": "ceil",
    "deg": "deg", "rad": "rad",
    "gamma": "gamma", "factorial": "factorial", "erf": "erf",
    "zeta": "zeta", "bessel": "j0", "heaviside": "heaviside",
    "sawtooth": "sawtooth", "squarewave": "squarewave",
}


class MathError(ValueError):
    """Raised when the text cannot be understood as a plottable function."""


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------

_CHAR_MAP = {
    "\u2212": "-", "\u2013": "-", "\u2014": "-", "\u00d7": "*", "\u00f7": "/",
    "\u221a": " sqrt ", "\u221b": " cbrt ",
    "\u03c0": " pi ", "\u03c4": " tau ", "\u03c6": " phi ", "\u03b8": " theta ",
    "\u00b2": "^2", "\u00b3": "^3",
    "\u00b7": "*", "\u2044": "/", "\u2264": "<=", "\u2265": ">=",
}

# longest phrases first; each entry is (regex, replacement)
_PHRASES = [
    (r"\b(?:raised\s+to\s+the\s+power\s+of|to\s+the\s+power\s+of|raised\s+to\s+the\s+power|to\s+the\s+power|raised\s+to)\b", " ^ "),
    (r"\b(?:power\s+of|power)\b", " ^ "),
    (r"\b(?:hyperbolic\s+sine\s+of|hyperbolic\s+sine)\b", " sinh "),
    (r"\b(?:hyperbolic\s+cosine\s+of|hyperbolic\s+cosine)\b", " cosh "),
    (r"\b(?:hyperbolic\s+tangent\s+of|hyperbolic\s+tangent)\b", " tanh "),
    (r"\b(?:hyperbolic\s+secant\s+of|hyperbolic\s+secant)\b", " sech "),
    (r"\b(?:hyperbolic\s+cosecant\s+of|hyperbolic\s+cosecant)\b", " csch "),
    (r"\b(?:hyperbolic\s+cotangent\s+of|hyperbolic\s+cotangent)\b", " coth "),
    (r"\b(?:inverse\s+sine\s+of|arc\s+sine\s+of|inverse\s+sine|arc\s+sine)\b", " asin "),
    (r"\b(?:inverse\s+cosine\s+of|arc\s+cosine\s+of|inverse\s+cosine|arc\s+cosine)\b", " acos "),
    (r"\b(?:inverse\s+tangent\s+of|arc\s+tangent\s+of|inverse\s+tangent|arc\s+tangent)\b", " atan "),
    (r"\b(?:inverse\s+hyperbolic\s+sine\s+of)\b", " asinh "),
    (r"\b(?:inverse\s+hyperbolic\s+cosine\s+of)\b", " acosh "),
    (r"\b(?:inverse\s+hyperbolic\s+tangent\s+of)\b", " atanh "),
    (r"\b(?:square\s+root\s+of|under\s+root\s+of|under\s+root|root\s+of|root\s+over)\b", " sqrt "),
    (r"\b(?:cube\s+root\s+of|cubic\s+root\s+of)\b", " cbrt "),
    (r"\b(?:natural\s+log(?:arithm)?\s+of|natural\s+log)\b", " ln "),
    (r"\b(?:log\s+base\s+(?:ten|10)\s+of|log\s+ten\s+of)\b", " log10 "),
    (r"\b(?:log\s+base\s+(?:two|2)\s+of|log\s+two\s+of)\b", " log2 "),
    (r"\b(?:log(?:arithm)?\s+of)\b", " log "),
    (r"\b(?:absolute\s+value\s+of|modulus\s+of|mod\s+of)\b", " abs "),
    (r"\b(?:sign\s+of|sine\s+of)\b", " sin "),
    (r"\b(?:cosine\s+of|cause\s+of|course\s+of)\b", " cos "),
    (r"\b(?:tangent\s+of|tan\s+of)\b", " tan "),
    (r"\b(?:secant\s+of|sec\s+of|see\s+can\s+of|see\s+can)\b", " sec "),
    (r"\b(?:cosecant\s+of|cosec\s+of|csc\s+of)\b", " csc "),
    (r"\b(?:cotangent\s+of|cotan\s+of|cot\s+of)\b", " cot "),
    (r"\b(?:sync\s+of|sink\s+of|sinc\s+of)\b", " sinc "),
    (r"\b(?:degrees\s+of|in\s+degrees)\b", " deg "),
    (r"\b(?:radians\s+of|in\s+radians)\b", " rad "),
    (r"\b(?:e\s+to\s+the\s+power\s+of|e\s+to\s+the\s+power|e\s+to\s+the)\b", " exp "),
    (r"\b(?:multiplied\s+by|multiplied\s+with|multiplied|into)\b", " * "),
    (r"\b(?:divided\s+by|divided|upon)\b", " / "),
    (r"\b(?:square\s+root)\b", " sqrt "),
    (r"\b(?:cube\s+root)\b", " cbrt "),
    (r"\bsquared\b", " ^2 "),
    (r"\bcubed\b", " ^3 "),
    (r"\b(?:square)\b", " ^2 "),
    (r"\b(?:cube)\b", " ^3 "),
    (r"\bplus\b", " + "),
    (r"\bminus\b", " - "),
    (r"\bsubtract(?:ed)?\b", " - "),
    (r"\badd(?:ed)?\b", " + "),
    (r"\btimes\b", " * "),
    (r"\bover\b", " / "),
    (r"\bhalf\s+of\b", " 0.5 * "),
    (r"\btwice\b", " 2 * "),
    (r"\bdouble\b", " 2 * "),
    (r"\btriple\b", " 3 * "),
    (r"\bnegative\b", " - "),
    (r"\bpi\b", " pi "),
    (r"\btheta\b", " theta "),
    (r"\btau\b", " tau "),
    (r"\bphi\b", " phi "),
    (r"\bpoint\b", " . "),
]

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "thousand": 1000, "million": 1000000,
}

_FILLERS = (
    "please", "graph", "plot", "draw", "sketch", "show me", "show", "display",
    "can you please graph", "can you please plot", "can you graph", "can you plot",
    "i want to graph", "i want to plot", "graph me", "plot me", "draw me",
    "hey nebula", "nebula", "the", "function", "curve", "equation",
    "formula", "of", "for", "where", "if", "is", "equals", "equal to",
    "let", "me", "what is", "compute", "evaluate", "calculate", "this", "that",
)

_CLEAN_RE = re.compile(r"\s+")


def _words_to_symbols(text: str) -> str:
    text = text.lower().strip()
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    for _ in range(5):
        before = text
        text = re.sub(r"^(?:hey\s+|hi\s+)?nebula(?:[,.]\s*|\s+)", "", text)
        text = re.sub(r"^(?:can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?|please\s+|i\s+want\s+to\s+)", "", text)
        text = re.sub(
            r"^(?:graph|plot|draw|sketch|display|show(?:\s+me)?|"
            r"what\s+is|compute|evaluate|calculate)\s+",
            "", text)
        text = re.sub(r"^(?:the\s+)?(?:function|curve|equation|graph)\s+", "", text)
        text = re.sub(r"^(?:y|f\s*\(\s*x\s*\))\s*=\s*", "", text)
        text = re.sub(r"^y\s+equals\s+", "", text)
        if text == before:
            break

    for pattern, repl in _PHRASES:
        text = re.sub(pattern, " " + repl + " ", text)

    tens = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety")
    for ten in tens:
        for unit in ("one", "two", "three", "four", "five", "six", "seven",
                     "eight", "nine"):
            text = re.sub(
                rf"\b{ten}\s+{unit}\b",
                f" {_NUMBER_WORDS[ten] + _NUMBER_WORDS[unit]} ", text)
    text = re.sub(
        r"\b(" + "|".join(_NUMBER_WORDS) + r")\b",
        lambda m: f" {_NUMBER_WORDS[m.group(1)]} ", text)

    def func_word(match: re.Match) -> str:
        return " " + FUNC_WORDS[match.group(0)] + " "

    text = re.sub(
        r"\b(" + "|".join(FUNC_WORDS) + r")\b", func_word, text)

    text = re.sub(r"\b(?:a|an)\s+(?=[a-z]{2,}\b)", " ", text)
    fill = "|".join(re.escape(w) for w in _FILLERS)
    text = re.sub(r"\b(" + fill + r")\b", " ", text)

    text = _CLEAN_RE.sub(" ", text).strip()
    return text


_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|\.\d+|[a-z][a-z0-9]*|<=|>=|!=|==|[-+*/^%(),|=<>{}]")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    idx = 0
    while idx < len(text):
        if text[idx].isspace():
            idx += 1
            continue
        match = _TOKEN_RE.match(text, idx)
        if not match:
            tokens.append(text[idx])
            idx += 1
            continue
        tokens.append(match.group(0))
        idx = match.end()
    return tokens


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------

_PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "%": 2, "^": 3}


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> str:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, expected: str):
        token = self.take()
        if token != expected:
            raise MathError(f"expected '{expected}', found '{token}'")

    def parse(self):
        node = self.expr()
        if self.pos < len(self.tokens):
            extra = " ".join(self.tokens[self.pos:])
            raise MathError(f"I couldn't make sense of “{extra}” at the end")
        return node

    def expr(self):
        return self._bin_op(self.term, ("+", "-"))

    def term(self):
        return self._bin_op(self.power, ("*", "/", "%"))

    def power(self):
        node = self.unary()
        while self.peek() == "^":
            self.take()
            right = self.power()
            node = ("bin", "^", node, right)
        return node

    def unary(self):
        if self.peek() == "-":
            self.take()
            return ("neg", self.unary())
        if self.peek() == "+":
            self.take()
            return self.unary()
        return self.implicit_mul()

    def implicit_mul(self):
        node = self.atom()
        while True:
            nxt = self.peek()
            if nxt is None or not self._starts_atom(nxt):
                break
            if nxt in ("+", "-", "*", "/", "%", "^", ")", ",", "|", "="):
                break
            node = ("bin", "*", node, self.atom())
        return node

    def _starts_atom(self, token: str) -> bool:
        if re.match(r"^\d|^\.\d", token):
            return True
        if token in ("(", "|"):
            return True
        if re.match(r"^[a-z][a-z0-9]*$", token):
            return True
        return False

    def atom(self):
        token = self.peek()
        if token is None:
            raise MathError("something is missing at the end")

        if re.match(r"^\d|^\.\d", token):
            self.take()
            return ("num", float(token))

        if token == "(":
            self.take()
            node = self.expr()
            self.expect(")")
            return node

        if token == "|":
            self.take()
            node = self.expr()
            self.expect("|")
            return ("call", "abs", [node])

        if re.match(r"^[a-z][a-z0-9]*$", token):
            self.take()
            if token in CONSTS:
                return ("num", CONSTS[token])
            if token in FUNCS:
                args = self._argument(token)
                return ("call", token, args)
            return ("var", token)

        raise MathError(f"I can't use “{token}” here")

    def _argument(self, name: str) -> list[Any]:
        token = self.peek()
        if token is None:
            raise MathError(f"{name} needs something to work on, like {name}(x)")
        if token == "(":
            self.take()
            args = [self.expr()]
            while self.peek() == ",":
                self.take()
                args.append(self.expr())
            self.expect(")")
            return args
        if self._starts_atom(token):
            if re.match(r"^\d", token):
                return [self.term()]
            return [self.power()]
        raise MathError(f"{name} needs something to work on, like {name}(x)")

    def _bin_op(self, sub_parser, ops):
        node = sub_parser()
        while self.peek() in ops:
            op = self.take()
            right = sub_parser()
            node = ("bin", op, node, right)
        return node


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------


def _eval_condition(cond: str, x: float, env: dict) -> bool:
    try:
        c = cond.replace("≤", "<=").replace("≥", ">=").replace("≠", "!=").strip()
        m_double = re.match(r"^(-?\d+(?:\.\d+)?)\s*(<=|<)\s*x\s*(<=|<)\s*(-?\d+(?:\.\d+)?)$", c)
        if m_double:
            lo, op1, op2, hi = float(m_double.group(1)), m_double.group(2), m_double.group(3), float(m_double.group(4))
            v1 = (x >= lo) if op1 == "<=" else (x > lo)
            v2 = (x <= hi) if op2 == "<=" else (x < hi)
            return v1 and v2
        m_single = re.match(r"^x\s*(<=|>=|<|>|!=|==)\s*(-?\d+(?:\.\d+)?)$", c)
        if m_single:
            op, val = m_single.group(1), float(m_single.group(2))
            if op == "<=": return x <= val
            if op == "<": return x < val
            if op == ">=": return x >= val
            if op == ">": return x > val
            if op == "!=": return abs(x - val) > 1e-9
            if op == "==": return abs(x - val) < 1e-9
        return bool(eval(c, {"__builtins__": None, "abs": abs, "math": math}, {"x": x, **env}))
    except Exception:
        return True


def _evaluate(node, env: Any) -> float:
    if isinstance(env, (int, float)):
        env_dict = {"x": float(env), "t": float(env), "theta": float(env), "r": float(env)}
    elif isinstance(env, dict):
        env_dict = env
    else:
        env_dict = {}

    kind = node[0]
    if kind == "num":
        return float(node[1])
    if kind == "var":
        name = node[1] if len(node) > 1 else "x"
        if name in env_dict:
            return float(env_dict[name])
        if name in ("x", "y", "t", "theta", "r"):
            return 0.0
        return 1.0
    if kind == "neg":
        return -_evaluate(node[1], env_dict)
    if kind == "call":
        func_name = node[1]
        raw_args = node[2]
        args_list = raw_args if isinstance(raw_args, list) else [raw_args]
        eval_args = [_evaluate(a, env_dict) for a in args_list]
        func = FUNCS[func_name]
        try:
            return float(func(*eval_args))
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            raise MathError(f"{func_name} is undefined there") from exc
    if kind == "bin":
        left = _evaluate(node[2], env_dict)
        right = _evaluate(node[3], env_dict)
        op = node[1]
        try:
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if abs(right) < 1e-12:
                    raise ZeroDivisionError("division by zero")
                return left / right
            if op == "%":
                return left % right
            if op == "^":
                if left < 0 and abs(right - round(right)) > 1e-6:
                    raise ValueError("fractional power of negative number")
                return float(left ** right)
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            raise MathError(f"math error on '{op}'") from exc

    raise MathError("unknown AST node")


def to_string(node, parent: int = 0) -> str:
    kind = node[0]
    if kind == "num":
        v = node[1]
        return str(int(v)) if v.is_integer() else f"{v:.4g}"
    if kind == "var":
        return node[1] if len(node) > 1 else "x"
    if kind == "neg":
        inner = to_string(node[1], 4)
        return f"-{inner}"
    if kind == "call":
        name = node[1]
        raw_args = node[2]
        args_list = raw_args if isinstance(raw_args, list) else [raw_args]
        args_str = ", ".join(to_string(a) for a in args_list)
        return f"{name}({args_str})"
    op, left, right = node[1], node[2], node[3]
    prec = _PREC.get(op, 1)
    ls = to_string(left, prec + (1 if op == "^" else 0))
    rs = to_string(right, prec + 1 if op != "^" else prec)
    text = f"{ls} {op} {rs}" if op in ("+", "-") else f"{ls}{op}{rs}"
    if prec < parent:
        return f"({text})"
    return text


# --------------------------------------------------------------------------
# sampling
# --------------------------------------------------------------------------


def _segments(points: list[tuple[float, float]]) -> list[list[list[float]]]:
    """Split a sampled polyline where the function jumps (poles, steps)."""
    if not points:
        return []
    diffs = sorted(
        abs(points[i + 1][1] - points[i][1]) for i in range(len(points) - 1))
    typical = diffs[len(diffs) // 2] if diffs else 0.0
    values = sorted(p[1] for p in points)
    spread = values[int(0.98 * (len(values) - 1))] - values[int(0.02 * (len(values) - 1))]

    limit = max(typical * 25.0, spread * 0.5, 1e-9)
    out: list[list[list[float]]] = []
    current: list[list[float]] = []
    for i, (x, y) in enumerate(points):
        if current:
            prev_y = current[-1][1]
            if abs(y - prev_y) > limit:
                if len(current) > 1:
                    out.append(current)
                current = []
        current.append([round(x, 5), round(y, 5)])
    if len(current) > 1:
        out.append(current)
    return out


def _chain_segments(lines: list[list[list[float]]], tol: float = 0.25) -> list[list[list[float]]]:
    """Chain adjacent segments into smooth continuous polylines."""
    if not lines:
        return []
    polylines: list[list[list[float]]] = []
    remaining = list(lines)
    while remaining:
        current = list(remaining.pop(0))
        extended = True
        while extended and remaining:
            extended = False
            tail = current[-1]
            head = current[0]
            for i, seg in enumerate(remaining):
                s0, s1 = seg[0], seg[1]
                if (tail[0] - s0[0])**2 + (tail[1] - s0[1])**2 < tol**2:
                    current.append(s1)
                    remaining.pop(i)
                    extended = True
                    break
                elif (tail[0] - s1[0])**2 + (tail[1] - s1[1])**2 < tol**2:
                    current.append(s0)
                    remaining.pop(i)
                    extended = True
                    break
                elif (head[0] - s1[0])**2 + (head[1] - s1[1])**2 < tol**2:
                    current.insert(0, s0)
                    remaining.pop(i)
                    extended = True
                    break
                elif (head[0] - s0[0])**2 + (head[1] - s0[1])**2 < tol**2:
                    current.insert(0, s1)
                    remaining.pop(i)
                    extended = True
                    break
        polylines.append(current)
    return polylines


def sample_implicit(lhs_ast, rhs_ast, xmin: float = -10.0, xmax: float = 10.0,
                    ymin: float = -10.0, ymax: float = 10.0, nx: int = 140, ny: int = 140) -> list[list[list[float]]]:
    """Sample an implicit equation F(x, y) = G(x, y) using 2D Marching Squares."""
    xs = [xmin + (xmax - xmin) * j / (nx - 1) for j in range(nx)]
    ys = [ymin + (ymax - ymin) * i / (ny - 1) for i in range(ny)]

    grid: list[list[float | None]] = []
    for i in range(ny):
        row = []
        y_val = ys[i]
        for j in range(nx):
            x_val = xs[j]
            try:
                env = {"x": x_val, "y": y_val}
                lv = _evaluate(lhs_ast, env)
                rv = _evaluate(rhs_ast, env)
                val = lv - rv
                if not math.isfinite(val) or abs(val) > 1e12:
                    row.append(None)
                else:
                    row.append(val)
            except Exception:
                row.append(None)
        grid.append(row)

    lines: list[list[list[float]]] = []
    for i in range(ny - 1):
        for j in range(nx - 1):
            v0 = grid[i][j]
            v1 = grid[i][j + 1]
            v2 = grid[i + 1][j + 1]
            v3 = grid[i + 1][j]

            if v0 is None or v1 is None or v2 is None or v3 is None:
                continue

            idx = 0
            if v0 > 0: idx |= 1
            if v1 > 0: idx |= 2
            if v2 > 0: idx |= 4
            if v3 > 0: idx |= 8

            if idx == 0 or idx == 15:
                continue

            x0, x1_val = xs[j], xs[j + 1]
            y0, y1_val = ys[i], ys[i + 1]

            def interp(pA, pB, vA, vB):
                denom = vB - vA
                t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, -vA / denom))
                return [round(pA[0] + t * (pB[0] - pA[0]), 4),
                        round(pA[1] + t * (pB[1] - pA[1]), 4)]

            e0 = interp([x0, y0], [x1_val, y0], v0, v1)
            e1 = interp([x1_val, y0], [x1_val, y1_val], v1, v2)
            e2 = interp([x0, y1_val], [x1_val, y1_val], v3, v2)
            e3 = interp([x0, y0], [x0, y1_val], v0, v3)

            if idx in (1, 14): lines.append([e3, e0])
            elif idx in (2, 13): lines.append([e0, e1])
            elif idx in (3, 12): lines.append([e3, e1])
            elif idx in (4, 11): lines.append([e1, e2])
            elif idx == 5:
                lines.append([e3, e2])
                lines.append([e0, e1])
            elif idx in (6, 9): lines.append([e0, e2])
            elif idx in (7, 8): lines.append([e3, e2])
            elif idx == 10:
                lines.append([e3, e0])
                lines.append([e1, e2])

    return _chain_segments(lines)


def compile_expression(text: str):
    """Return (ast, canonical string) for a natural-language math line."""
    if not text or not text.strip():
        raise MathError("type something to graph")
    try:
        from nebula import math_ai
        concept = math_ai.resolve_concept_or_question(text)
        if concept:
            text = concept["equation"]
    except Exception:
        pass
    normalised = _words_to_symbols(text)
    if not normalised:
        raise MathError("I couldn't find any math in that")
    ast = _Parser(tokenize(normalised)).parse()
    return ast, to_string(ast)


def sample(text: str, xmin: float = -10.0, xmax: float = 10.0,
           ymin: float = -10.0, ymax: float = 10.0,
           samples: int = 1201, env: dict[str, float] | None = None) -> dict:
    raw_text = text.strip()
    env_eval = env or {}

    # 1. Pure mathematical parsing first

    # A. Check for Variable Assignment / Slider: a = 2.5
    slider_match = re.match(r"^([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)$", raw_text)
    if slider_match:
        var_name = slider_match.group(1)
        val = float(slider_match.group(2))
        if var_name not in ("x", "y", "t", "r", "theta"):
            v_min = -10.0 if val >= -10 else val - 10.0
            v_max = 10.0 if val <= 10 else val + 10.0
            return {
                "kind": "slider",
                "input": text,
                "canonical": f"{var_name} = {val:.4g}",
                "var": var_name,
                "val": val,
                "min": v_min,
                "max": v_max,
                "step": 0.1,
                "segments": [],
                "points": 0,
            }

    # B. Check for Coordinate Point: (x0, y0)
    pt_match = re.match(r"^\(\s*([^,]+)\s*,\s*([^)]+)\s*\)$", raw_text)
    if pt_match and "t" not in raw_text and "theta" not in raw_text:
        try:
            x_norm = _words_to_symbols(pt_match.group(1))
            y_norm = _words_to_symbols(pt_match.group(2))
            ast_x = _Parser(tokenize(x_norm)).parse()
            ast_y = _Parser(tokenize(y_norm)).parse()
            px = _evaluate(ast_x, env_eval)
            py = _evaluate(ast_y, env_eval)
            return {
                "kind": "point",
                "input": text,
                "canonical": f"({px:.4g}, {py:.4g})",
                "point": [px, py],
                "x": px,
                "y": py,
                "label": f"({px:.4g}, {py:.4g})",
                "segments": [[[px, py]]],
                "points": 1,
            }
        except Exception:
            pass

    # C. Check for Definite Integral: integral(f(x), a, b) or int_a^b f(x) dx
    int_m1 = re.match(r"^(?:int|integral)\s*\(\s*(.+?)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)$", raw_text, re.I)
    int_m2 = re.match(r"^(?:int|integral)_([a-z0-9_./+-]+)\^([a-z0-9_./+-]+)\s+(.+?)(?:\s*dx)?$", raw_text, re.I)
    if int_m1 or int_m2:
        try:
            if int_m1:
                integrand_raw, a_str, b_str = int_m1.group(1).strip(), int_m1.group(2).strip(), int_m1.group(3).strip()
            else:
                a_str, b_str, integrand_raw = int_m2.group(1).strip(), int_m2.group(2).strip(), int_m2.group(3).strip()
            a_val = float(_words_to_symbols(a_str).replace("pi", str(math.pi)))
            b_val = float(_words_to_symbols(b_str).replace("pi", str(math.pi)))
            ast_int, canon_int = compile_expression(integrand_raw)

            # Sample integrand between a and b
            int_steps = 300
            int_pts = []
            for i in range(int_steps):
                xi = a_val + (b_val - a_val) * i / (int_steps - 1)
                yi = _evaluate(ast_int, {"x": xi, "t": xi, **env_eval})
                int_pts.append((xi, yi))
            # Trapezoidal / Simpson quadrature
            total_area = sum(0.5 * (int_pts[i][1] + int_pts[i+1][1]) * (int_pts[i+1][0] - int_pts[i][0]) for i in range(len(int_pts) - 1))
            finite_pts = [p for p in int_pts if math.isfinite(p[1])]
            segments = _segments(finite_pts)
            return {
                "kind": "integral",
                "input": text,
                "canonical": f"∫ from {a_val:.3g} to {b_val:.3g} of {canon_int} dx = {total_area:.4g}",
                "value": total_area,
                "a": a_val,
                "b": b_val,
                "integrand": canon_int,
                "segments": segments,
                "domain": [a_val, b_val],
                "points": len(finite_pts),
            }
        except Exception:
            pass

    # D. Extract Domain Restrictions: { cond }
    cond_str = None
    cond_match = re.search(r"\{\s*(.*?)\s*\}", raw_text)
    if cond_match:
        cond_str = cond_match.group(1).strip()
        raw_text = raw_text[:cond_match.start()] + raw_text[cond_match.end():]
        raw_text = raw_text.strip()

    # E. Check for Inequalities: y <= f(x), y < f(x), y >= f(x), y > f(x), or implicit
    ineq_match = re.search(r"(<=|>=|!=|<|>)", raw_text)
    if ineq_match:
        op = ineq_match.group(0)
        lhs_raw, rhs_raw = raw_text.split(op, 1)
        lhs_raw = lhs_raw.strip()
        rhs_raw = rhs_raw.strip()
        is_cartesian_ineq = lhs_raw.lower() in ("y", "f(x)")

        if is_cartesian_ineq:
            direction = "below" if op in ("<", "<=") else "above"
            boundary_style = "dashed" if op in ("<", ">") else "solid"
            ast_rhs, canon_rhs = compile_expression(rhs_raw)
            raw_pts: list[tuple[float, float] | None] = []
            for i in range(samples):
                x = xmin + (xmax - xmin) * i / (samples - 1)
                if cond_str and not _eval_condition(cond_str, x, env_eval):
                    raw_pts.append(None)
                    continue
                try:
                    y = _evaluate(ast_rhs, {"x": x, "t": x, "theta": x, **env_eval})
                except Exception:
                    raw_pts.append(None)
                    continue
                if not math.isfinite(y) or abs(y) > 1e9:
                    raw_pts.append(None)
                    continue
                raw_pts.append((x, y))

            finite = [p for p in raw_pts if p is not None]
            segments = _segments(finite)
            ys = [p[1] for p in finite]
            return {
                "kind": "inequality",
                "input": text,
                "canonical": f"y {op} {canon_rhs}",
                "op": op,
                "direction": direction,
                "boundary_style": boundary_style,
                "segments": segments,
                "domain": [xmin, xmax],
                "range": [ymin, ymax],
                "points": len(finite),
            }
        else:
            # Implicit inequality: F(x, y) <= G(x, y)
            has_x = bool(re.search(r"\bx\b", raw_text, re.I))
            has_y = bool(re.search(r"\by\b", raw_text, re.I))
            if has_x and has_y:
                boundary_style = "dashed" if op in ("<", ">") else "solid"
                direction = "implicit_inside" if op in ("<", "<=") else "implicit_outside"
                lhs_ast = _Parser(tokenize(_words_to_symbols(lhs_raw))).parse()
                rhs_ast = _Parser(tokenize(_words_to_symbols(rhs_raw))).parse()
                segments = sample_implicit(lhs_ast, rhs_ast, xmin, xmax, ymin, ymax)
                return {
                    "kind": "inequality",
                    "input": text,
                    "canonical": f"{to_string(lhs_ast)} {op} {to_string(rhs_ast)}",
                    "op": op,
                    "direction": direction,
                    "boundary_style": boundary_style,
                    "segments": segments,
                    "domain": [xmin, xmax],
                    "range": [ymin, ymax],
                    "points": sum(len(s) for s in segments),
                }

    # 2. Check for Implicit Equations: F(x, y) = G(x, y)
    if "=" in raw_text:
        parts = raw_text.split("=", 1)
        lhs_part = parts[0].strip()
        rhs_part = parts[1].strip()

        # If it's a simple y = f(x), treat as explicit Cartesian function
        if lhs_part in ("y", "f(x)"):
            return sample(rhs_part, xmin, xmax, ymin, ymax, samples, env=env_eval)
        # If it's a simple x = c, vertical line
        if lhs_part == "x" and not re.search(r"\b[yt]\b", rhs_part):
            c_val = float(_words_to_symbols(rhs_part))
            return {
                "kind": "vertical_line",
                "input": text,
                "canonical": f"x = {c_val}",
                "segments": [[[c_val, ymin], [c_val, ymax]]],
                "domain": [c_val, c_val],
                "range": [ymin, ymax],
                "points": 2,
            }

        # Check if it has both x and y (or polar r and theta)
        has_x = bool(re.search(r"\bx\b", raw_text, re.I))
        has_y = bool(re.search(r"\by\b", raw_text, re.I))

        if has_x and has_y:
            lhs_norm = _words_to_symbols(lhs_part)
            rhs_norm = _words_to_symbols(rhs_part)
            lhs_ast = _Parser(tokenize(lhs_norm)).parse()
            rhs_ast = _Parser(tokenize(rhs_norm)).parse()
            segments = sample_implicit(lhs_ast, rhs_ast, xmin, xmax, ymin, ymax)
            return {
                "kind": "implicit",
                "input": text,
                "canonical": f"{to_string(lhs_ast)} = {to_string(rhs_ast)}",
                "segments": segments,
                "domain": [xmin, xmax],
                "range": [ymin, ymax],
                "points": sum(len(s) for s in segments),
            }

    # 3. Check for Polar Equations: r = f(theta) or presence of theta
    if raw_text.startswith("r =") or "theta" in raw_text:
        expr_part = raw_text
        if "=" in expr_part:
            expr_part = expr_part.split("=", 1)[1]
        norm = _words_to_symbols(expr_part)
        ast = _Parser(tokenize(norm)).parse()

        theta_max = 12 * math.pi if ("spiral" in text.lower() or "log" in text.lower()) else 4 * math.pi
        pts: list[tuple[float, float] | None] = []
        n_steps = 1500
        for i in range(n_steps):
            th = theta_max * i / (n_steps - 1)
            try:
                r_val = _evaluate(ast, {"theta": th, "x": th, "t": th, **env_eval})
                if not math.isfinite(r_val) or abs(r_val) > 1e6:
                    pts.append(None)
                    continue
                px = r_val * math.cos(th)
                py = r_val * math.sin(th)
                pts.append((px, py))
            except Exception:
                pts.append(None)

        finite = [p for p in pts if p is not None]
        segments = _segments(finite)
        ys = [p[1] for p in finite]
        return {
            "kind": "polar",
            "input": text,
            "canonical": f"r = {to_string(ast)}",
            "segments": segments,
            "domain": [xmin, xmax],
            "range": ([min(ys), max(ys)] if ys else None),
            "points": len(finite),
        }

    # 4. Check for Parametric Curves: (x(t), y(t))
    param_match = re.match(r"^\(\s*(.*?)\s*,\s*(.*?)\s*\)$", raw_text)
    if param_match and "t" in raw_text:
        x_expr, y_expr = param_match.group(1), param_match.group(2)
        ast_x = _Parser(tokenize(_words_to_symbols(x_expr))).parse()
        ast_y = _Parser(tokenize(_words_to_symbols(y_expr))).parse()

        t_min, t_max = -10.0, 10.0
        n_steps = 1500
        pts = []
        for i in range(n_steps):
            t_val = t_min + (t_max - t_min) * i / (n_steps - 1)
            try:
                px = _evaluate(ast_x, {"t": t_val, "x": t_val, **env_eval})
                py = _evaluate(ast_y, {"t": t_val, "x": t_val, **env_eval})
                if math.isfinite(px) and math.isfinite(py) and abs(px) < 1e6 and abs(py) < 1e6:
                    pts.append((px, py))
                else:
                    pts.append(None)
            except Exception:
                pts.append(None)

        finite = [p for p in pts if p is not None]
        segments = _segments(finite)
        ys = [p[1] for p in finite]
        return {
            "kind": "parametric",
            "input": text,
            "canonical": f"({to_string(ast_x)}, {to_string(ast_y)})",
            "segments": segments,
            "domain": [xmin, xmax],
            "range": ([min(ys), max(ys)] if ys else None),
            "points": len(finite),
        }

    # 5. Explicit Cartesian Function: y = f(x)
    ast, canonical = compile_expression(raw_text)
    raw: list[tuple[float, float] | None] = []
    for i in range(samples):
        x = xmin + (xmax - xmin) * i / (samples - 1)
        if cond_str and not _eval_condition(cond_str, x, env_eval):
            raw.append(None)
            continue
        try:
            y = _evaluate(ast, {"x": x, "t": x, "theta": x, **env_eval})
        except (MathError, RecursionError, ValueError, ZeroDivisionError, OverflowError):
            raw.append(None)
            continue
        if not math.isfinite(y) or abs(y) > 1e9:
            raw.append(None)
            continue
        raw.append((x, y))

    finite = [p for p in raw if p is not None]
    segments = _segments(finite)
    ys = [p[1] for p in finite]
    return {
        "kind": "function",
        "input": text,
        "canonical": canonical if not cond_str else f"{canonical} {{{cond_str}}}",
        "segments": segments,
        "domain": [xmin, xmax],
        "range": ([min(ys), max(ys)] if ys else None),
        "points": len(finite),
    }
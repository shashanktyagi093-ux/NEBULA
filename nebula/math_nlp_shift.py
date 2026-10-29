"""NEBULA NLP Shift and Geometric Transformation Engine.

Parses natural language shifting commands, coordinate translations,
stretches, reflections, 2D rotations, calculus operations (derivatives, tangents, normals, integrals),
function morphing (inverses, reciprocals, absolute value), and graph settings.
"""

from __future__ import annotations

import math
import re
from typing import Any, TypedDict
import sympy as sp


class ShiftResult(TypedDict, total=False):
    action: str  # "shift_equation" | "add_equation" | "shift_view" | "set_setting"
    ok: bool
    equation: str
    canonical: str
    original_equation: str
    dx: float
    dy: float
    scale_x: float
    scale_y: float
    reflect_x: bool
    reflect_y: bool
    target_x: float | None
    target_y: float | None
    setting: str | None
    value: Any
    title: str
    explanation: str
    transformations: list[str]
    feedback: str
    mode: str
    error: str


NUM_WORDS: dict[str, float] = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "half": 0.5,
    "quarter": 0.25,
    "third": 1.0 / 3.0,
    "pi": math.pi,
    "tau": math.tau,
    "pi/2": math.pi / 2.0,
    "pi/4": math.pi / 4.0,
    "2pi": math.tau,
}

BASE_CURVE_DEFAULTS: dict[str, str] = {
    "parabola": "x^2 - 4",
    "inverted parabola": "-x^2 + 4",
    "hyperbola": "1 / x",
    "circle": "x^2 + y^2 = 25",
    "ellipse": "x^2 / 25 + y^2 / 9 = 1",
    "sine": "sin(x)",
    "sine wave": "sin(x)",
    "cosine": "cos(x)",
    "cosine wave": "cos(x)",
    "tangent curve": "tan(x)",
    "tangent wave": "tan(x)",
    "cubic": "x^3 - 3 * x",
    "exponential": "exp(x)",
    "logarithm": "ln(x)",
    "gaussian": "exp(-x^2)",
    "bell curve": "exp(-x^2 / 2)",
    "heaviside": "heaviside(x)",
    "cardioid": "r = 2 * (1 - cos(theta))",
    "astroid": "(cos(t)^3, sin(t)^3)",
    "heart": "(x^2 + y^2 - 1)^3 = x^2 * y^3",
    "heart curve": "(x^2 + y^2 - 1)^3 = x^2 * y^3",
    "folium": "x^3 + y^3 = 6 * x * y",
    "folium of descartes": "x^3 + y^3 = 6 * x * y",
    "lemniscate": "(x^2 + y^2)^2 = 8 * (x^2 - y^2)",
}


def _parse_val(token: str | None, default: float = 1.0) -> float:
    """Parse a token into a float value supporting numbers, fractions and words."""
    if not token:
        return default
    token = token.strip().lower()
    if token in NUM_WORDS:
        return NUM_WORDS[token]
    if "pi" in token:
        t = token.replace("*", "")
        if t == "pi":
            return math.pi
        if t in ("pi/2", "0.5pi", ".5pi"):
            return math.pi / 2.0
        if t in ("pi/4", "0.25pi"):
            return math.pi / 4.0
        if t in ("2pi",):
            return 2.0 * math.pi
        m1 = re.match(r"^(\d+(?:\.\d+)?)pi$", t)
        if m1:
            return float(m1.group(1)) * math.pi
        m2 = re.match(r"^pi/(\d+(?:\.\d+)?)$", t)
        if m2:
            return math.pi / float(m2.group(1))
    try:
        if "/" in token:
            num, denom = token.split("/", 1)
            return float(num) / float(denom)
        return float(token)
    except ValueError:
        return default


def _format_float(val: float) -> str:
    """Format float cleanly avoiding unnecessary trailing decimals."""
    if abs(val - round(val)) < 1e-5:
        return str(int(round(val)))
    if abs(val - math.pi) < 1e-4:
        return "pi"
    if abs(val - math.pi / 2) < 1e-4:
        return "pi/2"
    if abs(val - math.pi / 4) < 1e-4:
        return "pi/4"
    return f"{val:.4g}"


def _sub_xy(expr_str: str, sub_x: str, sub_y: str) -> str:
    """Safely replace variable symbols x and y without token collision."""
    tmp = re.sub(r"\bx\b", "___VAR_X___", expr_str)
    tmp = re.sub(r"\by\b", "___VAR_Y___", tmp)
    tmp = tmp.replace("___VAR_X___", sub_x)
    tmp = tmp.replace("___VAR_Y___", sub_y)
    return tmp


def _split_parametric(expr: str) -> tuple[str, str] | None:
    """Split (x(t), y(t)) respecting nested parentheses."""
    s = expr.strip()
    if not (s.startswith("(") and s.endswith(")")):
        return None
    inner = s[1:-1].strip()
    depth = 0
    comma_idx = -1
    for i, ch in enumerate(inner):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            comma_idx = i
            break
    if comma_idx != -1:
        return inner[:comma_idx].strip(), inner[comma_idx + 1:].strip()
    return None


def transform_equation_symbolic(
    expr_str: str,
    dx: float = 0.0,
    dy: float = 0.0,
    sx: float = 1.0,
    sy: float = 1.0,
    rx: bool = False,
    ry: bool = False,
    mirror_origin: bool = False,
    mirror_diag: bool = False,      # reflect across line y = x (Inverse function)
    mirror_diag_neg: bool = False,  # reflect across line y = -x
    mirror_x_val: float | None = None, # reflect across line x = c
    mirror_y_val: float | None = None, # reflect across line y = c
    rotate_deg: float = 0.0,
    operation: str | None = None,   # "derivative" | "antiderivative" | "tangent" | "normal" | "abs" | "reciprocal" | "square" | "sqrt" | "damped"
    op_param: float = 0.0,
) -> tuple[str, list[str]]:
    """Apply symbolic shifts, scaling, reflections, 2D rotations and calculus operations."""
    transformations: list[str] = []
    expr_clean = expr_str.strip()

    # Special Calculus & Morphing Operations
    if operation:
        if operation == "derivative":
            try:
                x = sp.Symbol("x")
                body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
                expr_sp = sp.sympify(body.replace("^", "**"))
                df_sp = sp.diff(expr_sp, x)
                df_str = sp.sstr(df_sp).replace("**", "^")
                transformations.append(f"Derivative d/dx[{body}]")
                return f"y = {df_str}", transformations
            except Exception as e:
                return f"derivative({expr_clean})", [f"Error differentiating: {e}"]

        if operation == "antiderivative":
            try:
                x = sp.Symbol("x")
                body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
                expr_sp = sp.sympify(body.replace("^", "**"))
                int_sp = sp.integrate(expr_sp, x)
                int_str = sp.sstr(int_sp).replace("**", "^")
                transformations.append(f"Antiderivative ∫({body})dx")
                return f"y = {int_str}", transformations
            except Exception as e:
                return f"integral({expr_clean})", [f"Error integrating: {e}"]

        if operation in ("tangent", "normal"):
            try:
                x = sp.Symbol("x")
                body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
                expr_sp = sp.sympify(body.replace("^", "**"))
                x0 = op_param
                y0 = expr_sp.subs(x, x0)
                df_sp = sp.diff(expr_sp, x)
                slope = df_sp.subs(x, x0)
                if operation == "tangent":
                    line_eq = sp.expand(slope * (x - x0) + y0)
                    transformations.append(f"Tangent line at x = {x0} (slope = {_format_float(float(slope))})")
                else:
                    if abs(float(slope)) < 1e-9:
                        return f"x = {_format_float(x0)}", [f"Vertical normal line at x = {x0}"]
                    norm_slope = -1 / slope
                    line_eq = sp.expand(norm_slope * (x - x0) + y0)
                    transformations.append(f"Normal line at x = {x0} (perpendicular slope = {_format_float(float(norm_slope))})")
                line_str = sp.sstr(line_eq).replace("**", "^")
                return f"y = {line_str}", transformations
            except Exception as e:
                return expr_clean, [f"Error computing line: {e}"]

        if operation == "abs":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            transformations.append("Full rectification: |f(x)|")
            return f"y = abs({body})", transformations

        if operation == "abs_x":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            new_body = re.sub(r"\bx\b", "abs(x)", body)
            transformations.append("Even symmetry: f(|x|)")
            return f"y = {new_body}", transformations

        if operation == "reciprocal":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            transformations.append("Reciprocal: 1 / f(x)")
            return f"y = 1 / ({body})", transformations

        if operation == "square":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            transformations.append("Squared function: (f(x))^2")
            return f"y = ({body})^2", transformations

        if operation == "sqrt":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            transformations.append("Square root: sqrt(f(x))")
            return f"y = sqrt({body})", transformations

        if operation == "damped":
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            transformations.append("Exponential decay damping: f(x) · exp(-0.2x)")
            return f"y = ({body}) * exp(-0.2 * x)", transformations

    # 1. Polar equations: r = f(theta)
    polar_match = re.match(r"^r\s*=\s*(.+)$", expr_clean, re.I)
    if polar_match:
        rhs = polar_match.group(1).strip()
        # Rotation / Phase shift (dx or rotate_deg)
        dtheta = dx + math.radians(rotate_deg) if rotate_deg != 0 else dx
        if abs(dtheta) > 1e-5:
            shift_sym = f"- {_format_float(dtheta)}" if dtheta > 0 else f"+ {_format_float(abs(dtheta))}"
            rhs = re.sub(r"\btheta\b", f"(theta {shift_sym})", rhs)
            transformations.append(f"Angular rotation: θ → θ {shift_sym}")
        if abs(sy - 1.0) > 1e-5:
            rhs = f"{_format_float(sy)} * ({rhs})"
            transformations.append(f"Radial scale: r → {sy} · r")
        if abs(dy) > 1e-5:
            shift_y = f"+ {_format_float(dy)}" if dy > 0 else f"- {_format_float(abs(dy))}"
            rhs = f"({rhs}) {shift_y}"
            transformations.append(f"Radial offset: {shift_y}")
        return f"r = {rhs}", transformations

    # 2. Parametric equations: (x(t), y(t))
    param_parts = _split_parametric(expr_clean)
    if param_parts:
        x_expr, y_expr = param_parts
        if rx:
            y_expr = f"-({y_expr})"
            transformations.append("Reflect over X-axis: y(t) → -y(t)")
        if ry:
            x_expr = f"-({x_expr})"
            transformations.append("Reflect over Y-axis: x(t) → -x(t)")
        if mirror_origin:
            x_expr = f"-({x_expr})"
            y_expr = f"-({y_expr})"
            transformations.append("Reflect over origin: (x, y) → (-x, -y)")
        if mirror_diag:
            x_expr, y_expr = y_expr, x_expr
            transformations.append("Reflect over line y = x: swap x(t) and y(t)")
        if abs(rotate_deg) > 1e-4:
            ang = math.radians(rotate_deg)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            new_x = f"({_format_float(cos_a)}*({x_expr}) - {_format_float(sin_a)}*({y_expr}))"
            new_y = f"({_format_float(sin_a)}*({x_expr}) + {_format_float(cos_a)}*({y_expr}))"
            x_expr, y_expr = new_x, new_y
            transformations.append(f"Planar rotation by {rotate_deg}°")
        if abs(sx - 1.0) > 1e-5:
            x_expr = f"{_format_float(sx)} * ({x_expr})"
            transformations.append(f"Scale X: x(t) → {_format_float(sx)} · x(t)")
        if abs(sy - 1.0) > 1e-5:
            y_expr = f"{_format_float(sy)} * ({y_expr})"
            transformations.append(f"Scale Y: y(t) → {_format_float(sy)} · y(t)")
        if abs(dx) > 1e-5:
            shift_x = f"+ {_format_float(dx)}" if dx > 0 else f"- {_format_float(abs(dx))}"
            x_expr = f"({x_expr}) {shift_x}"
            transformations.append(f"Shift X: x(t) {shift_x}")
        if abs(dy) > 1e-5:
            shift_y = f"+ {_format_float(dy)}" if dy > 0 else f"- {_format_float(abs(dy))}"
            y_expr = f"({y_expr}) {shift_y}"
            transformations.append(f"Shift Y: y(t) {shift_y}")
        return f"({x_expr}, {y_expr})", transformations

    # 3. Reflection across line y = x (Inverse function)
    if mirror_diag:
        try:
            x_sym, y_sym = sp.symbols("x y")
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            # If implicit equation: LHS = RHS, swap x and y
            if "=" in body and not body.lower().startswith("y ="):
                lhs_str, rhs_str = body.split("=", 1)
                lhs_swapped = _sub_xy(lhs_str, "y", "x")
                rhs_swapped = _sub_xy(rhs_str, "y", "x")
                transformations.append("Reflect over line y = x: swapped x and y")
                return f"{lhs_swapped} = {rhs_swapped}", transformations

            # Explicit function: solve f(y) = x for y
            f_sp = sp.sympify(body.replace("^", "**"))
            sols = sp.solve(sp.Eq(f_sp.subs(x_sym, y_sym), x_sym), y_sym)
            if sols:
                # Pick positive branch if multiple (e.g. sqrt(x))
                sol = sols[-1]
                inv_str = sp.sstr(sol).replace("**", "^")
                transformations.append("Inverse function (reflection across y = x)")
                return f"y = {inv_str}", transformations
        except Exception:
            # Fallback to swapping x and y in an implicit equation
            body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
            swapped = _sub_xy(body, "y", "x")
            transformations.append("Inverse function: x = f(y)")
            return f"x = {swapped}", transformations

    # 4. Rotation by angle (90 deg, 180 deg, 270 deg, or arbitrary angle)
    if abs(rotate_deg) > 1e-4:
        norm_deg = rotate_deg % 360
        body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()
        is_implicit = "=" in body and not body.lower().startswith("y =")

        if is_implicit:
            lhs_str, rhs_str = body.split("=", 1)
            lhs_str, rhs_str = lhs_str.strip(), rhs_str.strip()
            if abs(norm_deg - 90) < 1e-4:
                new_lhs = _sub_xy(lhs_str, "y", "(-x)")
                new_rhs = _sub_xy(rhs_str, "y", "(-x)")
                transformations.append("Rotated 90° counterclockwise: x → y, y → -x")
                return f"{new_lhs} = {new_rhs}", transformations
            elif abs(norm_deg - 180) < 1e-4:
                new_lhs = _sub_xy(lhs_str, "(-x)", "(-y)")
                new_rhs = _sub_xy(rhs_str, "(-x)", "(-y)")
                transformations.append("Rotated 180°: x → -x, y → -y")
                return f"{new_lhs} = {new_rhs}", transformations
            elif abs(norm_deg - 270) < 1e-4:
                new_lhs = _sub_xy(lhs_str, "(-y)", "x")
                new_rhs = _sub_xy(rhs_str, "(-y)", "x")
                transformations.append("Rotated 90° clockwise: x → -y, y → x")
                return f"{new_lhs} = {new_rhs}", transformations
            else:
                rad = math.radians(rotate_deg)
                cos_a = _format_float(math.cos(rad))
                sin_a = _format_float(math.sin(rad))
                sub_x = f"({cos_a}*x + {sin_a}*y)"
                sub_y = f"({cos_a}*y - {sin_a}*x)"
                new_lhs = _sub_xy(lhs_str, sub_x, sub_y)
                new_rhs = _sub_xy(rhs_str, sub_x, sub_y)
                transformations.append(f"Planar rotation by {rotate_deg}°")
                return f"{new_lhs} = {new_rhs}", transformations
        else:
            # Explicit function y = f(x)
            if abs(norm_deg - 90) < 1e-4:
                swapped = re.sub(r"\bx\b", "y", body)
                transformations.append("Rotated 90° counterclockwise: x = -f(y)")
                return f"x = -({swapped})", transformations
            elif abs(norm_deg - 180) < 1e-4:
                mirror_origin = True
            elif abs(norm_deg - 270) < 1e-4:
                swapped = re.sub(r"\bx\b", "(-y)", body)
                transformations.append("Rotated 90° clockwise: x = f(-y)")
                return f"x = {swapped}", transformations
            else:
                rad = math.radians(rotate_deg)
                cos_a = _format_float(math.cos(rad))
                sin_a = _format_float(math.sin(rad))
                sub_x_rot = f"({cos_a}*x + {sin_a}*y)"
                sub_y_rot = f"({cos_a}*y - {sin_a}*x)"
                new_rhs = re.sub(r"\bx\b", sub_x_rot, body)
                transformations.append(f"Planar rotation by {rotate_deg}°")
                return f"{sub_y_rot} = {new_rhs}", transformations

    # 5. 2D Implicit equations: LHS = RHS
    if "=" in expr_clean and not expr_clean.lower().startswith("y ="):
        lhs_raw, rhs_raw = expr_clean.split("=", 1)
        lhs_raw, rhs_raw = lhs_raw.strip(), rhs_raw.strip()

        sub_x = "x"
        if abs(dx) > 1e-5:
            sign = "-" if dx > 0 else "+"
            sub_x = f"(x {sign} {_format_float(abs(dx))})"
            transformations.append(f"Horizontal shift: x → (x {sign} {_format_float(abs(dx))})")
        if abs(sx - 1.0) > 1e-5:
            sub_x = f"({sub_x} / {_format_float(sx)})"
            transformations.append(f"Horizontal scale: x → x / {_format_float(sx)}")
        if ry:
            sub_x = f"(-{sub_x})"
            transformations.append("Reflect over Y-axis: x → -x")
        if mirror_origin:
            sub_x = f"(-{sub_x})"
            transformations.append("Reflect over origin: x → -x")
        if mirror_x_val is not None:
            c2 = _format_float(2.0 * mirror_x_val)
            sub_x = f"({c2} - {sub_x})"
            transformations.append(f"Reflect over line x = {mirror_x_val}")

        sub_y = "y"
        if abs(dy) > 1e-5:
            sign = "-" if dy > 0 else "+"
            sub_y = f"(y {sign} {_format_float(abs(dy))})"
            transformations.append(f"Vertical shift: y → (y {sign} {_format_float(abs(dy))})")
        if abs(sy - 1.0) > 1e-5:
            sub_y = f"({sub_y} / {_format_float(sy)})"
            transformations.append(f"Vertical scale: y → y / {_format_float(sy)}")
        if rx:
            sub_y = f"(-{sub_y})"
            transformations.append("Reflect over X-axis: y → -y")
        if mirror_origin:
            sub_y = f"(-{sub_y})"
            transformations.append("Reflect over origin: y → -y")
        if mirror_y_val is not None:
            c2 = _format_float(2.0 * mirror_y_val)
            sub_y = f"({c2} - {sub_y})"
            transformations.append(f"Reflect over line y = {mirror_y_val}")

        try:
            x, y = sp.symbols("x y")
            lhs_sp = sp.sympify(lhs_raw.replace("^", "**"))
            rhs_sp = sp.sympify(rhs_raw.replace("^", "**"))
            sub_x_sp = sp.sympify(sub_x.replace("^", "**"))
            sub_y_sp = sp.sympify(sub_y.replace("^", "**"))
            new_lhs = lhs_sp.subs([(x, sub_x_sp), (y, sub_y_sp)])
            new_rhs = rhs_sp.subs([(x, sub_x_sp), (y, sub_y_sp)])
            return f"{sp.sstr(new_lhs).replace('**', '^')} = {sp.sstr(new_rhs).replace('**', '^')}", transformations
        except Exception:
            new_lhs_str = re.sub(r"\bx\b", sub_x, lhs_raw)
            new_lhs_str = re.sub(r"\by\b", sub_y, new_lhs_str)
            new_rhs_str = re.sub(r"\bx\b", sub_x, rhs_raw)
            new_rhs_str = re.sub(r"\by\b", sub_y, new_rhs_str)
            return f"{new_lhs_str} = {new_rhs_str}", transformations

    # 6. Explicit functions: y = f(x) or f(x)
    expr_body = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", expr_clean, flags=re.I).strip()

    # Step A: Horizontal transformations on x
    sub_x_str = "x"
    if abs(dx) > 1e-5:
        sign = "-" if dx > 0 else "+"
        sub_x_str = f"(x {sign} {_format_float(abs(dx))})"
        transformations.append(f"Horizontal shift: x → (x {sign} {_format_float(abs(dx))})")
    if abs(sx - 1.0) > 1e-5:
        inv_sx = 1.0 / sx
        if abs(inv_sx - round(inv_sx)) < 1e-4:
            k = int(round(inv_sx))
            sub_x_str = f"({k} * {sub_x_str})"
            transformations.append(f"Horizontal compression: x → {k} · x")
        elif abs(sx - round(sx)) < 1e-4:
            k = int(round(sx))
            sub_x_str = f"({sub_x_str} / {k})"
            transformations.append(f"Horizontal stretch: x → x / {k}")
        else:
            sub_x_str = f"({sub_x_str} / {_format_float(sx)})"
            transformations.append(f"Horizontal scale: x → x / {_format_float(sx)}")
    if ry or mirror_origin:
        sub_x_str = f"(-{sub_x_str})"
        transformations.append("Reflect over Y-axis: x → -x")
    if mirror_x_val is not None:
        c2 = _format_float(2.0 * mirror_x_val)
        sub_x_str = f"({c2} - {sub_x_str})"
        transformations.append(f"Reflect over line x = {mirror_x_val}")

    # Step B: Vertical transformations on output
    if rx or mirror_origin:
        transformations.append("Reflect over X-axis: f(x) → -f(x)")
    if mirror_y_val is not None:
        transformations.append(f"Reflect over line y = {mirror_y_val}")
    if abs(sy - 1.0) > 1e-5:
        transformations.append(f"Vertical scale: f(x) → {_format_float(sy)} · f(x)")
    if abs(dy) > 1e-5:
        sign = "+" if dy > 0 else "-"
        transformations.append(f"Vertical shift: f(x) {sign} {_format_float(abs(dy))}")

    try:
        x = sp.Symbol("x")
        expr_sp = sp.sympify(expr_body.replace("^", "**"))
        sub_sp = sp.sympify(sub_x_str.replace("^", "**"))
        res_sp = expr_sp.subs(x, sub_sp)
        if rx or mirror_origin:
            res_sp = -res_sp
        if mirror_y_val is not None:
            res_sp = 2.0 * mirror_y_val - res_sp
        if abs(sy - 1.0) > 1e-5:
            scale_factor = int(sy) if abs(sy - round(sy)) < 1e-5 else sy
            res_sp = res_sp * scale_factor
        if abs(dy) > 1e-5:
            dy_val = int(dy) if abs(dy - round(dy)) < 1e-5 else dy
            res_sp = res_sp + dy_val
        final_str = sp.sstr(res_sp).replace("**", "^")
        return f"y = {final_str}", transformations
    except Exception:
        res_str = re.sub(r"\bx\b", sub_x_str, expr_body)
        if rx or mirror_origin:
            res_str = f"-({res_str})"
        if mirror_y_val is not None:
            res_str = f"{_format_float(2.0 * mirror_y_val)} - ({res_str})"
        if abs(sy - 1.0) > 1e-5:
            res_str = f"{_format_float(sy)} * ({res_str})"
        if abs(dy) > 1e-5:
            sign = "+" if dy > 0 else "-"
            res_str = f"({res_str}) {sign} {_format_float(abs(dy))}"
        return f"y = {res_str}", transformations


def parse_shift_intent(
    prompt: str,
    current_expr: str | None = None,
    viewport: dict[str, float] | None = None,
) -> ShiftResult | None:
    """Parse natural language shifting, mirroring, rotation, calculus, morphing, and settings prompts."""
    raw = prompt.strip()
    if not raw:
        return None

    cleaned = raw.lower().strip()
    cleaned = re.sub(r"^(?:hey\s+|hi\s+)?nebula[,.]?\s*", "", cleaned)
    cleaned = re.sub(r"^(?:can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?|please\s+|i\s+want\s+to\s+)", "", cleaned)

    # -------------------------------------------------------------------------
    # 1. GRAPH SETTINGS COMMANDS VIA NLP
    # -------------------------------------------------------------------------
    if re.search(r"\b(?:switch\s+to\s+polar|change\s+to\s+polar|polar\s+grid|polar\s+mode)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "gridType",
            "value": "polar",
            "feedback": "Switched to Polar grid mode",
            "explanation": "Concentric circle radius intervals and radial angle spokes",
        }
    if re.search(r"\b(?:switch\s+to\s+cartesian|change\s+to\s+cartesian|cartesian\s+grid|cartesian\s+mode)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "gridType",
            "value": "cartesian",
            "feedback": "Switched to Cartesian grid mode",
            "explanation": "Standard orthogonal X and Y coordinate grid",
        }
    if re.search(r"\b(?:turn\s+on\s+projector|enable\s+projector|projector\s+mode\s+on|presentation\s+mode)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "projectorMode",
            "value": True,
            "feedback": "Projector Mode activated (high-contrast bold rendering)",
            "explanation": "High-contrast thick axes and bold mathematical typography for presentations",
        }
    if re.search(r"\b(?:turn\s+off\s+projector|disable\s+projector|projector\s+mode\s+off|standard\s+mode)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "projectorMode",
            "value": False,
            "feedback": "Standard Display Mode restored",
            "explanation": "Standard line weights and contrast",
        }
    if re.search(r"\b(?:degrees\s+mode|switch\s+to\s+degrees|use\s+degrees)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "angleMode",
            "value": "deg",
            "feedback": "Angle mode set to Degrees (°)",
            "explanation": "Angles displayed in degrees (0° to 360°)",
        }
    if re.search(r"\b(?:radians\s+mode|switch\s+to\s+radians|use\s+radians)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "angleMode",
            "value": "rad",
            "feedback": "Angle mode set to Radians (rad)",
            "explanation": "Angles displayed in radians (0 to 2π)",
        }
    if re.search(r"\b(?:show\s+(?:poi|points\s+of\s+interest)|turn\s+on\s+poi)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "showPOI",
            "value": True,
            "feedback": "Points of Interest enabled (roots, intercepts, extrema)",
            "explanation": "Display markers and coordinate tooltips at key mathematical points",
        }
    if re.search(r"\b(?:hide\s+(?:poi|points\s+of\s+interest)|turn\s+off\s+poi)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "showPOI",
            "value": False,
            "feedback": "Points of Interest hidden",
            "explanation": "Hide POI markers",
        }
    if re.search(r"\b(?:turn\s+on\s+tracing|enable\s+tracing|show\s+tracing)\b", cleaned):
        return {
            "action": "set_setting",
            "ok": True,
            "setting": "showTracing",
            "value": True,
            "feedback": "Curve Tracing enabled",
            "explanation": "Real-time snap-to-curve coordinate cursor indicator",
        }

    # -------------------------------------------------------------------------
    # 2. VIEWPORT / CAMERA / PAN SHIFTING
    # -------------------------------------------------------------------------
    is_view_intent = bool(
        re.search(r"\b(?:view|camera|screen|viewport|canvas|window|focus)\b", cleaned)
        or re.search(r"^\s*pan\b", cleaned)
    )
    if is_view_intent and not re.search(r"\b(?:curve|equation|function|line|parabola|sine|wave)\b", cleaned):
        coord_match = re.search(
            r"(?:to|at)\s+(?:origin|\(?\s*(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)\s*\)?)", cleaned
        )
        if coord_match:
            if "origin" in cleaned:
                tx, ty = 0.0, 0.0
            else:
                tx = float(coord_match.group(1))
                ty = float(coord_match.group(2))
            return {
                "action": "shift_view",
                "ok": True,
                "target_x": tx,
                "target_y": ty,
                "dx": 0.0,
                "dy": 0.0,
                "feedback": f"Centering view at ({_format_float(tx)}, {_format_float(ty)})",
                "explanation": f"Pan camera view to coordinates ({_format_float(tx)}, {_format_float(ty)})",
            }

        pdx = 0.0
        pdy = 0.0
        default_pan = 4.0

        r_match = re.search(r"\b(?:right|east)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned)
        if r_match:
            pdx += _parse_val(r_match.group(1), default_pan)
        l_match = re.search(r"\b(?:left|west)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned)
        if l_match:
            pdx -= _parse_val(l_match.group(1), default_pan)
        u_match = re.search(r"\b(?:up|upward|upwards|north)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned)
        if u_match:
            pdy += _parse_val(u_match.group(1), default_pan)
        d_match = re.search(r"\b(?:down|downward|downwards|south)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned)
        if d_match:
            pdy -= _parse_val(d_match.group(1), default_pan)

        if abs(pdx) > 1e-5 or abs(pdy) > 1e-5:
            dir_parts = []
            if pdx > 0:
                dir_parts.append(f"right {_format_float(pdx)}")
            elif pdx < 0:
                dir_parts.append(f"left {_format_float(abs(pdx))}")
            if pdy > 0:
                dir_parts.append(f"up {_format_float(pdy)}")
            elif pdy < 0:
                dir_parts.append(f"down {_format_float(abs(pdy))}")
            return {
                "action": "shift_view",
                "ok": True,
                "dx": pdx,
                "dy": pdy,
                "target_x": None,
                "target_y": None,
                "feedback": f"Panning view {', '.join(dir_parts)}",
                "explanation": f"Shift viewport camera: Δx = {_format_float(pdx)}, Δy = {_format_float(pdy)}",
            }

    # -------------------------------------------------------------------------
    # 3. BASE EQUATION RESOLUTION
    # -------------------------------------------------------------------------
    base_eq: str | None = None
    target_curve_name: str | None = None

    for name, default_formula in BASE_CURVE_DEFAULTS.items():
        if re.search(r"\b" + re.escape(name) + r"\b", cleaned):
            target_curve_name = name
            base_eq = default_formula
            break

    if not base_eq:
        formula_candidate = re.search(
            r"\b(?:of|for|equation|curve)\s+([xyt0-9+\-*/^().\s=]+?)(?:\s+(?:at|across|over|by|to|and)|$)", cleaned
        )
        if formula_candidate and any(c in formula_candidate.group(1) for c in "+-*/^="):
            base_eq = formula_candidate.group(1).strip()

    if not base_eq:
        if current_expr and current_expr.strip():
            base_eq = current_expr.strip()
        else:
            base_eq = "x^2 - 4"

    # Clean base equation
    clean_base = re.sub(r"^(?:y\s*=\s*|f\(x\)\s*=\s*)", "", base_eq, flags=re.I).strip()

    # -------------------------------------------------------------------------
    # 4. CALCULUS & TANGENTS NLP
    # -------------------------------------------------------------------------
    # Tangent line at x = c
    tangent_match = re.search(r"\btangent(?:\s+line)?(?:\s+at)?\s*(?:x\s*=\s*)?(-?\d+(?:\.\d+)?)\b", cleaned)
    if tangent_match:
        x0 = float(tangent_match.group(1))
        eq, trans = transform_equation_symbolic(base_eq, operation="tangent", op_param=x0)
        return {
            "action": "add_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": f"Tangent Line at x = {_format_float(x0)}",
            "feedback": f"Generated tangent line: {eq}",
            "explanation": f"Tangent line to {base_eq} at x = {_format_float(x0)}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Normal line at x = c
    normal_match = re.search(r"\b(?:normal|perpendicular)(?:\s+line)?(?:\s+at)?\s*(?:x\s*=\s*)?(-?\d+(?:\.\d+)?)\b", cleaned)
    if normal_match:
        x0 = float(normal_match.group(1))
        eq, trans = transform_equation_symbolic(base_eq, operation="normal", op_param=x0)
        return {
            "action": "add_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": f"Normal Line at x = {_format_float(x0)}",
            "feedback": f"Generated normal line: {eq}",
            "explanation": f"Perpendicular normal line to {base_eq} at x = {_format_float(x0)}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Definite integral with area under curve
    integral_match = re.search(
        r"\b(?:area\s+under\s+(?:the\s+)?curve|definite\s+integral|shade\s+area|integrate)\s+(?:from\s+(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)|between\s+(-?\d+(?:\.\d+)?)\s+and\s+(-?\d+(?:\.\d+)?))\b",
        cleaned,
    )
    if integral_match:
        g = integral_match.groups()
        a_val = float(g[0] if g[0] is not None else g[2])
        b_val = float(g[1] if g[1] is not None else g[3])
        int_expr = f"integral({clean_base}, {_format_float(a_val)}, {_format_float(b_val)})"
        return {
            "action": "add_equation",
            "ok": True,
            "equation": int_expr,
            "canonical": int_expr,
            "title": f"Definite Integral from {_format_float(a_val)} to {_format_float(b_val)}",
            "feedback": f"Shading area under curve: {int_expr}",
            "explanation": f"Riemann definite integral of {clean_base} from x={_format_float(a_val)} to x={_format_float(b_val)}",
            "transformations": [f"Definite integral from x={a_val} to x={b_val}"],
            "mode": "math",
        }

    # Derivative
    if re.search(r"\b(?:derivative|differentiate|f\s*prime|tangent\s+slope|rate\s+of\s+change|slope\s+function)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="derivative")
        action = "add_equation" if re.search(r"\b(?:add|plot|draw|show)\b", cleaned) else "shift_equation"
        return {
            "action": action,
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Derivative f'(x)",
            "feedback": f"Computed derivative: {eq}",
            "explanation": f"First derivative d/dx of {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Antiderivative
    if re.search(r"\b(?:antiderivative|integrate(?:\s+this)?|indefinite\s+integral)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="antiderivative")
        action = "add_equation" if re.search(r"\b(?:add|plot|draw|show)\b", cleaned) else "shift_equation"
        return {
            "action": action,
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Antiderivative ∫f(x)dx",
            "feedback": f"Computed antiderivative: {eq}",
            "explanation": f"Indefinite integral of {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # -------------------------------------------------------------------------
    # 5. FUNCTION MORPHING NLP
    # -------------------------------------------------------------------------
    # Absolute value |f(x)|
    if re.search(r"\b(?:absolute\s+value|abs|rectify|make\s+(?:it\s+)?positive)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="abs")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Absolute Value |f(x)|",
            "feedback": f"Applied absolute value: {eq}",
            "explanation": f"Full-wave rectification of {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Even symmetry f(|x|)
    if re.search(r"\b(?:abs\s+of\s+x|even\s+symmetric|absolute\s+x)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="abs_x")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Even Symmetry f(|x|)",
            "feedback": f"Applied even symmetry: {eq}",
            "explanation": f"Symmetric reflection across y-axis using f(|x|): {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Reciprocal 1 / f(x)
    if re.search(r"\b(?:reciprocal|1\s+over|one\s+over|invert\s+values)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="reciprocal")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Reciprocal 1 / f(x)",
            "feedback": f"Computed reciprocal: {eq}",
            "explanation": f"Value reciprocal 1 / ({base_eq}): {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Square function (f(x))^2
    if re.search(r"\b(?:square\s+this|raise\s+to\s+power\s+2|f\(x\)\s*squared)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="square")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Squared Function (f(x))^2",
            "feedback": f"Squared function: {eq}",
            "explanation": f"Squared polynomial/function of {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Square root sqrt(f(x))
    if re.search(r"\b(?:square\s+root|take\s+sqrt)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="sqrt")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Square Root sqrt(f(x))",
            "feedback": f"Applied square root: {eq}",
            "explanation": f"Square root of {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Damping envelope
    if re.search(r"\b(?:damp|decay\s+envelope|damped\s+oscillator|exponential\s+decay)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, operation="damped")
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Damped Oscillator",
            "feedback": f"Applied damping envelope: {eq}",
            "explanation": f"Multiplied {base_eq} by exponential decay envelope exp(-0.2x): {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # -------------------------------------------------------------------------
    # 6. INEQUALITIES & SHADING VIA NLP
    # -------------------------------------------------------------------------
    if re.search(r"\b(?:shade\s+below|less\s+than\s+or\s+equal|less\s+than|fill\s+under)\b", cleaned):
        if "=" in clean_base:
            lhs, rhs = clean_base.split("=", 1)
            ineq_eq = f"{lhs.strip()} <= {rhs.strip()}"
        else:
            ineq_eq = f"y <= {clean_base}"
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": ineq_eq,
            "canonical": ineq_eq,
            "title": "Shaded Inequality (Below)",
            "feedback": f"Created shaded inequality: {ineq_eq}",
            "explanation": f"Shaded region below boundary {clean_base}",
            "transformations": ["Inequality conversion: y ≤ f(x)"],
            "mode": "math",
        }

    if re.search(r"\b(?:shade\s+above|greater\s+than\s+or\s+equal|greater\s+than|fill\s+above)\b", cleaned):
        if "=" in clean_base:
            lhs, rhs = clean_base.split("=", 1)
            ineq_eq = f"{lhs.strip()} >= {rhs.strip()}"
        else:
            ineq_eq = f"y >= {clean_base}"
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": ineq_eq,
            "canonical": ineq_eq,
            "title": "Shaded Inequality (Above)",
            "feedback": f"Created shaded inequality: {ineq_eq}",
            "explanation": f"Shaded region above boundary {clean_base}",
            "transformations": ["Inequality conversion: y ≥ f(x)"],
            "mode": "math",
        }

    # -------------------------------------------------------------------------
    # 7. MIRRORING & REFLECTIONS NLP
    # -------------------------------------------------------------------------
    # Mirror across line y = x (Inverse function)
    if re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|over|on)?\s*(?:(?:the\s+)?line\s+)?y\s*=\s*x\b", cleaned) or \
       re.search(r"\b(?:inverse(?:\s+function)?|find\s+(?:the\s+)?inverse|swap\s+x\s+and\s+y)\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, mirror_diag=True)
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Inverse Function (Mirrored across y = x)",
            "feedback": f"Mirrored across line y = x: {eq}",
            "explanation": f"Calculated inverse function by reflecting {base_eq} across the diagonal line y = x",
            "transformations": trans,
            "mode": "math",
        }

    # Mirror across origin
    if re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|through|over|around)?\s*(?:the\s+)?origin\b", cleaned) or \
       re.search(r"\bpoint\s+reflection\s+(?:at|across)?\s*origin\b", cleaned):
        eq, trans = transform_equation_symbolic(base_eq, mirror_origin=True)
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": "Point Reflection (Mirrored across Origin)",
            "feedback": f"Mirrored across origin: {eq}",
            "explanation": f"Point reflection of {base_eq} through the origin (x → -x, y → -y): {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # Mirror across arbitrary line x = c
    line_x_match = re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|over|on)?\s*(?:(?:the\s+)?line\s+)?x\s*=\s*(-?\d+(?:\.\d+)?)\b", cleaned)
    if line_x_match:
        c = float(line_x_match.group(1))
        eq, trans = transform_equation_symbolic(base_eq, mirror_x_val=c)
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": f"Mirrored across line x = {_format_float(c)}",
            "feedback": f"Mirrored across line x = {_format_float(c)}: {eq}",
            "explanation": f"Reflected {base_eq} across vertical axis x = {_format_float(c)}",
            "transformations": trans,
            "mode": "math",
        }

    # Mirror across arbitrary line y = c
    line_y_match = re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|over|on)?\s*(?:(?:the\s+)?line\s+)?y\s*=\s*(-?\d+(?:\.\d+)?)\b", cleaned)
    if line_y_match:
        c = float(line_y_match.group(1))
        eq, trans = transform_equation_symbolic(base_eq, mirror_y_val=c)
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": f"Mirrored across line y = {_format_float(c)}",
            "feedback": f"Mirrored across line y = {_format_float(c)}: {eq}",
            "explanation": f"Reflected {base_eq} across horizontal axis y = {_format_float(c)}",
            "transformations": trans,
            "mode": "math",
        }

    # Mirror across X-axis
    rx = bool(
        re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|over|around|on)?\s*(?:the\s+)?x(?:\s*-\s*axis)?\b", cleaned)
        or re.search(r"\b(?:flip\s+vertically|flip\s+upside\s+down|invert\s+y|invert\s+vertically)\b", cleaned)
    )

    # Mirror across Y-axis
    ry = bool(
        re.search(r"\b(?:mirror|reflect|flip)\s+(?:across|over|around|on)?\s*(?:the\s+)?y(?:\s*-\s*axis)?\b", cleaned)
        or re.search(r"\b(?:flip\s+horizontally|invert\s+x|invert\s+horizontally)\b", cleaned)
    )

    # -------------------------------------------------------------------------
    # 8. 2D ROTATION NLP
    # -------------------------------------------------------------------------
    rot_match = re.search(
        r"\b(?:rotate|turn)\s+(?:by\s+)?(-?\d+(?:\.\d+)?|pi(?:/\d+)?)\s*(?:degrees?|deg|rad|radians?)?(?:\s*(?:clockwise|counterclockwise|ccw|cw))?\b",
        cleaned,
    ) or re.search(r"\brotate\s+(-?\d+)\b", cleaned)

    rotate_deg = 0.0
    if rot_match:
        ang_token = rot_match.group(1)
        is_rad = "rad" in cleaned or "pi" in ang_token
        is_cw = "clockwise" in cleaned or "cw" in cleaned
        val = _parse_val(ang_token, 90.0)
        deg_val = math.degrees(val) if is_rad else val
        rotate_deg = -deg_val if is_cw else deg_val
        eq, trans = transform_equation_symbolic(base_eq, rotate_deg=rotate_deg)
        return {
            "action": "shift_equation",
            "ok": True,
            "equation": eq,
            "canonical": eq,
            "title": f"Rotated by {_format_float(rotate_deg)}°",
            "feedback": f"Rotated by {_format_float(rotate_deg)}°: {eq}",
            "explanation": f"Applied planar 2D rotation of {_format_float(rotate_deg)}° to {base_eq}: {eq}",
            "transformations": trans,
            "mode": "math",
        }

    # -------------------------------------------------------------------------
    # 9. SCALING, STRETCHING & COMPRESSION NLP
    # -------------------------------------------------------------------------
    sx = 1.0
    sy = 1.0

    stretch_y = re.search(r"\b(?:stretch|scale)\s+(?:vertically|y)(?:\s+by)?\s*([a-z0-9_./+-]+)", cleaned) or \
                re.search(r"\bscale\s+y\s*(?:by)?\s*([a-z0-9_./+-]+)", cleaned)
    if stretch_y:
        sy = _parse_val(stretch_y.group(1), 2.0)

    compress_y = re.search(r"\b(?:compress|shrink)\s+(?:vertically|y)(?:\s+by)?\s*([a-z0-9_./+-]+)", cleaned)
    if compress_y:
        factor = _parse_val(compress_y.group(1), 2.0)
        sy = 1.0 / factor if factor != 0 else 1.0

    stretch_x = re.search(r"\b(?:stretch|scale|widen)\s+(?:horizontally|x)(?:\s+by)?\s*([a-z0-9_./+-]+)", cleaned)
    if stretch_x:
        sx = _parse_val(stretch_x.group(1), 2.0)

    compress_x = re.search(r"\b(?:compress|shrink|narrow)\s+(?:horizontally|x)(?:\s+by)?\s*([a-z0-9_./+-]+)", cleaned)
    if compress_x:
        factor = _parse_val(compress_x.group(1), 2.0)
        sx = 1.0 / factor if factor != 0 else 1.0

    if re.search(r"\bdouble\s+(?:the\s+)?(?:height|vertical|size|amplitude)\b", cleaned):
        sy = 2.0
    if re.search(r"\btriple\s+(?:the\s+)?(?:height|vertical|amplitude)\b", cleaned):
        sy = 3.0
    if re.search(r"\bhalve\s+(?:the\s+)?(?:height|vertical|amplitude)\b", cleaned):
        sy = 0.5
    if re.search(r"\bdouble\s+(?:the\s+)?(?:period|frequency)\b", cleaned):
        sx = 2.0
    if re.search(r"\btriple\s+(?:the\s+)?frequency\b", cleaned):
        sx = 1.0 / 3.0

    # -------------------------------------------------------------------------
    # 10. COORDINATE SHIFTS & TRANSLATIONS NLP
    # -------------------------------------------------------------------------
    dx = 0.0
    dy = 0.0

    target_point_match = re.search(
        r"(?:to\s+(?:center|vertex|origin|point)|center\s+to|vertex\s+to)\s*\(?(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)\)?",
        cleaned,
    )
    if target_point_match:
        dx = float(target_point_match.group(1))
        dy = float(target_point_match.group(2))
    else:
        vec_match = re.search(r"\b(?:shift|translate|move)\s+(?:by\s+)?\(?(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)\)?", cleaned)
        if vec_match:
            dx = float(vec_match.group(1))
            dy = float(vec_match.group(2))
        else:
            by_match = re.search(r"\bby\s+([a-z0-9_./+-]+)\b", cleaned)
            by_val = _parse_val(by_match.group(1), 1.0) if by_match else None

            # Horizontal: Right
            right_match = re.search(
                r"\b(?:right|to\s+the\s+right|forward)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned
            ) or re.search(r"([a-z0-9_./+-]+)\s*units?\s+(?:to\s+the\s+)?right", cleaned)
            if right_match:
                val_token = right_match.group(1)
                if val_token and val_token in ["and", "up", "down", "by"]:
                    val_token = None
                dx += _parse_val(val_token, by_val or 1.0)

            # Horizontal: Left
            left_match = re.search(
                r"\b(?:left|to\s+the\s+left|backward)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned
            ) or re.search(r"([a-z0-9_./+-]+)\s*units?\s+(?:to\s+the\s+)?left", cleaned)
            if left_match:
                val_token = left_match.group(1)
                if val_token and val_token in ["and", "up", "down", "by"]:
                    val_token = None
                dx -= _parse_val(val_token, by_val or 1.0)

            # Vertical: Up / Raise
            up_match = re.search(
                r"\b(?:up|upward|upwards|raise|elevate)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned
            ) or re.search(r"([a-z0-9_./+-]+)\s*units?\s+(?:up|upward)", cleaned)
            if up_match:
                val_token = up_match.group(1)
                if val_token and val_token in ["and", "right", "left", "by"]:
                    val_token = None
                dy += _parse_val(val_token, by_val or 1.0)

            # Vertical: Down / Lower
            down_match = re.search(
                r"\b(?:down|downward|downwards|lower|drop)\b(?:\s+(?:by\s+)?([a-z0-9_./+-]+))?", cleaned
            ) or re.search(r"([a-z0-9_./+-]+)\s*units?\s+(?:down|downward)", cleaned)
            if down_match:
                val_token = down_match.group(1)
                if val_token and val_token in ["and", "right", "left", "by"]:
                    val_token = None
                dy -= _parse_val(val_token, by_val or 1.0)

    # If action keywords were matched (shift, reflect, stretch, compress)
    has_action = (abs(dx) > 1e-5 or abs(dy) > 1e-5 or abs(sx - 1.0) > 1e-5 or abs(sy - 1.0) > 1e-5 or rx or ry)

    if not has_action:
        # Check if shift keyword exists with direction words
        if re.search(r"\b(?:shift|translate|move)\b", cleaned):
            if "right" in cleaned:
                dx = 1.0
            elif "left" in cleaned:
                dx = -1.0
            elif "up" in cleaned or "raise" in cleaned:
                dy = 1.0
            elif "down" in cleaned or "lower" in cleaned:
                dy = -1.0
            else:
                dx = 2.0
                dy = 1.0
            has_action = True

    if not has_action:
        return None

    # Perform the symbolic mathematical transformation
    new_eq, transformations = transform_equation_symbolic(
        base_eq, dx=dx, dy=dy, sx=sx, sy=sy, rx=rx, ry=ry
    )

    trans_summary = []
    if abs(dx) > 1e-5:
        trans_summary.append(f"{'right' if dx > 0 else 'left'} {_format_float(abs(dx))}")
    if abs(dy) > 1e-5:
        trans_summary.append(f"{'up' if dy > 0 else 'down'} {_format_float(abs(dy))}")
    if rx:
        trans_summary.append("reflected over x-axis")
    if ry:
        trans_summary.append("reflected over y-axis")
    if abs(sx - 1.0) > 1e-5:
        trans_summary.append(f"scaled x by {_format_float(sx)}")
    if abs(sy - 1.0) > 1e-5:
        trans_summary.append(f"scaled y by {_format_float(sy)}")

    title = f"Shifted {target_curve_name.title()}" if target_curve_name else "Transformed Equation"
    summary_str = ", ".join(trans_summary) if trans_summary else "shifted"
    feedback = f"Shifted {summary_str}: {new_eq}"
    explanation = f"Applied geometric transformation ({summary_str}) to {base_eq}: {new_eq}"

    return {
        "action": "shift_equation",
        "ok": True,
        "equation": new_eq,
        "canonical": new_eq,
        "original_equation": base_eq,
        "dx": dx,
        "dy": dy,
        "scale_x": sx,
        "scale_y": sy,
        "reflect_x": rx,
        "reflect_y": ry,
        "target_x": None,
        "target_y": None,
        "title": title,
        "explanation": explanation,
        "transformations": transformations,
        "feedback": feedback,
        "mode": "math",
    }

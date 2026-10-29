"""
Nebula - A Desmos-like Graphing Calculator
Built with Streamlit and HTML5 Canvas
"""

import streamlit as st  # type: ignore[import-not-found]
import streamlit.components.v1 as components
import json
import math
import uuid
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

# ─── Page Config ───
st.set_page_config(page_title="Nebula Graphing Calculator", page_icon="🌌", layout="wide", initial_sidebar_state="collapsed")

# ─── CSS ───
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
:root{--nbg:#0d1117;--npan:#161b22;--npanh:#1c2128;--nbd:#2d333b;--ntxt:#e6edf3;--ntxtm:#7d8b99;--nacc:#00d4aa;--naccd:#00d4aa33;--ndng:#ff4757;--ntrk:#2d333b;--nthb:#00d4aa;--ninp:#0d1117;--nbrd:#2d333b;--nexbg:#10151b;--nexh:#161b22;}
*{font-family:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif!important}
html,body,[data-testid="stAppViewContainer"]{background:var(--nbg)!important;color:var(--ntxt)!important}
#MainMenu,footer,header,[data-testid="stDecoration"]{display:none!important}
[data-testid="stHeader"]{background:transparent!important}
.nebula-app{display:grid;grid-template-columns:380px 1fr;grid-template-rows:1fr;overflow:hidden;height:100vh}
.nebula-sidebar{background:var(--npan);border-right:1px solid var(--nbd);display:flex;flex-direction:column;overflow:hidden}
.nebula-canvas-area{position:relative;background:var(--nbg);overflow:hidden}
.nebula-header{padding:12px 16px;border-bottom:1px solid var(--nbd);display:flex;align-items:center;gap:12px;flex-shrink:0}
.nebula-logo{display:flex;align-items:center;gap:8px;font-weight:600;font-size:18px;color:var(--ntxt)}
.nebula-logo-icon{width:28px;height:28px;background:linear-gradient(135deg,#00d4aa 0%,#0099ff 100%);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px}
.nebula-expressions{flex:1;overflow-y:auto;padding:8px;display:flex;flex-direction:column;gap:4px}
.nebula-expression-row{background:var(--nexbg);border:1px solid var(--nbd);border-radius:8px;transition:all .15s ease}
.nebula-expression-row:hover{background:var(--nexh);border-color:#3d4450}
.nebula-expression-main{display:flex;align-items:center;gap:8px;padding:10px 12px}
.nebula-color-indicator{width:14px;height:14px;border-radius:4px;flex-shrink:0;border:2px solid var(--nbd);cursor:pointer;transition:transform .1s ease}
.nebula-color-indicator:hover{transform:scale(1.15)}
.nebula-expression-input{flex:1;background:transparent!important;border:none!important;color:var(--ntxt)!important;font-size:15px!important;font-family:'IBM Plex Sans',monospace!important;line-height:1.4!important;padding:0!important;outline:none!important;min-width:0}
.nebula-expression-input::placeholder{color:var(--ntxtm)!important}
.nebula-expression-actions{display:flex;align-items:center;gap:4px;opacity:0;transition:opacity .15s ease}
.nebula-expression-row:hover .nebula-expression-actions,.nebula-expression-row:focus-within .nebula-expression-actions{opacity:1}
.nebula-btn-icon{width:32px;height:32px;border-radius:6px;background:transparent;border:1px solid var(--nbd);color:var(--ntxtm);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .1s ease;font-size:16px}
.nebula-btn-icon:hover{background:var(--npanh);border-color:#3d4450;color:var(--ntxt)}
.nebula-btn-icon.danger:hover{background:var(--ndng);border-color:var(--ndng);color:white}
.nebula-expression-details{padding:0 12px 10px;display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--nbd);margin-top:-1px;animation:slideDown .2s ease}
@keyframes slideDown{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
.nebula-slider{display:flex;align-items:center;gap:10px;padding:8px 0}
.nebula-slider-label{font-size:13px;color:var(--ntxtm);min-width:40px;font-variant-numeric:tabular-nums}
.nebula-slider-input{width:70px;background:var(--ninp)!important;border:1px solid var(--nbrd)!important;border-radius:6px!important;color:var(--ntxt)!important;font-size:13px!important;padding:6px 10px!important;font-family:'IBM Plex Sans',monospace!important}
.nebula-slider-track{flex:1;height:6px;background:var(--ntrk);border-radius:3px;position:relative;cursor:pointer}
.nebula-slider-fill{height:100%;background:var(--nacc);border-radius:3px;transition:width .05s linear}
.nebula-slider-thumb{position:absolute;top:50%;width:18px;height:18px;background:var(--nthb);border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 2px 8px rgba(0,0,0,.4);transition:transform .05s linear,box-shadow .1s ease}
.nebula-slider-thumb.dragging{box-shadow:0 4px 16px rgba(0,212,170,.4)}
.nebula-slider-bounds{display:flex;justify-content:space-between;font-size:11px;color:var(--ntxtm);padding-top:4px;padding-left:80px}
.nebula-table{background:var(--nexbg);border:1px solid var(--nbd);border-radius:8px;overflow:hidden}
.nebula-table-header{display:grid;grid-template-columns:40px 1fr 1fr;padding:8px 10px;border-bottom:1px solid var(--nbd);font-size:12px;font-weight:500;color:var(--ntxtm)}
.nebula-table-row{display:grid;grid-template-columns:40px 1fr 1fr;align-items:center;padding:6px 10px;border-bottom:1px solid var(--nbd);transition:background .1s ease}
.nebula-table-row:last-child{border-bottom:none}.nebula-table-row:hover{background:var(--npanh)}
.nebula-table-cell input{width:100%;background:transparent!important;border:none!important;color:var(--ntxt)!important;font-size:13px!important;font-family:'IBM Plex Sans',monospace!important;padding:4px 0!important;outline:none!important}
.nebula-keypad{padding:12px;border-top:1px solid var(--nbd);flex-shrink:0}
.nebula-keypad-tabs{display:flex;gap:4px;margin-bottom:10px;border-bottom:1px solid var(--nbd);padding-bottom:8px}
.nebula-keypad-tab{padding:6px 12px;border-radius:6px;font-size:12px;font-weight:500;color:var(--ntxtm);background:transparent;border:none;cursor:pointer;transition:all .1s ease}
.nebula-keypad-tab.active{background:var(--naccd);color:var(--nacc)}
.nebula-keypad-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.nebula-key{aspect-ratio:1;border-radius:8px;background:var(--npan);border:1px solid var(--nbd);color:var(--ntxt);font-size:16px;font-weight:500;cursor:pointer;transition:all .1s ease;display:flex;align-items:center;justify-content:center}
.nebula-key:hover{background:var(--npanh);border-color:#3d4450}.nebula-key:active{transform:scale(.95)}.nebula-key.wide{grid-column:span 2}.nebula-key.accent{background:var(--nacc);border-color:var(--nacc);color:var(--nbg)}.nebula-key.accent:hover{background:#00e8bb;border-color:#00e8bb}
.nebula-canvas-toolbar{position:absolute;top:12px;right:12px;z-index:100;display:flex;flex-direction:column;gap:6px}
.nebula-toolbar-btn{width:40px;height:40px;border-radius:10px;background:var(--npan);border:1px solid var(--nbd);color:var(--ntxt);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .1s ease;font-size:18px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
.nebula-toolbar-btn:hover{background:var(--npanh);border-color:#3d4450;transform:scale(1.05)}.nebula-toolbar-btn.active{background:var(--naccd);border-color:var(--nacc);color:var(--nacc)}
.nebula-coords-display{position:absolute;bottom:12px;left:12px;z-index:100;background:var(--npan);border:1px solid var(--nbd);border-radius:8px;padding:8px 12px;font-size:12px;font-family:monospace;color:var(--ntxtm);display:flex;align-items:center;gap:16px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
.nebula-coords-display span{font-variant-numeric:tabular-nums}
.nebula-wrench-menu{position:absolute;top:12px;left:12px;z-index:200;background:var(--npan);border:1px solid var(--nbd);border-radius:10px;padding:8px;min-width:200px;box-shadow:0 8px 32px rgba(0,0,0,.4);animation:fadeIn .15s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
.nebula-wrench-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:6px;font-size:13px;color:var(--ntxt);cursor:pointer;transition:background .1s ease}
.nebula-wrench-item:hover{background:var(--npanh)}.nebula-wrench-item.danger{color:var(--ndng)}.nebula-wrench-divider{height:1px;background:var(--nbd);margin:4px 0}
.nebula-settings-panel{position:absolute;top:12px;right:12px;z-index:200;background:var(--npan);border:1px solid var(--nbd);border-radius:10px;padding:16px;width:280px;box-shadow:0 8px 32px rgba(0,0,0,.4);max-height:80vh;overflow-y:auto}
.nebula-settings-section{margin-bottom:20px}.nebula-settings-title{font-size:12px;font-weight:600;color:var(--ntxtm);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
.nebula-setting-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0}.nebula-setting-label{font-size:13px;color:var(--ntxt)}
.nebula-toggle{width:44px;height:24px;background:var(--ntrk);border-radius:12px;position:relative;cursor:pointer;transition:background .1s ease}
.nebula-toggle.on{background:var(--nacc)}.nebula-toggle-knob{width:20px;height:20px;background:white;border-radius:50%;position:absolute;top:2px;left:2px;transition:left .15s ease;box-shadow:0 2px 6px rgba(0,0,0,.3)}.nebula-toggle.on .nebula-toggle-knob{left:22px}
.nebula-resize-handle{position:absolute;left:0;top:0;bottom:0;width:8px;cursor:col-resize;background:linear-gradient(90deg,transparent,var(--nbd));opacity:0;transition:opacity .15s ease;z-index:50}
.nebula-resize-handle:hover,.nebula-sidebar:hover .nebula-resize-handle{opacity:1}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--nbd);border-radius:4px;border:2px solid var(--npan)}::-webkit-scrollbar-thumb:hover{background:#3d4450}
::selection{background:var(--naccd)}::-moz-selection{background:var(--naccd)}
@media(max-width:1024px){.nebula-app{grid-template-columns:1fr;grid-template-rows:auto 1fr}.nebula-sidebar{border-right:none;border-bottom:1px solid var(--nbd);max-height:50vh}.nebula-resize-handle{left:0;right:0;top:auto;bottom:0;height:8px;width:100%;cursor:row-resize;background:linear-gradient(180deg,transparent,var(--nbd))}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─── Data Models ───
class ExprType(Enum):
    FUNCTION = "function"
    PARAMETRIC = "parametric"
    POLAR = "polar"
    IMPLICIT = "implicit"
    POINT = "point"
    TABLE = "table"
    REGRESSION = "regression"
    LIST = "list"

@dataclass
class Color:
    r: int; g: int; b: int; a: float = 1.0
    def css(self) -> str: return f"rgba({self.r},{self.g},{self.b},{self.a})"

DEFAULT_COLORS = [
    Color(0, 212, 170), Color(255, 71, 87), Color(255, 165, 2), Color(0, 153, 255),
    Color(189, 95, 255), Color(0, 200, 120), Color(255, 100, 200), Color(100, 220, 255),
]

@dataclass
class Slider:
    id: str
    name: str
    value: float = 1.0
    min_val: float = -10.0
    max_val: float = 10.0
    step: float = 0.1
    playing: bool = False
    speed: float = 1.0
    direction: int = 1

@dataclass
class TableColumn:
    name: str
    values: List[float] = field(default_factory=list)
    color: Optional[Color] = None

@dataclass
class Expression:
    id: str
    type: ExprType
    raw: str = ""
    latex: str = ""
    color: Color = field(default_factory=lambda: DEFAULT_COLORS[0])
    visible: bool = True
    line_width: float = 2.5
    line_style: str = "solid"
    point_size: float = 6
    label: str = ""
    show_label: bool = False
    param_min: float = 0
    param_max: float = 2*math.pi
    param_step: float = 0.01
    columns: List[TableColumn] = field(default_factory=list)
    regression_type: str = "linear"
    regression_x_col: str = "x"
    regression_y_col: str = "y"
    list_values: List[float] = field(default_factory=list)
    slider_ids: List[str] = field(default_factory=list)

@dataclass
class Viewport:
    x_min: float = -10; x_max: float = 10; y_min: float = -10; y_max: float = 10
    show_grid: bool = True; show_axes: bool = True; show_numbers: bool = True
    grid_type: str = "cartesian"; axis_step_x: float = 1; axis_step_y: float = 1
    label_step_x: float = 1; label_step_y: float = 1
    background_color: str = "#0d1117"; grid_color: str = "#2d333b"
    axis_color: str = "#4a535d"; label_color: str = "#7d8b99"
    projector_mode: bool = False; degree_mode: bool = False; contrast_mode: bool = False

@dataclass
class AppState:
    expressions: List[Expression] = field(default_factory=list)
    sliders: Dict[str, Slider] = field(default_factory=dict)
    viewport: Viewport = field(default_factory=Viewport)
    selected_expr_id: Optional[str] = None
    keypad_tab: str = "functions"
    sidebar_width: int = 380
    settings_open: bool = False
    wrench_open: bool = False

# ─── Init State ───
def init_state():
    if "nebula_state" not in st.session_state:
        state = AppState()
        welcome = Expression(
            id=str(uuid.uuid4()), type=ExprType.FUNCTION, raw="f(x) = x^2",
            latex="f(x) = x^2", color=DEFAULT_COLORS[0]
        )
        state.expressions.append(welcome)
        state.selected_expr_id = welcome.id
        slider = Slider(id=str(uuid.uuid4()), name="a", value=1, min_val=-5, max_val=5, step=0.1)
        state.sliders[slider.id] = slider
        welcome.slider_ids.append(slider.id)
        st.session_state.nebula_state = state
    return st.session_state.nebula_state

state = init_state()

# ─── Expression Parser ───
class ExpressionParser:
    @staticmethod
    def parse(raw: str) -> Dict[str, Any]:
        raw = raw.strip()
        if not raw: return {"type": ExprType.FUNCTION, "valid": False}
        
        m = re.match(r'^(\w+)_(\d+)\s*[,;~]\s*(\w+)_(\d+)$', raw)
        if m: return {"type": ExprType.TABLE, "valid": True, "cols": [m.group(1), m.group(3)]}
        
        m = re.match(r'^(linear|quadratic|cubic|quartic|exponential|logarithmic|power|logistic|sinusoidal)\s*\((.+)\)$', raw, re.I)
        if m: return {"type": ExprType.REGRESSION, "latex": raw, "valid": True, "reg_type": m.group(1).lower(), "table_ref": m.group(2)}
        
        if raw.startswith('(') and '),' in raw:
            return {"type": ExprType.PARAMETRIC, "latex": raw, "valid": True}
        
        if raw.startswith('r=') or raw.startswith('r ='):
            return {"type": ExprType.POLAR, "latex": raw, "valid": True}
        
        m = re.match(r'^\((.+),(.+)\)$', raw)
        if m: return {"type": ExprType.POINT, "latex": raw, "valid": True}
        
        if raw.startswith('[') and raw.endswith(']'):
            return {"type": ExprType.LIST, "latex": raw, "valid": True}
        
        if '=' in raw and not re.match(r'^[fg]\([a-z]\)\s*=', raw):
            parts = raw.split('=', 1)
            lhs = parts[0].strip()
            if re.match(r'^[fg]\([a-z]\)$', lhs):
                return {"type": ExprType.FUNCTION, "latex": raw, "valid": True}
            else:
                return {"type": ExprType.IMPLICIT, "latex": raw, "valid": True}
        
        return {"type": ExprType.FUNCTION, "latex": raw, "valid": True}

# ─── Sidebar Rendering ───
def render_sidebar():
    st.markdown('<div class="nebula-sidebar">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="nebula-header">
        <div class="nebula-logo">
            <div class="nebula-logo-icon">🌌</div>
            <span class="nebula-title">Nebula</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Expression List
    st.markdown('<div class="nebula-expressions">', unsafe_allow_html=True)
    
    for expr in state.expressions:
        render_expression_row(expr)
    
    if st.button("➕ Add Expression", key="add_expr_main", use_container_width=True, type="secondary"):
        add_new_expression()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Keypad
    render_keypad()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_expression_row(expr: Expression):
    color_css = expr.color.css()
    
    col1, col2, col3 = st.columns([0.08, 0.72, 0.2])
    with col1:
        st.markdown(f'<div class="nebula-color-indicator" style="background:{color_css}"></div>', unsafe_allow_html=True)
    with col2:
        new_raw = st.text_input("Expression", value=expr.raw, key=f"expr_{expr.id}", label_visibility="collapsed", placeholder="Type an expression...")
        if new_raw != expr.raw:
            update_expression(expr.id, new_raw)
    with col3:
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("👁", key=f"vis_{expr.id}", help="Toggle visibility"):
                expr.visible = not expr.visible; st.rerun()
        with a2:
            if st.button("⋮", key=f"menu_{expr.id}", help="More options"):
                st.session_state[f"wrench_{expr.id}"] = True
        with a3:
            if st.button("🗑", key=f"del_{expr.id}", help="Delete"):
                state.expressions.remove(expr); st.rerun()
    
    # Details
    if expr.slider_ids or expr.type in (ExprType.TABLE, ExprType.REGRESSION):
        st.markdown('<div class="nebula-expression-details">', unsafe_allow_html=True)
        
        for sid in expr.slider_ids:
            slider = state.sliders.get(sid)
            if slider: render_slider(slider, expr)
        
        if expr.type == ExprType.TABLE: render_table_editor(expr)
        if expr.type == ExprType.REGRESSION:
            st.markdown(f'<div style="padding:8px;color:var(--ntxtm);font-size:12px">Regression: {expr.regression_type} on {expr.regression_x_col}, {expr.regression_y_col}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_slider(slider: Slider, expr: Expression):
    pct = (slider.value - slider.min_val) / (slider.max_val - slider.min_val) * 100
    
    st.markdown(f"""
    <div class="nebula-slider">
        <span class="nebula-slider-label">{slider.name}</span>
        <input type="number" class="nebula-slider-input" value="{slider.value:.3g}" 
               onchange="window.nebulaUpdateSlider('{slider.id}', parseFloat(this.value))"
               onkeydown="if(event.key==='Enter'){{window.nebulaUpdateSlider('{slider.id}', parseFloat(this.value));this.blur()}}"
               style="width:70px">
        <div class="nebula-slider-track" onclick="window.nebulaSliderClick('{slider.id}', event)">
            <div class="nebula-slider-fill" style="width:{pct}%"></div>
            <div class="nebula-slider-thumb" style="left:{pct}%"></div>
        </div>
    </div>
    <div class="nebula-slider-bounds"><span>{slider.min_val:g}</span><span>{slider.max_val:g}</span><span>{slider.step:g}</span></div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("▶" if not slider.playing else "⏸", key=f"play_{slider.id}", help="Animate"): slider.playing = not slider.playing; st.rerun()
    with c2:
        if st.button("⟲", key=f"rev_{slider.id}", help="Reverse"): slider.direction *= -1; st.rerun()
    with c3:
        new_speed = st.number_input("Speed", value=slider.speed, step=0.1, min_value=0.1, max_value=5.0, key=f"speed_{slider.id}", label_visibility="collapsed"); slider.speed = new_speed
    with c4:
        if st.button("⚙", key=f"slider_set_{slider.id}", help="Settings"): pass

def render_table_editor(expr: Expression):
    st.markdown('<div class="nebula-table">', unsafe_allow_html=True)
    
    col_names = [c.name for c in expr.columns]
    header = '<div class="nebula-table-header"><span>#</span>' + ''.join(f'<span>{n}</span>' for n in col_names) + '</div>'
    st.markdown(header, unsafe_allow_html=True)
    
    max_rows = max((len(c.values) for c in expr.columns), default=0)
    for i in range(max_rows):
        row = f'<div class="nebula-table-row"><span style="color:var(--ntxtm);font-size:11px">{i+1}</span>'
        for col in expr.columns:
            val = col.values[i] if i < len(col.values) else ""
            row += f'<div class="nebula-table-cell"><input type="text" value="{val}" onchange="window.nebulaUpdateTableCell(\'{expr.id}\', \'{col.name}\', {i}, parseFloat(this.value)||0)"></div>'
        row += '</div>'
        st.markdown(row, unsafe_allow_html=True)
    
    if st.button("+ Add Row", key=f"add_row_{expr.id}", use_container_width=True):
        for col in expr.columns: col.values.append(0); st.rerun()
    if st.button("+ Add Column", key=f"add_col_{expr.id}", use_container_width=True):
        new_name = f"col{len(expr.columns)+1}"
        expr.columns.append(TableColumn(name=new_name, values=[], color=DEFAULT_COLORS[len(expr.columns) % len(DEFAULT_COLORS)]))
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_keypad():
    st.markdown("""
    <div class="nebula-keypad">
        <div class="nebula-keypad-tabs">
            <button class="nebula-keypad-tab active" onclick="switchKeypad('functions')">Functions</button>
            <button class="nebula-keypad-tab" onclick="switchKeypad('symbols')">Symbols</button>
            <button class="nebula-keypad-tab" onclick="switchKeypad('greek')">Greek</button>
            <button class="nebula-keypad-tab" onclick="switchKeypad('stats')">Stats</button>
        </div>
        <div class="nebula-keypad-grid" id="keypad-functions">""", unsafe_allow_html=True)
    for i, f in enumerate(["sin","cos","tan","csc","sec","cot","arcsin","arccos","arctan","sinh","cosh","tanh","sqrt","cbrt","exp","ln","log","abs","floor","ceil","round","min","max","mean","median","sum","prod","factorial","nCr","nPr","gcd","lcm","mod","deg","rad"]):
        if st.button(f, key=f"key_fn_{i}", use_container_width=True): insert_at_cursor(f + "()")
    st.markdown("""</div><div class="nebula-keypad-grid" id="keypad-symbols" style="display:none">""", unsafe_allow_html=True)
    symbols = ["^","√","π","e","τ","φ","≤","≥","≠","±","·","÷","∞","!","|","||"]
    for i, s in enumerate(symbols):
        if st.button(s, key=f"key_sym_{i}", use_container_width=True): insert_at_cursor(s)
    st.markdown("""</div><div class="nebula-keypad-grid" id="keypad-greek" style="display:none">""", unsafe_allow_html=True)
    greek = ["α","β","γ","δ","ε","ζ","η","θ","ι","κ","λ","μ","ν","ξ","ο","π","ρ","σ","τ","υ","φ","χ","ψ","ω","Γ","Δ","Θ","Λ","Ξ","Π","Σ","Φ","Ψ","Ω"]
    for i, g in enumerate(greek):
        if st.button(g, key=f"key_grk_{i}", use_container_width=True): insert_at_cursor(g)
    st.markdown("""</div><div class="nebula-keypad-grid" id="keypad-stats" style="display:none">""", unsafe_allow_html=True)
    for i, s in enumerate(["mean","median","stdev","stdevp","var","varp","sum","prod","min","max","mad","quantile","cov","corr"]):
        if st.button(s, key=f"key_stt_{i}", use_container_width=True): insert_at_cursor(s + "()")
    st.markdown("""</div></div>""", unsafe_allow_html=True)

# ─── Canvas Area ───
def render_canvas_area():
    exprs_json = json.dumps(ser_expr())
    sliders_json = json.dumps(ser_sliders())
    viewport_json = json.dumps(ser_viewport())
    canvas_html = (
        """<!DOCTYPE html>
<html>
<head>
"""
        + CSS
        + """<style>
html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#0d1117; }
.nebula-canvas-area { width:100%; height:100vh; position:relative; overflow:hidden; }
</style>
</head>
<body>
<div class="nebula-canvas-area">
    <div class="nebula-canvas-toolbar">
        <button class="nebula-toolbar-btn" title="Zoom In" onclick="nebulaZoom(1/1.15)">🔍+</button>
        <button class="nebula-toolbar-btn" title="Zoom Out" onclick="nebulaZoom(1.15)">🔍-</button>
        <button class="nebula-toolbar-btn" title="Home" onclick="nebulaHome()">⌂</button>
        <button class="nebula-toolbar-btn" title="Settings" onclick="nebulaToggleSettings()">⚙</button>
        <button class="nebula-toolbar-btn" title="Wrench Menu" onclick="nebulaToggleWrench()">≡</button>
    </div>
    <div class="nebula-coords-display" id="coords-display"><span>x: 0.000</span><span>y: 0.000</span></div>
    <canvas id="nebula-canvas" style="width:100%;height:100%;display:block;touch-action:none"></canvas>
</div>
<script>
window.nebulaInitialState = {
    expressions: """
        + exprs_json
        + """,
    sliders: """
        + sliders_json
        + """,
    viewport: """
        + viewport_json
        + """
};
</script>
"""
        + RENDERER_JS
        + "</body></html>"
    )
    components.html(canvas_html, height=750, scrolling=False)

def render_settings_panel():
    v = state.viewport
    st.markdown(f"""
    <div class="nebula-settings-panel" id="settings-panel" style="display:{'block' if state.settings_open else 'none'}">
        <div class="nebula-settings-section"><div class="nebula-settings-title">Grid</div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Show Grid</span><label class="nebula-toggle {'on' if v.show_grid else ''}" onclick="nebulaToggleSetting('show_grid')"><span class="nebula-toggle-knob"></span></label></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Show Axes</span><label class="nebula-toggle {'on' if v.show_axes else ''}" onclick="nebulaToggleSetting('show_axes')"><span class="nebula-toggle-knob"></span></label></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Show Numbers</span><label class="nebula-toggle {'on' if v.show_numbers else ''}" onclick="nebulaToggleSetting('show_numbers')"><span class="nebula-toggle-knob"></span></label></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Grid Type</span><select class="nebula-select" onchange="nebulaSetSetting('grid_type', this.value)" style="width:140px;padding:6px 10px;background:var(--ninp);border:1px solid var(--nbrd);border-radius:6px;color:var(--ntxt);font-size:13px"><option value="cartesian" {'selected' if v.grid_type=='cartesian' else ''}>Cartesian</option><option value="polar" {'selected' if v.grid_type=='polar' else ''}>Polar</option></select></div>
        </div>
        <div class="nebula-settings-section"><div class="nebula-settings-title">Axis Steps</div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">X Grid Step</span><input type="number" value="{v.axis_step_x:g}" onchange="nebulaSetSetting('axis_step_x', parseFloat(this.value))" style="width:80px;padding:6px 10px;background:var(--ninp);border:1px solid var(--nbrd);border-radius:6px;color:var(--ntxt);font-size:13px"></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Y Grid Step</span><input type="number" value="{v.axis_step_y:g}" onchange="nebulaSetSetting('axis_step_y', parseFloat(this.value))" style="width:80px;padding:6px 10px;background:var(--ninp);border:1px solid var(--nbrd);border-radius:6px;color:var(--ntxt);font-size:13px"></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">X Label Step</span><input type="number" value="{v.label_step_x:g}" onchange="nebulaSetSetting('label_step_x', parseFloat(this.value))" style="width:80px;padding:6px 10px;background:var(--ninp);border:1px solid var(--nbrd);border-radius:6px;color:var(--ntxt);font-size:13px"></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Y Label Step</span><input type="number" value="{v.label_step_y:g}" onchange="nebulaSetSetting('label_step_y', parseFloat(this.value))" style="width:80px;padding:6px 10px;background:var(--ninp);border:1px solid var(--nbrd);border-radius:6px;color:var(--ntxt);font-size:13px"></div>
        </div>
        <div class="nebula-settings-section"><div class="nebula-settings-title">Display</div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Projector Mode</span><label class="nebula-toggle {'on' if v.projector_mode else ''}" onclick="nebulaToggleSetting('projector_mode')"><span class="nebula-toggle-knob"></span></label></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Degree Mode</span><label class="nebula-toggle {'on' if v.degree_mode else ''}" onclick="nebulaToggleSetting('degree_mode')"><span class="nebula-toggle-knob"></span></label></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">High Contrast</span><label class="nebula-toggle {'on' if v.contrast_mode else ''}" onclick="nebulaToggleSetting('contrast_mode')"><span class="nebula-toggle-knob"></span></label></div>
        </div>
        <div class="nebula-settings-section"><div class="nebula-settings-title">Colors</div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Background</span><input type="color" value="{v.background_color}" onchange="nebulaSetSetting('background_color', this.value)" style="width:40px;height:28px;border:none;border-radius:6px;cursor:pointer"></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Grid</span><input type="color" value="{v.grid_color}" onchange="nebulaSetSetting('grid_color', this.value)" style="width:40px;height:28px;border:none;border-radius:6px;cursor:pointer"></div>
            <div class="nebula-setting-row"><span class="nebula-setting-label">Axes</span><input type="color" value="{v.axis_color}" onchange="nebulaSetSetting('axis_color', this.value)" style="width:40px;height:28px;border:none;border-radius:6px;cursor:pointer"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_wrench_menu():
    st.markdown("""
    <div class="nebula-wrench-menu" id="wrench-menu" style="display:none">
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('share')"><span>🔗</span> Share Graph</div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('export_image')"><span>📥</span> Export Image</div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('export_latex')"><span>📄</span> Export LaTeX</div>
        <div class="nebula-wrench-divider"></div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('create_table')"><span>📊</span> Create Table</div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('create_slider')"><span>🎚</span> Create Slider</div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('create_folder')"><span>📁</span> Create Folder</div>
        <div class="nebula-wrench-divider"></div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('radians')"><span>📐</span> Radians</div>
        <div class="nebula-wrench-item" onclick="nebulaWrenchAction('degrees')"><span>📐</span> Degrees</div>
        <div class="nebula-wrench-divider"></div>
        <div class="nebula-wrench-item danger" onclick="nebulaWrenchAction('clear_all')"><span>🗑</span> Clear All</div>
    </div>
    """, unsafe_allow_html=True)

# ─── State Functions ───
def add_new_expression():
    ne = Expression(id=str(uuid.uuid4()), type=ExprType.FUNCTION, raw="", latex="", color=DEFAULT_COLORS[len(state.expressions) % len(DEFAULT_COLORS)])
    state.expressions.append(ne)
    state.selected_expr_id = ne.id

def update_expression(expr_id: str, new_raw: str):
    for e in state.expressions:
        if e.id == expr_id:
            e.raw = new_raw
            p = ExpressionParser.parse(new_raw)
            e.type = p.get("type", ExprType.FUNCTION)
            e.latex = p.get("latex", new_raw)
            if e.type == ExprType.TABLE and "cols" in p:
                e.columns = [TableColumn(name=c, values=[], color=DEFAULT_COLORS[i % len(DEFAULT_COLORS)]) for i, c in enumerate(p["cols"])]
            break

def insert_at_cursor(text: str):
    if state.selected_expr_id:
        for e in state.expressions:
            if e.id == state.selected_expr_id:
                e.raw += text; update_expression(e.id, e.raw); break
    elif state.expressions:
        e = state.expressions[-1]; e.raw += text; update_expression(e.id, e.raw)

# ─── Serialization ───
def ser_expr() -> List[Dict]:
    return [{"id":e.id,"type":e.type.value,"raw":e.raw,"latex":e.latex,"color":e.color.css(),"visible":e.visible,"line_width":e.line_width,"line_style":e.line_style,"point_size":e.point_size,"label":e.label,"show_label":e.show_label,"param_min":e.param_min,"param_max":e.param_max,"param_step":e.param_step,"columns":[{"name":c.name,"values":c.values,"color":c.color.css() if c.color else None} for c in e.columns],"regression_type":e.regression_type,"regression_x_col":e.regression_x_col,"regression_y_col":e.regression_y_col,"list_values":e.list_values,"slider_ids":e.slider_ids} for e in state.expressions]

def ser_sliders() -> Dict:
    return {sid:{"id":s.id,"name":s.name,"value":s.value,"min_val":s.min_val,"max_val":s.max_val,"step":s.step,"playing":s.playing,"speed":s.speed,"direction":s.direction} for sid,s in state.sliders.items()}

def ser_viewport() -> Dict:
    v = state.viewport
    return {"x_min":v.x_min,"x_max":v.x_max,"y_min":v.y_min,"y_max":v.y_max,"show_grid":v.show_grid,"show_axes":v.show_axes,"show_numbers":v.show_numbers,"grid_type":v.grid_type,"axis_step_x":v.axis_step_x,"axis_step_y":v.axis_step_y,"label_step_x":v.label_step_x,"label_step_y":v.label_step_y,"background_color":v.background_color,"grid_color":v.grid_color,"axis_color":v.axis_color,"label_color":v.label_color,"projector_mode":v.projector_mode,"degree_mode":v.degree_mode,"contrast_mode":v.contrast_mode}

# ─── Main Render ───
def main():
    col1, col2 = st.columns([1, 2.2])
    with col1:
        render_sidebar()
    with col2:
        render_canvas_area()

# ─── JavaScript Renderer (as a constant string) ───
RENDERER_JS = r"""
<script>
// ─── Nebula Graphing Calculator Renderer ───
class NebulaRenderer {
    constructor(canvas, initialState) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.state = initialState || {expressions:[], sliders:{}, viewport:{x_min:-10,x_max:10,y_min:-10,y_max:10,show_grid:true,show_axes:true,show_numbers:true,grid_type:'cartesian',axis_step_x:1,axis_step_y:1,label_step_x:1,label_step_y:1,background_color:'#0d1117',grid_color:'#2d333b',axis_color:'#4a535d',label_color:'#7d8b99',projector_mode:false,degree_mode:false,contrast_mode:false}};
        this.dpr = window.devicePixelRatio || 1;
        this.width = 0; this.height = 0;
        this.xScale = 1; this.yScale = 1; this.xOffset = 0; this.yOffset = 0;
        this.animationFrame = null;
        this.hoveredPoint = null;
        this.draggedPoint = null;
        this.sliderDrag = null;
        this.lastTime = 0;
        this.bindEvents();
        this.resize();
        this.startAnimation();
    }
    
    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.width = rect.width; this.height = rect.height;
        this.canvas.width = this.width * this.dpr;
        this.canvas.height = this.height * this.dpr;
        this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
        this.updateProjection();
        this.render();
    }
    
    updateProjection() {
        const v = this.state.viewport;
        this.xScale = this.width / (v.x_max - v.x_min);
        this.yScale = this.height / (v.y_max - v.y_min);
        this.xOffset = -v.x_min * this.xScale;
        this.yOffset = this.height + v.y_min * this.yScale;
    }
    
    mathToScreen(x, y) {
        return { x: x * this.xScale + this.xOffset, y: this.yOffset - y * this.yScale };
    }
    screenToMath(sx, sy) {
        return { x: (sx - this.xOffset) / this.xScale, y: (this.yOffset - sy) / this.yScale };
    }
    
    bindEvents() {
        this.canvas.addEventListener('mousedown', e => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', e => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', e => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', e => this.onWheel(e), { passive: false });
        this.canvas.addEventListener('dblclick', e => this.onDoubleClick(e));
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
        this.canvas.addEventListener('touchstart', e => this.onTouchStart(e), { passive: true });
        this.canvas.addEventListener('touchmove', e => this.onTouchMove(e), { passive: false });
        this.canvas.addEventListener('touchend', e => this.onTouchEnd(e));
        
        // Resize handle
        const handle = document.getElementById('resize-handle');
        let resizing = false;
        handle?.addEventListener('mousedown', e => { resizing = true; e.preventDefault(); });
        document.addEventListener('mousemove', e => {
            if (!resizing) return;
            const sidebar = document.querySelector('.nebula-sidebar');
            const app = document.querySelector('.nebula-app');
            const newWidth = Math.max(280, Math.min(600, e.clientX));
            sidebar.style.width = newWidth + 'px';
            sidebar.style.flexBasis = newWidth + 'px';
            app.style.gridTemplateColumns = newWidth + 'px 1fr';
            this.resize();
        });
        document.addEventListener('mouseup', () => resizing = false);
    }
    
    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
        this.state.last_mouse = [sx, sy];
        
        if (this.checkPointHit(sx, sy)) return;
        if (this.checkSliderHit(sx, sy)) return;
        
        this.state.viewport.is_panning = true;
        this.state.viewport.pan_start = [sx, sy];
        this.state.viewport.viewport_start = [this.state.viewport.x_min, this.state.viewport.x_max, this.state.viewport.y_min, this.state.viewport.y_max];
        this.canvas.style.cursor = 'grabbing';
    }
    
    onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
        this.state.last_mouse = [sx, sy];
        
        if (this.draggedPoint) {
            const m = this.screenToMath(sx, sy);
            this.draggedPoint.x = m.x; this.draggedPoint.y = m.y;
            this.requestRender(); this.sendPointUpdate();
            return;
        }
        if (this.sliderDrag) {
            this.updateSliderFromMouse(this.sliderDrag, sx);
            this.requestRender();
            return;
        }
        
        if (this.state.viewport.is_panning) {
            const v = this.state.viewport;
            const dx = (sx - v.pan_start[0]) / this.xScale;
            const dy = (sy - v.pan_start[1]) / this.yScale;
            v.x_min = v.viewport_start[0] - dx;
            v.x_max = v.viewport_start[1] - dx;
            v.y_min = v.viewport_start[2] + dy;
            v.y_max = v.viewport_start[3] + dy;
            this.updateProjection(); this.requestRender(); this.sendViewportUpdate();
            return;
        }
        
        this.hoveredPoint = this.findHoveredPoint(sx, sy);
        this.canvas.style.cursor = this.hoveredPoint ? 'pointer' : 'grab';
    }
    
    onMouseUp(e) {
        this.state.viewport.is_panning = false;
        this.draggedPoint = null; this.sliderDrag = null;
        this.canvas.style.cursor = 'grab';
    }
    
    onWheel(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
        const m = this.screenToMath(sx, sy);
        const zoomFactor = e.deltaY > 0 ? 1.15 : 1/1.15;
        const v = this.state.viewport;
        v.x_min = m.x - (m.x - v.x_min) * zoomFactor;
        v.x_max = m.x + (v.x_max - m.x) * zoomFactor;
        v.y_min = m.y - (m.y - v.y_min) * zoomFactor;
        v.y_max = m.y + (v.y_max - m.y) * zoomFactor;
        this.updateProjection(); this.requestRender(); this.sendViewportUpdate();
    }
    
    onDoubleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
        const m = this.screenToMath(sx, sy);
        const v = this.state.viewport;
        const snapX = Math.round(m.x / v.axis_step_x) * v.axis_step_x;
        const snapY = Math.round(m.y / v.axis_step_y) * v.axis_step_y;
        const w = v.x_max - v.x_min, h = v.y_max - v.y_min;
        v.x_min = snapX - w/2; v.x_max = snapX + w/2;
        v.y_min = snapY - h/2; v.y_max = snapY + h/2;
        this.updateProjection(); this.requestRender(); this.sendViewportUpdate();
    }
    
    pinchStart = null;
    onTouchStart(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const rect = this.canvas.getBoundingClientRect();
            const sx = touch.clientX - rect.left, sy = touch.clientY - rect.top;
            if (this.checkPointHit(sx, sy)) return;
            if (this.checkSliderHit(sx, sy)) return;
            this.state.viewport.is_panning = true;
            this.state.viewport.pan_start = [sx, sy];
            this.state.viewport.viewport_start = [this.state.viewport.x_min, this.state.viewport.x_max, this.state.viewport.y_min, this.state.viewport.y_max];
        } else if (e.touches.length === 2) {
            this.pinchStart = { dist: this.getPinchDist(e), center: this.getPinchCenter(e), viewport: {...this.state.viewport} };
        }
    }
    onTouchMove(e) {
        e.preventDefault();
        if (e.touches.length === 1 && this.state.viewport.is_panning) {
            const touch = e.touches[0];
            const rect = this.canvas.getBoundingClientRect();
            const sx = touch.clientX - rect.left, sy = touch.clientY - rect.top;
            const v = this.state.viewport;
            const dx = (sx - v.pan_start[0]) / this.xScale;
            const dy = (sy - v.pan_start[1]) / this.yScale;
            v.x_min = v.viewport_start[0] - dx; v.x_max = v.viewport_start[1] - dx;
            v.y_min = v.viewport_start[2] + dy; v.y_max = v.viewport_start[3] + dy;
            this.updateProjection(); this.requestRender(); this.sendViewportUpdate();
        } else if (e.touches.length === 2 && this.pinchStart) {
            const scale = this.getPinchDist(e) / this.pinchStart.dist;
            const center = this.getPinchCenter(e);
            const m = this.screenToMath(center.x, center.y);
            const v = this.state.viewport;
            const pw = this.pinchStart.viewport.x_max - this.pinchStart.viewport.x_min;
            const ph = this.pinchStart.viewport.y_max - this.pinchStart.viewport.y_min;
            v.x_min = m.x - (m.x - this.pinchStart.viewport.x_min) / scale;
            v.x_max = m.x + (this.pinchStart.viewport.x_max - m.x) / scale;
            v.y_min = m.y - (m.y - this.pinchStart.viewport.y_min) / scale;
            v.y_max = m.y + (this.pinchStart.viewport.y_max - m.y) / scale;
            this.updateProjection(); this.requestRender(); this.sendViewportUpdate();
        }
    }
    onTouchEnd(e) { this.state.viewport.is_panning = false; this.pinchStart = null; this.draggedPoint = null; this.sliderDrag = null; }
    getPinchDist(e) { const t1=e.touches[0], t2=e.touches[1]; return Math.hypot(t1.clientX-t2.clientX, t1.clientY-t2.clientY); }
    getPinchCenter(e) { const t1=e.touches[0], t2=e.touches[1]; const r=this.canvas.getBoundingClientRect(); return {x:(t1.clientX+t2.clientX)/2-r.left, y:(t1.clientY+t2.clientY)/2-r.top}; }
    
    checkSliderHit(sx, sy) {
        // Check if clicking on slider thumbs in sidebar
        return false;
    }
    
    checkPointHit(sx, sy) {
        for (const expr of this.state.expressions) {
            if (!expr.visible) continue;
            if (expr.type === 'point' || expr.type === 'table') {
                const points = this.getExpressionPoints(expr);
                for (const pt of points) {
                    const screen = this.mathToScreen(pt.x, pt.y);
                    const dx = sx - screen.x, dy = sy - screen.y;
                    if (dx*dx + dy*dy < 100) { this.draggedPoint = pt; return true; }
                }
            }
        }
        return false;
    }
    
    findHoveredPoint(sx, sy) {
        for (const expr of this.state.expressions) {
            if (!expr.visible) continue;
            if (expr.type === 'point' || expr.type === 'table') {
                const points = this.getExpressionPoints(expr);
                for (const pt of points) {
                    const screen = this.mathToScreen(pt.x, pt.y);
                    const dx = sx - screen.x, dy = sy - screen.y;
                    if (dx*dx + dy*dy < 100) return {...pt, exprId: expr.id, exprColor: expr.color};
                }
            }
        }
        return null;
    }
    
    getExpressionPoints(expr) {
        if (expr.type === 'point') {
            const m = expr.raw.match(/\\((.+),(.+)\\)/);
            if (m) try { return [{ x: eval(this.prepareExpr(m[1])), y: eval(this.prepareExpr(m[2])) }]; } catch { return []; }
        } else if (expr.type === 'table') {
            const pts = [], cols = expr.columns;
            if (cols.length >= 2) {
                const xCol = cols.find(c => c.name === 'x') || cols[0];
                const yCol = cols.find(c => c.name === 'y') || cols[1];
                for (let i=0; i<Math.min(xCol.values.length, yCol.values.length); i++)
                    pts.push({ x: xCol.values[i], y: yCol.values[i] });
            }
            return pts;
        }
        return [];
    }
    
    prepareExpr(e) { return e.replace(/\^/g,'**').replace(/(\d)([a-zA-Z(])/g,'$1*$2').replace(/([a-zA-Z)])(\()/g,'$1*$2'); }
    
    // ─── Rendering ───
    render() {
        const ctx = this.ctx, w = this.width, h = this.height, v = this.state.viewport;
        ctx.fillStyle = v.background_color; ctx.fillRect(0, 0, w, h);
        if (v.show_grid) this.drawGrid();
        if (v.show_axes) this.drawAxes();
        for (const expr of this.state.expressions) if (expr.visible) this.drawExpression(expr);
        if (this.hoveredPoint) this.drawPointHighlight(this.hoveredPoint);
        this.drawCoordinates();
    }
    
    drawGrid() {
        const ctx = this.ctx, v = this.state.viewport;
        const w = this.width, h = this.height;
        ctx.strokeStyle = v.grid_color; ctx.lineWidth = 1;
        const xs = Math.floor(v.x_min / v.axis_step_x) * v.axis_step_x;
        for (let x = xs; x <= v.x_max; x += v.axis_step_x) if (x !== 0) { const sx=this.mathToScreen(x,0).x; ctx.beginPath(); ctx.moveTo(sx,0); ctx.lineTo(sx,h); ctx.stroke(); }
        const ys = Math.floor(v.y_min / v.axis_step_y) * v.axis_step_y;
        for (let y = ys; y <= v.y_max; y += v.axis_step_y) if (y !== 0) { const sy=this.mathToScreen(0,y).y; ctx.beginPath(); ctx.moveTo(0,sy); ctx.lineTo(w,sy); ctx.stroke(); }
    }
    
    drawAxes() {
        const ctx = this.ctx, v = this.state.viewport;
        const w = this.width, h = this.height;
        ctx.strokeStyle = v.axis_color; ctx.lineWidth = 2;
        if (v.y_min <= 0 && v.y_max >= 0) { const sy=this.mathToScreen(0,0).y; ctx.beginPath(); ctx.moveTo(0,sy); ctx.lineTo(w,sy); ctx.stroke(); }
        if (v.x_min <= 0 && v.x_max >= 0) { const sx=this.mathToScreen(0,0).x; ctx.beginPath(); ctx.moveTo(sx,0); ctx.lineTo(sx,h); ctx.stroke(); }
        if (v.show_numbers) {
            ctx.fillStyle = v.label_color; ctx.font = '11px monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
            const xs = Math.floor(v.x_min / v.label_step_x) * v.label_step_x;
            for (let x = xs; x <= v.x_max; x += v.label_step_x) if (x !== 0) { const p=this.mathToScreen(x,0), sy=this.mathToScreen(0,0).y; ctx.beginPath(); ctx.moveTo(p.x,sy-6); ctx.lineTo(p.x,sy+6); ctx.stroke(); ctx.fillText(this.fmt(x), p.x, sy+8); }
            const ys = Math.floor(v.y_min / v.label_step_y) * v.label_step_y;
            for (let y = ys; y <= v.y_max; y += v.label_step_y) if (y !== 0) { const p=this.mathToScreen(0,y), sx=this.mathToScreen(0,0).x; ctx.beginPath(); ctx.moveTo(sx-6,p.y); ctx.lineTo(sx+6,p.y); ctx.stroke(); ctx.textAlign='right'; ctx.fillText(this.fmt(y), sx-8, p.y+4); ctx.textAlign='center'; }
            const p=this.mathToScreen(0,0); ctx.fillText('0', p.x+8, p.y+8);
        }
    }
    
    fmt(n) { if (Math.abs(n)<1e-10) return '0'; if (Math.abs(n)>=1e6 || (Math.abs(n)<1e-3 && n!==0)) return n.toExponential(2); return parseFloat(n.toPrecision(10)).toString(); }
    
    drawExpression(expr) {
        const ctx = this.ctx; ctx.strokeStyle = expr.color; ctx.fillStyle = expr.color; ctx.lineWidth = expr.line_width;
        if (expr.line_style==='dashed') ctx.setLineDash([8,6]); else if (expr.line_style==='dotted') ctx.setLineDash([2,6]); else ctx.setLineDash([]);
        switch(expr.type) {
            case 'function': this.drawFunction(expr); break;
            case 'parametric': this.drawParametric(expr); break;
            case 'polar': this.drawPolar(expr); break;
            case 'implicit': this.drawImplicit(expr); break;
            case 'point': this.drawPoint(expr); break;
            case 'table': this.drawTable(expr); break;
            case 'regression': this.drawRegression(expr); break;
            case 'list': this.drawList(expr); break;
        }
        if (expr.show_label && expr.label) this.drawLabel(expr);
    }
    
    drawFunction(expr) {
        const ctx=this.ctx, v=this.state.viewport; let fe=expr.raw, fn='f';
        const m = expr.raw.match(/^([fg]\\([a-z]\\))\\s*=\\s*(.+)$/);
        if (m) { fn = m[1].slice(0,1); fe = m[2]; }
        const js = this.prepareForJS(fe); const step = (v.x_max-v.x_min)/this.width*0.5;
        ctx.beginPath(); let first=true, lastY=null;
        for (let x=v.x_min; x<=v.x_max; x+=step) {
            try { const y = eval(js.replace(new RegExp(fn,'g'), `(${x})`)); if (!isFinite(y)) { lastY=null; continue; }
            const p=this.mathToScreen(x,y); if (first) { ctx.moveTo(p.x,p.y); first=false; }
            else { if (lastY!==null && Math.abs(y-lastY) > (v.y_max-v.y_min)*0.5) { ctx.stroke(); ctx.beginPath(); ctx.moveTo(p.x,p.y); } else ctx.lineTo(p.x,p.y); } lastY=y; } catch { lastY=null; }
        }
        ctx.stroke();
    }
    
    drawParametric(expr) {
        const ctx=this.ctx; const m=expr.raw.match(/^(.+),(.+)$/); if (!m) return;
        const xe=this.prepareForJS(m[1]), ye=this.prepareForJS(m[2]);
        const tmin=expr.param_min, tmax=expr.param_max, tstep=expr.param_step;
        ctx.beginPath(); let first=true;
        for (let t=tmin; t<=tmax; t+=tstep) { try { const x=eval(xe.replace(/t/g,`(${t})`)), y=eval(ye.replace(/t/g,`(${t})`)); if (!isFinite(x)||!isFinite(y)) {first=true;continue;} const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y);} catch {first=true;} } ctx.stroke();
    }
    
    drawPolar(expr) {
        const ctx=this.ctx; const re=expr.raw.replace(/^r\\s*=\\s*/,''); const rjs=this.prepareForJS(re);
        const tmin=expr.param_min, tmax=expr.param_max, tstep=expr.param_step;
        ctx.beginPath(); let first=true;
        for (let th=tmin; th<=tmax; th+=tstep) { try { const r=eval(rjs.replace(/theta|t/g,`(${th})`)); if (!isFinite(r)) {first=true;continue;} const x=r*Math.cos(th), y=r*Math.sin(th); const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y);} catch {first=true;} } ctx.stroke();
    }
    
    drawImplicit(expr) {
        const ctx=this.ctx, v=this.state.viewport; const parts=expr.raw.split('='); if (parts.length!==2) return;
        const lhs=this.prepareForJS(parts[0]), rhs=this.prepareForJS(parts[1]); const ejs=`(${lhs})-(${rhs})`;
        const cs=Math.max(2,Math.min(this.width,this.height)/200); const cols=Math.ceil(this.width/cs), rows=Math.ceil(this.height/cs);
        const vals=new Float32Array((cols+1)*(rows+1));
        for (let i=0;i<=cols;i++) for (let j=0;j<=rows;j++) { const m=this.screenToMath(i*cs,j*cs); try { const v=eval(ejs.replace(/x/g,`(${m.x})`).replace(/y/g,`(${m.y})`)); vals[i+j*(cols+1)]=isFinite(v)?v:NaN; } catch { vals[i+j*(cols+1)]=NaN; } }
        for (let i=0;i<cols;i++) for (let j=0;j<rows;j++) {
            const v00=vals[i+j*(cols+1)], v10=vals[i+1+j*(cols+1)], v01=vals[i+(j+1)*(cols+1)], v11=vals[i+1+(j+1)*(cols+1)];
            if (isNaN(v00)||isNaN(v10)||isNaN(v01)||isNaN(v11)) continue;
            const s=[v00,v10,v11,v01].map(v=>v>0); const sc=s.filter((x,i)=>x!==s[(i+1)%4]).length;
            if (sc===2) { const pts=[]; if(v00*v01<0){const t=v00/(v00-v01);pts.push({x:i*cs,y:(j+t)*cs});} if(v10*v11<0){const t=v10/(v10-v11);pts.push({x:(i+1)*cs,y:(j+t)*cs});} if(v00*v10<0){const t=v00/(v00-v10);pts.push({x:(i+t)*cs,y:j*cs});} if(v01*v11<0){const t=v01/(v01-v11);pts.push({x:(i+t)*cs,y:(j+1)*cs});} if(pts.length===2){ctx.moveTo(pts[0].x,pts[0].y);ctx.lineTo(pts[1].x,pts[1].y);} }
        }
        ctx.stroke();
    }
    
    drawPoint(expr) {
        const ctx=this.ctx; const m=expr.raw.match(/\\((.+),(.+)\\)/); if (!m) return;
        try { const x=eval(this.prepareExpr(m[1])), y=eval(this.prepareExpr(m[2])); if(!isFinite(x)||!isFinite(y)) return; const p=this.mathToScreen(x,y); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); ctx.fillStyle='#0d1117'; ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size*0.4,0,2*Math.PI); ctx.fill(); ctx.fillStyle=expr.color; } catch {}
    }
    
    drawTable(expr) {
        const ctx=this.ctx, cols=expr.columns; if (cols.length<2) return;
        const xCol=cols.find(c=>c.name==='x')||cols[0], yCol=cols.find(c=>c.name==='y')||cols[1];
        for (let i=0;i<Math.min(xCol.values.length,yCol.values.length);i++) { const x=xCol.values[i], y=yCol.values[i]; if(!isFinite(x)||!isFinite(y)) continue; const p=this.mathToScreen(x,y); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); ctx.fillStyle='#0d1117'; ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size*0.4,0,2*Math.PI); ctx.fill(); ctx.fillStyle=expr.color; }
    }
    
    drawRegression(expr) {
        // Find table by matching column names
        let tableExpr = null;
        for (const e of this.state.expressions) {
            if (e.type === 'table' && e.columns.some(c => c.name === expr.regression_x_col) && e.columns.some(c => c.name === expr.regression_y_col)) {
                tableExpr = e; break;
            }
        }
        if (!tableExpr) return;
        const xVals = tableExpr.columns.find(c => c.name === expr.regression_x_col)?.values || [];
        const yVals = tableExpr.columns.find(c => c.name === expr.regression_y_col)?.values || [];
        this.drawRegressionLine(expr, xVals, yVals);
    }
    
    drawRegressionLine(expr, xVals, yVals) {
        if (xVals.length < 2) return;
        const ctx=this.ctx, v=this.state.viewport; ctx.strokeStyle=expr.color; ctx.lineWidth=expr.line_width; ctx.setLineDash([6,4]);
        const coeffs = this.computeRegression(expr.regression_type, xVals, yVals);
        if (!coeffs) return;
        const step=(v.x_max-v.x_min)/this.width*0.5; ctx.beginPath(); let first=true;
        for(let x=v.x_min;x<=v.x_max;x+=step){ const y=this.evalRegression(expr.regression_type,coeffs,x); if(!isFinite(y)){first=true;continue;} const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y); } ctx.stroke(); ctx.setLineDash([]);
    }
    
    computeRegression(type, x, y) {
        const n = Math.min(x.length, y.length);
        if (n < 2) return null;
        switch (type) {
            case 'linear': return this.linearReg(x, y, n);
            case 'quadratic': return this.polyReg(x, y, n, 2);
            case 'cubic': return this.polyReg(x, y, n, 3);
            case 'quartic': return this.polyReg(x, y, n, 4);
            case 'exponential': return this.expReg(x, y, n);
            case 'logarithmic': return this.logReg(x, y, n);
            case 'power': return this.powerReg(x, y, n);
            default: return this.linearReg(x, y, n);
        }
    }
    
    linearReg(x, y, n) { let sx=0,sy=0,sxy=0,sx2=0; for(let i=0;i<n;i++){sx+=x[i];sy+=y[i];sxy+=x[i]*y[i];sx2+=x[i]*x[i];} const den=n*sx2-sx*sx; if(Math.abs(den)<1e-10)return null; return [(n*sxy-sx*sy)/den,(sy*sx2-sx*sxy)/den]; }
    polyReg(x, y, n, deg) { const A=Array(deg+1).fill().map(()=>Array(deg+1).fill(0)), b=Array(deg+1).fill(0); for(let i=0;i<n;i++){const xp=Array(deg+1).fill(1);for(let d=1;d<=deg;d++)xp[d]=xp[d-1]*x[i];for(let r=0;r<=deg;r++){for(let c=0;c<=deg;c++)A[r][c]+=xp[r]*xp[c];b[r]+=xp[r]*y[i];}}return this.gauss(A,b); }
    gauss(A, b) { const n=A.length; for(let i=0;i<n;i++){let mr=i;for(let r=i+1;r<n;r++)if(Math.abs(A[r][i])>Math.abs(A[mr][i]))mr=r;[A[i],A[mr]]=[A[mr],A[i]];[b[i],b[mr]]=[b[mr],b[i]];const piv=A[i][i];if(Math.abs(piv)<1e-12)return null;for(let c=i;c<n;c++)A[i][c]/=piv;b[i]/=piv;for(let r=0;r<n;r++)if(r!==i){const f=A[r][i];for(let c=i;c<n;c++)A[r][c]-=f*A[i][c];b[r]-=f*b[i];}}return b; }
    expReg(x, y, n) { const ly=y.map(v=>v>0?Math.log(v):NaN); if(ly.some(isNaN))return null; const l=this.linearReg(x,ly,n); if(!l)return null; return [Math.exp(l[1]),l[0]]; }
    logReg(x, y, n) { const lx=x.map(v=>v>0?Math.log(v):NaN); if(lx.some(isNaN))return null; const l=this.linearReg(lx,y,n); if(!l)return null; return [Math.exp(l[1]),l[0]]; }
    powerReg(x, y, n) { const lx=x.map(v=>v>0?Math.log(v):NaN), ly=y.map(v=>v>0?Math.log(v):NaN); if(lx.some(isNaN)||ly.some(isNaN))return null; const l=this.linearReg(lx,ly,n); if(!l)return null; return [Math.exp(l[1]),l[0]]; }
    evalRegression(type, coeffs, x) { switch(type){case'linear':return coeffs[0]*x+coeffs[1];case'quadratic':return coeffs[0]*x*x+coeffs[1]*x+coeffs[2];case'cubic':return coeffs[0]*x*x*x+coeffs[1]*x*x+coeffs[2]*x+coeffs[3];case'quartic':return coeffs[0]*x*x*x*x+coeffs[1]*x*x*x+coeffs[2]*x*x+coeffs[3]*x+coeffs[4];case'exponential':return coeffs[0]*Math.exp(coeffs[1]*x);case'logarithmic':return coeffs[0]+coeffs[1]*Math.log(x);case'power':return coeffs[0]*Math.pow(x,coeffs[1]);default:return coeffs[0]*x+coeffs[1];} }
    
    drawList(expr) { const ctx=this.ctx; for(const x of expr.list_values){ const p=this.mathToScreen(x,0); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); } }
    
    drawPointHighlight(pt) { const ctx=this.ctx, p=this.mathToScreen(pt.x,pt.y); ctx.strokeStyle=pt.exprColor||'#00d4aa'; ctx.lineWidth=3; ctx.beginPath(); ctx.arc(p.x,p.y,14,0,2*Math.PI); ctx.stroke(); ctx.fillStyle=pt.exprColor||'#00d4aa'; ctx.font='12px monospace'; ctx.textAlign='left'; ctx.fillText(`(${this.fmt(pt.x)}, ${this.fmt(pt.y)})`, p.x+18, p.y-18); }
    
    drawCoordinates() { const ctx=this.ctx, v=this.state.viewport, m=this.screenToMath(this.state.last_mouse?.[0]||0,this.state.last_mouse?.[1]||0); ctx.fillStyle='rgba(22,27,34,0.95)'; ctx.strokeStyle=v.grid_color; ctx.lineWidth=1; const text=`x: ${this.fmt(m.x)}  y: ${this.fmt(m.y)}`; ctx.font='12px monospace'; const h = this.height; const tw=ctx.measureText(text).width+24, th=28, x=12, y=h-12-th; ctx.roundRect(x,y,tw,th,8); ctx.fill(); ctx.stroke(); ctx.fillStyle=v.label_color; ctx.textBaseline='middle'; ctx.fillText(text, x+12, y+th/2); }
    
    drawLabel(expr) { if(!expr||!expr.label)return; const ctx=this.ctx; ctx.fillStyle=expr.color||'#e6edf3'; ctx.font='12px monospace'; ctx.fillText(expr.label, 20, 30); }
    requestRender() { if(this.animationFrame)return; this.animationFrame=requestAnimationFrame(()=>{this.animationFrame=null;this.render();}); }
    startAnimation() { const animate=(time)=>{this.lastTime=time/1000; for(const s of Object.values(this.state.sliders||{}))if(s&&s.playing){s.value+=(s.direction||1)*(s.speed||1)*0.016;if(s.value>=s.max_val){s.value=s.max_val;s.direction=-1;}if(s.value<=s.min_val){s.value=s.min_val;s.direction=1;}}this.render();requestAnimationFrame(animate);};requestAnimationFrame(animate); }
    sendViewportUpdate() {}
    sendPointUpdate() {}
    setState(newState) { this.state=newState; this.updateProjection(); this.requestRender(); }
    
    prepareForJS(e) { let js=e; js=js.replace(/\^/g,'**').replace(/(\d)([a-zA-Z(])/g,'$1*$2').replace(/([a-zA-Z)])(\()/g,'$1*$2'); js=js.replace(/pi/g,'Math.PI').replace(/tau/g,'2*Math.PI').replace(/e(?![a-zA-Z])/g,'Math.E').replace(/phi/g,'(1+Math.sqrt(5))/2'); const fs={'sin':'Math.sin','cos':'Math.cos','tan':'Math.tan','csc':'x=>1/Math.sin(x)','sec':'x=>1/Math.cos(x)','cot':'x=>1/Math.tan(x)','arcsin':'Math.asin','arccos':'Math.acos','arctan':'Math.atan','sinh':'Math.sinh','cosh':'Math.cosh','tanh':'Math.tanh','sqrt':'Math.sqrt','cbrt':'Math.cbrt','exp':'Math.exp','ln':'Math.log','log':'Math.log10','log10':'Math.log10','log2':'Math.log2','abs':'Math.abs','floor':'Math.floor','ceil':'Math.ceil','round':'Math.round','sign':'x=>x>0?1:x<0?-1:0','min':'Math.min','max':'Math.max'}; for(const[k,v] of Object.entries(fs))js=js.replace(new RegExp(`\b${k}\b`,'gi'),v); return js; }
}

window.nebulaZoom = function(f) { if(window.nebulaRenderer){ const v=window.nebulaRenderer.state.viewport, cx=(v.x_min+v.x_max)/2, cy=(v.y_min+v.y_max)/2, w=(v.x_max-v.x_min)*f, h=(v.y_max-v.y_min)*f; v.x_min=cx-w/2; v.x_max=cx+w/2; v.y_min=cy-h/2; v.y_max=cy+h/2; window.nebulaRenderer.updateProjection(); window.nebulaRenderer.requestRender(); } };
window.nebulaHome = function() { if(window.nebulaRenderer){ const v=window.nebulaRenderer.state.viewport; v.x_min=-10; v.x_max=10; v.y_min=-10; v.y_max=10; window.nebulaRenderer.updateProjection(); window.nebulaRenderer.requestRender(); } };
window.nebulaToggleSettings = function() { const el=document.getElementById('settings-panel'); if(el) el.style.display=el.style.display==='none'?'block':'none'; };
window.nebulaToggleWrench = function() { const el=document.getElementById('wrench-menu'); if(el) el.style.display=el.style.display==='none'?'block':'none'; };
window.nebulaToggleSetting = function(k) { if(window.nebulaRenderer){ window.nebulaRenderer.state.viewport[k]=!window.nebulaRenderer.state.viewport[k]; window.nebulaRenderer.requestRender(); } };
window.nebulaSetSetting = function(k, val) { if(window.nebulaRenderer){ window.nebulaRenderer.state.viewport[k]=val; window.nebulaRenderer.updateProjection(); window.nebulaRenderer.requestRender(); } };
window.nebulaWrenchAction = function(act) { if(act==='clear_all'&&window.nebulaRenderer){ window.nebulaRenderer.state.expressions=[]; window.nebulaRenderer.requestRender(); } const el=document.getElementById('wrench-menu'); if(el) el.style.display='none'; };
window.switchKeypad = function(tab) { ['functions','symbols','greek','stats'].forEach(t => { const g=document.getElementById('keypad-'+t); if(g) g.style.display=t===tab?'grid':'none'; }); };
window.nebulaUpdateSlider = function(id, val) { if(window.nebulaRenderer && window.nebulaRenderer.state.sliders[id]){ window.nebulaRenderer.state.sliders[id].value=val; window.nebulaRenderer.requestRender(); } };
window.nebulaSliderClick = function(id, e) { const r=e.currentTarget.getBoundingClientRect(), pct=(e.clientX-r.left)/r.width; if(window.nebulaRenderer && window.nebulaRenderer.state.sliders[id]){ const s=window.nebulaRenderer.state.sliders[id]; s.value=s.min_val+pct*(s.max_val-s.min_val); window.nebulaRenderer.requestRender(); } };
window.nebulaUpdateTableCell = function(exprId, colName, rowIdx, val) { if(window.nebulaRenderer){ const expr=window.nebulaRenderer.state.expressions.find(e=>e.id===exprId); if(expr){ const col=expr.columns.find(c=>c.name===colName); if(col){ col.values[rowIdx]=val; window.nebulaRenderer.requestRender(); } } } };

setTimeout(() => {
    const canvas = document.getElementById('nebula-canvas');
    if (canvas && !window.nebulaRenderer) {
        window.nebulaRenderer = new NebulaRenderer(canvas, window.nebulaInitialState);
    }
}, 50);
</script>
"""

if __name__ == "__main__":
    main()
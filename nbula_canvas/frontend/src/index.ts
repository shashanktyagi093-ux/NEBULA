import { StreamlitComponent, ComponentProps, registerComponent } from "streamlit-component-lib";

interface Expression {
  id: string;
  type: string;
  raw: string;
  latex: string;
  color: string;
  visible: boolean;
  line_width: number;
  line_style: string;
  point_size: number;
  label: string;
  show_label: boolean;
  param_min: number;
  param_max: number;
  param_step: number;
  columns: Array<{name: string; values: number[]; color: string}>;
  regression_type: string;
  regression_x_col: string;
  regression_y_col: string;
  list_values: number[];
  slider_ids: string[];
}

interface Slider {
  id: string;
  name: string;
  value: number;
  min_val: number;
  max_val: number;
  step: number;
  playing: boolean;
  speed: number;
  direction: number;
}

interface Viewport {
  x_min: number; x_max: number; y_min: number; y_max: number;
  show_grid: boolean; show_axes: boolean; show_numbers: boolean;
  grid_type: string; axis_step_x: number; axis_step_y: number;
  label_step_x: number; label_step_y: number;
  background_color: string; grid_color: string; axis_color: string; label_color: string;
  projector_mode: boolean; degree_mode: boolean; contrast_mode: boolean;
}

interface NebulaState {
  expressions: Expression[];
  sliders: Record<string, Slider>;
  viewport: Viewport;
  last_mouse?: [number, number];
}

interface NebulaProps extends ComponentProps {
  args: NebulaState;
}

class NebulaRenderer {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  state: NebulaState;
  dpr: number;
  width: number = 0;
  height: number = 0;
  xScale: number = 1;
  yScale: number = 1;
  xOffset: number = 0;
  yOffset: number = 0;
  animationFrame: number | null = null;
  hoveredPoint: any = null;
  draggedPoint: any = null;
  lastTime: number = 0;

  constructor(canvas: HTMLCanvasElement, initialState: NebulaState) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d')!;
    this.state = initialState;
    this.dpr = window.devicePixelRatio || 1;
    this.bindEvents();
    this.resize();
    this.startAnimation();
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
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

  mathToScreen(x: number, y: number) {
    return { x: x * this.xScale + this.xOffset, y: this.yOffset - y * this.yScale };
  }
  screenToMath(sx: number, sy: number) {
    return { x: (sx - this.xOffset) / this.xScale, y: (this.yOffset - sy) / this.yScale };
  }

  bindEvents() {
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
    this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));
    this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    this.canvas.addEventListener('touchstart', (e) => this.onTouchStart(e), { passive: true });
    this.canvas.addEventListener('touchmove', (e) => this.onTouchMove(e), { passive: false });
    this.canvas.addEventListener('touchend', (e) => this.onTouchEnd(e));
  }

  onMouseDown(e: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    this.state.last_mouse = [sx, sy];

    if (this.checkPointHit(sx, sy)) return;
    
    this.state.viewport.is_panning = true;
    this.state.viewport.pan_start = [sx, sy];
    this.state.viewport.viewport_start = [this.state.viewport.x_min, this.state.viewport.x_max, this.state.viewport.y_min, this.state.viewport.y_max];
    this.canvas.style.cursor = 'grabbing';
  }

  onMouseMove(e: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    this.state.last_mouse = [sx, sy];

    if (this.draggedPoint) {
      const m = this.screenToMath(sx, sy);
      this.draggedPoint.x = m.x; this.draggedPoint.y = m.y;
      this.requestRender();
      this.sendPointUpdate();
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

  onMouseUp(e: MouseEvent) {
    this.state.viewport.is_panning = false;
    this.draggedPoint = null;
    this.canvas.style.cursor = 'grab';
  }

  onWheel(e: WheelEvent) {
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

  onDoubleClick(e: MouseEvent) {
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

  pinchStart: any = null;
  onTouchStart(e: TouchEvent) {
    if (e.touches.length === 1) {
      const touch = e.touches[0];
      const rect = this.canvas.getBoundingClientRect();
      const sx = touch.clientX - rect.left, sy = touch.clientY - rect.top;
      if (this.checkPointHit(sx, sy)) return;
      this.state.viewport.is_panning = true;
      this.state.viewport.pan_start = [sx, sy];
      this.state.viewport.viewport_start = [this.state.viewport.x_min, this.state.viewport.x_max, this.state.viewport.y_min, this.state.viewport.y_max];
    } else if (e.touches.length === 2) {
      this.pinchStart = { dist: this.getPinchDist(e), center: this.getPinchCenter(e), viewport: {...this.state.viewport} };
    }
  }
  onTouchMove(e: TouchEvent) {
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
  onTouchEnd(e: TouchEvent) { this.state.viewport.is_panning = false; this.pinchStart = null; this.draggedPoint = null; }
  getPinchDist(e: TouchEvent) { const t1=e.touches[0], t2=e.touches[1]; return Math.hypot(t1.clientX-t2.clientX, t1.clientY-t2.clientY); }
  getPinchCenter(e: TouchEvent) { const t1=e.touches[0], t2=e.touches[1]; const r=this.canvas.getBoundingClientRect(); return {x:(t1.clientX+t2.clientX)/2-r.left, y:(t1.clientY+t2.clientY)/2-r.top}; }

  checkPointHit(sx: number, sy: number) {
    for (const expr of this.state.expressions) {
      if (!expr.visible) continue;
      if (expr.type === 'point' || expr.type === 'table') {
        const points = this.getExpressionPoints(expr);
        for (const pt of points) {
          const screen = this.mathToScreen(pt.x, pt.y);
          const dx = sx - screen.x, dy = sy - screen.y;
          if (dx*dx + dy*dy < 100) { this.draggedPoint = {...pt, exprId: expr.id, exprColor: expr.color}; return true; }
        }
      }
    }
    return false;
  }

  findHoveredPoint(sx: number, sy: number) {
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

  getExpressionPoints(expr: Expression) {
    if (expr.type === 'point') {
      const m = expr.raw.match(/\((.+),(.+)\)/);
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

  prepareExpr(e: string) { return e.replace(/\^/g,'**').replace(/(\d)([a-zA-Z(])/g,'$1*$2').replace(/([a-zA-Z)])(\()/g,'$1*$2'); }

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
    ctx.strokeStyle = v.grid_color; ctx.lineWidth = 1;
    const xs = Math.floor(v.x_min / v.axis_step_x) * v.axis_step_x;
    for (let x = xs; x <= v.x_max; x += v.axis_step_x) if (x !== 0) { const sx=this.mathToScreen(x,0).x; ctx.beginPath(); ctx.moveTo(sx,0); ctx.lineTo(sx,h); ctx.stroke(); }
    const ys = Math.floor(v.y_min / v.axis_step_y) * v.axis_step_y;
    for (let y = ys; y <= v.y_max; y += v.axis_step_y) if (y !== 0) { const sy=this.mathToScreen(0,y).y; ctx.beginPath(); ctx.moveTo(0,sy); ctx.lineTo(w,sy); ctx.stroke(); }
  }

  drawAxes() {
    const ctx = this.ctx, v = this.state.viewport;
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

  fmt(n: number) { if (Math.abs(n)<1e-10) return '0'; if (Math.abs(n)>=1e6 || (Math.abs(n)<1e-3 && n!==0)) return n.toExponential(2); return parseFloat(n.toPrecision(10)).toString(); }

  drawExpression(expr: Expression) {
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

  drawFunction(expr: Expression) {
    const ctx=this.ctx, v=this.state.viewport; let fe=expr.raw, fn='f';
    const m = expr.raw.match(/^([fg]\([a-z]\))\s*=\s*(.+)$/);
    if (m) { fn = m[1].slice(0,1); fe = m[2]; }
    const js = this.prepareForJS(fe); const step = (v.x_max-v.x_min)/this.width*0.5;
    ctx.beginPath(); let first=true, lastY:number|null=null;
    for (let x=v.x_min; x<=v.x_max; x+=step) {
      try { const y = eval(js.replace(new RegExp(fn,'g'), `(${x})`)); if (!isFinite(y)) { lastY=null; continue; }
      const p=this.mathToScreen(x,y); if (first) { ctx.moveTo(p.x,p.y); first=false; }
      else { if (lastY!==null && Math.abs(y-lastY) > (v.y_max-v.y_min)*0.5) { ctx.stroke(); ctx.beginPath(); ctx.moveTo(p.x,p.y); } else ctx.lineTo(p.x,p.y); } lastY=y; } catch { lastY=null; }
    }
    ctx.stroke();
  }

  drawParametric(expr: Expression) {
    const ctx=this.ctx; const m=expr.raw.match(/^\((.+),(.+)\)$/); if (!m) return;
    const xe=this.prepareForJS(m[1]), ye=this.prepareForJS(m[2]);
    const tmin=expr.param_min, tmax=expr.param_max, tstep=expr.param_step;
    ctx.beginPath(); let first=true;
    for (let t=tmin; t<=tmax; t+=tstep) { try { const x=eval(xe.replace(/t/g,`(${t})`)), y=eval(ye.replace(/t/g,`(${t})`)); if (!isFinite(x)||!isFinite(y)) {first=true;continue;} const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y);} catch {first=true;} } ctx.stroke();
  }

  drawPolar(expr: Expression) {
    const ctx=this.ctx; const re=expr.raw.replace(/^r\s*=\s*/,''); const rjs=this.prepareForJS(re);
    const tmin=expr.param_min, tmax=expr.param_max, tstep=expr.param_step;
    ctx.beginPath(); let first=true;
    for (let th=tmin; th<=tmax; th+=tstep) { try { const r=eval(rjs.replace(/theta|t/g,`(${th})`)); if (!isFinite(r)) {first=true;continue;} const x=r*Math.cos(th), y=r*Math.sin(th); const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y);} catch {first=true;} } ctx.stroke();
  }

  drawImplicit(expr: Expression) {
    const ctx=this.ctx, v=this.state.viewport; const parts=expr.raw.split('='); if (parts.length!==2) return;
    const lhs=this.prepareForJS(parts[0]), rhs=this.prepareForJS(parts[1]); const ejs=`(${lhs})-(${rhs})`;
    const cs=Math.max(2,Math.min(w,h)/200); const cols=Math.ceil(w/cs), rows=Math.ceil(h/cs);
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

  drawPoint(expr: Expression) {
    const ctx=this.ctx; const m=expr.raw.match(/\((.+),(.+)\)/); if (!m) return;
    try { const x=eval(this.prepareExpr(m[1])), y=eval(this.prepareExpr(m[2])); if(!isFinite(x)||!isFinite(y)) return; const p=this.mathToScreen(x,y); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); ctx.fillStyle='#0d1117'; ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size*0.4,0,2*Math.PI); ctx.fill(); ctx.fillStyle=expr.color; } catch {}
  }

  drawTable(expr: Expression) {
    const ctx=this.ctx, cols=expr.columns; if (cols.length<2) return;
    const xCol=cols.find(c=>c.name==='x')||cols[0], yCol=cols.find(c=>c.name==='y')||cols[1];
    for (let i=0;i<Math.min(xCol.values.length,yCol.values.length);i++) { const x=xCol.values[i], y=yCol.values[i]; if(!isFinite(x)||!isFinite(y)) continue; const p=this.mathToScreen(x,y); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); ctx.fillStyle='#0d1117'; ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size*0.4,0,2*Math.PI); ctx.fill(); ctx.fillStyle=expr.color; }
  }

  drawRegression(expr: Expression) {
    const tableExpr = this.state.expressions.find(e => e.id === expr.regression_x_col);
    if (!tableExpr) return;
    this.drawRegressionLine(expr, 
      tableExpr.columns.find(c => c.name === expr.regression_x_col)?.values || [],
      tableExpr.columns.find(c => c.name === expr.regression_y_col)?.values || []
    );
  }

  drawRegressionLine(expr: Expression, xVals: number[], yVals: number[]) {
    if (xVals.length < 2) return;
    const ctx=this.ctx, v=this.state.viewport; ctx.strokeStyle=expr.color; ctx.lineWidth=expr.line_width; ctx.setLineDash([6,4]);
    const coeffs = this.computeRegression(expr.regression_type, xVals, yVals);
    if (!coeffs) return;
    const step=(v.x_max-v.x_min)/this.width*0.5; ctx.beginPath(); let first=true;
    for(let x=v.x_min;x<=v.x_max;x+=step){ const y=this.evalRegression(expr.regression_type,coeffs,x); if(!isFinite(y)){first=true;continue;} const p=this.mathToScreen(x,y); if(first){ctx.moveTo(p.x,p.y);first=false;}else ctx.lineTo(p.x,p.y); } ctx.stroke(); ctx.setLineDash([]);
  }

  computeRegression(type: string, x: number[], y: number[]) {
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
  linearReg(x: number[], y: number[], n: number) { let sx=0,sy=0,sxy=0,sx2=0; for(let i=0;i<n;i++){sx+=x[i];sy+=y[i];sxy+=x[i]*y[i];sx2+=x[i]*x[i];} const den=n*sx2-sx*sx; if(Math.abs(den)<1e-10)return null; return [(n*sxy-sx*sy)/den,(sy*sx2-sx*sxy)/den]; }
  polyReg(x: number[], y: number[], n: number, deg: number) { const A=Array(deg+1).fill().map(()=>Array(deg+1).fill(0)), b=Array(deg+1).fill(0); for(let i=0;i<n;i++){const xp=Array(deg+1).fill(1);for(let d=1;d<=deg;d++)xp[d]=xp[d-1]*x[i];for(let r=0;r<=deg;r++){for(let c=0;c<=deg;c++)A[r][c]+=xp[r]*xp[c];b[r]+=xp[r]*y[i];}}return this.gauss(A,b); }
  gauss(A: number[][], b: number[]) { const n=A.length; for(let i=0;i<n;i++){let mr=i;for(let r=i+1;r<n;r++)if(Math.abs(A[r][i])>Math.abs(A[mr][i]))mr=r;[A[i],A[mr]]=[A[mr],A[i]];[b[i],b[mr]]=[b[mr],b[i]];const piv=A[i][i];if(Math.abs(piv)<1e-12)return null;for(let c=i;c<n;c++)A[i][c]/=piv;b[i]/=piv;for(let r=0;r<n;r++)if(r!==i){const f=A[r][i];for(let c=i;c<n;c++)A[r][c]-=f*A[i][c];b[r]-=f*b[i];}}return b; }
  expReg(x: number[], y: number[], n: number) { const ly=y.map(v=>v>0?Math.log(v):NaN); if(ly.some(isNaN))return null; const l=this.linearReg(x,ly,n); if(!l)return null; return [Math.exp(l[1]),l[0]]; }
  logReg(x: number[], y: number[], n: number) { const lx=x.map(v=>v>0?Math.log(v):NaN); if(lx.some(isNaN))return null; return this.linearReg(lx,y,n); }
  powerReg(x: number[], y: number[], n: number) { const lx=x.map(v=>v>0?Math.log(v):NaN), ly=y.map(v=>v>0?Math.log(v):NaN); if(lx.some(isNaN)||ly.some(isNaN))return null; const l=this.linearReg(lx,ly,n); if(!l)return null; return [Math.exp(l[1]),l[0]]; }
  evalRegression(type: string, c: number[], x: number) { switch(type){case'linear':return c[0]*x+c[1];case'quadratic':return c[0]*x*x+c[1]*x+c[2];case'cubic':return c[0]*x*x*x+c[1]*x*x+c[2]*x+c[3];case'quartic':return c[0]*x*x*x*x+c[1]*x*x*x+c[2]*x*x+c[3]*x+c[4];case'exponential':return c[0]*Math.exp(c[1]*x);case'logarithmic':return c[0]+c[1]*Math.log(x);case'power':return c[0]*Math.pow(x,c[1]);default:return c[0]*x+c[1];} }

  drawList(expr: Expression) { const ctx=this.ctx; for(const x of expr.list_values){ const p=this.mathToScreen(x,0); ctx.beginPath(); ctx.arc(p.x,p.y,expr.point_size,0,2*Math.PI); ctx.fill(); } }

  drawPointHighlight(pt: any) { const ctx=this.ctx, p=this.mathToScreen(pt.x,pt.y); ctx.strokeStyle=pt.exprColor||'#00d4aa'; ctx.lineWidth=3; ctx.beginPath(); ctx.arc(p.x,p.y,14,0,2*Math.PI); ctx.stroke(); ctx.fillStyle=pt.exprColor||'#00d4aa'; ctx.font='12px monospace'; ctx.textAlign='left'; ctx.fillText(`(${this.fmt(pt.x)}, ${this.fmt(pt.y)})`, p.x+18, p.y-18); }

  drawCoordinates() { const ctx=this.ctx, v=this.state.viewport, m=this.screenToMath(this.state.last_mouse?.[0]||0,this.state.last_mouse?.[1]||0); ctx.fillStyle='rgba(22,27,34,0.95)'; ctx.strokeStyle=v.grid_color; ctx.lineWidth=1; const text=`x: ${this.fmt(m.x)}  y: ${this.fmt(m.y)}`; ctx.font='12px monospace'; const tw=ctx.measureText(text).width+24, th=28, x=12, y=h-12-th; ctx.roundRect(x,y,tw,th,8); ctx.fill(); ctx.stroke(); ctx.fillStyle=v.label_color; ctx.textBaseline='middle'; ctx.fillText(text, x+12, y+th/2); }

  prepareForJS(e: string) { let js=e.replace(/\^/g,'**').replace(/(\d)([a-zA-Z(])/g,'$1*$2').replace(/([a-zA-Z)])(\()/g,'$1*$2'); js=js.replace(/pi/g,'Math.PI').replace(/tau/g,'2*Math.PI').replace(/e(?![a-zA-Z])/g,'Math.E').replace(/phi/g,'(1+Math.sqrt(5))/2'); const fs={'sin':'Math.sin','cos':'Math.cos','tan':'Math.tan','csc':'x=>1/Math.sin(x)','sec':'x=>1/Math.cos(x)','cot':'x=>1/Math.tan(x)','arcsin':'Math.asin','arccos':'Math.acos','arctan':'Math.atan','sinh':'Math.sinh','cosh':'Math.cosh','tanh':'Math.tanh','sqrt':'Math.sqrt','cbrt':'Math.cbrt','exp':'Math.exp','ln':'Math.log','log':'Math.log10','log10':'Math.log10','log2':'Math.log2','abs':'Math.abs','floor':'Math.floor','ceil':'Math.ceil','round':'Math.round','sign':'x=>x>0?1:x<0?-1:0','min':'Math.min','max':'Math.max'}; for(const[k,v]of Object.entries(fs))js=js.replace(new RegExp(`\\b${k}\\b`,'gi'),v); return js; }

  requestRender() { if(this.animationFrame)return; this.animationFrame=requestAnimationFrame(()=>{this.animationFrame=null;this.render();}); }
  startAnimation() { const animate=(time:number)=>{this.lastTime=time/1000; for(const s of Object.values(this.state.sliders))if(s.playing){s.value+=s.direction*s.speed*0.016;if(s.value>=s.max_val){s.value=s.max_val;s.direction=-1;}if(s.value<=s.min_val){s.value=s.min_val;s.direction=1;}}this.render();requestAnimationFrame(animate);};requestAnimationFrame(animate); }
  sendViewportUpdate() { this.dispatchEvent('viewport_update', this.state.viewport); }
  sendPointUpdate() { if(this.draggedPoint) this.dispatchEvent('point_update', this.draggedPoint); }
  dispatchEvent(type: string, detail: any) { this.canvas.dispatchEvent(new CustomEvent('nebula', {detail:{type,...detail}})); }
  setState(newState: NebulaState) { this.state = newState; this.updateProjection(); this.requestRender(); }
}

// Extend Canvas for roundRect
CanvasRenderingContext2D.prototype.roundRect = function(x:number,y:number,w:number,h:number,r:number){this.beginPath();this.moveTo(x+r,y);this.lineTo(x+w-r,y);this.quadraticCurveTo(x+w,y,x+w,y+r);this.lineTo(x+w,y+h-r);this.quadraticCurveTo(x+w,y+h,x+w-r,y+h);this.lineTo(x+r,y+h);this.quadraticCurveTo(x,y+h,x,y+h-r);this.lineTo(x,y+r);this.quadraticCurveTo(x,y,x+r,y);};

// ─── Streamlit Component ───
class NebulaCanvas extends StreamlitComponent<NebulaProps> {
  private renderer: NebulaRenderer | null = null;
  private canvasEl: HTMLCanvasElement | null = null;

  render() {
    return <canvas 
      ref={(el) => { this.canvasEl = el; }}
      style={{width: '100%', height: '100%', touchAction: 'none'}}
      onNebula={(e: CustomEvent) => this.handleNebulaEvent(e.detail)}
    />;
  }

  handleNebulaEvent(detail: any) {
    this.dispatchEvent({type: 'nebula_event', ...detail});
  }

  mount() {
    if (this.canvasEl && !this.renderer) {
      this.renderer = new NebulaRenderer(this.canvasEl, this.props.args);
      (window as any).nebulaRenderer = this.renderer;
    }
  }

  update() {
    if (this.renderer) {
      this.renderer.setState(this.props.args);
    }
  }
}

registerComponent("nebula_canvas", NebulaCanvas);
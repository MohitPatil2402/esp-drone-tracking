from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from utils import process_data, get_positions, get_devices, get_nodes, get_history

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESP Location Tracker</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d1117;--surf:#161b22;--border:#30363d;
  --text:#c9d1d9;--muted:#8b949e;--accent:#58a6ff;
  --green:#3fb950;--red:#f85149;--yellow:#d29922;
}
body{font-family:'Courier New',monospace;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;gap:16px;padding:8px 16px;background:var(--surf);border-bottom:1px solid var(--border);flex-shrink:0;min-height:44px}
.brand{font-weight:bold;font-size:14px;color:var(--accent);letter-spacing:.05em}
.status-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.status-dot.live{background:var(--green);box-shadow:0 0 6px var(--green)}
.status-dot.off{background:var(--red)}
#status-text{font-size:12px;color:var(--muted)}
.hstat{font-size:12px;color:var(--muted);margin-left:auto}
.content{display:flex;flex:1;overflow:hidden}
/* Sidebar */
.sidebar{width:240px;flex-shrink:0;background:var(--surf);border-right:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column}
.sb-section{padding:10px 12px}
.sb-title{font-size:10px;font-weight:bold;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.device-card{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:8px;transition:border-color .3s}
.device-card.located{border-color:#30363d}
.d-header{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.d-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.d-mac{font-size:12px;font-weight:bold;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.d-age{font-size:10px;color:var(--muted);white-space:nowrap}
.d-pos{font-size:11px;color:var(--accent);margin-bottom:6px}
.node-row{display:flex;align-items:center;gap:6px;margin-bottom:3px}
.node-label{font-size:10px;color:var(--muted);width:44px;flex-shrink:0}
.sig-bar{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden}
.sig-fill{height:100%;border-radius:2px;transition:width .4s}
.node-rssi{font-size:10px;color:var(--muted);width:44px;text-align:right;flex-shrink:0}
.empty-msg{font-size:11px;color:var(--muted);text-align:center;padding:16px}
.node-info{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border)}
.node-info:last-child{border-bottom:none}
.node-icon{width:10px;height:10px;background:#58a6ff;transform:rotate(45deg);flex-shrink:0}
.node-text{font-size:11px}
.node-coords{font-size:10px;color:var(--muted);margin-left:auto}
/* Map */
.map-wrap{flex:1;position:relative;overflow:hidden;background:var(--bg)}
#map{display:block;width:100%;height:100%}
.map-controls{position:absolute;top:10px;right:10px;display:flex;flex-direction:column;gap:4px}
.map-controls button{width:30px;height:30px;background:var(--surf);border:1px solid var(--border);color:var(--text);border-radius:4px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;transition:background .2s}
.map-controls button:hover{background:var(--border)}
.trail-btn{font-size:11px!important;width:52px!important;color:var(--green)!important}
.trail-btn.off{color:var(--muted)!important}
#coord-display{position:absolute;bottom:8px;right:10px;font-size:11px;color:var(--muted);pointer-events:none;background:var(--surf);padding:2px 6px;border-radius:3px;border:1px solid var(--border)}
</style>
</head>
<body>
<header>
  <span class="brand">ESP Location Tracker</span>
  <span class="status-dot off" id="status-dot"></span>
  <span id="status-text">Connecting…</span>
  <span class="hstat" id="hstat"></span>
</header>
<div class="content">
  <aside class="sidebar">
    <div class="sb-section">
      <div class="sb-title">Active Devices</div>
      <div id="device-list"><div class="empty-msg">Waiting for devices…</div></div>
    </div>
    <div class="sb-section" style="border-top:1px solid var(--border);margin-top:4px">
      <div class="sb-title">ESP Nodes</div>
      <div id="node-list"></div>
    </div>
  </aside>
  <div class="map-wrap">
    <canvas id="map"></canvas>
    <div class="map-controls">
      <button title="Zoom in" onclick="zoomAt(1.25)">+</button>
      <button title="Zoom out" onclick="zoomAt(0.8)">−</button>
      <button title="Fit view" onclick="fitView()">⊙</button>
      <button class="trail-btn" id="trail-btn" title="Toggle trails" onclick="toggleTrails()">Trail</button>
    </div>
    <div id="coord-display">x: — &nbsp; y: —</div>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let nodes={}, positions={}, devices={};
let trails={};          // mac -> [{x,y}]
let colorMap={};        // mac -> css color
let showTrails=true;
let viewFitted=false;

// Canvas transform: canvas(px) = [panX + wx*scale,  panY - wy*scale]
let scale=30, panX=0, panY=0;
let dragging=false, lastMX=0, lastMY=0;
let updateCount=0;

const PALETTE=['#58a6ff','#3fb950','#f78166','#d2a8ff',
               '#ffa657','#79c0ff','#56d364','#ff7b72'];
const TRAIL_MAX=30;

// ── Canvas setup ───────────────────────────────────────────────────────────
const canvas=document.getElementById('map');
const ctx=canvas.getContext('2d');

function resizeCanvas(){
  const wrap=canvas.parentElement;
  canvas.width=wrap.clientWidth;
  canvas.height=wrap.clientHeight;
  draw();
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ── Coordinate transforms ──────────────────────────────────────────────────
function w2c(wx,wy){ return [panX+wx*scale, panY-wy*scale]; }
function c2w(cx,cy){ return [(cx-panX)/scale, (panY-cy)/scale]; }

// ── Colour assignment ──────────────────────────────────────────────────────
function deviceColor(mac){
  if(!colorMap[mac]){
    const idx=Object.keys(colorMap).length % PALETTE.length;
    colorMap[mac]=PALETTE[idx];
  }
  return colorMap[mac];
}

// ── RSSI → signal strength 0..1 ───────────────────────────────────────────
function rssiStrength(rssi){ return Math.max(0,Math.min(1,(rssi+90)/60)); }

// ── Fit view to node layout ────────────────────────────────────────────────
function fitView(){
  const pts=Object.values(nodes);
  if(!pts.length) return;
  const xs=pts.map(p=>p[0]), ys=pts.map(p=>p[1]);
  const MARGIN=50;
  const minX=Math.min(...xs)-3, maxX=Math.max(...xs)+3;
  const minY=Math.min(...ys)-3, maxY=Math.max(...ys)+3;
  const ww=maxX-minX, wh=maxY-minY;
  const avW=canvas.width-2*MARGIN, avH=canvas.height-2*MARGIN;
  scale=Math.min(avW/ww, avH/wh);
  panX=MARGIN-minX*scale;
  panY=MARGIN+maxY*scale;
  draw();
}
function zoomAt(factor){
  const cx=canvas.width/2, cy=canvas.height/2;
  const [wx,wy]=c2w(cx,cy);
  scale*=factor;
  panX=cx-wx*scale;
  panY=cy+wy*scale;
  draw();
}
function toggleTrails(){
  showTrails=!showTrails;
  const btn=document.getElementById('trail-btn');
  btn.classList.toggle('off',!showTrails);
  draw();
}

// ── Drawing ────────────────────────────────────────────────────────────────
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='#0d1117';
  ctx.fillRect(0,0,canvas.width,canvas.height);
  drawGrid();
  if(showTrails) drawTrails();
  drawNodes();
  drawDeviceMarkers();
  drawScaleBar();
}

function drawGrid(){
  const [wx0,wy0]=c2w(0,canvas.height);
  const [wx1,wy1]=c2w(canvas.width,0);
  const step=gridStep();
  ctx.strokeStyle='#1c2430'; ctx.lineWidth=1;
  // vertical lines
  for(let x=Math.floor(wx0/step)*step; x<=wx1; x+=step){
    const [cx]=w2c(x,0);
    ctx.beginPath(); ctx.moveTo(cx,0); ctx.lineTo(cx,canvas.height); ctx.stroke();
  }
  // horizontal lines
  for(let y=Math.floor(wy0/step)*step; y<=wy1; y+=step){
    const [,cy]=w2c(0,y);
    ctx.beginPath(); ctx.moveTo(0,cy); ctx.lineTo(canvas.width,cy); ctx.stroke();
  }
  // axis labels
  ctx.fillStyle='#2d3748'; ctx.font='10px Courier New'; ctx.textAlign='center';
  for(let x=Math.floor(wx0/step)*step; x<=wx1; x+=step){
    const [cx,cy]=w2c(x,0);
    if(cy>10 && cy<canvas.height-4) ctx.fillText(x+'m',cx,Math.min(cy+12,canvas.height-4));
  }
  ctx.textAlign='right';
  for(let y=Math.floor(wy0/step)*step; y<=wy1; y+=step){
    const [cx,cy]=w2c(0,y);
    if(cx>4 && cx<canvas.width-4) ctx.fillText(y+'m',Math.max(cx-4,28),cy+4);
  }
}

function gridStep(){
  if(scale>=40) return 1;
  if(scale>=15) return 2;
  if(scale>=6)  return 5;
  return 10;
}

function drawTrails(){
  Object.entries(trails).forEach(([mac,trail])=>{
    if(trail.length<2) return;
    const color=deviceColor(mac);
    ctx.setLineDash([4,4]);
    ctx.lineWidth=1.5;
    ctx.strokeStyle=color+'88';
    ctx.beginPath();
    trail.forEach((p,i)=>{
      const [cx,cy]=w2c(p.x,p.y);
      i===0 ? ctx.moveTo(cx,cy) : ctx.lineTo(cx,cy);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  });
}

function drawNodes(){
  Object.entries(nodes).forEach(([id,p])=>{
    const [cx,cy]=w2c(p[0],p[1]);
    // diamond
    ctx.save();
    ctx.translate(cx,cy);
    ctx.rotate(Math.PI/4);
    ctx.fillStyle='#1a3a5c';
    ctx.strokeStyle='#58a6ff';
    ctx.lineWidth=2;
    ctx.fillRect(-7,-7,14,14);
    ctx.strokeRect(-7,-7,14,14);
    ctx.restore();
    // label
    ctx.fillStyle='#c9d1d9';
    ctx.font='bold 11px Courier New';
    ctx.textAlign='center';
    ctx.fillText('Node '+id, cx, cy+22);
    ctx.fillStyle='#8b949e';
    ctx.font='10px Courier New';
    ctx.fillText('('+p[0]+', '+p[1]+')', cx, cy+33);
  });
}

function drawDeviceMarkers(){
  Object.entries(positions).forEach(([mac,pos])=>{
    const color=deviceColor(mac);
    const [cx,cy]=w2c(pos.x,pos.y);
    const shortMac=mac.split(':').slice(-3).join(':');

    // glow
    const g=ctx.createRadialGradient(cx,cy,0,cx,cy,22);
    g.addColorStop(0,color+'33');
    g.addColorStop(1,'transparent');
    ctx.fillStyle=g;
    ctx.beginPath(); ctx.arc(cx,cy,22,0,2*Math.PI); ctx.fill();

    // circle
    ctx.beginPath(); ctx.arc(cx,cy,9,0,2*Math.PI);
    ctx.fillStyle=color; ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.stroke();

    ctx.textAlign='center';
    ctx.fillStyle='#c9d1d9'; ctx.font='bold 11px Courier New';
    ctx.fillText(shortMac, cx, cy-16);
    ctx.fillStyle='#8b949e'; ctx.font='10px Courier New';
    ctx.fillText('('+pos.x.toFixed(2)+', '+pos.y.toFixed(2)+')', cx, cy+22);
  });
}

function drawScaleBar(){
  const barM=5; // 5 metres
  const barPx=barM*scale;
  const x=16, y=canvas.height-16;
  ctx.fillStyle='#8b949e'; ctx.fillRect(x,y-4,barPx,4);
  ctx.fillStyle='#8b949e'; ctx.font='10px Courier New'; ctx.textAlign='left';
  ctx.fillText(barM+'m', x+barPx+4, y);
}

// ── Trail update ───────────────────────────────────────────────────────────
function pushTrail(mac,x,y){
  if(!trails[mac]) trails[mac]=[];
  const t=trails[mac], last=t[t.length-1];
  if(!last || Math.hypot(x-last.x,y-last.y)>0.05){
    t.push({x,y});
    if(t.length>TRAIL_MAX) t.shift();
  }
}

// ── API polling ────────────────────────────────────────────────────────────
let consecutiveErrors=0;

async function fetchData(){
  try{
    const res=await fetch('/data');
    if(!res.ok) throw new Error(res.status);
    const d=await res.json();

    nodes=d.nodes||{};
    devices=d.devices||{};
    const newPos=d.positions||{};

    Object.entries(newPos).forEach(([mac,p])=>pushTrail(mac,p.x,p.y));
    positions=newPos;

    consecutiveErrors=0;
    updateCount++;
    updateStatus(true);
    renderDevicePanel();
    renderNodePanel();

    if(!viewFitted && Object.keys(nodes).length){
      viewFitted=true;
      fitView();
    } else {
      draw();
    }
  }catch(e){
    consecutiveErrors++;
    if(consecutiveErrors>2) updateStatus(false);
  }
}

function updateStatus(live){
  const dot=document.getElementById('status-dot');
  const txt=document.getElementById('status-text');
  const stat=document.getElementById('hstat');
  dot.className='status-dot '+(live?'live':'off');
  txt.textContent=live?'Live':'Offline';
  const devCount=Object.keys(positions).length;
  stat.textContent=devCount+' device'+(devCount===1?'':'s')+' located  ·  '+updateCount+' updates';
}

// ── Device panel HTML ──────────────────────────────────────────────────────
function renderDevicePanel(){
  const el=document.getElementById('device-list');
  if(!Object.keys(devices).length){
    el.innerHTML='<div class="empty-msg">No devices detected</div>';
    return;
  }
  el.innerHTML=Object.entries(devices).map(([mac,dev])=>{
    const color=deviceColor(mac);
    const pos=positions[mac];
    const posStr=pos?pos.x.toFixed(2)+'m, '+pos.y.toFixed(2)+'m':'Locating…';
    const shortMac=mac.split(':').slice(-3).join(':');
    const age=dev.age;
    const ageStr=age<60?Math.round(age)+'s ago':Math.round(age/60)+'m ago';

    const rows=Object.entries(dev.node_rssi||{}).map(([nid,rssi])=>{
      const pct=Math.round(rssiStrength(rssi)*100);
      return `<div class="node-row">
        <span class="node-label">Node ${nid}</span>
        <div class="sig-bar"><div class="sig-fill" style="width:${pct}%;background:${color}"></div></div>
        <span class="node-rssi">${rssi}</span>
      </div>`;
    }).join('');

    return `<div class="device-card ${pos?'located':''}">
      <div class="d-header">
        <span class="d-dot" style="background:${color}"></span>
        <span class="d-mac" title="${mac}">${shortMac}</span>
        <span class="d-age">${ageStr}</span>
      </div>
      <div class="d-pos">${posStr}</div>
      ${rows}
    </div>`;
  }).join('');
}

function renderNodePanel(){
  const el=document.getElementById('node-list');
  el.innerHTML=Object.entries(nodes).map(([id,p])=>`
    <div class="node-info">
      <span class="node-icon"></span>
      <span class="node-text">Node ${id}</span>
      <span class="node-coords">(${p[0]}, ${p[1]})</span>
    </div>`).join('');
}

// ── Pan / zoom events ──────────────────────────────────────────────────────
canvas.addEventListener('mousedown', e=>{ dragging=true; lastMX=e.clientX; lastMY=e.clientY; });
window.addEventListener('mouseup',   ()=>{ dragging=false; });
window.addEventListener('mousemove', e=>{
  if(dragging){
    panX+=e.clientX-lastMX; panY+=e.clientY-lastMY;
    lastMX=e.clientX; lastMY=e.clientY;
    draw();
  }
  const rect=canvas.getBoundingClientRect();
  const [wx,wy]=c2w(e.clientX-rect.left, e.clientY-rect.top);
  document.getElementById('coord-display').textContent=
    'x: '+wx.toFixed(2)+'m  y: '+wy.toFixed(2)+'m';
});
canvas.addEventListener('wheel', e=>{
  e.preventDefault();
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const [wx,wy]=c2w(mx,my);
  const f=e.deltaY<0?1.12:0.88;
  scale*=f;
  panX=mx-wx*scale; panY=my+wy*scale;
  draw();
},{passive:false});

// ── Boot ───────────────────────────────────────────────────────────────────
setInterval(fetchData, 500);
fetchData();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/endpoint', methods=['POST'])
def receive_data():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "no JSON"}), 400
    process_data(data)
    return jsonify({"status": "ok"})


@app.route('/data', methods=['GET'])
def combined_data():
    """Single endpoint the frontend polls — positions + devices + nodes."""
    return jsonify({
        'positions': get_positions(),
        'devices':   get_devices(),
        'nodes':     get_nodes(),
    })


@app.route('/positions', methods=['GET'])
def positions():
    return jsonify(get_positions())


@app.route('/devices', methods=['GET'])
def devices():
    return jsonify(get_devices())


@app.route('/nodes', methods=['GET'])
def nodes():
    return jsonify(get_nodes())


@app.route('/history/<path:mac>', methods=['GET'])
def history(mac):
    return jsonify(get_history(mac))


@app.route('/', methods=['GET'])
def home():
    return render_template_string(_HTML)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

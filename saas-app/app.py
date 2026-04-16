from flask import Flask, jsonify, render_template_string
import platform, datetime, os, subprocess, json, time
import psutil

app = Flask(__name__)
START_TIME = time.time()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloudWatch — OpenStack Monitor</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  :root{
    --bg:#0f1117;--surface:#1a1d27;--surface2:#22263a;--border:#2e3350;
    --text:#e8eaf6;--muted:#7b82a8;--accent:#6c63ff;--accent2:#00d4aa;
    --green:#00d4aa;--yellow:#ffb347;--red:#ff5c5c;--blue:#4da6ff;
    --card-r:12px;
  }
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
  
  /* TOP NAV */
  nav{background:var(--surface);border-bottom:1px solid var(--border);padding:0 2rem;
      display:flex;align-items:center;justify-content:space-between;height:56px;position:sticky;top:0;z-index:100}
  .nav-brand{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:600;color:var(--text)}
  .nav-brand svg{color:var(--accent)}
  .nav-status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted)}
  .pulse{width:8px;height:8px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}
  @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
  .nav-time{font-size:13px;color:var(--muted);font-family:monospace}

  /* LAYOUT */
  main{padding:1.5rem 2rem;max-width:1400px;margin:0 auto}
  .page-title{font-size:13px;color:var(--muted);margin-bottom:1.5rem;text-transform:uppercase;letter-spacing:.08em}
  
  /* STAT CARDS ROW */
  .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem}
  .stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--card-r);padding:1.2rem 1.4rem}
  .stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem}
  .stat-value{font-size:28px;font-weight:600;line-height:1;margin-bottom:.3rem}
  .stat-sub{font-size:12px;color:var(--muted)}
  .stat-bar{height:3px;background:var(--border);border-radius:2px;margin-top:.8rem;overflow:hidden}
  .stat-bar-fill{height:100%;border-radius:2px;transition:width .5s ease}
  .c-green{color:var(--green)}.c-yellow{color:var(--yellow)}.c-red{color:var(--red)}.c-blue{color:var(--blue)}.c-accent{color:var(--accent)}

  /* MAIN CONTENT GRID */
  .content-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
  .content-grid.wide{grid-template-columns:2fr 1fr}
  @media(max-width:900px){.content-grid,.content-grid.wide{grid-template-columns:1fr}}
  
  /* PANELS */
  .panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--card-r);padding:1.4rem}
  .panel-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem}
  .panel-title{font-size:13px;font-weight:600;color:var(--text);text-transform:uppercase;letter-spacing:.06em}
  .panel-badge{font-size:11px;padding:3px 8px;border-radius:20px;font-weight:500}
  .badge-green{background:rgba(0,212,170,.15);color:var(--green)}
  .badge-blue{background:rgba(77,166,255,.15);color:var(--blue)}
  .badge-yellow{background:rgba(255,179,71,.15);color:var(--yellow)}
  .badge-red{background:rgba(255,92,92,.15);color:var(--red)}

  /* CHART CONTAINERS */
  .chart-wrap{position:relative;height:180px}
  
  /* INSTANCE TABLE */
  .instance-table{width:100%;border-collapse:collapse;font-size:13px}
  .instance-table th{text-align:left;color:var(--muted);font-size:11px;text-transform:uppercase;
      letter-spacing:.07em;padding:0 0 .8rem;font-weight:500;border-bottom:1px solid var(--border)}
  .instance-table td{padding:.7rem 0;border-bottom:1px solid var(--border);color:var(--text);vertical-align:middle}
  .instance-table tr:last-child td{border-bottom:none}
  .status-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px}
  .dot-green{background:var(--green)}.dot-red{background:var(--red)}.dot-yellow{background:var(--yellow)}.dot-gray{background:var(--muted)}
  .inst-name{font-weight:500;color:var(--text)}
  .inst-id{font-family:monospace;font-size:11px;color:var(--muted)}

  /* PROCESS LIST */
  .proc-row{display:flex;align-items:center;justify-content:space-between;
      padding:.5rem 0;border-bottom:1px solid var(--border);font-size:13px}
  .proc-row:last-child{border-bottom:none}
  .proc-name{color:var(--text);font-family:monospace;font-size:12px}
  .proc-cpu{color:var(--muted);font-size:12px;min-width:50px;text-align:right}
  
  /* DISK ROW */
  .disk-row{margin-bottom:1rem}
  .disk-row:last-child{margin-bottom:0}
  .disk-info{display:flex;justify-content:space-between;font-size:13px;margin-bottom:.4rem}
  .disk-name{color:var(--text)}
  .disk-pct{color:var(--muted)}
  .disk-bar{height:5px;background:var(--border);border-radius:3px;overflow:hidden}
  .disk-fill{height:100%;border-radius:3px;transition:width .5s}

  /* NETWORK ROW */
  .net-grid{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-top:.5rem}
  .net-item{background:var(--surface2);border-radius:8px;padding:.8rem 1rem}
  .net-dir{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-bottom:.3rem}
  .net-val{font-size:18px;font-weight:600}
  .net-sub{font-size:11px;color:var(--muted);margin-top:.2rem}

  /* UPTIME / INFO */
  .info-row{display:flex;justify-content:space-between;align-items:center;
      padding:.6rem 0;border-bottom:1px solid var(--border);font-size:13px}
  .info-row:last-child{border-bottom:none}
  .info-key{color:var(--muted)}
  .info-val{color:var(--text);font-family:monospace;font-size:12px;text-align:right}

  /* BOTTOM FULL ROW */
  .full-row{margin-bottom:1rem}

  /* SLA GAUGE */
  .sla-wrap{display:flex;align-items:center;justify-content:space-around;padding:.5rem 0}
  .sla-circle{position:relative;width:110px;height:110px}
  .sla-circle svg{transform:rotate(-90deg)}
  .sla-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}
  .sla-pct{font-size:20px;font-weight:600}
  .sla-label-txt{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
  .sla-details{flex:1;padding-left:1.5rem}
  .sla-row{display:flex;justify-content:space-between;font-size:13px;padding:.4rem 0;border-bottom:1px solid var(--border)}
  .sla-row:last-child{border-bottom:none}

  /* ALERTS */
  .alert{display:flex;align-items:flex-start;gap:.7rem;padding:.8rem 1rem;
      border-radius:8px;margin-bottom:.6rem;font-size:13px}
  .alert:last-child{margin-bottom:0}
  .alert-warn{background:rgba(255,179,71,.1);border:1px solid rgba(255,179,71,.3);color:var(--yellow)}
  .alert-ok{background:rgba(0,212,170,.1);border:1px solid rgba(0,212,170,.3);color:var(--green)}
  .alert-icon{font-size:14px;margin-top:1px;flex-shrink:0}
  .alert-text b{display:block;font-weight:600;margin-bottom:2px}
  .alert-time{font-size:11px;opacity:.7}
  
  .refresh-note{font-size:11px;color:var(--muted);text-align:right;margin-top:.5rem}
  .tag{display:inline-block;font-size:10px;padding:2px 7px;border-radius:4px;font-family:monospace;
       background:var(--surface2);color:var(--muted);border:1px solid var(--border);margin-left:4px}
</style>
</head>
<body>

<nav>
  <div class="nav-brand">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
    </svg>
    CloudWatch <span style="color:var(--muted);font-weight:400;font-size:14px;margin-left:4px">/ OpenStack Monitor</span>
  </div>
  <div style="display:flex;align-items:center;gap:1.5rem">
    <div class="nav-status"><div class="pulse"></div><span>Live</span></div>
    <div class="nav-time" id="clock">--:--:--</div>
  </div>
</nav>

<main>
  <div class="page-title">Infrastructure Overview — OpenStack (DevStack)</div>

  <!-- STAT CARDS -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">CPU Usage</div>
      <div class="stat-value c-blue" id="cpu-val">--%</div>
      <div class="stat-sub" id="cpu-cores">-- cores</div>
      <div class="stat-bar"><div class="stat-bar-fill" id="cpu-bar" style="background:var(--blue);width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Memory</div>
      <div class="stat-value c-accent" id="ram-val">--%</div>
      <div class="stat-sub" id="ram-sub">-- / -- GB</div>
      <div class="stat-bar"><div class="stat-bar-fill" id="ram-bar" style="background:var(--accent);width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Disk (root)</div>
      <div class="stat-value c-yellow" id="disk-val">--%</div>
      <div class="stat-sub" id="disk-sub">-- / -- GB</div>
      <div class="stat-bar"><div class="stat-bar-fill" id="disk-bar" style="background:var(--yellow);width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Uptime</div>
      <div class="stat-value c-green" id="uptime-val" style="font-size:20px;padding-top:4px">--h --m</div>
      <div class="stat-sub" id="uptime-sub">App started --</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Instances</div>
      <div class="stat-value c-green" id="inst-count">--</div>
      <div class="stat-sub" id="inst-active">-- active</div>
      <div class="stat-bar"><div class="stat-bar-fill" id="inst-bar" style="background:var(--green);width:0%"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Network I/O</div>
      <div class="stat-value c-accent2" id="net-val" style="font-size:18px;padding-top:4px">-- MB/s</div>
      <div class="stat-sub" id="net-sub">↑ -- ↓ --</div>
    </div>
  </div>

  <!-- CHARTS ROW -->
  <div class="content-grid" style="margin-bottom:1rem">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">CPU History</span>
        <span class="panel-badge badge-blue">60s window</span>
      </div>
      <div class="chart-wrap"><canvas id="cpuChart"></canvas></div>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Memory History</span>
        <span class="panel-badge badge-blue">60s window</span>
      </div>
      <div class="chart-wrap"><canvas id="ramChart"></canvas></div>
    </div>
  </div>

  <!-- INSTANCES + DISK -->
  <div class="content-grid wide" style="margin-bottom:1rem">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">OpenStack Instances</span>
        <span class="panel-badge badge-green" id="nova-badge">Nova</span>
      </div>
      <table class="instance-table">
        <thead><tr>
          <th>Name</th><th>Status</th><th>Flavor</th><th>IP</th><th>Age</th>
        </tr></thead>
        <tbody id="inst-tbody">
          <tr><td colspan="5" style="color:var(--muted);padding:1rem 0">Loading instances...</td></tr>
        </tbody>
      </table>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Disk Partitions</span>
        <span class="panel-badge badge-yellow">Storage</span>
      </div>
      <div id="disk-list">Loading...</div>
      <div style="margin-top:1.5rem">
        <div class="panel-header" style="margin-bottom:.8rem">
          <span class="panel-title">Network I/O</span>
          <span class="panel-badge badge-blue">Cumulative</span>
        </div>
        <div class="net-grid">
          <div class="net-item">
            <div class="net-dir">Sent</div>
            <div class="net-val c-accent2" id="net-sent">--</div>
            <div class="net-sub">total transferred</div>
          </div>
          <div class="net-item">
            <div class="net-dir">Received</div>
            <div class="net-val c-blue" id="net-recv">--</div>
            <div class="net-sub">total received</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLA + PROCESSES + SYSINFO -->
  <div class="content-grid" style="margin-bottom:1rem">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">SLA Status</span>
        <span class="panel-badge badge-green" id="sla-badge">Evaluating</span>
      </div>
      <div class="sla-wrap">
        <div class="sla-circle">
          <svg width="110" height="110" viewBox="0 0 110 110">
            <circle cx="55" cy="55" r="45" fill="none" stroke="var(--border)" stroke-width="8"/>
            <circle cx="55" cy="55" r="45" fill="none" stroke="var(--green)" stroke-width="8"
              stroke-linecap="round" stroke-dasharray="283" id="sla-arc" stroke-dashoffset="283"/>
          </svg>
          <div class="sla-center">
            <div class="sla-pct c-green" id="sla-pct">--%</div>
            <div class="sla-label-txt">avail.</div>
          </div>
        </div>
        <div class="sla-details">
          <div class="sla-row"><span style="color:var(--muted)">Target</span><span>99.5%</span></div>
          <div class="sla-row"><span style="color:var(--muted)">Period</span><span>Daily</span></div>
          <div class="sla-row"><span style="color:var(--muted)">Check interval</span><span>5 min</span></div>
          <div class="sla-row"><span style="color:var(--muted)">Result</span><span id="sla-result" class="c-green">--</span></div>
          <div class="sla-row"><span style="color:var(--muted)">Last check</span><span id="sla-last" style="font-family:monospace;font-size:11px">--</span></div>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Top Processes</span>
        <span class="panel-badge badge-blue">by CPU</span>
      </div>
      <div id="proc-list">Loading...</div>
    </div>
  </div>

  <!-- SYSTEM INFO -->
  <div class="content-grid" style="margin-bottom:1rem">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Host System</span>
        <span class="panel-badge badge-blue">IaaS Layer</span>
      </div>
      <div id="sys-info">Loading...</div>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Service Alerts</span>
        <span class="panel-badge badge-green" id="alert-badge">Monitoring</span>
      </div>
      <div id="alerts-list">Checking services...</div>
    </div>
  </div>

  <div class="refresh-note" id="last-refresh">Auto-refresh every 5s</div>
</main>

<script>
const cpuData = Array(60).fill(0), ramData = Array(60).fill(0);
const labels = Array(60).fill('');

function mkChart(id, data, color, label){
  return new Chart(document.getElementById(id), {
    type:'line',
    data:{
      labels,
      datasets:[{label, data, borderColor:color, backgroundColor:color+'22',
        borderWidth:2, pointRadius:0, fill:true, tension:.35}]
    },
    options:{
      responsive:true, maintainAspectRatio:false, animation:{duration:300},
      plugins:{legend:{display:false}},
      scales:{
        x:{display:false},
        y:{min:0,max:100,grid:{color:'rgba(255,255,255,.05)'},
           ticks:{color:'#7b82a8',font:{size:10},callback:v=>v+'%'}}
      }
    }
  });
}

const cpuChart = mkChart('cpuChart', cpuData, '#4da6ff', 'CPU %');
const ramChart = mkChart('ramChart', ramData, '#6c63ff', 'RAM %');

function colorPct(p){return p>85?'var(--red)':p>60?'var(--yellow)':'var(--green)'}

function fmtBytes(b){
  if(b>=1e9)return(b/1e9).toFixed(2)+' GB';
  if(b>=1e6)return(b/1e6).toFixed(1)+' MB';
  return(b/1e3).toFixed(0)+' KB';
}

function fmtUptime(s){
  const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);
  if(d>0)return d+'d '+h+'h '+m+'m';
  return h+'h '+m+'m';
}

async function refresh(){
  try{
    const r=await fetch('/api/metrics');
    const d=await r.json();

    // Clock
    document.getElementById('clock').textContent=new Date().toLocaleTimeString();

    // CPU
    const cpu=d.cpu.percent;
    document.getElementById('cpu-val').textContent=cpu+'%';
    document.getElementById('cpu-val').style.color=colorPct(cpu);
    document.getElementById('cpu-cores').textContent=d.cpu.cores+' cores / '+d.cpu.threads+' threads';
    document.getElementById('cpu-bar').style.width=cpu+'%';
    document.getElementById('cpu-bar').style.background=colorPct(cpu);
    cpuData.push(cpu); cpuData.shift();
    cpuChart.update();

    // RAM
    const ram=d.ram.percent;
    document.getElementById('ram-val').textContent=ram+'%';
    document.getElementById('ram-val').style.color=colorPct(ram);
    document.getElementById('ram-sub').textContent=
      d.ram.used_gb.toFixed(1)+' / '+d.ram.total_gb.toFixed(1)+' GB';
    document.getElementById('ram-bar').style.width=ram+'%';
    ramData.push(ram); ramData.shift();
    ramChart.update();

    // Disk top
    const dk=d.disk[0];
    if(dk){
      document.getElementById('disk-val').textContent=dk.percent+'%';
      document.getElementById('disk-val').style.color=colorPct(dk.percent);
      document.getElementById('disk-sub').textContent=
        dk.used_gb.toFixed(1)+' / '+dk.total_gb.toFixed(1)+' GB';
      document.getElementById('disk-bar').style.width=dk.percent+'%';
      document.getElementById('disk-bar').style.background=colorPct(dk.percent);
    }

    // All disks
    document.getElementById('disk-list').innerHTML=d.disk.map(dk=>`
      <div class="disk-row">
        <div class="disk-info">
          <span class="disk-name">${dk.mountpoint}<span class="tag">${dk.fstype}</span></span>
          <span class="disk-pct">${dk.used_gb.toFixed(1)}/${dk.total_gb.toFixed(1)} GB</span>
        </div>
        <div class="disk-bar"><div class="disk-fill" style="width:${dk.percent}%;background:${colorPct(dk.percent)}"></div></div>
      </div>`).join('');

    // Uptime
    document.getElementById('uptime-val').textContent=fmtUptime(d.system.uptime_seconds);
    document.getElementById('uptime-sub').textContent='App: '+fmtUptime(d.system.app_uptime);

    // Network
    document.getElementById('net-sent').textContent=fmtBytes(d.network.bytes_sent);
    document.getElementById('net-recv').textContent=fmtBytes(d.network.bytes_recv);
    document.getElementById('net-val').textContent=fmtBytes(d.network.bytes_recv+d.network.bytes_sent);
    document.getElementById('net-sub').textContent=
      '↑ '+fmtBytes(d.network.bytes_sent)+' ↓ '+fmtBytes(d.network.bytes_recv);

    // Instances
    const insts=d.instances;
    const active=insts.filter(i=>i.status==='ACTIVE').length;
    document.getElementById('inst-count').textContent=insts.length;
    document.getElementById('inst-active').textContent=active+' active';
    document.getElementById('inst-bar').style.width=(insts.length?active/insts.length*100:0)+'%';

    if(insts.length===0){
      document.getElementById('inst-tbody').innerHTML=
        '<tr><td colspan="5" style="color:var(--muted);padding:1rem 0">No instances found. Check OpenStack credentials.</td></tr>';
    } else {
      document.getElementById('inst-tbody').innerHTML=insts.map(i=>{
        const dot=i.status==='ACTIVE'?'dot-green':i.status==='SHUTOFF'?'dot-red':'dot-yellow';
        const sc=i.status==='ACTIVE'?'c-green':i.status==='SHUTOFF'?'c-red':'c-yellow';
        return `<tr>
          <td><div class="inst-name">${i.name}</div><div class="inst-id">${i.id.slice(0,8)}...</div></td>
          <td><span class="status-dot ${dot}"></span><span class="${sc}">${i.status}</span></td>
          <td><span class="tag">${i.flavor||'--'}</span></td>
          <td style="font-family:monospace;font-size:11px;color:var(--muted)">${i.ip||'--'}</td>
          <td style="color:var(--muted);font-size:12px">${i.age||'--'}</td>
        </tr>`;
      }).join('');
    }

    document.getElementById('nova-badge').textContent=insts.length+' total';

    // SLA
    const avail=d.sla.availability;
    const arc=document.getElementById('sla-arc');
    const circumference=283;
    arc.style.strokeDashoffset=circumference*(1-avail/100);
    arc.style.stroke=avail>=99.5?'var(--green)':avail>=95?'var(--yellow)':'var(--red)';
    document.getElementById('sla-pct').textContent=avail.toFixed(1)+'%';
    document.getElementById('sla-pct').style.color=avail>=99.5?'var(--green)':avail>=95?'var(--yellow)':'var(--red)';
    const ok=avail>=99.5;
    document.getElementById('sla-result').textContent=ok?'COMPLIANT':'BREACH';
    document.getElementById('sla-result').className=ok?'c-green':'c-red';
    document.getElementById('sla-badge').textContent=ok?'Compliant':'Breach';
    document.getElementById('sla-badge').className='panel-badge '+(ok?'badge-green':'badge-red');
    document.getElementById('sla-last').textContent=new Date().toLocaleTimeString();

    // Processes
    document.getElementById('proc-list').innerHTML=d.processes.map(p=>`
      <div class="proc-row">
        <span class="proc-name">${p.name.slice(0,22)}</span>
        <span style="display:flex;gap:.5rem;align-items:center">
          <span style="width:60px;height:4px;background:var(--border);border-radius:2px;display:inline-block;overflow:hidden">
            <span style="display:block;height:100%;width:${Math.min(p.cpu,100)}%;background:${colorPct(p.cpu)}"></span>
          </span>
          <span class="proc-cpu">${p.cpu.toFixed(1)}%</span>
          <span class="proc-cpu">${fmtBytes(p.mem*1024*1024)}</span>
        </span>
      </div>`).join('');

    // System info
    document.getElementById('sys-info').innerHTML=[
      ['Hostname', d.system.hostname],
      ['OS', d.system.os],
      ['Kernel', d.system.kernel],
      ['Python', d.system.python],
      ['CPU Model', d.system.cpu_model],
      ['Load Avg', d.system.load_avg],
      ['Boot Time', d.system.boot_time],
      ['Platform', 'OpenStack Nova / DevStack'],
    ].map(([k,v])=>`
      <div class="info-row">
        <span class="info-key">${k}</span>
        <span class="info-val">${v}</span>
      </div>`).join('');

    // Alerts
    const alerts=d.alerts;
    document.getElementById('alerts-list').innerHTML=alerts.length?
      alerts.map(a=>`
        <div class="alert alert-${a.level}">
          <span class="alert-icon">${a.level==='warn'?'▲':'✓'}</span>
          <div class="alert-text"><b>${a.title}</b>${a.msg}
          <div class="alert-time">${a.time}</div></div>
        </div>`).join('')
      :'<div class="alert alert-ok"><span class="alert-icon">✓</span><div class="alert-text"><b>All clear</b>No alerts at this time.</div></div>';

    document.getElementById('alert-badge').textContent=alerts.filter(a=>a.level==='warn').length+' warnings';
    document.getElementById('alert-badge').className='panel-badge '+(alerts.some(a=>a.level==='warn')?'badge-yellow':'badge-green');

    document.getElementById('last-refresh').textContent='Last refresh: '+new Date().toLocaleTimeString()+' — auto-refresh every 5s';

  }catch(e){console.error('Metrics error:',e)}
}

refresh();
setInterval(refresh, 5000);
setInterval(()=>document.getElementById('clock').textContent=new Date().toLocaleTimeString(), 1000);
</script>
</body>
</html>
"""

def get_openstack_instances():
    """Fetch instances via OpenStack CLI."""
    try:
        env = os.environ.copy()
        result = subprocess.run(
            ['openstack', 'server', 'list', '-f', 'json', '--all-projects'],
            capture_output=True, text=True, env=env, timeout=10
        )
        if result.returncode != 0:
            return []
        instances = json.loads(result.stdout)
        now = datetime.datetime.utcnow()
        out = []
        for i in instances:
            created_raw = i.get('Created') or i.get('created_at', '')
            age = '--'
            if created_raw:
                try:
                    created = datetime.datetime.strptime(created_raw[:19], '%Y-%m-%dT%H:%M:%S')
                    diff = now - created
                    h = int(diff.total_seconds() // 3600)
                    m = int((diff.total_seconds() % 3600) // 60)
                    age = f"{h}h {m}m" if h > 0 else f"{m}m"
                except:
                    pass
            networks = i.get('Networks', '')
            ip = '--'
            if networks:
                parts = str(networks).split('=')
                if len(parts) > 1:
                    ip = parts[-1].split(',')[0].strip()
            out.append({
                'id': i.get('ID', ''),
                'name': i.get('Name', ''),
                'status': i.get('Status', 'UNKNOWN'),
                'flavor': i.get('Flavor', '--'),
                'ip': ip,
                'age': age
            })
        return out
    except Exception:
        return []

def get_top_processes(n=7):
    procs = []
    for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
        try:
            procs.append({
                'name': p.info['name'],
                'cpu': round(p.info['cpu_percent'] or 0, 1),
                'mem': round((p.info['memory_info'].rss if p.info['memory_info'] else 0) / (1024*1024), 1)
            })
        except:
            pass
    return sorted(procs, key=lambda x: x['cpu'], reverse=True)[:n]

def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total_gb': round(usage.total / 1e9, 1),
                'used_gb': round(usage.used / 1e9, 1),
                'free_gb': round(usage.free / 1e9, 1),
                'percent': usage.percent
            })
        except:
            pass
    return disks[:4]

def get_alerts(cpu, ram, disk_pct):
    alerts = []
    now = datetime.datetime.now().strftime('%H:%M:%S')
    if cpu > 85:
        alerts.append({'level':'warn','title':'High CPU','msg':f'CPU at {cpu}% — above 85% threshold','time':now})
    if ram > 85:
        alerts.append({'level':'warn','title':'High Memory','msg':f'RAM at {ram}% — consider scaling','time':now})
    if disk_pct > 80:
        alerts.append({'level':'warn','title':'Disk Space','msg':f'Root disk at {disk_pct}% — low space','time':now})
    if not alerts:
        alerts.append({'level':'ok','title':'All systems normal','msg':' — operating within thresholds','time':now})
    return alerts

def calc_sla(instances):
    total = len(instances)
    if total == 0:
        return 100.0
    active = sum(1 for i in instances if i['status'] == 'ACTIVE')
    return round((active / total) * 100, 2)

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/metrics')
def metrics():
    cpu_pct = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    net = psutil.net_io_counters()
    disks = get_disk_info()
    instances = get_openstack_instances()
    processes = get_top_processes()
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    load = os.getloadavg()

    disk_pct = disks[0]['percent'] if disks else 0
    alerts = get_alerts(cpu_pct, ram.percent, disk_pct)
    sla_avail = calc_sla(instances)

    try:
        cpu_model = open('/proc/cpuinfo').read().split('model name')[1].split('\n')[0].replace('\t:','').strip()[:40]
    except:
        cpu_model = platform.processor()[:40] or 'Unknown'

    return jsonify({
        'cpu': {
            'percent': round(cpu_pct, 1),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True)
        },
        'ram': {
            'percent': round(ram.percent, 1),
            'total_gb': round(ram.total / 1e9, 2),
            'used_gb': round(ram.used / 1e9, 2),
            'available_gb': round(ram.available / 1e9, 2)
        },
        'disk': disks,
        'network': {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        },
        'system': {
            'hostname': platform.node(),
            'os': platform.system() + ' ' + platform.release(),
            'kernel': platform.release(),
            'python': platform.python_version(),
            'cpu_model': cpu_model,
            'load_avg': f"{load[0]:.2f} {load[1]:.2f} {load[2]:.2f}",
            'boot_time': boot.strftime('%Y-%m-%d %H:%M'),
            'uptime_seconds': int(time.time() - psutil.boot_time()),
            'app_uptime': int(time.time() - START_TIME)
        },
        'instances': instances,
        'processes': processes,
        'alerts': alerts,
        'sla': {
            'availability': sla_avail,
            'target': 99.5,
            'met': sla_avail >= 99.5
        },
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

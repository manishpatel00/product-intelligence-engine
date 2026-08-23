#!/usr/bin/env python3
"""
Unilog Product Intelligence Engine — live demo server
=====================================================
Zero-dependency web UI (stdlib http.server). Paste or pick a raw catalogue row
and watch it explode into the standardised record: the five description formats,
resolved brand/manufacturer/classpath, normalised attributes with approved UOMs,
a per-field confidence gauge and a human-review queue with specific reasons.

Run:   python3 app/server.py            # then open http://localhost:8000
       PORT=9000 python3 app/server.py
Set ANTHROPIC_API_KEY to enable the Claude path; otherwise the deterministic
fallback runs (clearly badged in the UI).
"""
from __future__ import annotations
import csv
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import process_row
from src.schema import DELIVERY_HEADERS
from src import llm_client

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_presets():
    presets = []
    # a couple of interesting real rows + the anomaly dishwasher
    gt = os.path.join(ROOT, "data", "ground_truth_input.csv")
    samp = os.path.join(ROOT, "data", "input_sample_1000.csv")
    try:
        for r in list(csv.DictReader(open(gt)))[:2]:
            presets.append(r)
    except Exception:
        pass
    try:
        rows = list(csv.DictReader(open(samp)))
        for r in rows[:6]:
            presets.append(r)
    except Exception:
        pass
    return presets


PRESETS = load_presets()

PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Unilog Product Intelligence Engine</title>
<style>
:root{--bg:#0b0f17;--panel:#141b28;--panel2:#1b2434;--line:#26324a;--txt:#e7edf7;--mut:#8ea0bd;--acc:#4da3ff;--good:#37d39b;--warn:#ffb454;--bad:#ff6b6b}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial;background:var(--bg);color:var(--txt)}
header{padding:18px 26px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;background:linear-gradient(90deg,#111826,#0b0f17)}
header h1{font-size:18px;margin:0;font-weight:650;letter-spacing:.2px}
.badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line)}
.badge.on{color:var(--good);border-color:#1f5c48;background:#0f2a22}
.badge.off{color:var(--warn);border-color:#5c4a1f;background:#2a220f}
.wrap{display:grid;grid-template-columns:380px 1fr;gap:0;min-height:calc(100vh - 59px)}
.left{padding:20px;border-right:1px solid var(--line);background:var(--panel)}
.right{padding:22px;overflow:auto}
label{display:block;font-size:12px;color:var(--mut);margin:12px 0 4px}
input,textarea,select{width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:9px 10px;font:inherit}
textarea{min-height:64px;resize:vertical}
button{margin-top:16px;width:100%;background:var(--acc);color:#04121f;border:0;border-radius:9px;padding:12px;font-weight:700;font-size:15px;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
.hint{font-size:12px;color:var(--mut);margin-top:8px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:16px}
.card h3{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.kv{display:grid;grid-template-columns:150px 1fr;gap:6px 12px}
.kv .k{color:var(--mut)}
.desc{border-left:3px solid var(--acc);padding:8px 12px;margin:8px 0;background:var(--panel2);border-radius:0 8px 8px 0}
.desc .lab{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px}
.desc .val{font-size:14px}
.desc .meta{font-size:11px;color:var(--mut);margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:500;font-size:11px;text-transform:uppercase}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;background:#12324a;color:#8fd0ff}
.gauge{height:10px;border-radius:6px;background:#26324a;overflow:hidden}
.gauge>i{display:block;height:100%}
.flag{background:#2a1414;border:1px solid #5c2626;color:#ffc2c2;border-radius:8px;padding:8px 12px;margin:6px 0;font-size:13px}
.ok{color:var(--good)} .muted{color:var(--mut)}
.grid252{columns:2;font-size:12px}
.grid252 div{break-inside:avoid;padding:2px 0;border-bottom:1px solid #1b2434}
.grid252 .c{color:var(--mut)}
details summary{cursor:pointer;color:var(--acc);font-size:13px}
.spin{display:inline-block;width:14px;height:14px;border:2px solid #04121f;border-top-color:transparent;border-radius:50%;animation:s .7s linear infinite;vertical-align:-2px}
@keyframes s{to{transform:rotate(360deg)}}
</style></head><body>
<header>
  <h1>⚙️ Unilog Product Intelligence Engine</h1>
  <span class="badge %AI_CLASS%">%AI_LABEL%</span>
  <span class="muted" style="margin-left:auto;font-size:12px">messy row → 252-column commerce record · confidence-scored · human-in-the-loop</span>
</header>
<div class=wrap>
  <div class=left>
    <label>Load a sample row</label>
    <select id=preset onchange="fillPreset()"><option value="">— choose —</option>%PRESETS%</select>
    <label>Mfg_Part_Num (MPN)</label><input id=mpn placeholder="e.g. PDSH4816AF">
    <label>Part_Desc (cryptic description)</label><textarea id=desc placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only"></textarea>
    <label>Part_Manuf</label><input id=manuf placeholder="e.g. Appliance Dealers Cooperative (APPDE)">
    <label>E1_Brand / Unilog_Brand / DIB_Brand</label><input id=brands placeholder="often -- Unbranded -- (placeholders auto-filtered)">
    <button id=go onclick="enrich()">Enrich →</button>
    <div class=hint>Runs the real 9-stage pipeline. With an API key set, Claude classifies &amp; extracts; a deterministic gate then enforces UOM/fraction/char-limit rules and flags low-confidence fields.</div>
  </div>
  <div class=right id=out>
    <div class=card><h3>Output</h3><div class=muted>Pick a sample row or type one on the left, then press <b>Enrich</b>. You'll see the five description formats, resolved identity, normalised attributes, confidence and the review queue.</div></div>
  </div>
</div>
<script>
const PRE = %PRESETS_JSON%;
function fillPreset(){const i=document.getElementById('preset').value;if(i==='')return;const p=PRE[i];
 document.getElementById('mpn').value=p.Mfg_Part_Num||'';document.getElementById('desc').value=p.Part_Desc||'';
 document.getElementById('manuf').value=p.Part_Manuf||'';
 document.getElementById('brands').value=[p.E1_Brand,p.Unilog_Brand,p.DIB_Brand].filter(Boolean).join(' | ');}
function bar(v){const c=v>=.75?'var(--good)':v>=.5?'var(--warn)':'var(--bad)';return `<div class=gauge><i style="width:${Math.round(v*100)}%;background:${c}"></i></div>`}
async function enrich(){
 const btn=document.getElementById('go');btn.disabled=true;btn.innerHTML='<span class=spin></span> Enriching…';
 const brands=(document.getElementById('brands').value||'').split('|').map(s=>s.trim());
 const row={Mfg_Part_Num:document.getElementById('mpn').value,Part_Desc:document.getElementById('desc').value,
  Part_Manuf:document.getElementById('manuf').value,E1_Brand:brands[0]||'',Unilog_Brand:brands[1]||'',DIB_Brand:brands[2]||''};
 let r;try{r=await (await fetch('/api/enrich',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({row})})).json();}
 catch(e){document.getElementById('out').innerHTML='<div class=card><h3>Error</h3><div class=flag>'+e+'</div></div>';btn.disabled=false;btn.textContent='Enrich →';return;}
 render(r);btn.disabled=false;btn.textContent='Enrich →';
}
function render(r){
 const rec=r.record,qa=r.qa;
 const D=(lab,key,meta)=>`<div class=desc><div class=lab>${lab}</div><div class=val>${(rec[key]||'<span class=muted>(empty)</span>')}</div>${meta?`<div class=meta>${meta}</div>`:''}</div>`;
 let attrs='';for(let i=1;i<=50;i++){const l=rec['ATTRIBUTE_LABEL '+i];if(!l)continue;
   attrs+=`<tr><td>${l}</td><td><b>${rec['ATTRIBUTE_VALUE '+i]||''}</b></td><td><span class=pill>${rec['ATTRIBUTE_UOM '+i]||'—'}</span></td></tr>`;}
 let flags=qa.review_reasons.map(x=>`<div class=flag>⚑ ${x}</div>`).join('')||'<div class=ok>✓ No blocking issues — auto-shippable.</div>';
 let fc='';for(const[k,v]of Object.entries(qa.field_confidence)){fc+=`<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;font-size:12px"><span class=muted>${k}</span><span>${v}</span></div>${bar(v)}</div>`}
 let g252='';let filled=0;for(const h of Object.keys(rec)){if(rec[h])filled++;g252+=`<div><span class=c>${h}:</span> ${rec[h]||''}</div>`}
 document.getElementById('out').innerHTML=`
  <div class=card><h3>Identity &amp; Taxonomy</h3><div class=kv>
    <div class=k>Brand</div><div><b>${rec.BRAND_NAME||'—'}</b></div>
    <div class=k>Manufacturer</div><div>${rec.MANUFACTURER_NAME||'<span class=muted>(withheld/flagged)</span>'}</div>
    <div class=k>MPN</div><div>${rec.MANUFACTURER_PART_NUMBER||'—'}</div>
    <div class=k>Product</div><div>${rec['Product Name']||'—'}</div>
    <div class=k>Classpath</div><div>${rec.Classpath||'—'}</div>
    <div class=k>Dept / Class / Fine</div><div>${[rec.Dept,rec.Class,rec.Fine].filter(Boolean).join(' › ')||'—'}</div>
    <div class=k>MFR URL</div><div>${rec['MFR URL']?`<a href="${rec['MFR URL']}" target=_blank style=color:var(--acc)>${rec['MFR URL']}</a>`:'—'}</div>
  </div></div>
  <div class=card><h3>The same product, five formats</h3>
    ${D('Invoice desc (≤40, CAPS)','INVOICE_DESC',`len ${rec.INVOICE_DESC.length}/40`)}
    ${D('Mobile desc (60–80)','MOBILE_DESC',`len ${rec.MOBILE_DESC.length}`)}
    ${D('Short desc / Product title','SHORT_DESC')}
    ${D('Long description','LONG_DESC1')}
    ${D('Marketing','MARKETING_DESCRIPTION')}
  </div>
  <div class=card><h3>Attributes (normalised · approved UOM)</h3>
    <table><tr><th>Label</th><th>Value</th><th>UOM</th></tr>${attrs||'<tr><td class=muted colspan=3>none extracted</td></tr>'}</table></div>
  <div class=card><h3>Confidence &amp; review queue</h3>
    <div style="display:flex;gap:20px;align-items:center;margin-bottom:10px">
      <div style="font-size:34px;font-weight:800;color:${qa.overall_confidence>=.6?'var(--good)':'var(--warn)'}">${qa.overall_confidence}</div>
      <div><div>${qa.needs_human_review?'<span style=color:var(--warn)>⚑ Routed to human review</span>':'<span class=ok>✓ Auto-shippable</span>'}</div>
      <div class=muted style=font-size:12px>engine: ${qa.ai_used?'Claude AI + rule gate':'deterministic fallback'} · ${qa.n_attributes} attributes</div></div></div>
    ${fc}<div style=margin-top:10px>${flags}</div></div>
  <div class=card><h3>Full 252-column record <span class=muted style=text-transform:none>· ${filled} populated</span>
    <button onclick="dl('csv')" style="width:auto;margin:0 0 0 10px;padding:5px 12px;font-size:12px">⬇ CSV</button>
    <button onclick="dl('json')" style="width:auto;margin:0 0 0 6px;padding:5px 12px;font-size:12px;background:#2a3346;color:var(--txt)">⬇ JSON</button></h3>
    <details><summary>expand all 252 delivery-format columns</summary><div class=grid252 style=margin-top:10px>${g252}</div></details></div>`;
 window.__rec=rec;
}
function dl(kind){
 const rec=window.__rec; if(!rec)return;
 const mpn=(rec.Mfg_Part_Num||'record').replace(/[^A-Za-z0-9_-]/g,'_');
 let blob,name;
 if(kind==='json'){blob=new Blob([JSON.stringify(rec,null,2)],{type:'application/json'});name=mpn+'.json';}
 else{const hs=Object.keys(rec);const esc=v=>{v=(v==null?'':String(v));return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  const csv=hs.map(esc).join(',')+'\n'+hs.map(h=>esc(rec[h])).join(',')+'\n';
  blob=new Blob([csv],{type:'text/csv'});name=mpn+'_enriched.csv';}
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();URL.revokeObjectURL(a.href);
}
</script></body></html>"""


# ---------------------------------------------------------------------------
# Pure request core (no sockets) — kept separate so it is unit-testable without
# binding a port. The socket Handler below is a thin transport over these.
# ---------------------------------------------------------------------------
def render_index() -> str:
    ai_on = llm_client.have_api_key()
    opts = "".join(
        f'<option value="{i}">{(p.get("Mfg_Part_Num") or "row")[:18]} — {(p.get("Part_Desc") or "")[:34]}</option>'
        for i, p in enumerate(PRESETS))
    return (PAGE.replace("%PRESETS%", opts)
                .replace("%PRESETS_JSON%", json.dumps(PRESETS))
                .replace("%AI_CLASS%", "on" if ai_on else "off")
                .replace("%AI_LABEL%", ("● Claude AI: " + llm_client.DEFAULT_MODEL) if ai_on
                         else "● Deterministic fallback (set ANTHROPIC_API_KEY for AI)"))


def handle_enrich(raw_body: str):
    """raw JSON body -> (status_code, json_string). Never raises."""
    try:
        row = json.loads(raw_body or "{}").get("row", {}) or {}
        rec, qa = process_row(row)
        return 200, json.dumps({"record": rec, "qa": qa})
    except Exception as e:
        return 500, json.dumps({"error": str(e)})


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, render_index(), "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        if self.path == "/api/enrich":
            code, body = handle_enrich(raw)
            self._send(code, body)
        else:
            self._send(404, json.dumps({"error": "not found"}))


def main():
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 so tunnels/containers can reach it
    srv = ThreadingHTTPServer((host, port), Handler)
    ai = "ON (" + llm_client.DEFAULT_MODEL + ")" if llm_client.have_api_key() else "OFF (deterministic fallback)"
    print(f"Unilog Product Intelligence Engine — demo on http://localhost:{port}  | AI path: {ai}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()

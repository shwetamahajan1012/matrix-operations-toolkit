
import json
import sys
import threading
import time
import tracemalloc
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def read_matrix(name):
    r = int(input(f"Rows of {name}: "))
    c = int(input(f"Cols of {name}: "))
    print(f"Enter {name} row by row (space separated):")
    m = [list(map(float, input().split())) for _ in range(r)]
    if any(len(row) != c for row in m):
        raise ValueError("Each row must have exactly the given number of columns")
    return m


def add(a, b):
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("Addition needs both matrices to have the same size")
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def multiply(a, b):
    if len(a[0]) != len(b):
        raise ValueError("Multiplication needs cols of A == rows of B")
    res = [[0] * len(b[0]) for _ in range(len(a))]
    for i in range(len(a)):
        for j in range(len(b[0])):
            for k in range(len(b)):
                res[i][j] += a[i][k] * b[k][j]
    return res


def transpose(a):
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def show(m, title):
    print(f"\n{title}")
    for row in m:
        print("  ".join(f"{x:8.2f}" for x in row))


def memory_of(m):
    """Bytes used by the 2D list: outer list + each row list + each element."""
    total = sys.getsizeof(m)
    for row in m:
        total += sys.getsizeof(row) + sum(sys.getsizeof(x) for x in row)
    return total


def analyse(label, func, *mats):
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*mats)
    elapsed = (time.perf_counter() - t0) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    show(result, f"Result ({label})")
    print("\n--- Memory usage analysis ---")
    for name, m in zip("AB", mats):
        print(f"Matrix {name}: {len(m)}x{len(m[0])} -> {memory_of(m)} bytes")
    print(f"Result   : {len(result)}x{len(result[0])} -> {memory_of(result)} bytes")
    print(f"Peak memory while computing: {peak} bytes")
    print(f"Time taken: {elapsed:.4f} ms")


def main():
    while True:
        print("\n=== MATRIX TOOLKIT ===")
        print("1. Addition\n2. Multiplication\n3. Transpose\n4. Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                analyse("A + B", add, read_matrix("A"), read_matrix("B"))
            elif choice == "2":
                analyse("A x B", multiply, read_matrix("A"), read_matrix("B"))
            elif choice == "3":
                analyse("A transpose", transpose, read_matrix("A"))
            elif choice == "4":
                print("Bye!")
                break
            else:
                print("Invalid choice")
        except ValueError as e:
            print("Error:", e)


# ----------------------------------------------------------------------
# WEB UI (frontend) - served by the small Python server below
# ----------------------------------------------------------------------
PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Matrix Toolkit</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;800&family=JetBrains+Mono:wght@300;500;700&display=swap">
<style>
:root{--paper:#eef3f1;--grid:#d3dedb;--ink:#14302b;--soft:#4f6b65;--card:#fbfdfc;--hi:#f2c230;--teal:#0f766e;--err:#b42318;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);color-scheme:light}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0f1f1c;--grid:#1c3530;--ink:#e6f2ef;--soft:#92b1aa;--card:#162b27;--teal:#3fc3b4;--err:#ff8a7a;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0f1f1c;--grid:#1c3530;--ink:#e6f2ef;--soft:#92b1aa;--card:#162b27;--teal:#3fc3b4;--err:#ff8a7a;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background-color:var(--paper);color:var(--ink);font-family:'Bricolage Grotesque',system-ui,sans-serif;
background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:28px 28px}
main{max-width:1000px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:clamp(2.2rem,6vw,3.8rem);line-height:1;margin:0 0 8px;letter-spacing:-.03em;font-weight:800;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.br{font-family:'JetBrains Mono',monospace;font-weight:300;font-size:1.3em;color:var(--teal)}
.sub{color:var(--soft);max-width:60ch;margin:0 0 24px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.tab{border:2px solid var(--ink);background:var(--card);color:var(--ink);padding:10px 18px;border-radius:999px;font:inherit;font-weight:700;cursor:pointer}
.tab[aria-pressed="true"]{background:var(--hi);color:#14302b;box-shadow:3px 3px 0 var(--ink)}
.tab:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--teal);outline-offset:2px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.row{grid-template-columns:1fr}}
.card{background:var(--card);border:2px solid var(--ink);border-radius:14px;padding:16px;margin-bottom:16px}
.card h2{margin:0 0 10px;font-size:1.1rem}
.dims{display:flex;align-items:center;gap:8px;margin-bottom:12px;color:var(--soft);font-size:.9rem}
.dims input{width:56px;padding:6px;border:2px solid var(--grid);border-radius:8px;background:var(--paper);color:var(--ink);font:inherit;text-align:center}
.mx{display:inline-grid;gap:6px;padding:8px 14px;border-left:4px solid var(--ink);border-right:4px solid var(--ink);border-radius:10px;max-width:100%;overflow-x:auto}
.mx input,.cell{width:58px;height:42px;text-align:center;border:2px solid var(--grid);border-radius:8px;background:var(--paper);color:var(--ink);font:500 1rem 'JetBrains Mono',monospace}
.cell{display:flex;align-items:center;justify-content:center;border-color:var(--teal);background:transparent;font-weight:700}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 18px}
button.go{background:var(--ink);color:var(--paper);border:0;padding:12px 24px;border-radius:10px;font:inherit;font-weight:800;cursor:pointer}
button.alt{background:transparent;color:var(--ink);border:2px solid var(--ink);padding:10px 16px;border-radius:10px;font:inherit;font-weight:600;cursor:pointer}
#msg{color:var(--err);font-weight:600;min-height:1.4em}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px}
.stat{border-top:4px solid var(--hi);padding-top:6px}
.stat b{display:block;font:700 1.6rem 'JetBrains Mono',monospace}
.stat span{color:var(--soft);font-size:.85rem}
.bars{margin-top:16px;display:grid;gap:8px}
.bar{display:grid;grid-template-columns:120px 1fr 90px;align-items:center;gap:10px;font-size:.85rem}
.bar i{display:block;height:16px;border-radius:4px;background:var(--teal);min-width:3px}
.bar i.c{background:var(--hi)}
.bar em{font:normal .8rem 'JetBrains Mono',monospace;text-align:right}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin-top:10px}
td,th{padding:6px 8px;border-bottom:1px solid var(--grid);text-align:left}
td:last-child,th:last-child{text-align:right;font-family:'JetBrains Mono',monospace}
.note{color:var(--soft);font-size:.82rem;margin-top:8px}
</style>
</head>
<body>
<main>
<h1><span class="br">[</span>Matrix Toolkit<span class="br">]</span></h1>
<p class="sub">Add, multiply and transpose 2D arrays, then see exactly how much memory each matrix uses.</p>

<div class="tabs" role="group" aria-label="Operation">
<button class="tab" data-op="add" aria-pressed="true">Addition</button>
<button class="tab" data-op="mul" aria-pressed="false">Multiplication</button>
<button class="tab" data-op="tr" aria-pressed="false">Transpose</button>
</div>

<div class="row">
<section class="card"><h2>Matrix A</h2>
<div class="dims">Rows <input id="ar" type="number" min="1" max="6" value="2"> Cols <input id="ac" type="number" min="1" max="6" value="2"></div>
<div id="ga"></div></section>
<section class="card" id="bcard"><h2>Matrix B</h2>
<div class="dims">Rows <input id="br" type="number" min="1" max="6" value="2"> Cols <input id="bc" type="number" min="1" max="6" value="2"></div>
<div id="gb"></div></section>
</div>

<div class="actions">
<button class="go" id="calc">Calculate</button>
<button class="alt" id="rnd">Fill with random numbers</button>
<button class="alt" id="clr">Clear</button>
</div>
<div id="msg" role="alert"></div>

<section class="card" id="out" hidden>
<h2 id="rtitle">Result</h2>
<div id="gr"></div>
<div class="stats" id="stats"></div>
<div class="bars" id="bars"></div>
<table id="tbl"></table>
<p class="note">Computed by the Python backend: sizes come from sys.getsizeof (list headers, pointers and number objects) and peak usage from tracemalloc. The C column assumes a plain int[rows][cols] at 4 bytes per element.</p>
</section>
</main>

<script>
var op='add';
var $=function(i){return document.getElementById(i)};
function dims(p){return [Math.min(6,Math.max(1,+$(p+'r').value||1)),Math.min(6,Math.max(1,+$(p+'c').value||1))]}
function build(id,r,c){
  var old=readGrid(id),h='<div class="mx" style="grid-template-columns:repeat('+c+',auto)">';
  for(var i=0;i<r;i++)for(var j=0;j<c;j++){
    var v=(old[i]&&old[i][j]!==undefined)?old[i][j]:'0';
    h+='<input type="number" aria-label="Row '+(i+1)+' column '+(j+1)+'" data-i="'+i+'" data-j="'+j+'" value="'+v+'">';
  }
  $(id).innerHTML=h+'</div>';
}
function readGrid(id){
  var m=[];$(id).querySelectorAll('input').forEach(function(e){
    var i=+e.dataset.i,j=+e.dataset.j;(m[i]=m[i]||[])[j]=e.value});return m;
}
function nums(id){return readGrid(id).map(function(r){return r.map(function(x){return Number(x)||0})})}
function refresh(){
  var a=dims('a'),b=dims('b');
  if(op==='add'){$('br').value=a[0];$('bc').value=a[1];b=a}
  if(op==='mul'){$('br').value=a[1];b=[a[1],dims('b')[1]]}
  build('ga',a[0],a[1]);build('gb',b[0],b[1]);
}
function fmt(n){return n>=1024?(n/1024).toFixed(2)+' KB':n+' B'}
function show(m){
  $('gr').innerHTML='<div class="mx" style="grid-template-columns:repeat('+m[0].length+',auto)">'+
  m.map(function(r){return r.map(function(x){return '<div class="cell">'+(+x.toFixed(4))+'</div>'}).join('')}).join('')+'</div>';
}
async function calc(){
  $('msg').textContent='';
  var res=await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({op:op,A:nums('ga'),B:nums('gb')})});
  var d=await res.json();
  if(!res.ok){return $('msg').textContent=d.error}
  var items=d.items,max=Math.max.apply(null,items.map(function(x){return x.python_bytes}));
  var total=items.reduce(function(s,x){return s+x.python_bytes},0);
  $('out').hidden=false;
  $('rtitle').textContent={add:'A + B',mul:'A \u00d7 B',tr:'Transpose of A'}[op];
  show(d.result);
  $('stats').innerHTML='<div class="stat"><b>'+fmt(total)+'</b><span>total Python memory (sys.getsizeof)</span></div>'+
   '<div class="stat"><b>'+fmt(d.peak)+'</b><span>peak while computing (tracemalloc)</span></div>'+
   '<div class="stat"><b>'+d.time_ms+' ms</b><span>compute time</span></div>';
  $('bars').innerHTML=items.map(function(x,n){return '<div class="bar"><span>'+x.label+'</span><i class="'+(n===items.length-1?'c':'')+'" style="width:'+(x.python_bytes/max*100)+'%"></i><em>'+x.python_bytes+' B</em></div>'}).join('');
  $('tbl').innerHTML='<tr><th>Matrix</th><th>Size</th><th>Elements</th><th>Python bytes</th><th>C int bytes</th></tr>'+items.map(function(x){
    return '<tr><td>'+x.label+'</td><td>'+x.size+'</td><td>'+x.elements+'</td><td>'+x.python_bytes+'</td><td>'+x.c_bytes+'</td></tr>'}).join('');
  $('out').scrollIntoView({behavior:'smooth',block:'nearest'});
}
document.querySelectorAll('.tab').forEach(function(t){t.onclick=function(){
  op=t.dataset.op;document.querySelectorAll('.tab').forEach(function(x){x.setAttribute('aria-pressed',x===t)});
  $('bcard').style.display=op==='tr'?'none':'';$('out').hidden=true;$('msg').textContent='';refresh();}});
['ar','ac','br','bc'].forEach(function(id){$(id).onchange=refresh});
$('calc').onclick=calc;
$('clr').onclick=function(){document.querySelectorAll('.mx input').forEach(function(e){e.value=0})};
$('rnd').onclick=function(){document.querySelectorAll('.mx input').forEach(function(e){e.value=Math.floor(Math.random()*19)-9})};
refresh();
</script>
</body>
</html>
'''


def clean(m):
    """Convert incoming values to int when possible, else float."""
    return [[int(x) if float(x).is_integer() else float(x) for x in row] for row in m]


def info(label, m):
    rows, cols = len(m), len(m[0])
    return {"label": label, "size": f"{rows}x{cols}", "elements": rows * cols,
            "python_bytes": memory_of(m), "c_bytes": rows * cols * 4}


def calculate(data):
    op = data.get("op")
    a = clean(data["A"])
    b = clean(data["B"]) if op != "tr" else None
    tracemalloc.start()
    try:
        t0 = time.perf_counter()
        if op == "add":
            result = add(a, b)
        elif op == "mul":
            result = multiply(a, b)
        elif op == "tr":
            result = transpose(a)
        else:
            raise ValueError("Unknown operation")
        elapsed = (time.perf_counter() - t0) * 1000
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    items = [info("Matrix A", a)]
    if b:
        items.append(info("Matrix B", b))
    items.append(info("Result", result))
    return {"result": result, "items": items, "peak": peak, "time_ms": round(elapsed, 4)}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(size))
            out, code = calculate(data), 200
        except (ValueError, KeyError, TypeError, IndexError) as e:
            out, code = {"error": str(e)}, 400
        self._send(code, json.dumps(out).encode("utf-8"), "application/json")

    def log_message(self, *args):  # keep the terminal clean
        pass

def run_web():
    import os

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 10000))

    server = ThreadingHTTPServer((host, port), Handler)

    print(f"Matrix Toolkit running on port {port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


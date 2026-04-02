"""Generate a self-contained static HTML site from the skillich taxonomy.

Usage:
    python web/generate.py              # outputs web/index.html
    python web/generate.py out.html     # custom output path
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.taxonomy import TaxonomyLoader


def build_json(loader: TaxonomyLoader) -> str:
    """Serialize the full taxonomy to JSON for embedding in HTML."""
    data = {"functions": []}
    for func in loader.list_functions():
        f = {
            "id": func.id,
            "name": func.name,
            "description": func.description.strip(),
            "roles": [],
        }
        for role in loader.list_roles(func.id):
            r = {
                "id": role.id,
                "name": role.name,
                "also_known_as": role.also_known_as,
                "description": role.description.strip(),
                "ai_impact": {
                    "level": role.ai_impact.level,
                    "summary": role.ai_impact.summary.strip(),
                    "confidence": role.ai_impact.confidence,
                    "last_reviewed": role.ai_impact.last_reviewed,
                    "automating": role.ai_impact.automating,
                    "augmenting": role.ai_impact.augmenting,
                    "preserving": role.ai_impact.preserving,
                },
                "levels": [
                    {"id": lv.id, "name": lv.name, "years": lv.years_experience, "summary": lv.summary}
                    for lv in role.levels
                ],
                "skills": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category,
                        "description": s.description,
                        "ai_impact_rating": s.ai_impact_rating,
                        "ai_impact_detail": s.ai_impact_detail.strip(),
                        "proficiency": s.proficiency,
                    }
                    for s in role.skills
                ],
            }
            f["roles"].append(r)
        data["functions"].append(f)
    data["stats"] = loader.stats
    return json.dumps(data, ensure_ascii=False)


def load_resources() -> str:
    """Load the curated learning resources JSON."""
    res_path = Path(__file__).resolve().parent / "resources.json"
    if res_path.exists():
        with open(res_path, encoding="utf-8") as f:
            data = json.load(f)
        data.pop("_comment", None)
        return json.dumps(data, ensure_ascii=False)
    return "{}"


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="skillich: The open-source guide to thriving in the age of AI. Find your role, see which skills AI is automating, and get a personalized action plan.">
<title>skillich - Thrive in the Age of AI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;--text:#e0e0e8;--muted:#8888a0;--accent:#6c8cff;--green:#22c55e;--yellow:#eab308;--orange:#f97316;--red:#ef4444;--pink:#ec4899;--radius:10px}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.container{max-width:900px;margin:0 auto;padding:0 1rem}
button{cursor:pointer;font-family:inherit}
/* ---- HERO ---- */
.hero{text-align:center;padding:2.5rem 1rem 1.5rem;border-bottom:1px solid var(--border)}
.hero h1{font-size:2.2rem;margin-bottom:.4rem}
.hero .tagline{color:var(--muted);font-size:1.05rem;max-width:540px;margin:0 auto .8rem}
.hero .stats-row{display:flex;gap:1.5rem;justify-content:center;flex-wrap:wrap;margin:.8rem 0}
.stat{text-align:center}.stat-n{font-size:1.4rem;font-weight:700;color:var(--accent)}.stat-l{font-size:.75rem;color:var(--muted);text-transform:uppercase}
.hero .cta-row{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-top:1rem}
.btn{display:inline-block;padding:.65rem 1.4rem;border-radius:8px;font-weight:600;font-size:.95rem;border:none;transition:opacity .2s}
.btn-primary{background:var(--accent);color:#fff}.btn-primary:hover{opacity:.85;text-decoration:none}
.btn-secondary{background:var(--card);color:var(--text);border:1px solid var(--border)}.btn-secondary:hover{border-color:var(--accent);text-decoration:none}
/* ---- GUIDED FLOW ---- */
.wizard{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem;margin:1.5rem 0;display:none}
.wizard.active{display:block}
.wizard h2{font-size:1.2rem;margin-bottom:.75rem}
.wizard p{color:var(--muted);font-size:.9rem;margin-bottom:1rem}
.wizard-step{display:none}.wizard-step.active{display:block}
.role-search-input{width:100%;padding:.7rem 1rem;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:1rem;margin-bottom:.5rem}
.role-search-input:focus{outline:none;border-color:var(--accent)}
.role-option{padding:.6rem .8rem;border-radius:6px;cursor:pointer;margin-bottom:.3rem;border:1px solid transparent;transition:all .15s}
.role-option:hover{background:var(--bg);border-color:var(--border)}
.role-option .ro-name{font-weight:600}.role-option .ro-func{font-size:.8rem;color:var(--muted)}
.level-btns{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem}
.level-btn{padding:.5rem 1rem;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:.9rem}
.level-btn.selected{border-color:var(--accent);background:var(--accent);color:#fff}
.action-plan{margin-top:1rem}
.plan-skill{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:.75rem}
.plan-skill h4{margin-bottom:.3rem}
.plan-skill .plan-label{font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem}
.plan-label.invest{color:var(--green)}.plan-label.partner{color:var(--yellow)}.plan-label.delegate{color:var(--red)}
.plan-skill .plan-prof{font-size:.85rem;color:var(--muted);margin-top:.4rem}
/* ---- SEARCH ---- */
.search-bar{padding:.75rem 0;position:sticky;top:0;background:var(--bg);z-index:10;border-bottom:1px solid var(--border)}
.search-bar input{width:100%;padding:.65rem 1rem;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:.95rem}
.search-bar input:focus{outline:none;border-color:var(--accent)}
/* ---- NAV ---- */
nav.bc{padding:.6rem 0;color:var(--muted);font-size:.85rem}
nav.bc span{cursor:pointer;color:var(--accent)}nav.bc span:hover{text-decoration:underline}
/* ---- GRID ---- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem;padding:.75rem 0}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;cursor:pointer;transition:border-color .15s}
.card:hover{border-color:var(--accent)}
.card h3{font-size:1rem;margin-bottom:.2rem}
.card .meta{color:var(--muted);font-size:.8rem}
/* ---- BADGES ---- */
.badge{display:inline-block;padding:.12rem .45rem;border-radius:4px;font-size:.7rem;font-weight:700;text-transform:uppercase}
.badge-low{background:#22c55e22;color:var(--green)}.badge-moderate{background:#eab30822;color:var(--yellow)}
.badge-moderate-high{background:#f9731622;color:var(--orange)}.badge-high{background:#ef444422;color:var(--red)}
.badge-very-high{background:#ec489922;color:var(--pink)}
/* ---- ACTION LABELS (beginner-friendly) ---- */
.action-badge{display:inline-block;padding:.2rem .6rem;border-radius:4px;font-size:.72rem;font-weight:700}
.ab-invest{background:#22c55e28;color:var(--green)}.ab-partner{background:#eab30828;color:var(--yellow)}.ab-delegate{background:#ef444428;color:var(--red)}
/* ---- ROLE DETAIL ---- */
.detail{padding:.75rem 0}
.detail h2{margin-bottom:.4rem;font-size:1.3rem}
.detail .desc{color:var(--muted);margin-bottom:1rem;font-size:.9rem}
.section{margin-bottom:1.25rem}
.section h4{margin-bottom:.4rem;color:var(--accent);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em}
.impact-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.75rem}
.impact-col{background:var(--card);border-radius:8px;padding:.8rem;border:1px solid var(--border)}
.impact-col h5{margin-bottom:.4rem;font-size:.8rem}
.impact-col.automating h5{color:var(--red)}.impact-col.augmenting h5{color:var(--yellow)}.impact-col.preserving h5{color:var(--green)}
.impact-col li{font-size:.8rem;margin-left:1rem;margin-bottom:.2rem;color:var(--muted)}
.freshness{font-size:.78rem;color:var(--muted);margin-top:.5rem;padding:.4rem .6rem;background:var(--card);border-radius:4px;display:inline-block}
.skill-tbl{width:100%;border-collapse:collapse}
.skill-tbl th,.skill-tbl td{padding:.5rem .6rem;text-align:left;border-bottom:1px solid var(--border);font-size:.85rem}
.skill-tbl th{color:var(--muted);font-size:.75rem;text-transform:uppercase}
.skill-tbl tr{cursor:pointer;transition:background .1s}.skill-tbl tr:hover{background:var(--card)}
.bar{height:5px;border-radius:3px;display:inline-block;vertical-align:middle}
.bar-fill{height:100%;border-radius:3px}
.skill-expand td{padding:0!important;border:none!important}
.skill-detail{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;margin:.4rem 0}
.prof-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.6rem;margin-top:.6rem}
.prof-card{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:.6rem}
.prof-card h6{font-size:.75rem;color:var(--accent);margin-bottom:.2rem}
.prof-card p{font-size:.8rem;color:var(--muted)}
/* ---- SELF ASSESS ---- */
.assess-panel{background:var(--card);border:1px solid var(--accent);border-radius:var(--radius);padding:1.2rem;margin:1rem 0}
.assess-panel h4{color:var(--accent);margin-bottom:.5rem;font-size:.9rem}
.assess-row{display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem;flex-wrap:wrap}
.assess-row .skill-name{font-size:.85rem;min-width:160px}
.assess-select{padding:.3rem .5rem;border-radius:4px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:.8rem}
.assess-result{margin-top:1rem;padding:1rem;background:var(--bg);border-radius:8px;border:1px solid var(--border)}
.assess-result h5{margin-bottom:.5rem}
/* ---- FEEDBACK ---- */
.feedback-btn{position:fixed;bottom:1rem;right:1rem;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:.6rem 1rem;font-size:.85rem;font-weight:600;z-index:20;box-shadow:0 2px 8px rgba(0,0,0,.3)}
.feedback-btn:hover{opacity:.85}
/* ---- LEGEND ---- */
.legend{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:.8rem 1rem;margin:.75rem 0;display:flex;flex-wrap:wrap;gap:1rem;align-items:center;font-size:.82rem}
.legend-title{font-weight:600;color:var(--muted);font-size:.75rem;text-transform:uppercase;width:100%}
.legend-item{display:flex;align-items:center;gap:.35rem}
/* ---- GLOSSARY ---- */
.glossary-btn{background:var(--card);color:var(--muted);border:1px solid var(--border);border-radius:6px;padding:.3rem .6rem;font-size:.78rem;cursor:pointer;margin-left:.5rem}
.glossary-btn:hover{border-color:var(--accent);color:var(--accent)}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:30;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem;max-width:560px;width:90%;max-height:80vh;overflow-y:auto}
.modal h3{margin-bottom:.75rem}.modal dt{font-weight:600;color:var(--accent);margin-top:.6rem;font-size:.9rem}
.modal dd{color:var(--muted);font-size:.85rem;margin-left:0;margin-bottom:.3rem}
/* ---- FOOTER ---- */
footer{text-align:center;padding:1.5rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--border);margin-top:1.5rem}
footer a{color:var(--accent)}
/* ---- MOBILE ---- */
@media(max-width:640px){
  .hero h1{font-size:1.6rem}
  .grid{grid-template-columns:1fr}
  .impact-grid{grid-template-columns:1fr}
  .prof-grid{grid-template-columns:1fr}
  .hero .stats-row{gap:.8rem}
  .level-btns{flex-direction:column}
  .skill-tbl th:nth-child(4),.skill-tbl td:nth-child(4){display:none}
  .assess-row{flex-direction:column;align-items:flex-start}
}
</style>
</head>
<body>
<div class="container" id="app">

<!-- HERO -->
<div class="hero">
  <h1>skillich</h1>
  <p class="tagline">The open-source guide to thriving in the age of AI. Find your role. See what's changing. Build the skills that matter.</p>
  <div class="stats-row" id="stats"></div>
  <div class="cta-row">
    <button class="btn btn-primary" onclick="startWizard()">Get My Action Plan</button>
    <a class="btn btn-secondary" href="https://github.com/salahuddinuqaili/skillich/blob/main/docs/playbook.md">Read the Playbook</a>
    <button class="btn btn-secondary" onclick="$('#glossary-modal').classList.add('active')">Glossary</button>
  </div>
</div>

<!-- GUIDED WIZARD -->
<div class="wizard" id="wizard">
  <!-- Step 1: Find role -->
  <div class="wizard-step active" id="wiz-1">
    <h2>Step 1 of 3: What's your role?</h2>
    <p>Type your job title and select the closest match.</p>
    <input class="role-search-input" id="wiz-search" placeholder="e.g. Product Manager, Accountant, Backend Engineer..." autocomplete="off">
    <div id="wiz-results" style="max-height:280px;overflow-y:auto"></div>
  </div>
  <!-- Step 2: Level -->
  <div class="wizard-step" id="wiz-2">
    <h2>Step 2 of 3: What's your current level?</h2>
    <p id="wiz-role-name"></p>
    <div class="level-btns" id="wiz-levels"></div>
    <button class="btn btn-secondary" onclick="wizBack(1)" style="margin-right:.5rem">Back</button>
  </div>
  <!-- Step 3: Plan -->
  <div class="wizard-step" id="wiz-3">
    <h2>Your Personalized Action Plan</h2>
    <p id="wiz-plan-intro"></p>
    <div class="action-plan" id="wiz-plan"></div>
    <div style="margin-top:1rem;display:flex;gap:.5rem;flex-wrap:wrap">
      <button class="btn btn-primary" onclick="wizViewRole()">View Full Role Detail</button>
      <button class="btn btn-secondary" onclick="wizRestart()">Start Over</button>
      <a class="btn btn-secondary" href="https://github.com/salahuddinuqaili/skillich/blob/main/docs/playbook.md">Read Full Playbook</a>
    </div>
  </div>
</div>

<!-- MAIN BROWSE -->
<div class="search-bar" id="search-wrap" style="display:none"><input id="search" placeholder="Search roles, skills, or keywords..." autocomplete="off"></div>
<nav class="bc" id="bc"></nav>
<main id="main"></main>

<!-- FEEDBACK BUTTON -->
<a class="feedback-btn" href="https://github.com/salahuddinuqaili/skillich/issues/new?template=feedback.yml" target="_blank" rel="noopener">Is this accurate?</a>

<!-- GLOSSARY MODAL -->
<div class="modal-overlay" id="glossary-modal" onclick="if(event.target===this)this.classList.remove('active')">
<div class="modal">
<h3>Glossary <button onclick="$('#glossary-modal').classList.remove('active')" style="float:right;background:none;border:none;color:var(--muted);font-size:1.2rem;cursor:pointer">&times;</button></h3>
<dl>
<dt>AI Impact Rating (0.0 - 1.0)</dt>
<dd>How much of this skill's routine work AI can currently handle. 0.0 = entirely human, 1.0 = fully automated. <strong>This is not a prediction — it's a snapshot of today's AI capabilities.</strong></dd>
<dt>Invest Here (green, 0-30%)</dt>
<dd>AI struggles with this skill. It requires human judgment, creativity, or relationship-building that current AI can't replicate. <strong>This is where your career value compounds.</strong></dd>
<dt>Use AI as Partner (yellow, 30-60%)</dt>
<dd>AI handles parts of this skill well, but you still need to guide it, validate its output, and apply context. Learn to work <em>with</em> AI here.</dd>
<dt>Let AI Handle (red, 60-100%)</dt>
<dd>AI does most of this already. Stop spending time practicing this manually — automate it and redirect your energy to green skills.</dd>
<dt>Proficiency Level</dt>
<dd>What "good" looks like at each career stage. Descriptions use observable behaviors — things others can see you doing, not vague traits.</dd>
<dt>Automating</dt>
<dd>Tasks in this role that AI is absorbing. These are things you should stop doing manually and let AI tools handle.</dd>
<dt>Augmenting</dt>
<dd>Tasks where AI makes you dramatically faster or more effective. Learn to use AI as a force multiplier here.</dd>
<dt>Preserving</dt>
<dd>Tasks that remain fundamentally human. Judgment, trust, creativity, empathy, strategic thinking. Double down on these.</dd>
<dt>Confidence Level</dt>
<dd>How sure we are about the ratings. "Medium" means supported by published research. "Low" means expert estimate. "High" means validated with real data.</dd>
</dl>
</div>
</div>

<footer>
  skillich &mdash; MIT License &mdash; <a href="https://github.com/salahuddinuqaili/skillich">GitHub</a> &mdash; <a href="https://github.com/salahuddinuqaili/skillich/blob/main/docs/playbook.md">Playbook</a> &mdash; <a href="https://github.com/salahuddinuqaili/skillich/blob/main/CHANGELOG.md">Changelog</a>
</footer>
</div>

<script>
const DATA=__TAXONOMY_JSON__;
const RESOURCES=__RESOURCES_JSON__;
const $=s=>document.querySelector(s);

// --- Helpers ---
function impactClass(l){return'badge-'+(l||'moderate').replace(' ','-')}
function ratingColor(r){return r<=.3?'var(--green)':r<=.5?'var(--yellow)':r<=.7?'var(--orange)':'var(--red)'}
function pct(r){return Math.round(r*100)+'%'}
function findResources(skillName){
  const sn=skillName.toLowerCase();
  const matches=[];
  for(const[keyword,resources]of Object.entries(RESOURCES)){
    if(sn.includes(keyword)||keyword.split(' ').every(w=>sn.includes(w))){
      resources.forEach(r=>{if(!matches.find(m=>m.url===r.url))matches.push(r);});
    }
  }
  return matches.slice(0,4);
}
function actionLabel(r){
  if(r<=.3)return{text:'Invest Here',cls:'ab-invest',tip:'AI struggles with this. This is where your career value lives.'};
  if(r<=.6)return{text:'Use AI as Partner',cls:'ab-partner',tip:'AI helps with parts of this. Learn to combine your judgment with AI speed.'};
  return{text:'Let AI Handle',cls:'ab-delegate',tip:'AI does most of this already. Automate it and spend your time elsewhere.'};
}

// --- All roles flat for wizard search ---
const ALL_ROLES=[];
DATA.functions.forEach(f=>f.roles.forEach(r=>ALL_ROLES.push({func:f,role:r})));

// ===================== WIZARD =====================
let wizState={};

function startWizard(){
  $('#wizard').classList.add('active');
  $('#search-wrap').style.display='none';
  $('#main').innerHTML='';$('#bc').innerHTML='';
  showWizStep(1);
  $('#wiz-search').value='';$('#wiz-results').innerHTML='';
  setTimeout(()=>$('#wiz-search').focus(),100);
}

function showWizStep(n){
  document.querySelectorAll('.wizard-step').forEach(s=>s.classList.remove('active'));
  const el=$('#wiz-'+n);if(el)el.classList.add('active');
}

function wizBack(n){showWizStep(n)}

function wizRestart(){wizState={};startWizard()}

$('#wiz-search').addEventListener('input',function(){
  const q=this.value.toLowerCase().trim();
  if(!q){$('#wiz-results').innerHTML='';return;}
  const matches=ALL_ROLES.filter(({role:r})=>
    r.name.toLowerCase().includes(q)||
    r.description.toLowerCase().includes(q)||
    (r.also_known_as||[]).some(a=>a.toLowerCase().includes(q))
  ).slice(0,12);
  $('#wiz-results').innerHTML=matches.map(({func:f,role:r})=>
    `<div class="role-option" onclick="wizPickRole('${f.id}','${r.id}')">
      <div class="ro-name">${r.name} <span class="badge ${impactClass(r.ai_impact.level)}">${r.ai_impact.level}</span></div>
      <div class="ro-func">${f.name}</div>
    </div>`
  ).join('');
});

window.wizPickRole=function(fid,rid){
  const f=DATA.functions.find(x=>x.id===fid);
  const r=f.roles.find(x=>x.id===rid);
  wizState={funcId:fid,roleId:rid,func:f,role:r};
  // Step 2 - levels
  $('#wiz-role-name').textContent=r.name+' ('+f.name+')';
  $('#wiz-levels').innerHTML=r.levels.map(l=>
    `<button class="level-btn" onclick="wizPickLevel('${l.id}')">${l.name}<br><span style="font-size:.75rem;color:var(--muted)">${l.years} years</span></button>`
  ).join('');
  showWizStep(2);
};

window.wizPickLevel=function(levelId){
  wizState.level=levelId;
  const r=wizState.role;
  const sorted=[...r.skills].sort((a,b)=>a.ai_impact_rating-b.ai_impact_rating);
  const invest=sorted.filter(s=>s.ai_impact_rating<=.3).slice(0,3);
  const partner=sorted.filter(s=>s.ai_impact_rating>.3&&s.ai_impact_rating<=.6).slice(0,2);
  const delegate=sorted.filter(s=>s.ai_impact_rating>.6).slice(0,2);

  const levelName=r.levels.find(l=>l.id===levelId)?.name||levelId;
  $('#wiz-plan-intro').innerHTML=`As a <strong>${levelName}</strong> in <strong>${r.name}</strong>, here's where to focus your energy:`;

  let html='';
  const renderSkills=(skills,label,cls)=>{
    skills.forEach(s=>{
      const al=actionLabel(s.ai_impact_rating);
      const prof=s.proficiency[levelId]||s.proficiency[Object.keys(s.proficiency)[0]]||'';
      html+=`<div class="plan-skill">
        <div class="plan-label ${cls}">${label}</div>
        <h4>${s.name} <span class="action-badge ${al.cls}">${al.text} (${pct(s.ai_impact_rating)})</span></h4>
        <div style="font-size:.85rem;color:var(--muted);margin:.3rem 0">${al.tip}</div>
        <div class="plan-prof"><strong>What good looks like at your level:</strong> ${prof}</div>
      </div>`;
    });
  };
  if(invest.length){renderSkills(invest,'Your Top Career Investments','invest');}
  if(partner.length){renderSkills(partner,'Use AI as Your Partner Here','partner');}
  if(delegate.length){renderSkills(delegate,'Let AI Handle These','delegate');}
  $('#wiz-plan').innerHTML=html;
  showWizStep(3);
};

window.wizViewRole=function(){
  $('#wizard').classList.remove('active');
  nav('role',wizState.funcId,wizState.roleId);
};

// ===================== BROWSE =====================
let view={type:'functions'};

function render(){
  const m=$('#main');$('#search-wrap').style.display='block';
  if(view.type==='functions')renderFunctions(m);
  else if(view.type==='roles')renderRoles(m,view.funcId);
  else if(view.type==='role')renderRole(m,view.funcId,view.roleId);
  renderBC();
}

function renderBC(){
  let h='<span onclick="nav(\'functions\')">All Functions</span>';
  if(view.funcId){const f=DATA.functions.find(x=>x.id===view.funcId);h+=' / <span onclick="nav(\'roles\',\''+view.funcId+'\')">'+f.name+'</span>';}
  if(view.roleId){const f=DATA.functions.find(x=>x.id===view.funcId),r=f.roles.find(x=>x.id===view.roleId);h+=' / '+r.name;}
  $('#bc').innerHTML=h;
}

function nav(type,funcId,roleId){
  view={type,funcId,roleId};$('#search').value='';$('#wizard').classList.remove('active');
  render();window.scrollTo(0,0);
}

function renderFunctions(el){
  let h='<div class="grid">';
  for(const f of DATA.functions){
    const rc=f.roles.length,sc=f.roles.reduce((a,r)=>a+r.skills.length,0);
    h+=`<div class="card" onclick="nav('roles','${f.id}')"><h3>${f.name}</h3><div class="meta">${rc} roles &middot; ${sc} skills</div>
    <p style="margin-top:.4rem;font-size:.85rem;color:var(--muted)">${f.description.slice(0,120)}${f.description.length>120?'...':''}</p></div>`;
  }
  el.innerHTML=h+'</div>';
}

function renderRoles(el,funcId){
  const f=DATA.functions.find(x=>x.id===funcId);
  let h='<div class="grid">';
  for(const r of f.roles){
    const avg=r.skills.length?r.skills.reduce((a,s)=>a+s.ai_impact_rating,0)/r.skills.length:0;
    h+=`<div class="card" onclick="nav('role','${funcId}','${r.id}')">
    <h3>${r.name} <span class="badge ${impactClass(r.ai_impact.level)}">${r.ai_impact.level}</span></h3>
    <div class="meta">${r.skills.length} skills &middot; avg AI impact ${pct(avg)}</div>
    <p style="margin-top:.35rem;font-size:.82rem;color:var(--muted)">${r.description.slice(0,130)}${r.description.length>130?'...':''}</p></div>`;
  }
  el.innerHTML=h+'</div>';
}

function renderRole(el,funcId,roleId){
  const f=DATA.functions.find(x=>x.id===funcId),r=f.roles.find(x=>x.id===roleId),ai=r.ai_impact;
  let h=`<div class="detail"><h2>${r.name} <span class="badge ${impactClass(ai.level)}">${ai.level} AI impact</span></h2>`;
  if(r.also_known_as?.length)h+=`<div style="font-size:.82rem;color:var(--muted);margin-bottom:.4rem">Also: ${r.also_known_as.join(', ')}</div>`;
  h+=`<div class="desc">${r.description}</div>`;

  // AI transformation
  h+=`<div class="section"><h4>How AI Is Transforming This Role</h4><p style="font-size:.88rem;margin-bottom:.75rem">${ai.summary}</p>
  <div class="impact-grid">
    <div class="impact-col automating"><h5>Stop Doing Manually</h5><ul>${ai.automating.map(x=>'<li>'+x+'</li>').join('')}</ul></div>
    <div class="impact-col augmenting"><h5>Use AI to 10x These</h5><ul>${ai.augmenting.map(x=>'<li>'+x+'</li>').join('')}</ul></div>
    <div class="impact-col preserving"><h5>Double Down on These</h5><ul>${ai.preserving.map(x=>'<li>'+x+'</li>').join('')}</ul></div>
  </div>`;
  // Freshness
  const parts=[];
  if(ai.confidence)parts.push('Confidence: '+ai.confidence);
  if(ai.last_reviewed)parts.push('Last reviewed: '+ai.last_reviewed);
  if(parts.length)h+=`<div class="freshness">${parts.join(' &middot; ')}</div>`;
  h+=`</div>`;

  // Skills table
  const sorted=[...r.skills].sort((a,b)=>a.ai_impact_rating-b.ai_impact_rating);
  h+=`<div class="section"><h4>Skills (sorted by career value) <button class="glossary-btn" onclick="event.stopPropagation();$('#glossary-modal').classList.add('active')">What do these mean?</button></h4>
  <div class="legend"><div class="legend-title">How to read this table</div>
    <div class="legend-item"><span class="action-badge ab-invest">Invest Here</span> AI can't do this — build this skill</div>
    <div class="legend-item"><span class="action-badge ab-partner">AI as Partner</span> Use AI to go faster here</div>
    <div class="legend-item"><span class="action-badge ab-delegate">Let AI Handle</span> Automate this, spend time elsewhere</div>
  </div>
  <table class="skill-tbl"><thead><tr><th>Skill</th><th>Action</th><th>AI Impact</th><th></th></tr></thead><tbody>`;
  for(const s of sorted){
    const c=ratingColor(s.ai_impact_rating),w=Math.max(s.ai_impact_rating*100,4),al=actionLabel(s.ai_impact_rating);
    h+=`<tr onclick="toggleSkill(this,'${funcId}','${roleId}','${s.id}')">
      <td><strong>${s.name}</strong><br><span style="font-size:.78rem;color:var(--muted)">${s.description.slice(0,70)}${s.description.length>70?'...':''}</span></td>
      <td><span class="action-badge ${al.cls}">${al.text}</span></td>
      <td style="white-space:nowrap"><span style="color:${c};font-weight:600">${pct(s.ai_impact_rating)}</span></td>
      <td style="width:80px"><div class="bar" style="width:80px;background:var(--border)"><div class="bar-fill" style="width:${w*.8}px;background:${c}"></div></div></td></tr>`;
  }
  h+=`</tbody></table></div>`;

  // Self-assessment panel
  h+=`<div class="assess-panel"><h4>Quick Self-Assessment</h4><p style="font-size:.85rem;color:var(--muted);margin-bottom:.75rem">Rate your current level for each skill. We'll show your gaps and priorities.</p>
  <div id="assess-rows">`;
  const levels=r.levels.map(l=>l.id);
  for(const s of r.skills){
    h+=`<div class="assess-row"><span class="skill-name">${s.name}</span>
    <select class="assess-select" data-skill="${s.id}" data-rating="${s.ai_impact_rating}">
      <option value="">-- select --</option>${levels.map(l=>`<option value="${l}">${l}</option>`).join('')}
    </select></div>`;
  }
  h+=`</div><button class="btn btn-primary" style="margin-top:.75rem" onclick="runAssess('${funcId}','${roleId}')">Show My Gaps</button>
  <div id="assess-out"></div></div>`;

  // Levels
  h+=`<div class="section"><h4>Career Levels</h4><table class="skill-tbl"><thead><tr><th>Level</th><th>Years</th><th>Summary</th></tr></thead><tbody>`;
  for(const l of r.levels)h+=`<tr><td><strong>${l.name}</strong></td><td>${l.years}</td><td>${l.summary}</td></tr>`;
  h+=`</tbody></table></div></div>`;
  el.innerHTML=h;
}

window.toggleSkill=function(tr,funcId,roleId,skillId){
  const ex=tr.nextElementSibling;if(ex?.classList.contains('skill-expand')){ex.remove();return;}
  document.querySelectorAll('.skill-expand').forEach(x=>x.remove());
  const f=DATA.functions.find(x=>x.id===funcId),r=f.roles.find(x=>x.id===roleId),s=r.skills.find(x=>x.id===skillId);
  const al=actionLabel(s.ai_impact_rating);
  const res=findResources(s.name);
  const resHtml=res.length?`<div style="margin-top:.8rem"><h6 style="font-size:.75rem;color:var(--accent);text-transform:uppercase;margin-bottom:.4rem">Learn This Skill</h6>
    ${res.map(r=>`<a href="${r.url}" target="_blank" rel="noopener" style="display:inline-block;margin-right:.6rem;margin-bottom:.3rem;font-size:.82rem;padding:.2rem .5rem;border:1px solid var(--border);border-radius:4px;color:var(--accent)">${r.type==='free'?'Free: ':''}${r.name}</a>`).join('')}</div>`:'';
  const row=document.createElement('tr');row.className='skill-expand';
  row.innerHTML=`<td colspan="4"><div class="skill-detail">
    <strong>${s.name}</strong> <span class="badge" style="background:var(--border);color:var(--text)">${s.category}</span>
    <span class="action-badge ${al.cls}" style="margin-left:.4rem">${al.text}</span>
    <p style="margin:.4rem 0;font-size:.88rem">${s.description}</p>
    <p style="font-size:.82rem;color:var(--muted)"><strong>AI Impact (${pct(s.ai_impact_rating)}):</strong> ${s.ai_impact_detail}</p>
    <p style="font-size:.82rem;color:var(--muted);margin-top:.3rem"><strong>${al.tip}</strong></p>
    ${resHtml}
    <h6 style="margin-top:.8rem;font-size:.75rem;color:var(--accent);text-transform:uppercase">Proficiency by Level</h6>
    <div class="prof-grid">${Object.entries(s.proficiency).map(([k,v])=>`<div class="prof-card"><h6>${k}</h6><p>${v}</p></div>`).join('')}</div>
  </div></td>`;
  tr.after(row);
};

// ===================== SELF-ASSESS =====================
window.runAssess=function(funcId,roleId){
  const f=DATA.functions.find(x=>x.id===funcId),r=f.roles.find(x=>x.id===roleId);
  const levels=r.levels.map(l=>l.id);
  const selects=document.querySelectorAll('#assess-rows .assess-select');
  const assessed=[];
  selects.forEach(sel=>{
    if(sel.value){
      assessed.push({skillId:sel.dataset.skill,level:sel.value,rating:parseFloat(sel.dataset.rating)});
    }
  });
  if(!assessed.length){$('#assess-out').innerHTML='<p style="color:var(--muted)">Select at least one skill level above.</p>';return;}

  // Find highest level selected as target (one above)
  const maxIdx=Math.max(...assessed.map(a=>levels.indexOf(a.level)));
  const targetIdx=Math.min(maxIdx+1,levels.length-1);
  const targetLevel=levels[targetIdx];

  const gaps=[],strengths=[];
  assessed.forEach(a=>{
    const curIdx=levels.indexOf(a.level);
    if(curIdx<targetIdx)gaps.push({...a,target:targetLevel,delta:targetIdx-curIdx});
    else strengths.push(a);
  });
  // Sort gaps: low AI impact first (most career-valuable)
  gaps.sort((a,b)=>a.rating-b.rating);

  let h=`<div class="assess-result"><h5>Gap Analysis (target: ${targetLevel})</h5>`;
  if(gaps.length){
    h+=`<p style="font-size:.85rem;color:var(--muted);margin-bottom:.5rem">Focus on these skills first -- sorted by career value (lowest AI impact = highest priority):</p>`;
    gaps.forEach(g=>{
      const s=r.skills.find(x=>x.id===g.skillId);
      const al=actionLabel(g.rating);
      h+=`<div style="padding:.4rem 0;border-bottom:1px solid var(--border)">
        <strong>${s?.name||g.skillId}</strong> <span class="action-badge ${al.cls}">${al.text}</span>
        <span style="font-size:.8rem;color:var(--muted);margin-left:.5rem">${g.level} -> ${g.target} (${g.delta} level${g.delta>1?'s':''})</span>
      </div>`;
    });
  }
  if(strengths.length){
    h+=`<p style="margin-top:.75rem;font-size:.85rem;color:var(--green)"><strong>${strengths.length} skill${strengths.length>1?'s':''} already at or above target.</strong></p>`;
  }
  const unassessed=r.skills.length-assessed.length;
  if(unassessed>0)h+=`<p style="font-size:.82rem;color:var(--muted);margin-top:.4rem">${unassessed} skill${unassessed>1?'s':''} not assessed yet.</p>`;
  h+='</div>';
  $('#assess-out').innerHTML=h;
};

// ===================== SEARCH =====================
$('#search').addEventListener('input',function(){
  const q=this.value.toLowerCase().trim();if(!q){render();return;}
  let results=[];
  DATA.functions.forEach(f=>f.roles.forEach(r=>{
    const match=r.name.toLowerCase().includes(q)||r.description.toLowerCase().includes(q)||(r.also_known_as||[]).some(a=>a.toLowerCase().includes(q))||r.skills.some(s=>s.name.toLowerCase().includes(q));
    if(match)results.push({func:f,role:r});
  }));
  let h=`<p style="padding:.75rem 0;color:var(--muted)">${results.length} role(s) matching "${q}"</p><div class="grid">`;
  results.slice(0,20).forEach(({func:f,role:r})=>{
    h+=`<div class="card" onclick="nav('role','${f.id}','${r.id}')"><h3>${r.name} <span class="badge ${impactClass(r.ai_impact.level)}">${r.ai_impact.level}</span></h3><div class="meta">${f.name} &middot; ${r.skills.length} skills</div></div>`;
  });
  $('#main').innerHTML=h+'</div>';
  $('#bc').innerHTML='<span onclick="nav(\'functions\')">All Functions</span> / Search: "'+q+'"';
});

// ===================== INIT =====================
const s=DATA.stats;
$('#stats').innerHTML=`<div class="stat"><div class="stat-n">${s.functions}</div><div class="stat-l">Functions</div></div>
<div class="stat"><div class="stat-n">${s.roles}</div><div class="stat-l">Roles</div></div>
<div class="stat"><div class="stat-n">${s.skills}</div><div class="stat-l">Skills</div></div>`;
// Show functions by default (but wizard is the primary entry)
render();
</script>
</body>
</html>"""


def main():
    taxonomy_dir = str(Path(__file__).resolve().parent.parent / "taxonomy")
    output = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent / "index.html")

    loader = TaxonomyLoader(taxonomy_dir)
    taxonomy_json = build_json(loader)
    resources_json = load_resources()
    html = HTML_TEMPLATE.replace("__TAXONOMY_JSON__", taxonomy_json).replace("__RESOURCES_JSON__", resources_json)

    Path(output).write_text(html, encoding="utf-8")
    size_kb = Path(output).stat().st_size / 1024
    print(f"Generated {output} ({size_kb:.0f} KB)")
    print(f"  {loader.stats['functions']} functions, {loader.stats['roles']} roles, {loader.stats['skills']} skills")


if __name__ == "__main__":
    main()

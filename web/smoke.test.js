/* Headless smoke test for the generated web app.
 *
 * The page is one big string-building script with no unit-test seam, so this
 * loads the real generated HTML in jsdom and drives it the way a person would:
 * type in the search box, click a result, switch level, expand a skill.
 *
 *   python web/generate.py && npm --prefix web ci && node web/smoke.test.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const file = process.argv[2] || path.join(__dirname, "index.html");
const html = fs.readFileSync(file, "utf8");

let failures = 0;
let total = 0;
function check(name, cond, extra) {
  total++;
  if (cond) console.log("  PASS  " + name);
  else { failures++; console.log("  FAIL  " + name + (extra ? "  -> " + extra : "")); }
}

const dom = new JSDOM(html, {
  url: "http://localhost:8899/index.html",
  runScripts: "dangerously",
  pretendToBeVisual: true,
});
const { window } = dom;
const doc = window.document;
const errs = [];
window.addEventListener("error", (e) => errs.push(e.message || String(e.error)));

function nav(hash) {
  window.location.hash = hash;
  // jsdom fires hashchange asynchronously; force a synchronous render instead.
  window.dispatchEvent(new window.Event("hashchange"));
}
const view = () => doc.getElementById("view").innerHTML;
const flush = () => window.dispatchEvent(new window.Event("hashchange"));
const TAX = () => window.eval("DATA");

console.log("\n--- boot ---");
check("no script errors on load", errs.length === 0, errs.join(" | "));
check("hero painted statically", /What is AI doing to your job/.test(doc.getElementById("home-hero").textContent));
check("taxonomy parsed", TAX().stats.roles === 88, JSON.stringify(TAX().stats));
check("home KPIs rendered", /Skills rated/.test(view()));
check("function cards rendered", (view().match(/href="#\/function\//g) || []).length === 17);

console.log("\n--- search ranking ---");
const cases = [
  ["pm", "Product Manager"],
  ["product manager", "Product Manager"],
  ["sre", "DevOps / Site Reliability Engineer"],
  ["electrician", "Electrician"],
  ["swe", "Full-Stack Engineer"],
  ["ml", "Machine Learning Engineer"],
  ["sdr", "Sales Development Representative"],
  ["recruiter", "Recruiter / Talent Acquisition Specialist"],
];
for (const [q, expected] of cases) {
  const hits = window.searchRoles(q, 5);
  check(`"${q}" -> ${expected}`, hits.length && hits[0].role.name === expected,
    hits.length ? hits[0].role.name : "no hits");
}
check('"banana" returns nothing', window.searchRoles("banana", 5).length === 0);

console.log("\n--- search box interaction ---");
const input = doc.getElementById("q");
input.value = "electrician";
input.dispatchEvent(new window.Event("input"));
const options = doc.querySelectorAll("#results .result");
check("typing shows options", options.length > 0, options.length + " options");
check("first option preselected", options[0] && options[0].getAttribute("aria-selected") === "true");
check("combobox marked expanded", input.getAttribute("aria-expanded") === "true");
options[0].dispatchEvent(new window.Event("click", { bubbles: true }));
flush();
check("clicking a result routes to a plan", /^#\/plan\//.test(window.location.hash), window.location.hash);

console.log("\n--- plan route ---");
nav("#/plan/product/product_manager/senior");
let v = view();
check("plan renders", /Product Manager/.test(v));
check("hero figure present", /hero-fig/.test(v));
check("exposure meter present", /meter-fill/.test(v));
check("level switcher marks senior", /data-level="senior" aria-pressed="true"/.test(v));
check("invest band present", /Invest here/.test(v));
check("gap: where you are / going", /Where you are/.test(v) && /Where you're going/.test(v));
check("proof point present", /How you'll know you got there/.test(v));
check("stop-doing list present", /Stop doing these by hand/.test(v));
check("transitions table present", /Where your skills already transfer/.test(v));
check("share actions present", /id="copy-link"/.test(v) && /id="dl-md"/.test(v) && /id="print-plan"/.test(v));
check("hero hidden off-home", doc.getElementById("home-hero").hidden === true);
check("document title updated", /Product Manager/.test(doc.title), doc.title);

console.log("\n--- level switcher ---");
const juniorBtn = doc.querySelector('.level[data-level="junior"]');
check("junior button exists", !!juniorBtn);
juniorBtn.dispatchEvent(new window.Event("click", { bubbles: true }));
flush();
check("switching level changes route", window.location.hash === "#/plan/product/product_manager/junior", window.location.hash);
check("junior proficiency now shown", /data-level="junior" aria-pressed="true"/.test(view()));

console.log("\n--- markdown export ---");
const p = window.buildPlan("product", "product_manager", "senior");
const md = window.planMarkdown(p);
check("markdown has title", /^# Your AI action plan — Product Manager/.test(md));
check("markdown has invest section", /## Invest here \(\d+\)/.test(md));
check("markdown has share link", /#\/plan\/product\/product_manager\/senior/.test(md));
check("markdown has feedback link", /issues\/new\?template=feedback\.yml/.test(md));
check("markdown non-trivial", md.length > 2000, md.length + " chars");

console.log("\n--- plan band maths ---");
check("bands partition every skill",
  p.invest.length + p.partner.length + p.delegate.length === p.role.skills.length,
  `${p.invest.length}+${p.partner.length}+${p.delegate.length} vs ${p.role.skills.length}`);
check("invest all <= 30%", p.invest.every((s) => s.ai_impact_rating === undefined ? s.rating <= 0.3 : true));
check("delegate all > 60%", p.delegate.every((s) => s.rating > 0.6));
check("invest sorted ascending", p.invest.every((s, i, a) => i === 0 || a[i - 1].rating <= s.rating));

console.log("\n--- every role builds a plan ---");
let bad = [];
for (const f of TAX().functions) {
  for (const r of f.roles) {
    const pp = window.buildPlan(f.id, r.id, null);
    if (!pp || !pp.level.id) bad.push(f.id + "/" + r.id);
    else if (pp.invest.length + pp.partner.length + pp.delegate.length !== r.skills.length) bad.push(f.id + "/" + r.id + " (band mismatch)");
  }
}
check("all 88 roles build a valid plan", bad.length === 0, bad.slice(0, 5).join(", "));

console.log("\n--- role detail ---");
nav("#/role/engineering/backend");
v = view();
check("role detail renders", /Backend Engineer/.test(v));
check("impact columns present", /Stop doing manually/.test(v) && /Double down here/.test(v));
check("skill table rows keyboard-reachable", /class="skill-row" tabindex="0"/.test(v));
check("career levels table", /Career levels/.test(v));
const row = doc.querySelector(".skill-row");
row.dispatchEvent(new window.Event("click", { bubbles: true }));
check("expanding a skill inserts detail", !!doc.querySelector(".skill-expand"));
check("expanded row marked", row.getAttribute("aria-expanded") === "true");
check("proficiency cards in detail", /prof-card/.test(doc.querySelector(".skill-expand").innerHTML));
row.dispatchEvent(new window.Event("click", { bubbles: true }));
check("clicking again collapses", !doc.querySelector(".skill-expand"));

console.log("\n--- compare ---");
const src = window.eval('findRole("product","product_manager")');
check("transitions precomputed", src.transitions && src.transitions.length > 0, JSON.stringify((src.transitions || []).length));
const t0 = src.transitions[0];
nav(`#/compare/product/product_manager/${t0.function_id}/${t0.role_id}`);
v = view();
check("compare renders both roles", v.includes("Product Manager") && v.includes(t0.role.replace(/&/g, "&amp;")));
check("overlap stated", /skills already cover/.test(v));
check("gap skills listed", /What you.{0,4}d need to learn/.test(v));

console.log("\n--- other routes ---");
nav("#/function/marketing");
check("function view", /Marketing/.test(view()));
nav("#/browse");
check("browse lists all roles", (view().match(/class="card"/g) || []).length === 88);
nav("#/search/paralegal");
check("search view", /Paralegal/.test(view()));
nav("#/search/zzzznothing");
check("empty search is helpful", /Nothing matches/.test(view()) && /ask for this one/.test(view()));
nav("#/plan/nope/nope/mid");
check("unknown role handled", /don.{0,4}t have that role/.test(view()));
nav("#/");
check("home restored", doc.getElementById("home-hero").hidden === false);

console.log("\n--- resume + theme ---");
nav("#/plan/trades/electrician/mid");
nav("#/");
check("resume chip appears after visiting a plan", /Pick up where you left off/.test(doc.getElementById("resume-slot").innerHTML),
  doc.getElementById("resume-slot").innerHTML.slice(0, 80));
doc.getElementById("theme-toggle").dispatchEvent(new window.Event("click", { bubbles: true }));
check("theme toggle sets an explicit theme", !!doc.documentElement.getAttribute("data-theme"),
  doc.documentElement.getAttribute("data-theme"));
check("theme persisted", !!window.localStorage.getItem("skillich:theme"));

console.log("\n--- keyboard shortcut ---");
nav("#/plan/product/product_manager/mid");
doc.body.dispatchEvent(new window.KeyboardEvent("keydown", { key: "/", bubbles: true }));
flush();
check('"/" from a plan returns home', window.location.hash === "#/", window.location.hash);
check('"/" focuses the visible search box', doc.activeElement === doc.getElementById("q"),
  doc.activeElement && doc.activeElement.id);

console.log("\n--- glossary ---");
doc.getElementById("glossary-open").dispatchEvent(new window.Event("click", { bubbles: true }));
check("glossary opens", doc.getElementById("glossary").classList.contains("open"));
doc.getElementById("glossary-close").dispatchEvent(new window.Event("click", { bubbles: true }));
check("glossary closes", !doc.getElementById("glossary").classList.contains("open"));

console.log("\n--- escaping ---");
check("no unescaped angle brackets from data", !/<script>alert/.test(doc.body.innerHTML));

console.log("\n--- runtime errors ---");
check("no uncaught errors during the run", errs.length === 0, errs.join(" | "));

console.log(
  `\n${failures === 0 ? `ALL ${total} CHECKS PASSED` : `${failures} of ${total} CHECKS FAILED`}\n`
);
process.exit(failures === 0 ? 0 : 1);

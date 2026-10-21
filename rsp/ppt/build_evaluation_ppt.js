// Builds rsp/ppt/SkillBridge_Evaluation.pptx — 10-slide evaluation deck in the NMIMS STME format.
// Run (from repo root): cd rsp && npm install && cd .. && node rsp/ppt/build_evaluation_ppt.js
// Inputs: rsp/ppt/screens (capture_screens.py, crop_flows.py), rsp/ppt/brand (logos),
//         data/processed/model_metrics.json
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const ROOT = path.join(HERE, "..", "..");
const OUT = process.env.DECK_OUT || path.join(HERE, "SkillBridge_Evaluation.pptx");
const SHOT = (n) => path.join(HERE, "screens", `${n}.png`);
const FLOW = (n) => path.join(HERE, "screens", `flow_${n}`);
const BRAND = (n) => path.join(HERE, "brand", n);

const RED = "C00000", INK = "1F1F1F", MUTED = "5F6368", TINT = "FBEAEA", LINE = "E6C9C9";
const GREEN = "0E9F6E", BLUE = "1F4E9E";
const HEAD = "Cooper Black", BODY = "Calibri";

const TEAM = ["G. Vikram  -  D022", "L. Jahnavy  -  D023", "K. Janshi  -  D064"];
const MENTOR = "Prof. Anshi Bajaj";

const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, "data/processed/model_metrics.json"), "utf8"));
const pct = (x) => `${(x * 100).toFixed(1)}%`;
const AUC = metrics.auc.toFixed(3);
const ACC = pct(metrics.accuracy);
const am = metrics.all_models;

const pngSize = (f) => { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
function fitImage(s, file, bx, by, bw, bh, altText) {
  const [w, h] = pngSize(file);
  const k = Math.min(bw / w, bh / h), iw = w * k, ih = h * k;
  s.addImage({ path: file, x: bx + (bw - iw) / 2, y: by + (bh - ih) / 2, w: iw, h: ih, altText });
}

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "G. Vikram, L. Jahnavy, K. Janshi";
pres.title = "SkillBridge Analytics — Project Evaluation";

// ------------------------------------------------------------------ NMIMS chrome
function topBand(s) {
  s.addShape(pres.shapes.RECTANGLE, { x: 1.95, y: 0.02, w: 8.05, h: 0.8, fill: { color: RED }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 1.95, h: 0.82, fill: { color: "FFFFFF" },
    line: { color: "D0D0D0", width: 0.5 }, shadow: { type: "outer", color: "000000", opacity: 0.35, blur: 4, offset: 2, angle: 45 } });
  s.addImage({ path: BRAND("nmims_logo.png"), x: 0.17, y: 0.13, w: 1.64, h: 0.56, altText: "SVKM's NMIMS logo" });
}
function bottomStrip(s) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.47, w: 10, h: 0.11, fill: { color: RED }, line: { type: "none" } });
}

// title + thank-you slides: full template footer with school logo, team and mentor
function coverSlide(title, subtitle) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  topBand(s);
  s.addText(title, { x: 0.5, y: 1.15, w: 9, h: 1.0, fontFace: HEAD, fontSize: 36, color: RED,
    align: "center", valign: "middle", margin: 0 });
  if (subtitle) s.addText(subtitle, { x: 0.8, y: 2.2, w: 8.4, h: 1.4, fontFace: BODY, fontSize: 18,
    color: INK, align: "center", valign: "top", margin: 0 });
  s.addImage({ path: BRAND("stme_logo.png"), x: 0.1, y: 4.47, w: 3.82, h: 1.0, altText: "NMIMS School of Technology Management & Engineering, Hyderabad" });
  for (const x of [4.22, 6.6]) {
    s.addShape(pres.shapes.RECTANGLE, { x, y: 4.38, w: 0.05, h: 1.1, fill: { color: "404040" }, line: { type: "none" } });
  }
  s.addText([{ text: "Team Members:", options: { breakLine: true } },
    ...TEAM.map((t, i) => ({ text: t, options: { breakLine: i < TEAM.length - 1 } }))],
    { x: 4.42, y: 4.45, w: 2.1, h: 0.95, fontFace: "Cambria", fontSize: 13, color: INK, valign: "top", margin: 0, paraSpaceAfter: 0 });
  s.addText([{ text: "Mentor Name:", options: { breakLine: true } }, { text: MENTOR }],
    { x: 6.8, y: 4.45, w: 3.0, h: 0.6, fontFace: BODY, fontSize: 13, color: INK, valign: "top", margin: 0 });
  bottomStrip(s);
  return s;
}

let page = 1;
function content(title) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  topBand(s);
  s.addText(title, { x: 0.4, y: 0.9, w: 9.2, h: 0.6, fontFace: HEAD, fontSize: 24, color: RED,
    align: "center", valign: "middle", margin: 0 });
  page += 1;
  s.addText("SkillBridge Analytics  ·  NMIMS STME, Hyderabad", { x: 0.4, y: 5.2, w: 6, h: 0.25,
    fontFace: BODY, fontSize: 10, color: MUTED, margin: 0 });
  s.addText(String(page), { x: 9.0, y: 5.2, w: 0.6, h: 0.25, fontFace: BODY, fontSize: 10, color: MUTED,
    align: "right", margin: 0 });
  bottomStrip(s);
  return s;
}

function card(s, x, y, w, h) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: TINT },
    line: { color: LINE, width: 0.75 } });
}
function heading(s, x, y, w, text, color = RED) {
  s.addText(text, { x, y, w, h: 0.35, fontFace: BODY, fontSize: 15, bold: true, color, margin: 0, isTextBox: true });
}
function bullets(s, items, opts) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1 } })),
    { fontFace: BODY, fontSize: 13, color: INK, paraSpaceAfter: 5, valign: "top", margin: 0, isTextBox: true, ...opts });
}
function stat(s, x, y, w, big, label, color = RED) {
  s.addText(big, { x, y, w, h: 0.5, fontFace: HEAD, fontSize: 24, color, margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.5, w, h: 0.4, fontFace: BODY, fontSize: 11, color: INK, margin: 0, valign: "top", isTextBox: true });
}

// ================================================================== 1. title
coverSlide("SkillBridge Analytics",
  "A Big-Data Pipeline for Skill-Gap Analysis and Campus Placement Prediction\n\nBig Data Analytics — Project Evaluation");

// ================================================================== 2. problem + objectives
let s = content("Problem Statement & Objectives");
card(s, 0.4, 1.6, 4.45, 3.5);
heading(s, 0.6, 1.72, 4.0, "The problem");
bullets(s, [
  "Placement cells spot at-risk students late, one by one, by intuition",
  "Skill advice is based on last year's recruiters, not today's market",
  "Job postings list required skills — but as unstructured text",
], { x: 0.6, y: 2.15, w: 4.05, h: 2.0 });
s.addText("Can job-posting text tell each student what to learn, and tell staff who needs help first?",
  { x: 0.6, y: 4.2, w: 4.05, h: 0.8, fontFace: BODY, fontSize: 13, italic: true, color: RED, margin: 0, valign: "top", isTextBox: true });
card(s, 5.15, 1.6, 4.45, 3.5);
heading(s, 5.35, 1.72, 4.0, "Objectives");
[["Extract", "skills from free-text job postings (NLP)"],
 ["Measure", "each student's alignment with market demand"],
 ["Predict", "each student's placement probability"],
 ["Act", "dashboard with gaps, risk tiers, what-if"],
 ["Scale", "Kafka, Airflow, Elasticsearch, S3"]].forEach(([h, d], i) => {
  const y = 2.2 + i * 0.56;
  s.addShape(pres.shapes.OVAL, { x: 5.35, y, w: 0.36, h: 0.36, fill: { color: RED }, line: { type: "none" } });
  s.addText(String(i + 1), { x: 5.35, y, w: 0.36, h: 0.36, fontFace: BODY, fontSize: 12, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText([{ text: `${h}  `, options: { bold: true, color: RED } }, { text: d, options: { color: INK } }],
    { x: 5.85, y, w: 3.6, h: 0.36, fontFace: BODY, fontSize: 13, valign: "middle", margin: 0, isTextBox: true });
});

// ================================================================== 3. data + tech stack
s = content("Data & Tech Stack");
fitImage(s, FLOW("2_techstack_flow.png"), 0.35, 1.55, 4.9, 3.6, "Tech stack flow");
card(s, 5.5, 1.6, 4.1, 3.5);
heading(s, 5.7, 1.72, 3.7, "Real data (Kaggle)");
stat(s, 5.7, 2.1, 1.8, "215", "students with real placement outcomes");
stat(s, 7.55, 2.1, 1.9, "1,500", "LinkedIn job postings sampled");
heading(s, 5.7, 3.1, 3.7, "Synthetic data (validation)");
bullets(s, [
  "300 postings + 200 students with known skills",
  "Gives exact precision/recall for the NLP extractor",
  "Real data has no skill list → imputed from specialisation (a stated limitation)",
], { x: 5.7, y: 3.5, w: 3.75, h: 1.55, fontSize: 12 });

// ================================================================== 4. project flow
s = content("Project Flow (Architecture)");
fitImage(s, FLOW("1_project_flow.png"), 0.3, 1.55, 6.9, 3.6, "Project flow");
card(s, 7.35, 1.6, 2.3, 3.5);
heading(s, 7.5, 1.72, 2.0, "Four stages");
bullets(s, [
  "Ingest real data (synthetic fallback)",
  "Extract skills with spaCy",
  "Build features: demand, alignment, gaps",
  "Train & pick best model by AUC",
  "Airflow runs all four in order",
], { x: 7.5, y: 2.12, w: 2.05, h: 2.9, fontSize: 12 });

// ================================================================== 5. methodology + results
s = content("Methodology & Results");
card(s, 0.4, 1.6, 4.3, 3.5);
heading(s, 0.6, 1.72, 3.9, "How it works");
bullets(s, [
  "Skill NER: spaCy PhraseMatcher, ~150 skills in 8 categories; precision 99.2%, recall 99.7%",
  "Demand d(s) = share of postings asking for skill s",
  "Alignment = demand covered by the student's skills ÷ total demand",
  "6 features → logistic regression vs XGBoost, 75/25 stratified split, best ROC AUC kept",
], { x: 0.6, y: 2.12, w: 3.95, h: 2.9, fontSize: 12 });
stat(s, 5.0, 1.6, 1.5, AUC, "ROC AUC (real data)");
stat(s, 6.6, 1.6, 1.5, ACC, "accuracy (real data)");
stat(s, 8.2, 1.6, 1.5, am.xgboost.auc.toFixed(3), "XGBoost AUC (not selected)", MUTED);
s.addChart(pres.charts.BAR, [
  { name: "ROC AUC", labels: ["Logistic regression", "XGBoost"], values: [am.logistic_regression.auc, am.xgboost.auc] },
  { name: "Accuracy", labels: ["Logistic regression", "XGBoost"], values: [am.logistic_regression.accuracy, am.xgboost.accuracy] },
], { x: 4.9, y: 2.55, w: 4.75, h: 2.55, barDir: "col", barGrouping: "clustered", chartColors: [RED, "7F7F7F"],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", showLegend: true, legendPos: "b",
  valAxisMinVal: 0, valAxisMaxVal: 1, valAxisHidden: true, valGridLine: { style: "none" },
  catAxisLabelFontFace: BODY, catAxisLabelFontSize: 11, dataLabelFontSize: 10, legendFontSize: 11, legendFontFace: BODY });
s.addNotes("CGPA is the strongest predictor (coefficient 2.24), then internships (0.69). Skill features are weak because skills were imputed, so the high AUC is not evidence that skills predict placement.");

// ================================================================== 6. scenario
s = content("Scenario: Helping Student S0001");
fitImage(s, FLOW("3_scenario_flow.png"), 0.3, 1.55, 9.4, 3.3, "Scenario flow");
s.addText("Officer opens the student → model scores 85.6% (On track) → what-if adds Agile + C → Elasticsearch finds matching jobs → cohort list shows 50 at-risk students to help first.",
  { x: 0.4, y: 4.85, w: 9.2, h: 0.35, fontFace: BODY, fontSize: 11.5, italic: true, color: INK, align: "center", margin: 0, isTextBox: true });

// ================================================================== 7. live system
s = content("Live System: Dashboard & Airflow");
[["student", "Student 360"], ["simulator", "What-if simulator"], ["cohort", "Cohort analytics"], ["airflow", "Airflow DAG — all tasks green"]]
  .forEach(([n, cap], i) => {
    const x = 0.4 + (i % 2) * 3.2, y = 1.55 + Math.floor(i / 2) * 1.82;
    s.addImage({ path: SHOT(n), x, y, w: 2.5, h: 1.5625, altText: cap, line: { color: "BFBFBF", width: 0.75 } });
    s.addText(cap, { x, y: y + 1.57, w: 3.0, h: 0.22, fontFace: BODY, fontSize: 10.5, bold: true, color: RED, margin: 0, isTextBox: true });
  });
card(s, 6.75, 1.6, 2.9, 3.5);
heading(s, 6.95, 1.72, 2.5, "What it does");
bullets(s, [
  "Probability gauge, risk tier and skill radar per student",
  "What-if: change CGPA or skills, see the effect",
  "Cohort view: who to help first, downloadable list",
  "Market pulse from 1,500 real postings",
  "Airflow pipeline: 4 tasks, ~33 s per run",
], { x: 6.95, y: 2.12, w: 2.55, h: 2.9, fontSize: 12 });

// ================================================================== 8. development + testing
s = content("Development Flow & Testing");
fitImage(s, FLOW("4_development_flow.png"), 0.3, 1.5, 9.4, 2.95, "Development flow");
[["31", "automated tests, all passing on real data"],
 ["5", "real bugs found and fixed"],
 ["84.5→99.2%", "extractor precision after fixes"],
 ["1,500/1,500", "postings indexed in Elasticsearch"]].forEach(([b, l], i) => {
  const x = 0.4 + i * 2.33;
  s.addText(b, { x, y: 4.45, w: 2.2, h: 0.4, fontFace: HEAD, fontSize: 18, color: RED, margin: 0, isTextBox: true });
  s.addText(l, { x, y: 4.83, w: 2.2, h: 0.35, fontFace: BODY, fontSize: 10.5, color: INK, margin: 0, valign: "top", isTextBox: true });
});
s.addNotes("Bugs fixed: answer key missed soft skills and overlaps double-counted; Airflow overwrote real data; 15 postings rejected by Elasticsearch because a missing company was sent as NaN; dashboard crashed on models trained in Airflow (scikit-learn version mismatch); unpinned Elasticsearch client v9 couldn't talk to the v8 server.");

// ================================================================== 9. limitations + conclusion
s = content("Limitations, Future Work & Conclusion");
const cols = [
  ["Limitations", ["Real student skills were imputed, not recorded", "Taxonomy misses new or unusual skill names", "Demand not split by region or seniority"]],
  ["Future work", ["Collect real student skills via upload", "Learned skill-NER on annotated postings", "Spark + Delta Lake for larger volumes", "Track a full placement season"]],
  ["Conclusion", [`Works end to end on real data: AUC ${AUC}, accuracy ${ACC}`, "Real big-data stack: Kafka, Airflow, Elasticsearch, S3", "Honest about limits; 31 tests guard it"]],
];
cols.forEach(([h, items], i) => {
  const x = 0.4 + i * 3.1;
  card(s, x, 1.6, 2.9, 3.2);
  heading(s, x + 0.2, 1.72, 2.5, h, i === 2 ? GREEN : RED);
  bullets(s, items, { x: x + 0.2, y: 2.15, w: 2.55, h: 2.55, fontSize: 12.5 });
});
s.addText("Source code: github.com/Vikram5002/Equilearn", { x: 0.4, y: 4.85, w: 9.2, h: 0.3, fontFace: BODY,
  fontSize: 12, color: BLUE, align: "center", margin: 0, isTextBox: true });

// ================================================================== 10. thank you
coverSlide("Thank You", "Questions?");

pres.writeFile({ fileName: OUT }).then(() => console.log("saved", OUT));

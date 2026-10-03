// Builds rsp/ppt/SkillBridge_Evaluation.pptx — the deck for the project evaluator.
// Run (from repo root): cd rsp && npm install && cd .. && node rsp/ppt/build_evaluation_ppt.js
// Screenshots come from rsp/ppt/screens (python rsp/ppt/capture_screens.py).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("../apply_theme.js");

const HERE = __dirname;
const ROOT = path.join(HERE, "..", "..");
const OUT = path.join(HERE, "SkillBridge_Evaluation.pptx");
const SHOT = (n) => path.join(HERE, "screens", `${n}.png`);
const FIG = (n) => path.join(HERE, "..", "figures", n);

const THEME = {
  name: "SkillBridge",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14142B", lt1: "FFFFFF", dk2: "1E1B4B", lt2: "F1F0FB",
    accent1: "5B3DF5", accent2: "0E9F6E", accent3: "E02454", accent4: "D97706",
    accent5: "0284C7", accent6: "64748B", hlink: "5B3DF5", folHlink: "6D28D9",
  },
};
const HEX = THEME.colors;

const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, "data/processed/model_metrics.json"), "utf8"));
const market = fs.readFileSync(path.join(ROOT, "data/processed/market_skill_demand.csv"), "utf8")
  .trim().split(/\r?\n/).slice(1).map((l) => l.split(","));
const pct = (x) => `${(x * 100).toFixed(1)}%`;
const AUC = metrics.auc.toFixed(3);
const ACC = pct(metrics.accuracy);

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Vikram, Jahnavy, Jansi";
pres.title = "SkillBridge Analytics — Project Evaluation";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "DARK_TITLE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.3, w: 8.8, h: 1.6,
        fontSize: 38, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.1, w: 8.8, h: 1.8,
        fontSize: 16, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.75,
        fontSize: 28, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "SkillBridge Analytics  ·  Vikram, Jahnavy, Jansi", options: { x: 0.5, y: 5.2, w: 6, h: 0.3,
        fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

let section = "Introduction";
const content = (title) => {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
};
const newSection = (t) => { section = t; pres.addSection({ title: t }); };

function card(s, x, y, w, h, fill = C.background2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12,
    fill: { color: fill }, line: { type: "none" } });
}
function dot(s, x, y, label, color = C.accent1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color }, line: { type: "none" } });
  s.addText(String(label), { x, y, w: 0.5, h: 0.5, align: "center", valign: "middle", fontSize: 15,
    bold: true, color: C.background1, margin: 0, isTextBox: true });
}
function stat(s, x, y, w, big, label, color = C.accent1, size = 40) {
  s.addText(big, { x, y, w, h: 0.85, fontSize: size, bold: true, color, fontFace: THEME.headFontFace,
    margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.85, w, h: 0.6, fontSize: 13, color: C.text1, margin: 0,
    valign: "top", isTextBox: true });
}
function bullets(s, items, opts) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { fontSize: 14, color: C.text1, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true, ...opts });
}
// screenshot slide: framed image on the left, talking points on the right
function shotSlide(title, shot, heading, points, note) {
  const s = content(title);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.1, w: 6.1, h: 3.86, rectRadius: 0.06,
    fill: { color: C.text2 }, line: { type: "none" } });
  s.addImage({ path: shot, x: 0.5, y: 1.15, w: 6.0, h: 3.75, altText: title });
  s.addText(heading, { x: 6.8, y: 1.15, w: 2.7, h: 0.5, fontSize: 16, bold: true, color: C.accent1,
    margin: 0, isTextBox: true });
  bullets(s, points, { x: 6.8, y: 1.7, w: 2.7, h: 2.6, fontSize: 13 });
  if (note) s.addText(note, { x: 6.8, y: 4.3, w: 2.7, h: 0.7, fontSize: 11, italic: true, color: C.accent6,
    margin: 0, valign: "bottom", isTextBox: true });
  if (note) s.addNotes(note);
  return s;
}
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", legendFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, dataLabelFontSize: 10, legendFontSize: 11,
  catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent6, dataLabelColor: HEX.dk1,
  titleFontSize: 12, titleColor: HEX.dk1, valGridLine: { color: "E4E2F5", size: 0.5 },
  catGridLine: { style: "none" } };

// ================================================================== INTRO
newSection("Introduction");
let s = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: section });
s.addText("SkillBridge Analytics", { placeholder: "title" });
s.addText([
  { text: "A big-data pipeline for skill-gap analysis and campus placement prediction", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Vikram  ·  Jahnavy  ·  Jansi", options: { bold: true, color: C.accent2, breakLine: true } },
  { text: "Big Data Analytics — Project Evaluation", options: { fontSize: 14 } },
], { placeholder: "body" });

s = content("Agenda");
const agenda = ["Problem & objectives", "Data", "Architecture & tech stack", "Methodology",
  "Results", "Live system", "Testing & quality", "Limitations & future work"];
agenda.forEach((t, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.3 + row * 0.92;
  dot(s, x, y, i + 1, [C.accent1, C.accent2, C.accent5, C.accent4][row]);
  s.addText(t, { x: x + 0.7, y, w: 3.7, h: 0.5, fontSize: 17, color: C.text2, valign: "middle",
    margin: 0, isTextBox: true });
});

s = content("Problem statement");
const problems = [
  ["Late, manual risk spotting", "Placement cells find at-risk students by intuition, one by one, late in the season"],
  ["Outdated skill advice", "Recommendations come from last year's recruiters, not today's job market"],
  ["Data locked in text", "Thousands of postings a week list required skills — but as unstructured text"],
];
problems.forEach(([h, d], i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.3, 2.85, 2.95);
  dot(s, x + 0.3, 1.55, i + 1, [C.accent3, C.accent4, C.accent5][i]);
  s.addText(h, { x: x + 0.3, y: 2.2, w: 2.3, h: 0.7, fontSize: 17, bold: true, color: C.text2,
    margin: 0, valign: "top", isTextBox: true });
  s.addText(d, { x: x + 0.3, y: 2.9, w: 2.3, h: 1.25, fontSize: 13, color: C.text1, margin: 0,
    valign: "top", isTextBox: true });
});
s.addText("Question: can job-posting text tell each student what to learn, and tell staff who needs help first?",
  { x: 0.5, y: 4.45, w: 9, h: 0.5, fontSize: 15, italic: true, color: C.accent1, margin: 0, isTextBox: true });

s = content("Objectives");
const objectives = [
  ["Extract", "Recognise skills in free-text job postings automatically"],
  ["Measure", "Score how well each student's skills match current market demand"],
  ["Predict", "Estimate each student's placement probability"],
  ["Act", "Give staff and students a dashboard with gaps, risk tiers and what-if analysis"],
  ["Scale", "Run it on a real big-data stack: Kafka, Airflow, Elasticsearch, S3"],
];
objectives.forEach(([h, d], i) => {
  const y = 1.2 + i * 0.78;
  dot(s, 0.5, y + 0.05, i + 1, [C.accent1, C.accent2, C.accent5, C.accent4, C.accent3][i]);
  s.addText(h, { x: 1.2, y, w: 1.6, h: 0.6, fontSize: 18, bold: true, color: C.text2, valign: "middle",
    margin: 0, isTextBox: true });
  s.addText(d, { x: 2.9, y, w: 6.6, h: 0.6, fontSize: 15, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
});

// ================================================================== DATA + ARCHITECTURE
newSection("Data & architecture");
s = content("Data");
card(s, 0.5, 1.25, 4.35, 3.65);
card(s, 5.15, 1.25, 4.35, 3.65);
s.addText("Real data (Kaggle)", { x: 0.8, y: 1.4, w: 3.8, h: 0.45, fontSize: 17, bold: true, color: C.accent2, margin: 0, isTextBox: true });
stat(s, 0.8, 1.9, 1.8, "215", "students with real placement outcomes", C.accent2, 34);
stat(s, 2.75, 1.9, 1.9, "1,500", "LinkedIn postings sampled from ~500 MB", C.accent2, 34);
bullets(s, ["Placement rate 68.8%", "No skills in source data → imputed from specialisation (stated limitation)"],
  { x: 0.8, y: 3.45, w: 3.85, h: 1.35, fontSize: 13 });
s.addText("Synthetic data (validation)", { x: 5.45, y: 1.4, w: 3.8, h: 0.45, fontSize: 17, bold: true, color: C.accent1, margin: 0, isTextBox: true });
stat(s, 5.45, 1.9, 1.8, "300", "generated postings with known skills", C.accent1, 34);
stat(s, 7.4, 1.9, 1.9, "200", "generated students", C.accent1, 34);
bullets(s, ["Ground-truth skills allow exact precision/recall", "Used to test the extractor, not to report model accuracy"],
  { x: 5.45, y: 3.45, w: 3.85, h: 1.35, fontSize: 13 });
s.addNotes("We deliberately avoided scraping LinkedIn/Naukri because of their terms of service; both datasets are public on Kaggle.");

s = content("System architecture");
s.addImage({ path: FIG("fig1_architecture.png"), x: 0.9, y: 1.1, w: 8.2, h: 3.42, altText: "Architecture diagram" });
s.addText("Each stage reads the previous stage's output — every stage runs and is tested on its own.",
  { x: 0.5, y: 4.6, w: 9, h: 0.4, fontSize: 13, color: C.accent6, align: "center", margin: 0, isTextBox: true });

s = content("Technology choices");
const stack = [
  ["spaCy PhraseMatcher", "Skill NER", "Transparent, no training data, canonical names"],
  ["scikit-learn + XGBoost", "Prediction", "Linear baseline vs boosted trees, pick by AUC"],
  ["Apache Kafka (KRaft)", "Streaming", "Postings processed as they arrive; no ZooKeeper"],
  ["Apache Airflow", "Orchestration", "4-task DAG; LocalExecutor for Windows stability"],
  ["Elasticsearch 8", "Search", "Find real postings asking for a missing skill"],
  ["Amazon S3", "Storage", "Versioned archive of models and training data"],
  ["Streamlit + Plotly", "Dashboard", "Interactive UI built directly on the pipeline"],
];
const head = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 } } });
s.addTable([
  [head("Tool"), head("Role"), head("Why we chose it")],
  ...stack.map(([a, b, c], i) => [a, b, c].map((t, j) => ({ text: t, options: {
    bold: j === 0, fill: { color: i % 2 ? HEX.lt1 : HEX.lt2 } } }))),
], { x: 0.5, y: 1.15, w: 9, colW: [2.6, 1.6, 4.8], fontSize: 12, color: HEX.dk1,
  border: { type: "solid", pt: 0.5, color: "E4E2F5" }, rowH: 0.44, valign: "middle" });

// ================================================================== METHODS
newSection("Methodology");
s = content("Skill extraction (NLP)");
bullets(s, [
  "Taxonomy of ~150 skills in 8 categories",
  "Case-insensitive matching, except Go, C, R — stops \"go above and beyond\" being read as the Go language",
  "Overlapping matches keep the longest span: \"AWS Certified Solutions Architect\" is not also counted as \"AWS\"",
  "Same function runs in batch and on each Kafka message",
], { x: 0.5, y: 1.25, w: 5.1, h: 3.6, fontSize: 15 });
card(s, 6.0, 1.25, 3.5, 3.6);
stat(s, 6.3, 1.45, 3.0, "99.2%", "precision (up from 84.5% after our fixes)", C.accent2);
stat(s, 6.3, 3.05, 3.0, "99.7%", "recall, on synthetic postings with ground truth", C.accent1);

s = content("Market demand & alignment score");
card(s, 0.5, 1.25, 3.9, 3.65);
s.addText([
  { text: "Demand of a skill", options: { bold: true, color: C.accent1, breakLine: true } },
  { text: "d(s) = postings mentioning s ÷ all postings", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Student alignment", options: { bold: true, color: C.accent1, breakLine: true } },
  { text: "A(u) = Σ d(s) over the student's skills ÷ Σ d(s) over all skills", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "0 = covers nothing employers ask for, 1 = covers everything. Gaps are ranked by d(s).", options: { italic: true } },
], { x: 0.75, y: 1.45, w: 3.45, h: 3.3, fontSize: 13, color: C.text1, valign: "top", margin: 0, isTextBox: true });
const top = market.slice(0, 8);
s.addChart(pres.charts.BAR, [{ name: "% of postings", labels: top.map((r) => r[0]).reverse(),
  values: top.map((r) => +(r[2] * 100).toFixed(1)).reverse() }],
  { x: 4.6, y: 1.15, w: 4.9, h: 3.8, barDir: "bar", chartColors: [HEX.accent1], showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", showLegend: false, showTitle: true,
    title: "Most requested skills — 1,500 real LinkedIn postings", valAxisHidden: true, ...chartText });

s = content("Placement prediction model");
bullets(s, [
  "6 features: CGPA, projects, certifications, internships, skill count, alignment score",
  "Standardised; 75/25 stratified split, fixed seed",
  "Logistic regression vs XGBoost — higher held-out ROC AUC is kept",
  "AUC chosen because staff need a ranking of who to help first",
], { x: 0.5, y: 1.25, w: 4.0, h: 3.6, fontSize: 14 });
const am = metrics.all_models;
s.addChart(pres.charts.BAR, [
  { name: "ROC AUC", labels: ["Logistic regression", "XGBoost"], values: [am.logistic_regression.auc, am.xgboost.auc] },
  { name: "Accuracy", labels: ["Logistic regression", "XGBoost"], values: [am.logistic_regression.accuracy, am.xgboost.accuracy] },
], { x: 4.7, y: 1.15, w: 4.8, h: 3.8, barDir: "col", barGrouping: "clustered",
  chartColors: [HEX.accent1, HEX.accent2], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0.000", showLegend: true, legendPos: "b", showTitle: true,
  title: "Held-out results on real data", valAxisMinVal: 0, valAxisMaxVal: 1, valAxisHidden: true, ...chartText });

// ================================================================== RESULTS
newSection("Results");
s = content("Results at a glance");
[[AUC, "ROC AUC on real data", C.accent2], [ACC, "accuracy on real data", C.accent2],
 ["99.2%", "skill-extraction precision", C.accent1], ["1,500", "real postings indexed and searchable", C.accent5]]
  .forEach(([big, lbl, col], i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.3, 2.1, 2.2);
    stat(s, x + 0.2, 1.6, 1.8, big, lbl, col, 34);
  });
bullets(s, [
  "Logistic regression selected; CGPA is the strongest predictor (coefficient 2.24), then internships (0.69)",
  "Airflow DAG: all 4 tasks succeed in ~33 s  ·  Kafka: 10/10 streamed postings processed live",
], { x: 0.5, y: 3.8, w: 9, h: 1.1, fontSize: 14 });

const imp = metrics.feature_importances;
s = content("What drives placement in this data");
const featNames = Object.keys(imp).sort((a, b) => Math.abs(imp[a]) - Math.abs(imp[b]));
s.addChart(pres.charts.BAR, [{ name: "Coefficient", labels: featNames.map((f) => f.replace(/_/g, " ")),
  values: featNames.map((f) => +imp[f].toFixed(2)) }],
  { x: 0.5, y: 1.15, w: 5.4, h: 3.8, barDir: "bar", chartColors: [HEX.accent1], showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", showLegend: false, showTitle: true,
    title: "Standardised logistic-regression coefficients", valAxisHidden: true, catAxisLabelPos: "low", ...chartText });
card(s, 6.2, 1.25, 3.3, 3.65);
s.addText("Honest reading", { x: 6.45, y: 1.4, w: 2.9, h: 0.45, fontSize: 16, bold: true, color: C.accent4, margin: 0, isTextBox: true });
bullets(s, [
  "Academics dominate — expected for this dataset",
  "Projects and certifications are 0: not recorded in the source",
  "Skill features are weak because skills were imputed, so the high AUC is not evidence that skills predict placement",
], { x: 6.45, y: 1.9, w: 2.9, h: 2.9, fontSize: 13 });

// ================================================================== LIVE SYSTEM
newSection("Live system");
shotSlide("Dashboard — Student 360", SHOT("student"), "One student, one page", [
  "Placement probability gauge with risk tier",
  "KPIs compared with the cohort median",
  "Skill-coverage radar vs cohort average",
  "Gaps ranked by market demand",
]);
shotSlide("Dashboard — What-if simulator", SHOT("simulator"), "Try a change, see the effect", [
  "Edit CGPA, projects, internships or add skills",
  "Probability and alignment recompute instantly",
  "Ranks the single most useful skill to learn",
], "On the real data, adding skills lowers the estimate — the dashboard says so and explains why, rather than hiding it.");
shotSlide("Dashboard — Cohort analytics", SHOT("cohort"), "Who needs help first", [
  "Distribution of predicted probabilities",
  "Alignment vs outlook for every student",
  "Most common gaps across the cohort",
  "Downloadable intervention list",
]);
shotSlide("Dashboard — Market pulse", SHOT("market"), "What employers ask for", [
  "Top-N skills from 1,500 real postings",
  "Demand grouped by skill category",
  "Filter by job title (e.g. \"Data\", \"Engineer\")",
]);
shotSlide("Orchestration — Apache Airflow", SHOT("airflow"), "One DAG, four tasks", [
  "ingest → extract → features → train",
  "Uses real data when present, synthetic otherwise",
  "Verified green on real data, ~33 s per run",
]);
shotSlide("Dashboard — Data Studio", SHOT("data"), "Bring your own data", [
  "Upload postings and student CSVs",
  "Validated: columns, numbers, duplicate IDs",
  "Re-runs the pipeline with live progress",
]);

// ================================================================== QUALITY
newSection("Testing & quality");
s = content("Testing");
stat(s, 0.5, 1.3, 3.0, "31", "automated tests, all passing on real data", C.accent2, 54);
bullets(s, [
  "NLP extractor: casing, overlaps, empty text, ambiguous short names",
  "Feature store: empty input, students without skills",
  "Upload validation and training guards",
  "Kafka message handling and S3 upload (no live services needed)",
  "Every dashboard page rendered automatically",
], { x: 3.9, y: 1.3, w: 5.6, h: 3.6, fontSize: 14 });

s = content("Bugs we found and fixed");
const bugs = [
  ["Extractor precision only 84.5%", "Answer key missed soft skills; overlaps double-counted", "99.2%"],
  ["Airflow overwrote real data", "Ingest always generated synthetic data", "Prefers real data"],
  ["15 postings not searchable", "Missing company sent as NaN (invalid JSON)", "1,500 / 1,500"],
  ["Dashboard crash after Airflow run", "Different scikit-learn in Airflow vs local", "Versions pinned"],
  ["Fresh install couldn't search", "Unpinned client v9 vs Elasticsearch 8 server", "Client pinned to v8"],
];
s.addTable([
  [head("Symptom"), head("Root cause"), head("Result")],
  ...bugs.map((r, i) => r.map((t, j) => ({ text: t, options: {
    bold: j === 2, color: j === 2 ? HEX.accent2 : HEX.dk1, fill: { color: i % 2 ? HEX.lt1 : HEX.lt2 } } }))),
], { x: 0.5, y: 1.15, w: 9, colW: [3.0, 4.1, 1.9], fontSize: 12, color: HEX.dk1,
  border: { type: "solid", pt: 0.5, color: "E4E2F5" }, rowH: 0.55, valign: "middle" });

// ================================================================== CLOSE
newSection("Conclusion");
s = content("Limitations and future work");
card(s, 0.5, 1.25, 4.35, 3.0);
card(s, 5.15, 1.25, 4.35, 3.0);
s.addText("Limitations", { x: 0.8, y: 1.4, w: 3.8, h: 0.45, fontSize: 17, bold: true, color: C.accent3, margin: 0, isTextBox: true });
bullets(s, ["Real student skills were imputed, not recorded", "Taxonomy misses new or unusual skill names",
  "Demand not split by region or seniority"], { x: 0.8, y: 1.95, w: 3.85, h: 2.2, fontSize: 14 });
s.addText("Future work", { x: 5.45, y: 1.4, w: 3.8, h: 0.45, fontSize: 17, bold: true, color: C.accent2, margin: 0, isTextBox: true });
bullets(s, ["Collect real student skills via upload", "Learned skill-NER on annotated postings",
  "Spark + Delta Lake for larger volumes", "Track a full placement season"], { x: 5.45, y: 1.95, w: 3.85, h: 2.2, fontSize: 14 });

s = content("Conclusion");
const takeaways = [
  ["Works end to end", "Postings → skills → gaps → prediction → dashboard, on real data"],
  ["Strong, honest results", `AUC ${AUC}, accuracy ${ACC}, with clearly stated limits`],
  ["Real big-data stack", "Kafka, Airflow and Elasticsearch verified live; S3 upload covered by tests"],
];
takeaways.forEach(([h, d], i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.3, 2.85, 2.6);
  dot(s, x + 0.3, 1.55, "✓", [C.accent2, C.accent1, C.accent5][i]);
  s.addText(h, { x: x + 0.3, y: 2.2, w: 2.3, h: 0.5, fontSize: 17, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText(d, { x: x + 0.3, y: 2.7, w: 2.3, h: 1.1, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
});
s.addText("Source code: github.com/Vikram5002/Equilearn", { x: 0.5, y: 4.3, w: 9, h: 0.45, fontSize: 15,
  color: C.accent1, align: "center", margin: 0, isTextBox: true });

s = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: section });
s.addText("Thank you", { placeholder: "title" });
s.addText([
  { text: "Questions?", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Vikram  ·  Jahnavy  ·  Jansi", options: { bold: true, color: C.accent2, breakLine: true } },
  { text: "github.com/Vikram5002/Equilearn", options: {} },
], { placeholder: "body" });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("saved", OUT);
})();

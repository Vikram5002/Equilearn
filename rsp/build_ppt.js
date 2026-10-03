// Builds rsp/SkillBridge_Presentation.pptx
// Run (from repo root): cd rsp && npm install && cd .. && node rsp/build_ppt.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const OUT = path.join(__dirname, "SkillBridge_Presentation.pptx");
const FIG = path.join(__dirname, "figures");
const ROOT = path.join(__dirname, "..");

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

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Vikram, Jahnavy, Jansi";
pres.title = "SkillBridge Analytics";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "DARK_TITLE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.5,
        fontSize: 38, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.15, w: 8.8, h: 1.2,
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
    { text: { text: "SkillBridge Analytics", options: { x: 0.5, y: 5.2, w: 4, h: 0.3, fontSize: 10,
        color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

const content = (title, section) => {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
};

function card(s, x, y, w, h, fill = C.background2) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12,
    fill: { color: fill }, line: { type: "none" } });
}

function numberDot(s, x, y, n, color = C.accent1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color }, line: { type: "none" } });
  s.addText(String(n), { x, y, w: 0.5, h: 0.5, align: "center", valign: "middle", fontSize: 16,
    bold: true, color: C.background1, margin: 0, isTextBox: true });
}

function stat(s, x, y, w, big, label, color = C.accent1, size = 44) {
  s.addText(big, { x, y, w, h: 0.9, fontSize: size, bold: true, color, fontFace: THEME.headFontFace,
    margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.9, w, h: 0.6, fontSize: 13, color: C.text1, margin: 0,
    valign: "top", isTextBox: true });
}

const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", catAxisLabelFontSize: 11,
  valAxisLabelFontSize: 10, dataLabelFontSize: 10, catAxisLabelColor: HEX.dk1,
  valAxisLabelColor: HEX.accent6 };

// ------------------------------------------------------------------ 1 title
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: "Introduction" });
s.addText("SkillBridge Analytics", { placeholder: "title" });
s.addText([
  { text: "Skill-gap analysis and placement prediction from job-posting text", options: { breakLine: true } },
  { text: "Vikram  ·  Jahnavy  ·  Jansi", options: { bold: true, color: C.accent2 } },
], { placeholder: "body" });
s.addNotes("Introduce the team and the one-line goal: use real job postings to tell each student what to learn and who needs help first.");

// ------------------------------------------------------------------ 2 problem
s = content("Placement cells decide with old information", "Introduction");
const problems = [
  ["Who is at risk?", "Spotted by intuition, student by student, late in the season"],
  ["What should they learn?", "Advice comes from last year's recruiters, not today's postings"],
  ["What does the market want?", "Thousands of postings a week, all unstructured text"],
];
problems.forEach(([h, d], i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.35, 2.85, 2.9);
  numberDot(s, x + 0.3, 1.6, i + 1, [C.accent3, C.accent4, C.accent5][i]);
  s.addText(h, { x: x + 0.3, y: 2.25, w: 2.3, h: 0.7, fontSize: 18, bold: true, color: C.text2,
    margin: 0, valign: "top", isTextBox: true });
  s.addText(d, { x: x + 0.3, y: 2.95, w: 2.3, h: 1.2, fontSize: 14, color: C.text1, margin: 0,
    valign: "top", isTextBox: true });
});
s.addText("Goal: turn job-posting text into a per-student action plan.", { x: 0.5, y: 4.45, w: 9, h: 0.45,
  fontSize: 16, italic: true, color: C.accent1, margin: 0, isTextBox: true });

// ------------------------------------------------------------------ 3 pipeline
pres.addSection({ title: "System" });
s = content("Five stages from raw postings to a decision", "System");
const steps = [
  ["Ingest", "LinkedIn / CSV / Kafka stream + student records"],
  ["Extract", "spaCy matcher finds ~150 skills in text"],
  ["Feature store", "Demand per skill, gaps, alignment score"],
  ["Model", "LogReg vs XGBoost, best AUC wins"],
  ["Dashboard", "Student, cohort and market views"],
];
steps.forEach(([h, d], i) => {
  const x = 0.5 + i * 1.84;
  card(s, x, 1.5, 1.64, 2.6);
  numberDot(s, x + 0.57, 1.7, i + 1);
  s.addText(h, { x: x + 0.1, y: 2.35, w: 1.44, h: 0.5, fontSize: 15, bold: true, align: "center",
    color: C.text2, margin: 0, isTextBox: true });
  s.addText(d, { x: x + 0.12, y: 2.85, w: 1.4, h: 1.15, fontSize: 12, align: "center",
    color: C.text1, margin: 0, valign: "top", isTextBox: true });
});
s.addText("Orchestrated by Apache Airflow  ·  Outputs archived in Amazon S3", { x: 0.5, y: 4.4, w: 9,
  h: 0.4, fontSize: 14, color: C.accent6, align: "center", margin: 0, isTextBox: true });

// ------------------------------------------------------------------ 4 architecture
s = content("Architecture", "System");
s.addImage({ path: path.join(FIG, "fig1_architecture.png"), x: 0.9, y: 1.15, w: 8.2, h: 3.42 });
s.addText("Each stage reads the previous stage's output, so every stage can be tested on its own.",
  { x: 0.5, y: 4.65, w: 9, h: 0.4, fontSize: 13, color: C.accent6, align: "center", margin: 0, isTextBox: true });

// ------------------------------------------------------------------ 5 big data stack
s = content("Big-data stack", "System");
const stack = [
  ["Apache Kafka", "Streams postings in; same extractor runs per message"],
  ["Apache Airflow", "4-task DAG, LocalExecutor, ~12 s per run"],
  ["Elasticsearch", "Find real postings that ask for a missing skill"],
  ["Amazon S3", "Archives every model and its training data"],
  ["spaCy", "Fast phrase matching, no training data needed"],
  ["XGBoost + scikit-learn", "Two models compared on held-out AUC"],
];
stack.forEach(([h, d], i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.5 + col * 3.05, y = 1.3 + row * 1.85;
  card(s, x, y, 2.85, 1.6);
  s.addText(h, { x: x + 0.25, y: y + 0.2, w: 2.4, h: 0.45, fontSize: 16, bold: true, color: C.accent1,
    margin: 0, isTextBox: true });
  s.addText(d, { x: x + 0.25, y: y + 0.7, w: 2.4, h: 0.8, fontSize: 13, color: C.text1, margin: 0,
    valign: "top", isTextBox: true });
});

// ------------------------------------------------------------------ 6 extraction
pres.addSection({ title: "Methods" });
s = content("Skill extraction: 84% → 99% precision", "Methods");
s.addText([
  { text: "Taxonomy of ~150 skills in 8 categories", options: { bullet: true, breakLine: true } },
  { text: "Case-insensitive match, except Go, C and R (stops \"go above and beyond\")", options: { bullet: true, breakLine: true } },
  { text: "Overlaps keep the longest span: \"AWS Certified Solutions Architect\" ≠ extra \"AWS\"", options: { bullet: true, breakLine: true } },
  { text: "Fixed missing soft skill in the synthetic answer key", options: { bullet: true } },
], { x: 0.5, y: 1.3, w: 5.0, h: 3.3, fontSize: 15, color: C.text1, paraSpaceAfter: 10, valign: "top", isTextBox: true });
card(s, 6.0, 1.3, 3.5, 3.3);
stat(s, 6.3, 1.5, 3.0, "99.2%", "mean precision (was 84.5%)", C.accent2);
stat(s, 6.3, 3.0, 3.0, "99.7%", "mean recall on synthetic postings", C.accent1);

// ------------------------------------------------------------------ 7 alignment + market chart
s = content("Market alignment: share of demand covered", "Methods");
card(s, 0.5, 1.3, 3.9, 3.5);
s.addText([
  { text: "d(s) = postings with s ÷ all postings", options: { breakLine: true, bold: true } },
  { text: " ", options: { breakLine: true } },
  { text: "A(u) = Σ d(s) for the student's skills ÷ Σ d(s) for all skills", options: { breakLine: true, bold: true } },
  { text: " ", options: { breakLine: true } },
  { text: "0 = covers nothing employers ask for; 1 = covers everything. Skills never seen in postings earn no credit.", options: {} },
], { x: 0.75, y: 1.5, w: 3.4, h: 3.1, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0 });
const market = fs.readFileSync(path.join(ROOT, "data/processed/market_skill_demand.csv"), "utf8")
  .trim().split(/\r?\n/).slice(1, 9).map(l => l.split(","));
s.addChart(pres.charts.BAR, [{ name: "% of postings",
  labels: market.map(r => r[0]).reverse(), values: market.map(r => +(r[2] * 100).toFixed(1)).reverse() }],
  { x: 4.6, y: 1.2, w: 4.9, h: 3.7, barDir: "bar", chartColors: [HEX.accent1], showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", showLegend: false, showTitle: true,
    title: "Top skills in 1,500 real LinkedIn postings", titleFontSize: 12, titleColor: HEX.dk1,
    valGridLine: { color: "E4E2F5", size: 0.5 }, catGridLine: { style: "none" }, valAxisHidden: true,
    ...chartText, dataLabelColor: HEX.dk1 });

// ------------------------------------------------------------------ 8 model
s = content("Placement model", "Methods");
stat(s, 0.5, 1.35, 3.6, "0.947", "ROC AUC on real campus-placement + LinkedIn data", C.accent2);
s.addText([
  { text: "6 features: CGPA, projects, certifications, internships, skill count, alignment", options: { bullet: true, breakLine: true } },
  { text: "75/25 stratified split; higher held-out AUC wins", options: { bullet: true, breakLine: true } },
  { text: "CGPA proxy dominates on real data", options: { bullet: true } },
], { x: 0.5, y: 3.0, w: 3.8, h: 1.9, fontSize: 14, color: C.text1, paraSpaceAfter: 6, valign: "top", isTextBox: true, margin: 0 });
s.addChart(pres.charts.BAR, [
  { name: "ROC AUC", labels: ["Logistic regression", "XGBoost"], values: [0.947, 0.896] },
  { name: "Accuracy", labels: ["Logistic regression", "XGBoost"], values: [0.833, 0.778] },
], { x: 4.6, y: 1.2, w: 4.9, h: 3.7, barDir: "col", barGrouping: "clustered",
  chartColors: [HEX.accent1, HEX.accent2], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0.00", showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 11,
  showTitle: true, title: "Real data: campus placement + LinkedIn", titleFontSize: 12, titleColor: HEX.dk1,
  valAxisMinVal: 0, valAxisMaxVal: 1, valAxisHidden: true, valGridLine: { color: "E4E2F5", size: 0.5 },
  catGridLine: { style: "none" }, ...chartText, dataLabelColor: HEX.dk1 });

// ------------------------------------------------------------------ 9 dashboard
pres.addSection({ title: "Results" });
s = content("Dashboard: five pages", "Results");
const pages = [
  ["Student 360", "Probability gauge, risk tier, skill radar, ranked gaps", C.accent1],
  ["What-if simulator", "Change CGPA or add skills, see the new probability", C.accent2],
  ["Cohort analytics", "Risk distribution and downloadable intervention list", C.accent3],
  ["Market pulse", "Top skills, category treemap, full skill table", C.accent5],
  ["Data Studio", "Upload CSVs, validate, re-run the pipeline", C.accent4],
];
pages.forEach(([h, d, col], i) => {
  const y = 1.25 + i * 0.78;
  s.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.08, w: 0.45, h: 0.45, fill: { color: col }, line: { type: "none" } });
  s.addText(h, { x: 1.15, y, w: 2.4, h: 0.6, fontSize: 16, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true });
  s.addText(d, { x: 3.6, y, w: 5.9, h: 0.6, fontSize: 14, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
});

// ------------------------------------------------------------------ 10 results
s = content("Results at a glance", "Results");
const results = [
  ["0.947", "ROC AUC on real data", C.accent2],
  ["99.2%", "Skill-extraction precision", C.accent1],
  ["1,500", "Real postings indexed in Elasticsearch", C.accent5],
  ["30", "Automated tests, all passing", C.accent4],
];
results.forEach(([big, lbl, col], i) => {
  const x = 0.5 + i * 2.3;
  card(s, x, 1.5, 2.1, 2.6);
  stat(s, x + 0.2, 1.85, 1.8, big, lbl, col, 36);
});
s.addText("Kafka: 10/10 streamed postings processed live  ·  Airflow: all 4 tasks green", {
  x: 0.5, y: 4.4, w: 9, h: 0.4, fontSize: 14, color: C.accent6, align: "center", margin: 0, isTextBox: true });

// ------------------------------------------------------------------ 11 limitations
pres.addSection({ title: "Conclusion" });
s = content("Limitations and next steps", "Conclusion");
card(s, 0.5, 1.3, 4.35, 2.9);
card(s, 5.15, 1.3, 4.35, 2.9);
s.addText("Limitations", { x: 0.8, y: 1.45, w: 3.8, h: 0.5, fontSize: 18, bold: true, color: C.accent3, margin: 0, isTextBox: true });
s.addText([
  { text: "Real student skills were imputed from specialisation", options: { bullet: true, breakLine: true } },
  { text: "Taxonomy misses new or unusual skill names", options: { bullet: true, breakLine: true } },
  { text: "Demand not split by region or seniority", options: { bullet: true } },
], { x: 0.8, y: 2.0, w: 3.85, h: 2.6, fontSize: 14, color: C.text1, paraSpaceAfter: 8, valign: "top", isTextBox: true, margin: 0 });
s.addText("Next steps", { x: 5.45, y: 1.45, w: 3.8, h: 0.5, fontSize: 18, bold: true, color: C.accent2, margin: 0, isTextBox: true });
s.addText([
  { text: "Collect real student skills via upload", options: { bullet: true, breakLine: true } },
  { text: "Learned skill-NER on annotated postings", options: { bullet: true, breakLine: true } },
  { text: "Spark + Delta Lake at larger scale", options: { bullet: true, breakLine: true } },
  { text: "Track a full placement season", options: { bullet: true } },
], { x: 5.45, y: 2.0, w: 3.85, h: 2.6, fontSize: 14, color: C.text1, paraSpaceAfter: 8, valign: "top", isTextBox: true, margin: 0 });

// ------------------------------------------------------------------ 12 thanks
s = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: "Conclusion" });
s.addText("Thank you", { placeholder: "title" });
s.addText([
  { text: "Questions?", options: { breakLine: true } },
  { text: "github.com/Vikram5002/Equilearn", options: { color: C.accent2 } },
], { placeholder: "body" });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("saved", OUT);
})();

"""Draws the four project flow diagrams as PNGs in this folder.

Run (from repo root): python flow/make_flows.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent
plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]

INK, MUTED, BG = "#14142B", "#64748B", "#FFFFFF"
PAL = {  # border colour, light fill
    "indigo": ("#5B3DF5", "#EEEBFE"), "green": ("#0E9F6E", "#E3F6EF"),
    "blue": ("#0284C7", "#E2F2FB"), "amber": ("#D97706", "#FDF1E2"),
    "red": ("#E02454", "#FCE6EC"), "slate": ("#64748B", "#F1F3F7"),
}


def canvas(w_in, h_in, title, subtitle):
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h_in / w_in)
    ax.axis("off")
    top = 100 * h_in / w_in
    ax.text(2, top - 2.2, title, fontsize=22, fontweight="bold", color=INK, va="top")
    ax.text(2, top - 6.4, subtitle, fontsize=12, color=MUTED, va="top")
    return fig, ax


def box(ax, x, y, w, h, title, body="", color="indigo", tsize=11.5, bsize=9.5, num=None):
    edge, fill = PAL[color]
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                       linewidth=1.8, edgecolor=edge, facecolor=fill, zorder=2)
    ax.add_patch(p)
    ty = y + h / 2 - 1.6 if body else y
    label = f"{num}  {title}" if num is not None else title
    ax.text(x, ty, label, ha="center", va="top" if body else "center", fontsize=tsize,
            fontweight="bold", color=edge, zorder=3, wrap=True)
    if body:
        ax.text(x, ty - 2.6 - (tsize - 11.5) * 0.15, body, ha="center", va="top",
                fontsize=bsize, color=INK, zorder=3, linespacing=1.35)
    return p


def arrow(ax, a, b, color=MUTED, label=None, rad=0.0, style="-|>", dashed=False, lw=1.6, lpos=0.5,
          loff=(0, 1.2)):
    ax.annotate("", xy=(0, 0), xytext=(0, 0), xycoords="data")  # keeps annotate cache happy
    ca, cb = a.get_bbox(), b.get_bbox()
    pa = ((ca.x0 + ca.x1) / 2, (ca.y0 + ca.y1) / 2)
    pb = ((cb.x0 + cb.x1) / 2, (cb.y0 + cb.y1) / 2)
    ax.annotate("", xy=pb, xytext=pa, zorder=1,
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, patchA=a, patchB=b,
                                shrinkA=3, shrinkB=3, mutation_scale=16,
                                linestyle=(0, (4, 3)) if dashed else "solid",
                                connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx = pa[0] + (pb[0] - pa[0]) * lpos + loff[0]
        my = pa[1] + (pb[1] - pa[1]) * lpos + loff[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=8.5, color=color, style="italic",
                zorder=4, bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none"))


def save(fig, name):
    fig.savefig(OUT / name, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print("saved", OUT / name)


# --------------------------------------------------------------- 1. project flow
def project_flow():
    fig, ax = canvas(18, 10.5, "SkillBridge Analytics — Project Flow",
                     "How data moves from job postings and student records to predictions and the dashboard")
    # Airflow band around the four pipeline stages
    band = FancyBboxPatch((20.5, 30.5), 72, 19, boxstyle="round,pad=0,rounding_size=1.5",
                          lw=1.5, ec=PAL["amber"][0], fc="#FFFBF4", ls=(0, (5, 4)), zorder=0)
    ax.add_patch(band)
    ax.text(21.8, 48.4, "Apache Airflow DAG  ·  skillbridge_pipeline  (runs all four stages in order)",
            fontsize=9.5, color=PAL["amber"][0], fontweight="bold", va="top")

    ax.text(10, 49.0, "DATA SOURCES", ha="center", fontsize=9.5, color=MUTED, fontweight="bold")
    kag_jobs = box(ax, 10, 45, 16, 6, "LinkedIn postings", "Kaggle · 1,500 sampled", "blue")
    kag_stu = box(ax, 10, 37, 16, 6, "Campus placement", "Kaggle · 215 students", "blue")
    upload = box(ax, 10, 29, 16, 6, "CSV upload", "Dashboard · Data Studio", "blue")
    kafka = box(ax, 10, 21, 16, 6, "Live postings", "Apache Kafka stream", "blue")

    ingest = box(ax, 30, 39, 15, 12, "Ingest", "load_kaggle_data.py\nreal data first,\nsynthetic as fallback",
                 "indigo", num=1)
    nlp = box(ax, 48, 39, 15, 12, "Extract skills", "spaCy PhraseMatcher\n~150 skills, 8 categories\nprecision 99.2%",
              "indigo", num=2)
    feat = box(ax, 66, 39, 15, 12, "Feature store", "market demand d(s)\nalignment score A(u)\nskill gaps per student",
               "indigo", num=3)
    model = box(ax, 84, 39, 15, 12, "Train model", "LogReg vs XGBoost\nbest by ROC AUC\nAUC 0.947 · acc 83.3%",
                "indigo", num=4)

    es = box(ax, 48, 18, 15, 9, "Elasticsearch", "1,500 postings indexed\nskill search", "green")
    dash = box(ax, 66, 18, 15, 9, "Dashboard", "Streamlit + Plotly\n5 pages, what-if", "green")
    s3 = box(ax, 84, 18, 15, 9, "Amazon S3", "versioned archive of\nmodel + data", "green")
    users = box(ax, 66, 5, 22, 6, "Placement officers · Students", "", "slate")

    for src in (kag_jobs, kag_stu, upload):
        arrow(ax, src, ingest)
    arrow(ax, kafka, nlp, rad=0.3, label="streamed: skills extracted per message", lpos=0.5, loff=(4, -6.5))
    arrow(ax, ingest, nlp, color=INK)
    arrow(ax, nlp, feat, color=INK)
    arrow(ax, feat, model, color=INK)
    arrow(ax, nlp, es, label="index postings")
    arrow(ax, feat, dash, label="gaps, scores")
    arrow(ax, model, dash, label="predictions", lpos=0.45, loff=(1.5, 0.5))
    arrow(ax, model, s3, label="upload")
    arrow(ax, es, dash, label="search")
    arrow(ax, dash, users, style="<|-|>")
    save(fig, "1_project_flow.png")


# --------------------------------------------------------------- 2. tech stack
def techstack_flow():
    layers = [
        ("Data sources", "blue", [("Kaggle API", "LinkedIn postings,\ncampus placement"),
                                  ("Synthetic generator", "Python, known skills"),
                                  ("CSV upload", "via dashboard")]),
        ("Ingestion & streaming", "blue", [("Python 3.10 + pandas", "load, clean, sample"),
                                           ("Apache Kafka 3.7", "KRaft mode, Docker")]),
        ("Processing & NLP", "indigo", [("spaCy 3.8", "PhraseMatcher skill NER"),
                                        ("pandas", "demand + alignment features")]),
        ("Machine learning", "indigo", [("scikit-learn 1.7.2", "logistic regression"),
                                        ("XGBoost 3.2.0", "boosted trees"),
                                        ("joblib", "saved model bundle")]),
        ("Storage & search", "green", [("CSV files", "data/raw, data/processed"),
                                       ("Elasticsearch 8.15", "posting search"),
                                       ("Amazon S3 (boto3)", "model + data archive")]),
        ("Orchestration & infra", "amber", [("Apache Airflow 2.9", "4-task DAG, LocalExecutor"),
                                            ("PostgreSQL 13", "Airflow metadata"),
                                            ("Docker Compose", "Kafka, ES, Airflow")]),
        ("Presentation", "green", [("Streamlit", "5-page dashboard"),
                                   ("Plotly", "interactive charts")]),
        ("Quality & delivery", "slate", [("pytest", "31 automated tests"),
                                         ("Git + GitHub", "version control")]),
    ]
    fig, ax = canvas(16, 15.5, "SkillBridge Analytics — Tech Stack Flow",
                     "Each layer feeds the one below it; the tools used at every step")
    top = 100 * 15.5 / 16 - 12
    step = 10.6
    prev = None
    for i, (name, color, tools) in enumerate(layers):
        y = top - i * step
        lab = box(ax, 12, y, 19, 7.4, name, "", color, tsize=12)
        if prev is not None:
            arrow(ax, prev, lab, color=INK)
        prev = lab
        n = len(tools)
        w = min(24, (74 - (n - 1) * 2.5) / n)
        x0 = 25 + w / 2
        for j, (tool, desc) in enumerate(tools):
            box(ax, x0 + j * (w + 2.5), y, w, 7.4, tool, desc, color, tsize=11, bsize=9.2)
    save(fig, "2_techstack_flow.png")


# --------------------------------------------------------------- 3. scenario flow
def scenario_flow():
    fig, ax = canvas(22, 11, "Scenario Flow — Helping student S0001",
                     "A placement officer uses SkillBridge to check one student, plan their next skill, "
                     "and find students who need help")
    lanes = [("Placement officer", "slate"), ("Dashboard\n(Streamlit)", "green"),
             ("Feature store\n& model", "indigo"), ("Big-data services\n(Kafka · Airflow · ES)", "blue")]
    lane_y, lane_h = [37, 27, 17, 7], 9.4
    for (name, color), y in zip(lanes, lane_y):
        edge, fill = PAL[color]
        ax.add_patch(FancyBboxPatch((1, y - lane_h / 2), 98, lane_h, boxstyle="round,pad=0,rounding_size=0.8",
                                    lw=1, ec=edge, fc=fill, alpha=0.45, zorder=0))
        ax.text(2.2, y, name, fontsize=10.5, fontweight="bold", color=edge, va="center")

    steps = [
        (3, "New postings", "Kafka streams them;\nskills extracted;\nAirflow re-trains"),
        (0, "Opens Student 360", "selects S0001"),
        (1, "Loads profile", "CGPA 7.20\n12 market skills"),
        (2, "Scores student", "placement 85.6%\nalignment 70.0%\n→ On track"),
        (1, "Shows result", "gauge, skill radar,\ngaps ranked by\nmarket demand"),
        (0, "Tries a what-if", "adds Agile + C"),
        (2, "Re-scores", "alignment 76.2% (+6.1)\nplacement 81.3% (−4.3)"),
        (3, "Searches postings", "Elasticsearch finds\nreal jobs asking\nfor Agile"),
        (1, "Cohort analytics", "215 students:\n128 on track\n37 need a push · 50 at risk"),
        (0, "Acts", "downloads the\nintervention list"),
    ]
    boxes = []
    x0, dx, w = 17.5, 8.4, 8.0
    for i, (lane, title, body) in enumerate(steps):
        color = lanes[lane][1]
        boxes.append(box(ax, x0 + i * dx, lane_y[lane], w, 8.4, title, body, color,
                         tsize=9.2, bsize=8.0, num=i + 1))
    for a, b in zip(boxes, boxes[1:]):
        arrow(ax, a, b, color=INK, lw=1.4)
    ax.text(50, 0.3, "Numbers are from the real Kaggle run. Note: on this data, adding skills lowers the "
            "predicted chance because the source has no real skill records — the dashboard says so.",
            ha="center", fontsize=9, color=MUTED, style="italic")
    save(fig, "3_scenario_flow.png")


# --------------------------------------------------------------- 4. development flow
def development_flow():
    fig, ax = canvas(20, 10.5, "SkillBridge Analytics — Development Flow",
                     "The order the project was built in, from idea to delivery")
    phases = [
        ("Plan", "problem, objectives,\nscope, architecture", "slate"),
        ("Synthetic data", "generators for postings\n+ students, known skills", "blue"),
        ("NLP extractor", "spaCy matcher;\nprecision 84.5% → 99.2%", "indigo"),
        ("Features & model", "alignment score;\nLogReg vs XGBoost", "indigo"),
        ("Dashboard", "Streamlit, 5 pages,\nwhat-if simulator", "green"),
        ("Big-data stack", "Kafka, Airflow,\nElasticsearch, S3 (Docker)", "amber"),
        ("Real data", "Kaggle datasets;\nAUC 0.947, accuracy 83.3%", "blue"),
        ("Test & fix", "31 automated tests;\n5 real bugs fixed", "red"),
        ("Document", "research paper,\nslides, README", "slate"),
        ("Deliver", "GitHub push,\nevaluation deck", "green"),
    ]
    xs = [12, 31, 50, 69, 88]
    row_y = [36, 14]
    boxes = []
    for i, (t, b, c) in enumerate(phases):
        row, col = divmod(i, 5)
        x = xs[col] if row == 0 else xs[4 - col]
        boxes.append(box(ax, x, row_y[row], 15, 10, t, b, c, tsize=12.5, bsize=9.8, num=i + 1))
    for i, (a, b) in enumerate(zip(boxes, boxes[1:])):
        arrow(ax, a, b, color=INK, lw=1.8)
    arrow(ax, boxes[7], boxes[2], color=PAL["red"][0], dashed=True, rad=-0.25,
          label="iterate: find bug → fix → re-test", lpos=0.5, loff=(-6, 0))
    ax.text(50, 2.5, "Tests were written alongside each stage; every fix was re-checked on the full suite "
            "before moving on.", ha="center", fontsize=10, color=MUTED, style="italic")
    save(fig, "4_development_flow.png")


if __name__ == "__main__":
    project_flow()
    techstack_flow()
    scenario_flow()
    development_flow()

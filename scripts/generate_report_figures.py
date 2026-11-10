#!/usr/bin/env python3
"""
scripts/generate_report_figures.py
Generates publication-quality figures for the academic project report.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "figure.dpi": 300,
})

def generate_fig_6_1_accuracy_comparison():
    languages = ["English", "Hinglish", "Hindi", "Bengali", "Marathi", "Telugu", "Tamil"]
    paper_avg = [64.6, 58.3, 55.5, 56.9, 54.7, 51.8, 56.3]
    deepseek_v32 = [69.1, 66.2, 64.5, 65.4, 63.6, 63.6, 66.7]
    llama3_70b = [66.1, 65.1, 58.0, 62.2, 54.5, 58.0, 58.1]
    qwen3_8b = [55.1, 51.1, 52.7, 51.1, 49.4, 50.0, 49.4]
    indicsql = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 95.0]

    x = np.arange(len(languages))
    width = 0.16

    fig, ax = plt.subplots(figsize=(10, 5))
    
    rects1 = ax.bar(x - 2*width, paper_avg, width, label="Paper Avg (Table 1)", color="#94a3b8")
    rects2 = ax.bar(x - width, qwen3_8b, width, label="Qwen3 8B (DIN-SQL)", color="#cbd5e1")
    rects3 = ax.bar(x, llama3_70b, width, label="Llama 3.3 70B (DIN-SQL)", color="#60a5fa")
    rects4 = ax.bar(x + width, deepseek_v32, width, label="DeepSeek V3.2 671B", color="#3b82f6")
    rects5 = ax.bar(x + 2*width, indicsql, width, label="IndicSQL (Our Neuro-Symbolic)", color="#10b981", edgecolor="#047857", linewidth=1.2)

    ax.set_ylabel("Execution Accuracy (EX %)")
    ax.set_title("Cross-Lingual Execution Accuracy: IndicDBBench Baselines vs. IndicSQL (140-Query Suite)")
    ax.set_xticks(x)
    ax.set_xticklabels(languages, fontweight="bold")
    ax.set_ylim(40, 108)
    ax.axhline(100, color="#9ca3af", linestyle="--", alpha=0.5, linewidth=0.8)
    ax.legend(loc="lower right", framealpha=0.95)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    # Highlight Telugu jump
    ax.annotate("+48.2% Jump\n(Eliminated Gap)", xy=(5 + 2*width, 100), xytext=(4.7, 103),
                arrowprops=dict(facecolor="#059669", shrink=0.08, width=1.5, headwidth=6),
                fontsize=8.5, fontweight="bold", color="#065f46", ha="center")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_6_1_accuracy_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

def generate_fig_6_2_ablation_ladder():
    stages = [
        "Stage 1:\nBase Pretrained SLMs\n(Qwen-3B / Sarvam-2B)",
        "Stage 2:\nDomain LoRA Tuning\n(Dual-LoRA Adapters)",
        "Stage 3:\nMulti-Agent Pipeline\n(Raw Draft / No Guards)",
        "Stage 4:\nNeuro-Symbolic Guards\n(SQLGlot AST + DuckDB)"
    ]
    accuracies = [47.81, 75.49, 71.43, 99.29]
    colors = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.bar(stages, accuracies, color=colors, width=0.55, edgecolor="#1e293b", linewidth=1)

    for bar, acc in zip(bars, accuracies):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1.8, f"{acc:.2f}%", ha='center', va='bottom', fontweight='bold', fontsize=10.5)

    ax.set_ylabel("Execution Accuracy (EX %)")
    ax.set_title("Four-Stage Ablation Progression: Evolution to 99.29% Execution Parity")
    ax.set_ylim(30, 112)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    # Annotations
    ax.annotate("Tokenization Fertility\n& Vocabulary Mismatch", xy=(0, 47.81), xytext=(0, 65),
                ha='center', fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#ef4444"))
    ax.annotate("Learned Indian Schemas\n& SQL Grammar", xy=(1, 75.49), xytext=(1, 90),
                ha='center', fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#fef3c7", ec="#f59e0b"))
    ax.annotate("40 Stochastic Failures\n(Temporal & Aggregate)", xy=(2, 71.43), xytext=(2, 85),
                ha='center', fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#dbeafe", ec="#3b82f6"))
    ax.annotate("Symbolic AST Repairs\n(39 of 40 Fixed)", xy=(3, 99.29), xytext=(3, 106),
                ha='center', fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#d1fae5", ec="#10b981"), fontweight='bold')

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_6_2_ablation_ladder.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

def generate_fig_4_1_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.axis("off")

    # Define box layout
    boxes = [
        {"name": "Multilingual NLQ Input\n(7 Indian Languages)", "xy": (0.05, 0.65), "w": 0.22, "h": 0.22, "fc": "#e0f2fe", "ec": "#0284c7"},
        {"name": "Supervisor Router\n(Language & Script Det.)\n(Phonetic Normalizer)", "xy": (0.37, 0.65), "w": 0.26, "h": 0.22, "fc": "#f3e8ff", "ec": "#7e22ce"},
        {"name": "Dynamic Schema Linker\n(Multilingual Inverted Index)\n(BM25 + Vector Hybrid)", "xy": (0.73, 0.65), "w": 0.24, "h": 0.22, "fc": "#fef3c7", "ec": "#d97706"},
        {"name": "SQL Synthesizer\n(Local Dual-LoRA SLMs)\n(Raw Stochastic Draft)", "xy": (0.73, 0.15), "w": 0.24, "h": 0.22, "fc": "#fee2e2", "ec": "#dc2626"},
        {"name": "Deterministic AST Guardrails\n(SQLGlot AST Rewrite Engine)\n(TemporalGuard & MetricGuard)", "xy": (0.37, 0.15), "w": 0.26, "h": 0.22, "fc": "#d1fae5", "ec": "#059669"},
        {"name": "DuckDB Sandbox & Verbalizer\n(Zero-Cloud Execution Engine)\n(Bilingual Human Answer)", "xy": (0.05, 0.15), "w": 0.22, "h": 0.22, "fc": "#ccfbf1", "ec": "#0d9488"},
    ]

    for b in boxes:
        rect = patches.FancyBboxPatch(b["xy"], b["w"], b["h"], boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=b["fc"], edgecolor=b["ec"], linewidth=1.5)
        ax.add_patch(rect)
        ax.text(b["xy"][0] + b["w"]/2, b["xy"][1] + b["h"]/2, b["name"], ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="#0f172a")

    # Arrows
    def draw_arrow(start, end, label=""):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color="#334155", lw=2, mutation_scale=15))
        if label:
            mid = ((start[0]+end[0])/2, (start[1]+end[1])/2 + 0.03)
            ax.text(mid[0], mid[1], label, ha="center", fontsize=8, color="#475569", fontweight="bold")

    draw_arrow((0.27, 0.76), (0.37, 0.76), "Raw NLQ")
    draw_arrow((0.63, 0.76), (0.73, 0.76), "Normalized Text")
    draw_arrow((0.85, 0.65), (0.85, 0.37), "Linked Catalog")
    draw_arrow((0.73, 0.26), (0.63, 0.26), "Raw SQL")
    draw_arrow((0.37, 0.26), (0.27, 0.26), "Verified SQL")

    ax.set_title("Figure 4.1: IndicSQL End-to-End Neuro-Symbolic Multi-Agent Pipeline Architecture",
                 fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_1_architecture.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

def generate_fig_4_2_dfd():
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.axis("off")

    nodes = [
        {"label": "External Entity:\nUser / District Officer", "pos": (0.08, 0.5), "w": 0.18, "h": 0.26, "fc": "#f1f5f9", "ec": "#475569"},
        {"label": "Process 1.0:\nPhonetic & Script\nNormalization", "pos": (0.35, 0.7), "w": 0.18, "h": 0.22, "fc": "#ede9fe", "ec": "#6d28d9"},
        {"label": "Process 2.0:\nMultilingual Schema\nLinking & Routing", "pos": (0.65, 0.7), "w": 0.18, "h": 0.22, "fc": "#fef3c7", "ec": "#b45309"},
        {"label": "Process 3.0:\nNeural SQL\nDrafting (LoRA)", "pos": (0.65, 0.2), "w": 0.18, "h": 0.22, "fc": "#fee2e2", "ec": "#b91c1c"},
        {"label": "Process 4.0:\nDeterministic AST\nGuardrail Repair", "pos": (0.35, 0.2), "w": 0.18, "h": 0.22, "fc": "#dcfce7", "ec": "#15803d"},
    ]

    for n in nodes:
        rect = patches.FancyBboxPatch(n["pos"], n["w"], n["h"], boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=n["fc"], edgecolor=n["ec"], linewidth=1.4)
        ax.add_patch(rect)
        ax.text(n["pos"][0] + n["w"]/2, n["pos"][1] + n["h"]/2, n["label"], ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="#0f172a")

    # Storage Box (DuckDB Parquets)
    store_rect = patches.Rectangle((0.87, 0.35), 0.11, 0.32, facecolor="#e2e8f0", edgecolor="#334155", linewidth=1.5)
    ax.add_patch(store_rect)
    ax.text(0.925, 0.51, "Data Store:\n20 NDAP\nParquets", ha="center", va="center", fontsize=8, fontweight="bold")

    ax.annotate("", xy=(0.35, 0.78), xytext=(0.26, 0.6), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.65, 0.81), xytext=(0.53, 0.81), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.74, 0.42), xytext=(0.74, 0.7), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.53, 0.31), xytext=(0.65, 0.31), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.26, 0.45), xytext=(0.35, 0.31), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.87, 0.45), xytext=(0.83, 0.31), arrowprops=dict(arrowstyle="<|-|>", color="#047857", lw=1.5))

    ax.set_title("Figure 4.2: Data Flow Diagram (DFD Level 1) of IndicSQL Swarm", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_2_dfd.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

def generate_fig_5_1_er_diagram():
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.axis("off")

    tables = [
        {"name": "dim_geography\n-------------\nPK geography_key\nstate_id\nstate_name\ndistrict_id\ndistrict_name", "pos": (0.05, 0.55), "w": 0.22, "h": 0.36, "fc": "#eff6ff", "ec": "#2563eb"},
        {"name": "dim_time\n-------------\nPK time_key\ncalendar_year\nfinancial_year\nmonth_number\nquarter", "pos": (0.73, 0.55), "w": 0.22, "h": 0.36, "fc": "#eff6ff", "ec": "#2563eb"},
        {"name": "fact_crop_production\n--------------------\nPK fact_crop_id\nFK geography_key\nFK time_key\ncrop_name\narea_hectares\nproduction_tonnes\nyield_kg_per_ha", "pos": (0.38, 0.6), "w": 0.24, "h": 0.35, "fc": "#ecfdf5", "ec": "#059669"},
        {"name": "fact_pm_kisan_disbursement\n--------------------------\nPK fact_kisan_id\nFK geography_key\nFK time_key\nfarmer_beneficiaries\namount_inr\ninstallment_number", "pos": (0.15, 0.08), "w": 0.28, "h": 0.35, "fc": "#fefce8", "ec": "#ca8a04"},
        {"name": "fact_education_stats\n--------------------\nPK fact_edu_id\nFK geography_key\nFK time_key\nmale_literacy_rate\nfemale_literacy_rate\nstudent_count", "pos": (0.57, 0.08), "w": 0.28, "h": 0.35, "fc": "#fdf2f8", "ec": "#db2777"},
    ]

    for t in tables:
        rect = patches.FancyBboxPatch(t["pos"], t["w"], t["h"], boxstyle="round,pad=0.02,rounding_size=0.02",
                                      facecolor=t["fc"], edgecolor=t["ec"], linewidth=1.4)
        ax.add_patch(rect)
        ax.text(t["pos"][0] + 0.02, t["pos"][1] + t["h"] - 0.04, t["name"], ha="left", va="top",
                fontsize=8.5, fontfamily="monospace", color="#0f172a")

    # Connect lines
    ax.annotate("", xy=(0.38, 0.75), xytext=(0.27, 0.75), arrowprops=dict(arrowstyle="<|-", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.62, 0.75), xytext=(0.73, 0.75), arrowprops=dict(arrowstyle="<|-", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.25, 0.43), xytext=(0.18, 0.55), arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.65, 0.43), xytext=(0.78, 0.55), arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.5))

    ax.set_title("Figure 5.1: Third Normal Form (3NF) Star Schema Entity-Relationship (ER) Architecture", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_5_1_er_diagram.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_fig_6_1_accuracy_comparison()
    generate_fig_6_2_ablation_ladder()
    generate_fig_4_1_architecture()
    generate_fig_4_2_dfd()
    generate_fig_5_1_er_diagram()
    print("All figures successfully created!")

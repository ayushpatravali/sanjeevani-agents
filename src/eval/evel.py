# ================================================================
# File 2: eval_metrics.py  (Cross-Domain + True Routing Metrics)
# ================================================================

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def _normalize_agent(a: str) -> str:
    a = str(a).lower()
    if "research" in a: return "research"
    if "gis" in a: return "gis"
    if "iucn" in a: return "iucn"
    return "unknown"


def calculate_final_metrics(csv=r"D:\sanji\project\sanjeevani-agents\retrieval_results.csv"):

    df = pd.read_csv(csv)

    df["expected_agent"] = df["expected_agent"].str.lower()
    df["router_agent"] = df["router_agent"].str.lower()
    df["actual_norm"] = df["actual_agent"].apply(_normalize_agent)

    MAIN = ["research", "gis", "iucn"]
    df_main = df[df["expected_agent"].isin(MAIN)]
    df_cross = df[df["expected_agent"] == "cross"]

    # ROUTING ACCURACY (router vs expected)
    df_main["routing_correct"] = df_main["expected_agent"] == df_main["router_agent"]
    routing_accuracy = df_main["routing_correct"].mean() * 100

    # Precision/Recall/F1 (router vs expected)
    y_true = df_main["expected_agent"]
    y_pred = df_main["router_agent"]

    precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    cm = confusion_matrix(y_true, y_pred, labels=MAIN)

    # Latency & relevance
    avg_latency = df["latency"].mean()
    latency_by_agent = df_main.groupby("expected_agent")["latency"].mean()

    avg_relevance = df["relevance_score"].mean()
    relevance_by_agent = df_main.groupby("expected_agent")["relevance_score"].mean()

    # botanical match
    overall_match = df["botanical_match"].mean() * 100
    match_by_agent = df_main.groupby("expected_agent")["botanical_match"].mean() * 100

    # ================= GRAPH 1 — Overall Metrics =================
    plt.figure(figsize=(7,5))
    plt.bar(
        ["Routing Acc", "Precision", "Recall", "F1"],
        [routing_accuracy, precision*100, recall*100, f1*100],
    )
    plt.title("Overall Router Classification Metrics")
    plt.ylabel("Score (%)")
    plt.tight_layout()
    plt.savefig("overall_metrics.png", dpi=200)
    plt.close()

    # ================= GRAPH 2 — Confusion Matrix =================
    plt.figure(figsize=(6,5))
    plt.imshow(cm, cmap="Blues")
    plt.xticks(range(len(MAIN)), MAIN)
    plt.yticks(range(len(MAIN)), MAIN)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Router Confusion Matrix")

    for i in range(len(MAIN)):
        for j in range(len(MAIN)):
            plt.text(j, i, cm[i, j], ha="center", va="center")

    plt.colorbar()
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=200)
    plt.close()

    # ================= GRAPH 3 — Latency by Query =================
    plt.figure(figsize=(8,4))
    df["latency"].plot(kind="line")
    plt.title("Latency Across Queries")
    plt.xlabel("Query index")
    plt.ylabel("Seconds")
    plt.tight_layout()
    plt.savefig("latency_by_query.png", dpi=200)
    plt.close()

    # ================= GRAPH 4 — Latency by Agent =================
    plt.figure(figsize=(6,4))
    latency_by_agent.plot(kind="bar")
    plt.title("Avg Latency per Agent")
    plt.ylabel("Seconds")
    plt.tight_layout()
    plt.savefig("latency_by_agent.png", dpi=200)
    plt.close()

    # ================= GRAPH 5 — Relevance Histogram =============
    plt.figure(figsize=(7,4))
    df["relevance_score"].plot(kind="hist", bins=5, rwidth=0.9)
    plt.title("Relevance Score Distribution")
    plt.tight_layout()
    plt.savefig("relevance_histogram.png", dpi=200)
    plt.close()

    # ================= GRAPH 6 — Relevance per Agent =============
    plt.figure(figsize=(6,4))
    relevance_by_agent.plot(kind="bar")
    plt.title("Avg Relevance per Agent")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig("relevance_by_agent.png", dpi=200)
    plt.close()

    # ================= GRAPH 7 — Botanical Match per Agent =======
    plt.figure(figsize=(6,4))
    match_by_agent.plot(kind="bar")
    plt.title("Botanical Match Rate per Agent")
    plt.ylabel("Match %")
    plt.tight_layout()
    plt.savefig("botanical_match_rate.png", dpi=200)
    plt.close()

    # ================= GRAPH 8 — Latency vs Relevance ============
    plt.figure(figsize=(7,4))
    plt.scatter(df["latency"], df["relevance_score"], alpha=0.6)
    plt.xlabel("Latency")
    plt.ylabel("Relevance")
    plt.title("Latency vs Relevance Scatter")
    plt.tight_layout()
    plt.savefig("latency_vs_relevance.png", dpi=200)
    plt.close()

    # ================= PRINT METRICS =============================
    print("\n📌 FINAL EVALUATION METRICS")
    print(f"Routing Accuracy: {routing_accuracy:.2f}%")
    print(f"Precision (macro): {precision:.3f}")
    print(f"Recall (macro): {recall:.3f}")
    print(f"F1 Score: {f1:.3f}")
    print(f"Average Latency: {avg_latency:.3f}s")
    print(f"Average Relevance: {avg_relevance:.3f}")
    print(f"Overall Botanical Match: {overall_match:.2f}%")
    print("\nLatency per Agent:\n", latency_by_agent)
    print("\nRelevance per Agent:\n", relevance_by_agent)
    print("\nBotanical Match per Agent:\n", match_by_agent)
    print(f"\nCross-Domain Queries Evaluated: {len(df_cross)}")


if __name__ == "__main__":
    calculate_final_metrics()

# ================================================================
# File 1: eval_generate_csv.py  (Realistic Queries + True Routing)
# ================================================================

import csv
import time
from typing import List

from src.agents.research_agent import ResearchAgent
from src.agents.gis_agent import GISAgent
from src.agents.iucn_agent import IUCNAgent
from src.database.weaviate_client import weaviate_manager


# -------------------------------------------------
# ROUTER UNDER TEST — realistic rule-based classifier
# -------------------------------------------------
def route_query(query: str) -> str:
    q = query.lower()

    # IUCN patterns
    if (
        "iucn" in q
        or "endangered" in q
        or "threat" in q
        or "red list" in q
        or "conservation status" in q
    ):
        return "iucn"

    # GIS patterns
    if (
        "where" in q
        or "habitat" in q
        or "distribution" in q
        or "native" in q
        or "grow" in q
        or "region" in q
    ):
        return "gis"

    # Research patterns
    if (
        "use" in q
        or "benefit" in q
        or "medicinal" in q
        or "application" in q
        or "ayurveda" in q
    ):
        return "research"

    # fallback
    return "research"


# -------------------------------------------------
# Realistic Query Sets (60 total)
# -------------------------------------------------

RESEARCH_QUERIES = [
    "What are the medicinal uses of holy basil?",
    "Benefits of neem leaves in Ayurveda?",
    "Traditional uses of curry leaves?",
    "What is hibiscus good for medicinally?",
    "Health benefits of jamun fruit?",
    "How is betel leaf used in traditional medicine?",
    "Uses of sandalwood in herbal therapy.",
    "Medicinal applications of climbing spinach?",
    "Why is moringa called a superfood?",
    "Is Indian bael used for stomach issues?",
    "What Ayurvedic uses does ashwagandha have?",
    "What are the healing benefits of jasmine flowers?",
    "What remedies use amaranth leaves?",
    "How is pennywort used medicinally?",
    "Are guava leaves medically useful?",
]

GIS_QUERIES = [
    "Where does holy basil naturally grow?",
    "What is the native region of Indian gooseberry tree?",
    "Geographic distribution of jackfruit tree in India.",
    "Where is curry leaf plant commonly found?",
    "Native habitat of jasmine shrubs.",
    "Where do guava trees grow naturally?",
    "Climatic zone of hibiscus plants.",
    "Regions where jamun trees thrive.",
    "Habitat of bamboo species in South India.",
    "Which regions have abundant neem plantations?",
    "Growth regions for Indian spinach.",
    "Distribution of moringa across Karnataka.",
    "Natural habitat of Indian bay leaf tree.",
    "Where do oleander shrubs naturally occur?",
    "Climatic preference of tulsi plants.",
]

IUCN_QUERIES = [
    "Is the Ashoka tree endangered?",
    "IUCN status of Indian sandalwood.",
    "Is the jackfruit tree threatened?",
    "Conservation status of the neem tree.",
    "Is jasmine at risk according to IUCN?",
    "Endangered status of wild amla.",
    "Is pennywort vulnerable?",
    "Threat level of Indian bael tree.",
    "What is the red list category of jamun?",
    "Is guava considered an endangered species?",
    "Is oleander protected under IUCN?",
    "Is curry leaf plant endangered?",
    "IUCN red list for moringa plant.",
    "Is hibiscus under threat?",
    "Is saraca asoca listed as endangered?",
]

CROSS_QUERIES = [
    "What are the medicinal uses and habitat of neem?",
    "Give the distribution and IUCN status of sandalwood.",
    "What is the habitat and medicinal value of moringa?",
    "Provide medicinal uses and conservation status of jasmine.",
    "Habitat and endangered status of Ashoka tree?",
    "What is the IUCN status and habitat of guava tree?",
    "Uses and distribution of curry leaf plant?",
    "Traditional benefits and threatened status of jamun.",
    "How endangered is moringa and where does it grow?",
    "What are the uses and natural regions of hibiscus?",
    "Habitat, medicinal properties and threat level of holy basil.",
    "Give the GIS + IUCN details of Indian bael.",
    "How widespread is amaranth and what are its medicinal applications?",
    "Provide conservation data and distribution of jasmine shrubs.",
    "Uses, habitat and IUCN category of rauvolfia serpentina.",
]

ALL_QUERIES = (
    [(q, "research") for q in RESEARCH_QUERIES]
    + [(q, "gis") for q in GIS_QUERIES]
    + [(q, "iucn") for q in IUCN_QUERIES]
    + [(q, "cross") for q in CROSS_QUERIES]
)

AGENT_CLASSES = {
    "research": ResearchAgent,
    "gis": GISAgent,
    "iucn": IUCNAgent,
}


# -------------------------------------------------
# CSV GENERATOR
# -------------------------------------------------

def generate_results_csv(output_file="retrieval_results.csv"):

    header = [
        "query",
        "expected_agent",
        "router_agent",
        "actual_agent",
        "latency",
        "relevance_score",
        "botanical_name",
        "botanical_match",
        "num_results",
        "warnings",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for query, expected in ALL_QUERIES:

            router_agent = route_query(query)

            agent_class = AGENT_CLASSES.get(router_agent, ResearchAgent)
            agent = agent_class()

            start = time.perf_counter()
            result = agent.process_query(query)
            end = time.perf_counter()
            latency = end - start

            plants = result.get("results", [])
            num_results = len(plants)

            if num_results == 0:
                botanical = "None"
                match = 0
                relevance = 1
            else:
                botanical = plants[0].get("botanical_name", "Unknown")
                warnings = result.get("warnings", [])
                match = 1 if botanical.lower() in query.lower() else 0
                if match and not warnings:
                    relevance = 5
                elif match:
                    relevance = 4
                else:
                    relevance = 3

            writer.writerow([
                query,
                expected,
                router_agent,
                result.get("agent", "unknown"),
                latency,
                relevance,
                botanical,
                match,
                num_results,
                "; ".join(result.get("warnings", [])),
            ])

    try:
        if getattr(weaviate_manager, "client", None):
            weaviate_manager.client.close()
    except Exception:
        pass

    print(f"CSV generated: {output_file}")


if __name__ == "__main__":
    generate_results_csv()

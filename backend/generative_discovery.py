"""
CatalystOS — Generative Discovery Engine
=========================================
Task: Generative Discovery
  - Simulates "generative discovery" by perturbing known catalyst structures
    from the Open Catalyst Project to suggest novel variants
  - Scores each variant using the trained GradientBoost-E2J model
  - Ranks and filters by predicted improvement over the parent structure

"""

import json
import random
import itertools
import numpy as np
from prediction_engine import GradientBoostE2J, build_dataset

random.seed(42)
np.random.seed(42)


# ── 1. KNOWN CATALYST LIBRARY (Open Catalyst Project seed structures) ──────────

KNOWN_CATALYSTS = [
    {"name": "Cu-Zn/SiO2",    "base": "Cu", "promoter": "Zn",   "support": "SiO2",  "temp": 330, "pressure": 1},
    {"name": "Pd-Ag/Al2O3",   "base": "Pd", "promoter": "Ag",   "support": "Al2O3", "temp": 320, "pressure": 1},
    {"name": "Fe-Co/ZSM5",    "base": "Fe", "promoter": "Co",   "support": "ZSM5",  "temp": 335, "pressure": 1},
    {"name": "Ni-SAPO34",     "base": "Ni", "promoter": "None", "support": "SAPO34","temp": 310, "pressure": 1},
    {"name": "Ru-Fe/Al2O3",   "base": "Ru", "promoter": "Fe",   "support": "Al2O3", "temp": 320, "pressure": 1},
    {"name": "Pt/HZSM5",      "base": "Pt", "promoter": "None", "support": "HZSM5", "temp": 250, "pressure": 1},
    {"name": "Rh/Al2O3",      "base": "Rh", "promoter": "None", "support": "Al2O3", "temp": 290, "pressure": 1},
    {"name": "Cu-Ce/ZrO2",    "base": "Cu", "promoter": "Ce",   "support": "ZrO2",  "temp": 325, "pressure": 1},
]

# Perturbation search spaces
METALS    = ["Cu", "Pd", "Ru", "Fe", "Ni", "Pt", "Rh", "Co", "Mo", "Ag", "Ce", "La", "None"]
SUPPORTS  = ["SiO2", "Al2O3", "ZSM5", "TiO2", "ZrO2", "CeO2", "SAPO34", "HZSM5"]
TEMP_DELTAS    = [-20, -10, 0, +10, +20]
PRESSURE_STEPS = [1, 5, 10, 15]

# Catalysts that are already known failures — skip these
BLACKLIST = [
    ("Fe", "None", "Al2O3"),  # coking above 340°C
    ("Ni", "Mo",   "TiO2"),   # poor selectivity at 1 bar
]


# ── 2. PERTURBATION STRATEGIES ─────────────────────────────────────────────────

def perturb_promoter(cat: dict) -> list:
    """Swap the promoter metal with every other option."""
    variants = []
    for new_promoter in METALS:
        if new_promoter == cat["promoter"]:
            continue
        v = cat.copy()
        v["promoter"] = new_promoter
        v["perturbation"] = f"promoter: {cat['promoter']} → {new_promoter}"
        v["strategy"] = "promoter_swap"
        variants.append(v)
    return variants


def perturb_support(cat: dict) -> list:
    """Swap the support material."""
    variants = []
    for new_support in SUPPORTS:
        if new_support == cat["support"]:
            continue
        v = cat.copy()
        v["support"] = new_support
        v["perturbation"] = f"support: {cat['support']} → {new_support}"
        v["strategy"] = "support_swap"
        variants.append(v)
    return variants


def perturb_temperature(cat: dict) -> list:
    """Nudge operating temperature."""
    variants = []
    for delta in TEMP_DELTAS:
        if delta == 0:
            continue
        new_temp = cat["temp"] + delta
        if not (150 <= new_temp <= 500):
            continue
        v = cat.copy()
        v["temp"] = new_temp
        v["perturbation"] = f"temp: {cat['temp']}°C → {new_temp}°C"
        v["strategy"] = "temperature_shift"
        variants.append(v)
    return variants


def perturb_pressure(cat: dict) -> list:
    """Explore different pressure regimes (critical gap in current data)."""
    variants = []
    for new_pressure in PRESSURE_STEPS:
        if new_pressure == cat["pressure"]:
            continue
        v = cat.copy()
        v["pressure"] = new_pressure
        v["perturbation"] = f"pressure: {cat['pressure']} bar → {new_pressure} bar"
        v["strategy"] = "pressure_exploration"
        variants.append(v)
    return variants


def perturb_base_metal(cat: dict) -> list:
    """Swap the base metal — high-risk, high-reward."""
    variants = []
    candidate_bases = ["Cu", "Pd", "Ru", "Ni", "Pt", "Rh"]
    for new_base in candidate_bases:
        if new_base == cat["base"]:
            continue
        v = cat.copy()
        v["base"] = new_base
        v["perturbation"] = f"base_metal: {cat['base']} → {new_base}"
        v["strategy"] = "base_metal_swap"
        variants.append(v)
    return variants


def perturb_combined(cat: dict) -> list:
    """
    Two-way combined perturbations: promoter + support swap together.
    Simulates GNN-style multi-node graph edit.
    """
    variants = []
    # Only try promising combinations to limit search space
    good_promoters = ["Zn", "Ce", "La", "Ag", "Pt"]
    good_supports  = ["SiO2", "CeO2", "ZrO2", "HZSM5"]
    for p, s in itertools.product(good_promoters, good_supports):
        if p == cat["promoter"] and s == cat["support"]:
            continue
        v = cat.copy()
        v["promoter"] = p
        v["support"] = s
        v["perturbation"] = f"promoter→{p} + support→{s}"
        v["strategy"] = "combined_perturbation"
        variants.append(v)
    return variants


# ── 3. NOVELTY SCORE ───────────────────────────────────────────────────────────

def novelty_score(variant: dict) -> float:
    """
    Measures how different a variant is from all known catalysts.
    Score 0–1: higher = more novel.
    """
    score = 0.0
    for known in KNOWN_CATALYSTS:
        matches = sum([
            variant["base"]     == known["base"],
            variant["promoter"] == known["promoter"],
            variant["support"]  == known["support"],
        ])
        score = max(score, matches / 3.0)
    return round(1.0 - score, 3)


def is_blacklisted(variant: dict) -> bool:
    return (variant["base"], variant["promoter"], variant["support"]) in BLACKLIST


# ── 4. MAIN DISCOVERY PIPELINE ────────────────────────────────────────────────

def run_generative_discovery(model: GradientBoostE2J,
                              top_n: int = 15,
                              min_activity: float = 72.0,
                              min_improvement: float = 2.0) -> list:
    """
    Full generative discovery pipeline:
      1. Enumerate all perturbations of known structures
      2. Score each with the trained ML model
      3. Filter by minimum performance and improvement over parent
      4. Rank by composite score (activity + selectivity + novelty)
      5. Return top_n novel candidates

    Args:
        model:           Trained GradientBoostE2J instance
        top_n:           How many candidates to return
        min_activity:    Minimum predicted activity % to consider
        min_improvement: Minimum % improvement over parent to qualify

    Returns:
        List of dicts with candidate info and predictions
    """
    print("=" * 65)
    print("  CatalystOS — Generative Discovery Engine")
    print("=" * 65)
    print(f"\n  Seeding from {len(KNOWN_CATALYSTS)} known OCP structures...")

    all_variants = []
    for cat in KNOWN_CATALYSTS:
        # Get parent performance
        parent_pred = model.predict(cat["base"], cat["promoter"],
                                    cat["support"], cat["temp"], cat["pressure"])
        parent_activity = parent_pred["predictions"]["activity"]

        # Generate all perturbation types
        perturbations = (
            perturb_promoter(cat) +
            perturb_support(cat) +
            perturb_temperature(cat) +
            perturb_pressure(cat) +
            perturb_base_metal(cat) +
            perturb_combined(cat)
        )

        for v in perturbations:
            if is_blacklisted(v):
                continue

            pred = model.predict(v["base"], v["promoter"], v["support"],
                                 v["temp"], v["pressure"])
            p = pred["predictions"]

            improvement = p["activity"] - parent_activity
            nov = novelty_score(v)

            # Composite score: weighted sum
            composite = (
                0.40 * p["activity"] +
                0.30 * p["selectivity"] +
                0.20 * nov * 100 +
                0.10 * min(improvement * 5, 20)  # cap improvement bonus
            )

            all_variants.append({
                "parent":       cat["name"],
                "name":         f"{v['base']}-{v['promoter']}/{v['support']}",
                "base":         v["base"],
                "promoter":     v["promoter"],
                "support":      v["support"],
                "temp":         v["temp"],
                "pressure":     v["pressure"],
                "strategy":     v["strategy"],
                "perturbation": v["perturbation"],
                "activity":     round(p["activity"], 1),
                "selectivity":  round(p["selectivity"], 1),
                "delta_g":      round(p["delta_g_eV"], 3),
                "improvement_over_parent": round(improvement, 1),
                "novelty_score": nov,
                "composite_score": round(composite, 2),
                "feasibility":  pred["interpretation"]["feasibility"],
                "recommend_lab": pred["interpretation"]["recommend_lab"],
            })

    print(f"  Generated {len(all_variants)} candidate variants")

    # Filter
    filtered = [
        v for v in all_variants
        if v["activity"] >= min_activity
        and v["improvement_over_parent"] >= min_improvement
    ]
    print(f"  After filtering (activity≥{min_activity}%, improvement≥{min_improvement}%): {len(filtered)} candidates")

    # Remove duplicates (same base/promoter/support combo, keep best)
    seen = {}
    for v in filtered:
        key = (v["base"], v["promoter"], v["support"])
        if key not in seen or v["composite_score"] > seen[key]["composite_score"]:
            seen[key] = v
    deduped = list(seen.values())

    # Sort by composite score
    deduped.sort(key=lambda x: x["composite_score"], reverse=True)
    top = deduped[:top_n]

    # ── PRINT RESULTS ──────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print(f"  TOP {top_n} NOVEL CANDIDATES")
    print(f"{'─'*65}")
    print(f"  {'#':<3} {'Candidate':<26} {'Act%':>5} {'Sel%':>5} {'ΔG(eV)':>7} {'Δ vs parent':>12} {'Novelty':>8} {'Strategy'}")
    print(f"  {'─'*3} {'─'*26} {'─'*5} {'─'*5} {'─'*7} {'─'*12} {'─'*8} {'─'*20}")
    for i, v in enumerate(top, 1):
        delta_str = f"+{v['improvement_over_parent']}%" if v['improvement_over_parent'] >= 0 else f"{v['improvement_over_parent']}%"
        print(f"  {i:<3} {v['name']:<26} {v['activity']:>5} {v['selectivity']:>5} {v['delta_g']:>7} {delta_str:>12} {v['novelty_score']:>8} {v['strategy']}")

    # ── HIGHLIGHT TOP 3 ────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("  TOP 3 — DETAILED PROFILES")
    print(f"{'─'*65}")
    for i, v in enumerate(top[:3], 1):
        print(f"""
  [{i}] {v['name']}
      Parent:      {v['parent']}
      Perturbation:{v['perturbation']}
      Strategy:    {v['strategy']}
      Activity:    {v['activity']}%  |  Selectivity: {v['selectivity']}%
      ΔG:          {v['delta_g']} eV
      Improvement: +{v['improvement_over_parent']}% over parent
      Novelty:     {v['novelty_score']} / 1.0
      Composite:   {v['composite_score']}
      Recommend Lab: {v['recommend_lab']}""")

    # ── JSON OUTPUT ────────────────────────────────────────────────
    output = {
        "run_info": {
            "seed_structures": len(KNOWN_CATALYSTS),
            "total_variants_generated": len(all_variants),
            "after_filtering": len(filtered),
            "after_dedup": len(deduped),
            "top_n_returned": len(top),
        },
        "candidates": top
    }
    with open("generative_discovery_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  ✓ Full results saved → generative_discovery_results.json")
    print("=" * 65)

    return top


# ── 5. ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Train the model first
    X, y_act, y_sel, y_dg = build_dataset()
    model = GradientBoostE2J()
    metrics = model.train(X, y_act, y_sel, y_dg)
    print(f"\n  Model ready — Activity R²: {metrics['activity']['R2']}  |  Selectivity R²: {metrics['selectivity']['R2']}\n")

    # Run discovery
    top_candidates = run_generative_discovery(
        model=model,
        top_n=15,
        min_activity=72.0,
        min_improvement=2.0,
    )

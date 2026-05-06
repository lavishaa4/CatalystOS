"""
CatalystOS — Active Memory Training Loop
==========================================
Task: Training Loop
  - Takes logged experiment data from the database
  - Performs incremental model retraining (warm-start GBR)
  - Detects prediction gaps (where model was wrong)
  - Reports accuracy improvement after each retraining cycle
  - Saves model state so retraining is cumulative across sessions

"""

import json
import os
import pickle
import numpy as np
from datetime import datetime
from prediction_engine import GradientBoostE2J, build_dataset, engineer_features
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor
import warnings
warnings.filterwarnings("ignore")


# ── CONFIG ─────────────────────────────────────────────────────────────────────
MODEL_PATH        = "catalystos_model.pkl"
LOG_PATH          = "experiment_log.json"
RETRAIN_LOG_PATH  = "retrain_history.json"
GAP_THRESHOLD     = 10.0   # % — if |predicted - actual| > this, flag as gap
MIN_NEW_SAMPLES   = 3      # minimum new results before retraining triggers


# ── 1. EXPERIMENT DATABASE ────────────────────────────────────────────────────

def load_experiment_log() -> list:
    """Load all logged experiments from JSON database."""
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    return []


def save_experiment_log(log: list):
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def log_experiment(exp_id: str, base_metal: str, promoter: str, support: str,
                   temp: float, pressure: float,
                   actual_activity: float, actual_selectivity: float,
                   predicted_activity: float = None, predicted_selectivity: float = None,
                   outcome: str = "pass", notes: str = "") -> dict:
    """
    Log a new experimental result to the database.
    This is the entry point called when a lab result comes in.
    """
    record = {
        "exp_id":                exp_id,
        "timestamp":             datetime.now().isoformat(),
        "catalyst": {
            "base_metal": base_metal,
            "promoter":   promoter,
            "support":    support,
            "temp":       temp,
            "pressure":   pressure,
        },
        "results": {
            "actual_activity":    actual_activity,
            "actual_selectivity": actual_selectivity,
            "predicted_activity":    predicted_activity,
            "predicted_selectivity": predicted_selectivity,
            "outcome":  outcome,
            "notes":    notes,
        },
        "gap": {
            "activity_gap":    round(abs((predicted_activity or 0) - actual_activity), 2),
            "is_gap":          abs((predicted_activity or 0) - actual_activity) > GAP_THRESHOLD,
            "direction":       "over" if (predicted_activity or 0) > actual_activity else "under",
        }
    }
    log = load_experiment_log()
    log.append(record)
    save_experiment_log(log)
    return record


# ── 2. GAP DETECTION ──────────────────────────────────────────────────────────

def detect_prediction_gaps(log: list) -> dict:
    """
    Scan experiment log for prediction gaps.
    A gap is when |predicted - actual| > GAP_THRESHOLD.
    Groups gaps by catalyst family to identify systematic failure patterns.
    """
    gaps = []
    patterns = {}

    for exp in log:
        r = exp["results"]
        if r["predicted_activity"] is None:
            continue
        gap_val = abs(r["predicted_activity"] - r["actual_activity"])
        if gap_val > GAP_THRESHOLD:
            cat = exp["catalyst"]
            gaps.append({
                "exp_id":     exp["exp_id"],
                "catalyst":   f"{cat['base_metal']}-{cat['promoter']}/{cat['support']}",
                "base_metal": cat["base_metal"],
                "temp":       cat["temp"],
                "pressure":   cat.get("pressure", 1.0),
                "predicted":  r["predicted_activity"],
                "actual":     r["actual_activity"],
                "gap":        round(gap_val, 2),
                "direction":  "over-predicted" if r["predicted_activity"] > r["actual_activity"] else "under-predicted",
            })
            # Group by base metal for pattern detection
            bm = cat["base_metal"]
            if bm not in patterns:
                patterns[bm] = {"count": 0, "total_gap": 0, "direction_over": 0}
            patterns[bm]["count"] += 1
            patterns[bm]["total_gap"] += gap_val
            if r["predicted_activity"] > r["actual_activity"]:
                patterns[bm]["direction_over"] += 1

    # Summarise patterns
    pattern_summary = []
    for metal, p in patterns.items():
        avg_gap = p["total_gap"] / p["count"]
        dominant_dir = "over-predicted" if p["direction_over"] > p["count"] / 2 else "under-predicted"
        if p["count"] >= 2:  # only report if 2+ experiments show the same issue
            pattern_summary.append({
                "metal_family":       metal,
                "experiments_affected": p["count"],
                "avg_gap_pct":        round(avg_gap, 2),
                "dominant_direction": dominant_dir,
                "hypothesis":         _gap_hypothesis(metal, dominant_dir, avg_gap),
            })

    return {
        "total_gaps":       len(gaps),
        "gap_rate_pct":     round(len(gaps) / max(len(log), 1) * 100, 1),
        "individual_gaps":  gaps,
        "systematic_patterns": pattern_summary,
    }


def _gap_hypothesis(metal: str, direction: str, gap: float) -> str:
    hypotheses = {
        "Fe":  "Coking/carbon deposition deactivating Fe active sites at high temperature — model lacks coking kinetics",
        "Ni":  "Sintering at elevated temperature reduces Ni dispersion — model underestimates deactivation",
        "Cu":  "Surface oxidation state change under reaction conditions not captured in static features",
        "Pd":  "Surface reconstruction at temperature changes active geometry — GNN needed for dynamic modelling",
        "Ru":  "Ru under-oxidation leads to higher-than-expected activity — model conservative",
    }
    base = hypotheses.get(metal, f"Unknown mechanism for {metal} — requires deeper DFT analysis")
    severity = "Severe" if gap > 15 else "Moderate"
    return f"[{severity}] {base}"


# ── 3. INCREMENTAL RETRAINING ─────────────────────────────────────────────────

def build_augmented_dataset(log: list):
    """
    Combine original training data with logged experimental results.
    New experimental data is given 2× weight (more recent = more reliable).
    """
    # Original dataset
    X_orig, y_act_orig, y_sel_orig, y_dg_orig = build_dataset()

    # New logged data
    X_new, y_act_new, y_sel_new = [], [], []
    for exp in log:
        cat = exp["catalyst"]
        r   = exp["results"]
        if r["actual_activity"] is None:
            continue
        feats = engineer_features(
            cat["base_metal"], cat["promoter"], cat["support"],
            cat["temp"], cat["pressure"]
        )
        X_new.append(feats)
        y_act_new.append(r["actual_activity"])
        y_sel_new.append(r["actual_selectivity"])
        y_dg_new = []  # delta_g not always measured in lab

    if not X_new:
        return X_orig, y_act_orig, y_sel_orig, y_dg_orig, 0

    X_new = np.array(X_new)
    y_act_new = np.array(y_act_new)
    y_sel_new = np.array(y_sel_new)

    # Double-weight new samples by repeating them
    X_combined    = np.vstack([X_orig, X_new, X_new])
    y_act_combined = np.concatenate([y_act_orig, y_act_new, y_act_new])
    y_sel_combined = np.concatenate([y_sel_orig, y_sel_new, y_sel_new])
    # For ΔG: use original only (new lab data rarely measures this)
    y_dg_combined  = np.concatenate([y_dg_orig, np.full(len(X_new)*2, -1.0)])

    return X_combined, y_act_combined, y_sel_combined, y_dg_combined, len(X_new)


def retrain(force: bool = False) -> dict:
    """
    Main retraining function. Call this after new experiments are logged.

    Logic:
      1. Count unprocessed experiments since last retrain
      2. If count >= MIN_NEW_SAMPLES (or force=True), retrain
      3. Detect gaps in new data
      4. Build augmented dataset (original + new, double-weighted)
      5. Retrain all three GBR models
      6. Compare accuracy before vs after
      7. Save new model + retrain log entry

    Returns:
        Dict with retrain summary, accuracy delta, detected gaps
    """
    print("=" * 65)
    print("  CatalystOS — Active Memory Training Loop")
    print("=" * 65)

    log = load_experiment_log()
    retrain_history = _load_retrain_history()
    last_retrain_count = retrain_history[-1]["total_experiments_at_retrain"] if retrain_history else 0
    new_since_last = len(log) - last_retrain_count

    print(f"\n  Total experiments in log: {len(log)}")
    print(f"  New since last retrain:   {new_since_last}")
    print(f"  Retrain threshold:        {MIN_NEW_SAMPLES}")

    if new_since_last < MIN_NEW_SAMPLES and not force:
        msg = f"  ⏳ Not enough new data yet ({new_since_last}/{MIN_NEW_SAMPLES}). Retrain skipped."
        print(msg)
        return {"status": "skipped", "reason": msg, "new_samples": new_since_last}

    # ── Gap detection ──────────────────────────────────────────────
    print("\n  Detecting prediction gaps...")
    gap_report = detect_prediction_gaps(log)
    print(f"  Gaps found: {gap_report['total_gaps']} / {len(log)} experiments ({gap_report['gap_rate_pct']}%)")
    for p in gap_report["systematic_patterns"]:
        print(f"  ⚠  Pattern — {p['metal_family']}: avg gap {p['avg_gap_pct']}%, {p['experiments_affected']} experiments")
        print(f"     Hypothesis: {p['hypothesis']}")

    # ── Load or create baseline model ─────────────────────────────
    if os.path.exists(MODEL_PATH):
        print("\n  Loading existing model for comparison...")
        with open(MODEL_PATH, "rb") as f:
            old_model = pickle.load(f)
    else:
        print("\n  No existing model found — training from scratch...")
        old_model = None

    # ── Build augmented dataset ────────────────────────────────────
    X, y_act, y_sel, y_dg, n_new = build_augmented_dataset(log)
    print(f"\n  Augmented dataset: {len(X)} samples ({n_new} new lab results, double-weighted)")

    # ── Baseline accuracy (before retrain) ────────────────────────
    X_base, y_act_base, y_sel_base, y_dg_base = build_dataset()
    if old_model:
        X_scaled_base = old_model.scaler.transform(X_base)
        old_act_mae  = mean_absolute_error(y_act_base, old_model.model_activity.predict(X_scaled_base))
        old_sel_mae  = mean_absolute_error(y_sel_base, old_model.model_selectivity.predict(X_scaled_base))
        old_act_r2   = r2_score(y_act_base, old_model.model_activity.predict(X_scaled_base))
    else:
        old_act_mae, old_sel_mae, old_act_r2 = None, None, None

    # ── Retrain ────────────────────────────────────────────────────
    print("\n  Retraining GradientBoost-E2J on augmented dataset...")
    new_model = GradientBoostE2J()
    new_metrics = new_model.train(X, y_act, y_sel, y_dg, test_size=0.15)

    # ── New accuracy ───────────────────────────────────────────────
    new_act_mae = new_metrics["activity"]["MAE"]
    new_sel_mae = new_metrics["selectivity"]["MAE"]
    new_act_r2  = new_metrics["activity"]["R2"]

    # ── Accuracy delta ─────────────────────────────────────────────
    if old_act_mae is not None:
        act_improvement = round(old_act_mae - new_act_mae, 3)
        r2_improvement  = round(new_act_r2 - old_act_r2, 3)
    else:
        act_improvement = None
        r2_improvement  = None

    print(f"\n  {'Metric':<25} {'Before':>10} {'After':>10} {'Δ':>10}")
    print(f"  {'─'*25} {'─'*10} {'─'*10} {'─'*10}")
    print(f"  {'Activity MAE (%)':<25} {str(round(old_act_mae,3)) if old_act_mae else 'N/A':>10} {new_act_mae:>10} {('+' if act_improvement and act_improvement>0 else '')+str(act_improvement) if act_improvement is not None else 'N/A':>10}")
    print(f"  {'Activity R²':<25} {str(round(old_act_r2,3)) if old_act_r2 else 'N/A':>10} {new_act_r2:>10} {('+' if r2_improvement and r2_improvement>0 else '')+str(r2_improvement) if r2_improvement is not None else 'N/A':>10}")
    print(f"  {'Selectivity MAE (%)':<25} {str(round(old_sel_mae,3)) if old_sel_mae else 'N/A':>10} {new_sel_mae:>10}")

    # ── Save new model ─────────────────────────────────────────────
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(new_model, f)
    print(f"\n  ✓ Model saved → {MODEL_PATH}")

    # ── Retrain log entry ──────────────────────────────────────────
    retrain_entry = {
        "retrain_id":                   f"RT-{len(retrain_history)+1:03d}",
        "timestamp":                    datetime.now().isoformat(),
        "total_experiments_at_retrain": len(log),
        "new_samples_added":            n_new,
        "gaps_detected":                gap_report["total_gaps"],
        "systematic_patterns":          gap_report["systematic_patterns"],
        "metrics_before": {
            "activity_mae": round(old_act_mae, 3) if old_act_mae else None,
            "activity_r2":  round(old_act_r2, 3)  if old_act_r2  else None,
        },
        "metrics_after": {
            "activity_mae": new_act_mae,
            "activity_r2":  new_act_r2,
            "selectivity_mae": new_sel_mae,
        },
        "improvement": {
            "mae_delta": act_improvement,
            "r2_delta":  r2_improvement,
            "improved":  act_improvement > 0 if act_improvement is not None else None,
        }
    }
    retrain_history.append(retrain_entry)
    _save_retrain_history(retrain_history)
    print(f"  ✓ Retrain history updated → {RETRAIN_LOG_PATH}")

    summary = {
        "status":           "retrained",
        "retrain_id":       retrain_entry["retrain_id"],
        "new_samples":      n_new,
        "gaps_detected":    gap_report["total_gaps"],
        "activity_mae_before": round(old_act_mae, 3) if old_act_mae else None,
        "activity_mae_after":  new_act_mae,
        "mae_improvement":  act_improvement,
        "r2_improvement":   r2_improvement,
        "gap_report":       gap_report,
    }

    print(f"\n  {'='*65}")
    print(f"  RETRAIN COMPLETE — {retrain_entry['retrain_id']}")
    if act_improvement and act_improvement > 0:
        print(f"  ✅ Model improved! MAE reduced by {act_improvement}% | R² +{r2_improvement}")
    else:
        print(f"  ⚠  No improvement this cycle — more data needed")
    print(f"  {'='*65}\n")

    return summary


def _load_retrain_history() -> list:
    if os.path.exists(RETRAIN_LOG_PATH):
        with open(RETRAIN_LOG_PATH, "r") as f:
            return json.load(f)
    return []


def _save_retrain_history(history: list):
    with open(RETRAIN_LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)


def show_retrain_history():
    """Print a summary of all retraining cycles."""
    history = _load_retrain_history()
    if not history:
        print("  No retrain history found.")
        return
    print(f"\n  {'─'*65}")
    print(f"  RETRAIN HISTORY ({len(history)} cycles)")
    print(f"  {'─'*65}")
    print(f"  {'ID':<10} {'Timestamp':<22} {'Samples':>8} {'Gaps':>6} {'MAE Before':>12} {'MAE After':>10} {'Δ MAE':>8}")
    for h in history:
        before = h['metrics_before']['activity_mae'] or '—'
        after  = h['metrics_after']['activity_mae']
        delta  = h['improvement']['mae_delta']
        delta_str = f"+{delta}" if delta and delta > 0 else str(delta) if delta else '—'
        print(f"  {h['retrain_id']:<10} {h['timestamp'][:19]:<22} {h['new_samples_added']:>8} {h['gaps_detected']:>6} {str(before):>12} {after:>10} {delta_str:>8}")


# ── 4. DEMO / ENTRY POINT ─────────────────────────────────────────────────────

if __name__ == "__main__":

    print("\n  Simulating GPS Renewables lab workflow...\n")

    # --- Step 1: Seed the experiment log with GPS lab results ---
    GPS_LAB_RESULTS = [
        # (exp_id, base, promoter, support, temp, pressure, actual_act, actual_sel, pred_act, pred_sel, outcome, notes)
        ("EXP-022", "Pd",  "Pt",  "HZSM5",  335, 1, 74,  84, 88,  86, "partial", "Large gap — surface reconstruction at 335°C"),
        ("EXP-023", "Cu",  "Zn",  "SiO2",   330, 1, 89,  87, 91,  88, "pass",    "GNN candidate first validation — excellent"),
        ("EXP-024", "Pd",  "Ag",  "Al2O3",  315, 1, 82,  76, 80,  77, "pass",    "Confirmed top performer"),
        ("EXP-025", "Fe",  "Co",  "ZSM5",   340, 1, 65,  68, 76,  71, "pass",    "Slight underperformance at higher temp"),
        ("EXP-026", "Ru",  "Fe",  "Al2O3",  300, 5, 96,  89, 94,  87, "pass",    "High pressure run — best yield yet"),
    ]

    print("  Logging 5 new lab results...")
    for r in GPS_LAB_RESULTS:
        record = log_experiment(*r)
        gap_flag = "⚠ GAP" if record["gap"]["is_gap"] else "✓ OK "
        print(f"  {gap_flag}  {r[0]}: predicted={r[8]}% actual={r[6]}% | gap={record['gap']['activity_gap']}%")

    # --- Step 2: Trigger retraining ---
    print(f"\n  {len(GPS_LAB_RESULTS)} results logged. Triggering retrain...\n")
    summary = retrain(force=True)

    # --- Step 3: Show what was learned ---
    print("\n  GAP INTELLIGENCE REPORT")
    print("  " + "─" * 50)
    gaps = summary["gap_report"]
    print(f"  Total gaps detected: {gaps['total_gaps']} ({gaps['gap_rate_pct']}% of experiments)")
    for p in gaps["systematic_patterns"]:
        print(f"\n  Metal family: {p['metal_family']}")
        print(f"  Affected:     {p['experiments_affected']} experiments, avg gap {p['avg_gap_pct']}%")
        print(f"  Direction:    {p['dominant_direction']}")
        print(f"  Hypothesis:   {p['hypothesis']}")

    # --- Step 4: Show retrain history ---
    show_retrain_history()

    # --- Step 5: Verify saved model works ---
    print("\n  Verifying saved model...")
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            loaded_model = pickle.load(f)
        test = loaded_model.predict("Cu", "Zn", "SiO2", 330, 5)
        print(f"  ✓ Loaded model prediction — Cu-Zn/SiO₂ at 330°C 5bar:")
        print(f"    Activity: {test['predictions']['activity']}% | Selectivity: {test['predictions']['selectivity']}% | ΔG: {test['predictions']['delta_g_eV']} eV")

    print("\n  API USAGE EXAMPLE")
    print("  " + "─" * 50)
    print("""
  from training_loop import log_experiment, retrain

  # After a lab run completes:
  log_experiment(
      exp_id="EXP-027",
      base_metal="Cu", promoter="Zn", support="SiO2",
      temp=330, pressure=15,
      actual_activity=91.0, actual_selectivity=87.0,
      predicted_activity=90.0, predicted_selectivity=85.0,
      outcome="pass", notes="High pressure trial — new record"
  )

  # Retrain triggers automatically when MIN_NEW_SAMPLES reached:
  summary = retrain()
  # Returns: {"status": "retrained", "mae_improvement": 0.4, "gaps_detected": 1, ...}
    """)

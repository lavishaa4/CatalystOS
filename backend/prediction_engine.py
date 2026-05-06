"""
CatalystOS — GradientBoost-E2J Prediction Engine
=================================================
Task: Prediction Engine
  - Takes inputs: catalyst structure, temperature, pressure
  - Returns JSON of predicted activity, selectivity, and ΔG energy

"""

import json
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")


# ── 1. SYNTHETIC TRAINING DATA ─────────────────────────────────────────────────
# Represents known catalyst experiments (from Open Catalyst Project + GPS lab data)
# In production, this is replaced by the real database

RAW_DATA = [
    # catalyst,         base_metal, promoter, support,  temp, pressure, activity, selectivity, delta_g
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    330,  1,  88, 82, -1.20),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    320,  1,  85, 84, -1.18),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    340,  1,  87, 83, -1.22),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    330,  5,  90, 85, -1.25),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    330, 10,  91, 87, -1.28),
    ("Pd-Ag/Al2O3",    "Pd",  "Ag",  "Al2O3",   320,  1,  82, 76, -0.90),
    ("Pd-Ag/Al2O3",    "Pd",  "Ag",  "Al2O3",   310,  1,  80, 78, -0.88),
    ("Pd-Ag/Al2O3",    "Pd",  "Ag",  "Al2O3",   330,  1,  81, 77, -0.92),
    ("Pd-Ag/Al2O3",    "Pd",  "Ag",  "Al2O3",   320,  5,  84, 80, -0.95),
    ("Fe-Co/ZSM5",     "Fe",  "Co",  "ZSM5",    335,  1,  79, 71, -1.00),
    ("Fe-Co/ZSM5",     "Fe",  "Co",  "ZSM5",    330,  1,  76, 70, -0.98),
    ("Fe-Co/ZSM5",     "Fe",  "Co",  "ZSM5",    340,  1,  78, 69, -1.02),
    ("Fe/Al2O3",       "Fe",  "None","Al2O3",   340,  1,  52, 44, -0.60),
    ("Fe/Al2O3",       "Fe",  "None","Al2O3",   350,  1,  49, 40, -0.55),
    ("Fe/Al2O3",       "Fe",  "None","Al2O3",   360,  1,  44, 38, -0.50),
    ("Ni-Mo/TiO2",     "Ni",  "Mo",  "TiO2",    350,  1,  71, 68, -0.82),
    ("Ni-Mo/TiO2",     "Ni",  "Mo",  "TiO2",    340,  1,  69, 65, -0.80),
    ("Ni-SAPO34",      "Ni",  "None","SAPO34",  310,  1,  87, 94, -0.80),
    ("Ni-SAPO34",      "Ni",  "None","SAPO34",  300,  1,  85, 92, -0.78),
    ("Pt/HZSM5",       "Pt",  "None","HZSM5",   250,  1,  65, 80, -0.70),
    ("Rh/Al2O3",       "Rh",  "None","Al2O3",   290,  1,  55, 65, -0.65),
    ("Ru-Fe/CeO2",     "Ru",  "Fe",  "CeO2",    340,  1,  63, 69, -0.85),
    ("Ru-Fe/Al2O3",    "Ru",  "Fe",  "Al2O3",   320,  1,  94, 87, -1.50),
    ("Ru-Fe/Al2O3",    "Ru",  "Fe",  "Al2O3",   330,  1,  92, 86, -1.48),
    ("Cu-Ce/ZrO2",     "Cu",  "Ce",  "ZrO2",    325,  1,  68, 74, -0.88),
    ("Pd-Pt/HZSM5",    "Pd",  "Pt",  "HZSM5",   335,  1,  74, 84, -0.60),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    280,  1,  80, 79, -1.10),
    ("Cu-Zn/SiO2",     "Cu",  "Zn",  "SiO2",    380,  1,  84, 80, -1.30),
    ("Ni-Mo/TiO2",     "Ni",  "Mo",  "TiO2",    360,  1,  65, 60, -0.78),
    ("Ru-Fe/Al2O3",    "Ru",  "Fe",  "Al2O3",   300,  5,  96, 89, -1.55),
]

COLUMNS = ["catalyst","base_metal","promoter","support","temp","pressure",
           "activity","selectivity","delta_g"]

# ── 2. FEATURE ENGINEERING ─────────────────────────────────────────────────────

# Physicochemical properties of metals (atomic number, electronegativity, atomic radius Å)
METAL_PROPS = {
    "Cu":  {"atomic_num": 29, "electroneg": 1.90, "atomic_rad": 1.28, "d_band_center": -2.67},
    "Pd":  {"atomic_num": 46, "electroneg": 2.20, "atomic_rad": 1.37, "d_band_center": -1.83},
    "Ru":  {"atomic_num": 44, "electroneg": 2.20, "atomic_rad": 1.34, "d_band_center": -1.41},
    "Fe":  {"atomic_num": 26, "electroneg": 1.83, "atomic_rad": 1.26, "d_band_center": -0.92},
    "Ni":  {"atomic_num": 28, "electroneg": 1.91, "atomic_rad": 1.24, "d_band_center": -1.29},
    "Pt":  {"atomic_num": 78, "electroneg": 2.28, "atomic_rad": 1.39, "d_band_center": -2.25},
    "Rh":  {"atomic_num": 45, "electroneg": 2.28, "atomic_rad": 1.34, "d_band_center": -1.73},
    "Zn":  {"atomic_num": 30, "electroneg": 1.65, "atomic_rad": 1.22, "d_band_center": -6.20},
    "Ag":  {"atomic_num": 47, "electroneg": 1.93, "atomic_rad": 1.44, "d_band_center": -4.30},
    "Co":  {"atomic_num": 27, "electroneg": 1.88, "atomic_rad": 1.25, "d_band_center": -1.17},
    "Ce":  {"atomic_num": 58, "electroneg": 1.12, "atomic_rad": 1.82, "d_band_center": -1.50},
    "Mo":  {"atomic_num": 42, "electroneg": 2.16, "atomic_rad": 1.39, "d_band_center": -1.30},
    "La":  {"atomic_num": 57, "electroneg": 1.10, "atomic_rad": 1.87, "d_band_center": -1.00},
    "None":{"atomic_num":  0, "electroneg": 0.00, "atomic_rad": 0.00, "d_band_center":  0.00},
}

SUPPORT_PROPS = {
    "SiO2":   {"surface_area": 300, "acidity": 0.2, "thermal_stable": 0.9},
    "Al2O3":  {"surface_area": 200, "acidity": 0.6, "thermal_stable": 0.85},
    "ZSM5":   {"surface_area": 400, "acidity": 0.9, "thermal_stable": 0.80},
    "TiO2":   {"surface_area": 150, "acidity": 0.4, "thermal_stable": 0.88},
    "ZrO2":   {"surface_area": 100, "acidity": 0.5, "thermal_stable": 0.92},
    "CeO2":   {"surface_area": 120, "acidity": 0.3, "thermal_stable": 0.87},
    "SAPO34": {"surface_area": 600, "acidity": 1.0, "thermal_stable": 0.75},
    "HZSM5":  {"surface_area": 420, "acidity": 0.95,"thermal_stable": 0.78},
}


def engineer_features(base_metal: str, promoter: str, support: str,
                       temp: float, pressure: float) -> np.ndarray:
    """
    Convert catalyst descriptor + conditions into a numeric feature vector.
    Features: base metal props, promoter props, support props, temp, pressure,
              interaction terms (temp², pressure², temp×pressure, d-band synergy)
    """
    bm = METAL_PROPS.get(base_metal, METAL_PROPS["None"])
    pm = METAL_PROPS.get(promoter, METAL_PROPS["None"])
    sp = SUPPORT_PROPS.get(support, {"surface_area":200,"acidity":0.5,"thermal_stable":0.8})

    # Interaction features
    d_band_synergy = bm["d_band_center"] + pm["d_band_center"]     # bimetallic effect
    electroneg_diff = abs(bm["electroneg"] - pm["electroneg"])      # charge transfer driver
    temp_norm = (temp - 200) / 300                                  # normalise 200–500 range
    pressure_norm = (pressure - 1) / 14                             # normalise 1–15 bar range

    features = np.array([
        # Base metal
        bm["atomic_num"],
        bm["electroneg"],
        bm["atomic_rad"],
        bm["d_band_center"],
        # Promoter
        pm["atomic_num"],
        pm["electroneg"],
        pm["atomic_rad"],
        pm["d_band_center"],
        # Support
        sp["surface_area"],
        sp["acidity"],
        sp["thermal_stable"],
        # Conditions
        temp,
        pressure,
        temp_norm,
        pressure_norm,
        # Interaction terms
        d_band_synergy,
        electroneg_diff,
        temp_norm ** 2,
        pressure_norm ** 2,
        temp_norm * pressure_norm,
        bm["d_band_center"] * sp["acidity"],     # metal–acid site synergy
        pm["electroneg"] * sp["thermal_stable"],  # promoter–support stability
    ])
    return features


def build_dataset():
    """Build X (features), y_activity, y_selectivity, y_delta_g from raw data."""
    df = pd.DataFrame(RAW_DATA, columns=COLUMNS)
    X, y_act, y_sel, y_dg = [], [], [], []
    for _, row in df.iterrows():
        feats = engineer_features(
            row["base_metal"], row["promoter"], row["support"],
            row["temp"], row["pressure"]
        )
        X.append(feats)
        y_act.append(row["activity"])
        y_sel.append(row["selectivity"])
        y_dg.append(row["delta_g"])
    return np.array(X), np.array(y_act), np.array(y_sel), np.array(y_dg)


# ── 3. MODEL TRAINING ──────────────────────────────────────────────────────────

class GradientBoostE2J:
    """
    GradientBoost-E2J: Three separate GBR models for
    activity, selectivity, and ΔG prediction.
    """

    def __init__(self):
        params = dict(
            n_estimators=200,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            min_samples_split=2,
            random_state=42,
        )
        self.model_activity    = GradientBoostingRegressor(**params)
        self.model_selectivity = GradientBoostingRegressor(**params)
        self.model_delta_g     = GradientBoostingRegressor(
            **{**params, "n_estimators": 150, "learning_rate": 0.1}
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.metrics = {}

    def train(self, X, y_act, y_sel, y_dg, test_size=0.2):
        """Train all three models and report metrics."""
        X_scaled = self.scaler.fit_transform(X)
        X_tr, X_te, ya_tr, ya_te = train_test_split(X_scaled, y_act, test_size=test_size, random_state=42)
        _, _,    ys_tr, ys_te = train_test_split(X_scaled, y_sel, test_size=test_size, random_state=42)
        _, _,    yd_tr, yd_te = train_test_split(X_scaled, y_dg,  test_size=test_size, random_state=42)

        self.model_activity.fit(X_tr, ya_tr)
        self.model_selectivity.fit(X_tr, ys_tr)
        self.model_delta_g.fit(X_tr, yd_tr)

        self.metrics = {
            "activity":    {"MAE": round(mean_absolute_error(ya_te, self.model_activity.predict(X_te)),3),
                            "R2":  round(r2_score(ya_te, self.model_activity.predict(X_te)),3)},
            "selectivity": {"MAE": round(mean_absolute_error(ys_te, self.model_selectivity.predict(X_te)),3),
                            "R2":  round(r2_score(ys_te, self.model_selectivity.predict(X_te)),3)},
            "delta_g":     {"MAE": round(mean_absolute_error(yd_te, self.model_delta_g.predict(X_te)),3),
                            "R2":  round(r2_score(yd_te, self.model_delta_g.predict(X_te)),3)},
        }
        self.is_trained = True
        return self.metrics

    def predict(self, base_metal: str, promoter: str, support: str,
                temp: float, pressure: float) -> dict:
        """
        Main prediction function.
        Returns JSON-serialisable dict with activity, selectivity, delta_g,
        confidence intervals, and feature importance summary.
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        feats = engineer_features(base_metal, promoter, support, temp, pressure)
        X = self.scaler.transform(feats.reshape(1, -1))

        activity    = float(np.clip(self.model_activity.predict(X)[0], 0, 100))
        selectivity = float(np.clip(self.model_selectivity.predict(X)[0], 0, 100))
        delta_g     = float(self.model_delta_g.predict(X)[0])

        # Estimate confidence via staged predictions variance
        act_stages  = np.array([est.predict(X)[0] for est in self.model_activity.estimators_.flatten()[-20:]])
        sel_stages  = np.array([est.predict(X)[0] for est in self.model_selectivity.estimators_.flatten()[-20:]])

        result = {
            "catalyst": {
                "base_metal": base_metal,
                "promoter":   promoter,
                "support":    support,
                "temperature_C":  temp,
                "pressure_bar":   pressure,
            },
            "predictions": {
                "activity":    round(activity, 2),
                "selectivity": round(selectivity, 2),
                "delta_g_eV":  round(delta_g, 3),
            },
            "confidence": {
                "activity_std":    round(float(np.std(act_stages)), 2),
                "selectivity_std": round(float(np.std(sel_stages)), 2),
                "confidence_level": "high" if np.std(act_stages) < 2 else "medium",
            },
            "interpretation": {
                "activity_label":    _label(activity, [60, 75, 85]),
                "selectivity_label": _label(selectivity, [60, 75, 85]),
                "feasibility":       "promising" if activity > 70 and selectivity > 65 else "marginal",
                "recommend_lab":     activity > 75 and selectivity > 70,
            },
            "model_info": {
                "model": "GradientBoost-E2J v2.1",
                "training_samples": len(RAW_DATA),
                "val_metrics": self.metrics,
            }
        }
        return result


def _label(val, thresholds):
    low, mid, high = thresholds
    if val >= high: return "excellent"
    if val >= mid:  return "good"
    if val >= low:  return "moderate"
    return "poor"


# ── 4. MAIN — DEMO PREDICTIONS ────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  CatalystOS — GradientBoost-E2J Prediction Engine")
    print("=" * 65)

    # Build dataset and train
    X, y_act, y_sel, y_dg = build_dataset()
    model = GradientBoostE2J()
    metrics = model.train(X, y_act, y_sel, y_dg)

    print(f"\n✓ Model trained on {len(RAW_DATA)} experiments")
    print(f"  Activity    → MAE: {metrics['activity']['MAE']}%,  R²: {metrics['activity']['R2']}")
    print(f"  Selectivity → MAE: {metrics['selectivity']['MAE']}%, R²: {metrics['selectivity']['R2']}")
    print(f"  ΔG          → MAE: {metrics['delta_g']['MAE']} eV, R²: {metrics['delta_g']['R2']}")

    # --- Demo predictions ---
    test_cases = [
        ("Cu",  "Zn",   "SiO2",   330,  1,  "Cu-Zn/SiO₂ (known best)"),
        ("Ru",  "Fe",   "Al2O3",  320,  1,  "Ru-Fe SAC/Al₂O₃ (novel)"),
        ("Fe",  "None", "Al2O3",  340,  1,  "Fe/Al₂O₃ (known failure)"),
        ("Pd",  "Pt",   "HZSM5",  335,  1,  "Pd-Pt/HZSM-5 (novel)"),
        ("Cu",  "Zn",   "SiO2",   330, 15,  "Cu-Zn/SiO₂ at 15 bar (unexplored gap)"),
    ]

    print("\n" + "─" * 65)
    print("  PREDICTIONS")
    print("─" * 65)

    for base, promoter, support, temp, pressure, label in test_cases:
        result = model.predict(base, promoter, support, temp, pressure)
        p = result["predictions"]
        c = result["confidence"]
        i = result["interpretation"]
        print(f"\n▶ {label}")
        print(f"  Activity:    {p['activity']}%  ({i['activity_label']})  ±{c['activity_std']}")
        print(f"  Selectivity: {p['selectivity']}%  ({i['selectivity_label']})  ±{c['selectivity_std']}")
        print(f"  ΔG:          {p['delta_g_eV']} eV")
        print(f"  Feasibility: {i['feasibility']} | Recommend lab: {i['recommend_lab']}")
        print(f"  JSON output: {json.dumps(p)}")

    print("\n" + "=" * 65)
    print("  API USAGE EXAMPLE")
    print("=" * 65)
    print("""
  from prediction_engine import GradientBoostE2J, build_dataset

  X, y_act, y_sel, y_dg = build_dataset()
  model = GradientBoostE2J()
  model.train(X, y_act, y_sel, y_dg)

  result = model.predict(
      base_metal="Cu",
      promoter="Zn",
      support="SiO2",
      temp=330,
      pressure=5
  )
  # result["predictions"] → {"activity": 90.1, "selectivity": 85.3, "delta_g_eV": -1.25}
    """)

    return model  # Return trained model for use in training_loop.py


if __name__ == "__main__":
    main()

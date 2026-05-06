"""
CatalystOS — Backend API Server
================================
FastAPI backend for the National Molecular Discovery Platform (GPS Renewables NG SAF Program)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, json, os, math, time, pickle, re
from datetime import datetime

from prediction_engine import GradientBoostE2J, build_dataset
from training_loop import log_experiment as ml_log_experiment, retrain, load_experiment_log, detect_prediction_gaps

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CatalystOS API",
    description="Backend API for the GPS Renewables National Molecular Discovery Platform",
    version="1.0.0"
)

# CORS Setup
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database setup ─────────────────────────────────────────────────────────────
DB_PATH = "catalystos.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            reaction    TEXT,
            novel       INTEGER DEFAULT 0,
            rank        INTEGER,
            activity    REAL,
            selectivity REAL,
            stability   REAL,
            source      TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id          TEXT PRIMARY KEY,
            catalyst    TEXT,
            reaction    TEXT,
            temp        REAL,
            predicted   REAL,
            actual      REAL,
            selectivity REAL,
            status      TEXT,
            notes       TEXT,
            logged_at   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            year        INTEGER,
            relevance   TEXT,
            abstract    TEXT
        )
    """)
    conn.commit()

    if cur.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0:
        candidates = [
            (1, "Cu-Zn/SiO2",        "EtOH → Jet Fuel",    0, 1,  88, 82, 79, "Open Catalyst Project"),
            (2, "Pd-Ag/Al2O3",       "EtOH → Jet Fuel",    0, 2,  82, 76, 85, "Materials Project"),
            (3, "Fe-Co/ZSM-5",       "EtOH → Jet Fuel",    1, 3,  79, 71, 68, "AI Generated"),
            (4, "Ni-Mo/TiO2",        "EtOH → Jet Fuel",    0, 4,  71, 68, 74, "Open Catalyst Project"),
            (5, "Cu-Ce/ZrO2",        "EtOH → Jet Fuel",    1, 5,  68, 74, 71, "AI Generated"),
            (6, "Pt/HZSM-5",         "CO2 → Methanol",     0, 6,  65, 80, 62, "BRENDA DB"),
            (7, "Ru-Fe/CeO2",        "EtOH → Jet Fuel",    1, 7,  63, 69, 77, "AI Generated"),
            (8, "Cu/ZnO",            "CO2 → Methanol",     0, 8,  61, 72, 55, "Open Catalyst Project"),
            (9, "Pd-Pt/HZSM-5",      "EtOH → Jet Fuel",    1, 9,  58, 84, 60, "AI Generated"),
            (10,"Rh/Al2O3",          "Syngas → Ethanol",   0, 10, 55, 65, 80, "Materials Project"),
        ]
        cur.executemany("INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?,?)", candidates)

    conn.commit()
    conn.close()
    print("Database ready:", DB_PATH)


# ── Pydantic models ────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    catalyst: str
    temperature: float = 330.0
    pressure: float = 1.0
    reaction: str = "EtOH→Jet"

class PredictResponse(BaseModel):
    catalyst: str
    predicted_activity: float
    predicted_selectivity: float
    predicted_stability: float
    confidence: float
    energy_ev: float
    recommendation: str

class ExperimentLog(BaseModel):
    catalyst: str
    reaction: str
    temperature: float
    predicted: float
    actual: float
    selectivity: float
    status: str
    notes: Optional[str] = ""

class ExperimentResponse(BaseModel):
    id: str
    message: str
    gap: float


# ── ML Global Model ────────────────────────────────────────────────────────────
ml_model = None

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"system": "CatalystOS API", "status": "online"}

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "message": "Backend healthy", "timestamp": time.time()}

@app.get("/dashboard", tags=["System"])
def get_dashboard_data():
    return {
        "pipeline": [
            {"id": 1, "stage": "Ethanol dehydration", "product": "Ethylene", "catalyst": "ZSM-5 zeolite", "condition": "380°C", "status": "Optimized"},
            {"id": 2, "stage": "Ethylene oligomerization", "product": "C6–C16", "catalyst": "Ni-SAPO-34", "condition": "Target >65%", "status": "Active"},
            {"id": 3, "stage": "Hydroprocessing", "product": "Jet fuel range", "catalyst": "Cu-Zn/SiO2 top candidate", "condition": "Optimizing", "status": "Optimizing"},
            {"id": 4, "stage": "Isomerization", "product": "Freeze-point spec", "catalyst": "Pt/SAPO-11", "condition": "Target ≤-47°C", "status": "Pending"},
        ],
        "activity_log": [
            {"time": "2m ago", "message": "AI proposed Cu-Zn-Pd variant #3"},
            {"time": "1h ago", "message": "Gap detected: Fe catalysts fail above 320°C"},
            {"time": "1d ago", "message": "Model retrained"},
        ],
        "top_candidates": [
            {"name": "Cu-Zn/SiO2", "score": 88, "ai_tag": False},
            {"name": "Pd-Ag/Al2O3", "score": 82, "ai_tag": False},
            {"name": "Fe-Co/ZSM-5", "score": 79, "ai_tag": True},
        ]
    }

@app.get("/gaps", tags=["System"])
def get_gaps():
    log = load_experiment_log()
    return detect_prediction_gaps(log)

@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict(req: PredictRequest):
    try:
        if "/" in req.catalyst:
            metals, support = req.catalyst.split("/")
            if "-" in metals:
                base, promoter = metals.split("-")
            else:
                base, promoter = metals, "None"
        else:
            base, promoter, support = "Cu", "Zn", "SiO2"
    except:
        base, promoter, support = "Cu", "None", "SiO2"
    
    result = ml_model.predict(base, promoter, support, req.temperature, req.pressure)
    p = result["predictions"]
    i = result["interpretation"]
    c = result["confidence"]
    
    return PredictResponse(
        catalyst=req.catalyst,
        predicted_activity=p["activity"],
        predicted_selectivity=p["selectivity"],
        predicted_stability=75.0, # Default mock since model doesn't predict this
        confidence=c["activity_std"],
        energy_ev=p["delta_g_eV"],
        recommendation=f"Feasibility: {i['feasibility']}. Lab testing: {i['recommend_lab']}"
    )

@app.post("/log-experiment", response_model=ExperimentResponse, tags=["Experiments"])
def log_experiment_endpoint(exp: ExperimentLog):
    conn = get_db()
    cur = conn.cursor()
    count = cur.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
    exp_id = f"EXP-{count + 1:03d}"
    if cur.execute("SELECT id FROM experiments WHERE id=?", (exp_id,)).fetchone():
        exp_id = f"EXP-{count + 100:03d}"
    
    cur.execute("""
        INSERT INTO experiments (id, catalyst, reaction, temp, predicted, actual, selectivity, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (exp_id, exp.catalyst, exp.reaction, exp.temperature,
          exp.predicted, exp.actual, exp.selectivity, exp.status, exp.notes))
    conn.commit()
    conn.close()

    try:
        if "/" in exp.catalyst:
            metals, support = exp.catalyst.split("/")
            if "-" in metals:
                base, promoter = metals.split("-")
            else:
                base, promoter = metals, "None"
        else:
            base, promoter, support = "Cu", "Zn", "SiO2"
    except:
        base, promoter, support = "Cu", "None", "SiO2"

    ml_log_experiment(
        exp_id=exp_id, base_metal=base, promoter=promoter, support=support,
        temp=exp.temperature, pressure=1.0,
        actual_activity=exp.actual, actual_selectivity=exp.selectivity,
        predicted_activity=exp.predicted, predicted_selectivity=exp.selectivity,
        outcome=exp.status, notes=exp.notes
    )
    
    retrain_summary = retrain()
    gap = round(exp.actual - exp.predicted, 1)
    msg = f"Experiment {exp_id} logged."
    if retrain_summary and retrain_summary.get("status") == "retrained":
        msg += " Model automatically retrained based on new data."

    return ExperimentResponse(id=exp_id, message=msg, gap=gap)

@app.get("/candidates", tags=["Candidates"])
def get_candidates(reaction: Optional[str] = Query(None)):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM candidates"
    params = []
    if reaction:
        query += " WHERE reaction LIKE ?"
        params.append(f"%{reaction}%")
    query += " ORDER BY rank ASC"
    rows = cur.execute(query, params).fetchall()
    conn.close()
    return {"count": len(rows), "candidates": [dict(r) for r in rows]}

@app.get("/knowledge-graph", tags=["Intelligence"])
def get_knowledge_graph(q: Optional[str] = Query(None)):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM papers"
    params = []
    if q:
        query += " WHERE title LIKE ? OR abstract LIKE ?"
        params.extend([f"%{q}%", f"%{q}%"])
    query += " ORDER BY year DESC LIMIT 10"
    rows = cur.execute(query, params).fetchall()
    
    # If DB is empty, provide mock data for the demo
    if len(rows) == 0:
        mock = [
            {"id": 1, "title": "Mechanisms of coking in Fe-based Fischer-Tropsch synthesis", "year": 2021, "relevance": "High"},
            {"id": 2, "title": "Deactivation of Iron catalysts at high temperatures", "year": 2019, "relevance": "High"},
            {"id": 3, "title": "Synergistic effects of Cu-Zn in ethanol conversion", "year": 2023, "relevance": "Critical"}
        ]
        if q:
            mock = [m for m in mock if q.lower() in m["title"].lower()]
        return {"results": mock}
        
    conn.close()
    return {"results": [dict(r) for r in rows]}

@app.get("/experiments", tags=["Experiments"])
def get_experiments(catalyst: Optional[str] = Query(None)):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM experiments"
    params = []
    if catalyst:
        query += " WHERE catalyst LIKE ?"
        params.append(f"%{catalyst}%")
    query += " ORDER BY logged_at DESC"
    rows = cur.execute(query, params).fetchall()
    conn.close()
    return {"count": len(rows), "experiments": [dict(r) for r in rows]}


@app.on_event("startup")
def startup_event():
    init_db()
    global ml_model
    MODEL_PATH = "catalystos_model.pkl"
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            ml_model = pickle.load(f)
        print("ML Model loaded from disk.")
    else:
        print("Training ML model from scratch...")
        X, y_act, y_sel, y_dg = build_dataset()
        ml_model = GradientBoostE2J()
        ml_model.train(X, y_act, y_sel, y_dg)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(ml_model, f)
        print("ML Model trained and saved.")
    print("CatalystOS API running on port 8000")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi import HTTPException
from predict_model import predict_conditions, get_feature_order
feature_order = get_feature_order()
from fastapi.staticfiles import StaticFiles

# Ensure predict_model.py is in the same directory
try:
    from predict_model import predict_conditions
except ImportError:
    print("Warning: predict_model.py not found. AI predictions will fail.")

app = FastAPI()

# 1. Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 🔹 SERVE STATIC FILES (CSS, JS, Images)
# Ensure you have a folder named 'static' in your project root
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. 🔹 SERVE HOMEPAGE (Sign-in)
@app.get("/", response_class=HTMLResponse)
def serve_home():
    html_path = Path("index.html")
    if not html_path.exists():
        return HTMLResponse(content="Error: index.html not found in root directory.", status_code=404)
    return html_path.read_text(encoding="utf-8")

# 4. 🔹 SERVE LANDING PAGE (Body Selection)
@app.get("/landingpage.html", response_class=HTMLResponse)
def serve_landing():
    html_path = Path("landingpage.html")
    if not html_path.exists():
        # Fallback check if it's still named chicken.html
        alt_path = Path("chicken.html")
        if alt_path.exists():
            return alt_path.read_text(encoding="utf-8")
        return HTMLResponse(content="Error: landingpage.html not found.", status_code=404)
    return html_path.read_text(encoding="utf-8")


# -------- DATA MODELS --------
class ChatInput(BaseModel):
    message: str

# -------- SINGLE-USER DEMO STATE --------
# Note: This is global and shared by ALL users. 
# For a real app, you'd use a database or session tokens.
state = {
    "step": "body_part",
    "body_part": None,
    "symptoms": []
}

# -------- UI SYMPTOMS --------
SYMPTOMS = {
    "head": ["headache", "dizziness", "nausea"],
    "chest": ["chest_pain", "difficulty_breathing", "heart_palpitations"],
    "stomach": ["nausea", "abdominal_pain", "bloating"],
    "arms": ["numbness", "weakness", "pain"],
    "legs": ["swelling", "numbness", "weakness"],
    "back": ["back_pain", "stiffness", "numbness"]
}


# -------- CHAT ENDPOINT --------
@app.post("/chat")
def chat(input_data: ChatInput):
    user_input = input_data.message.lower().strip()

    # STEP 1: SELECTING BODY PART
    if state["step"] == "body_part":
        if user_input in SYMPTOMS:
            state["body_part"] = user_input
            state["step"] = "symptoms"
            options = ", ".join(SYMPTOMS[user_input])
            return {
                "reply": f"You selected {user_input}. Choose symptoms: {options}. Type 'done' when finished."
            }
        else:
            valid_parts = ", ".join(SYMPTOMS.keys())
            return {
                "reply": f"Please choose a body part: {valid_parts}."
            }

    # STEP 2: SELECTING SYMPTOMS
    if state["step"] == "symptoms":
        if user_input == "done":
            # BUILD FULL SYMPTOM VECTOR
            symptom_dict = {}
            for part_list in SYMPTOMS.values():
                for s in part_list:
                    symptom_dict[s] = 1 if s in state["symptoms"] else 0

            # CALL AI MODEL
            predictions = predict_conditions(symptom_dict)
            top_predictions = predictions[:3]

            response = "Based on your symptoms, possible conditions are:\n"
            # FIXED: Added unpacking for the tuple (disease, confidence)
            for disease, confidence in top_predictions:
                response += f"- {disease} ({confidence * 100:.1f}% confidence)\n"

            # RESET STATE
            state["step"] = "body_part"
            state["body_part"] = None
            state["symptoms"] = []
            
            return {"reply": response}

        # Handle switching body parts mid-stream
        if user_input in SYMPTOMS:
            state["body_part"] = user_input
            options = ", ".join(SYMPTOMS[user_input])
            return {
                "reply": f"Switched to {user_input}. Choose symptoms: {options}. Type 'done' when finished."
            }

        # Add symptom to the list
        if user_input in SYMPTOMS.get(state["body_part"], []):
            if user_input not in state["symptoms"]:
                state["symptoms"].append(user_input)
            return {
                "reply": f"Added symptom: {user_input}. Add more or type 'done' to see results."
            }

        return {
            "reply": "I didn't recognize that symptom. Please choose from the list or type 'done'."
        }

class ChestTriageInput(BaseModel):
    symptoms: List[str]

@app.post("/triage/chest")
def triage_chest(data: ChestTriageInput):
    ui_to_model = {
        "weakness": "weakness",
        "chest-pain": "chest_pain",
        "shortness-of-breath": "difficulty_breathing",
        "cough": "cough",
    }

    symptom_dict = {feature: 0 for feature in feature_order}

    for ui_symptom in data.symptoms:
        mapped = ui_to_model.get(ui_symptom)
        if mapped and mapped in symptom_dict:
            symptom_dict[mapped] = 1

    predictions = predict_conditions(symptom_dict)
    top = predictions[:3]

    return {
        "reply": [{"condition": d, "confidence": float(c)} for d, c in top]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "FastAPI server is running"}
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/chestssym.html", response_class=HTMLResponse)
def serve_chest():
    html_path = Path("static/chestssym.html")
    if not html_path.exists():
        return HTMLResponse(content="Error: chestssym.html not found in static/", status_code=404)
    return html_path.read_text(encoding="utf-8")
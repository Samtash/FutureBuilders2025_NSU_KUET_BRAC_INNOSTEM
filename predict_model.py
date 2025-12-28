import joblib
import numpy as np

# Load model and feature order
model = joblib.load("diagnosis_model.pkl")
feature_order = joblib.load("feature_order.pkl")

def predict_conditions(symptoms: dict):
    """
    symptoms example:
    {
        "headache": 1,
        "fever": 1,
        "nausea": 0,
        ...
    }
    """

    # Build input vector in correct feature order
    input_vector = [symptoms.get(feature, 0) for feature in feature_order]
    input_vector = np.array(input_vector).reshape(1, -1)

    # Predict probabilities
    probabilities = model.predict_proba(input_vector)[0]
    classes = model.classes_

    # Combine and sort results
    results = sorted(
        zip(classes, probabilities),
        key=lambda x: x[1],
        reverse=True
    )

    return results

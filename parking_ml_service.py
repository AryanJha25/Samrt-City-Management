# parking_ml_service.py

import joblib
import pandas as pd
import datetime
import os
import numpy as np

# --- Load the trained model pipeline on service startup ---
# Ensure this path is correct relative to where parking_ml_service.py is saved
MODEL_PATH = "parking_availability_predictor.pkl"

# Variables to hold the loaded model pipeline and known areas
loaded_pipeline = None
KNOWN_AREAS = []

try:
    # Check if the model file exists
    if not os.path.exists(MODEL_PATH):
         # Raise a specific error if the model is missing
         raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Please run train_parking_predictor.py first.")

    # Load the entire pipeline (preprocessor + model)
    loaded_pipeline = joblib.load(MODEL_PATH)
    print(f"Successfully loaded ML model pipeline from {MODEL_PATH}")

    # Attempt to extract the list of known areas from the loaded preprocessor
    # This assumes 'Area' was the first categorical feature in the ColumnTransformer
    try:
         # Access the 'preprocessor' step in the pipeline
         preprocessor_step = loaded_pipeline.named_steps['preprocessor']
         # Access the transformer for the 'Area' column (assuming it's the first 'cat' transformer)
         # Note: The exact way to access this can depend on how the ColumnTransformer was defined.
         # This attempts to find the OneHotEncoder by looking at the 'transformers_' attribute.
         area_transformer = None
         for name, transformer, cols in preprocessor_step.transformers_:
              if 'cat' in name and isinstance(transformer, OneHotEncoder):
                   area_transformer = transformer
                   break
         if area_transformer and hasattr(area_transformer, 'categories_') and len(area_transformer.categories_) > 0:
             KNOWN_AREAS = area_transformer.categories_[0].tolist()
             print(f"Known areas extracted from ML model: {KNOWN_AREAS}")
         else:
             print("Warning: Could not automatically extract known areas from the model pipeline preprocessor.")
             KNOWN_AREAS = [] # Keep as empty list

    except Exception as e:
         print(f"Warning: An error occurred while trying to extract known areas from the model pipeline: {e}")
         KNOWN_AREAS = [] # Fallback


except FileNotFoundError as e:
    print(f"Error loading ML model: {e}")
    loaded_pipeline = None # Model not loaded
    KNOWN_AREAS = []
except Exception as e:
    print(f"An unexpected error occurred during model loading: {e}")
    loaded_pipeline = None
    KNOWN_AREAS = []

# --- Prediction Function ---

def predict_available_slots(area_name: str, target_datetime: datetime.datetime) -> float | None:
    """
    Predicts the number of available parking slots for a given area and future time.

    Args:
        area_name: The name of the parking area (e.g., "MG Road").
        target_datetime: The datetime object for the prediction time.

    Returns:
        The predicted number of available slots (float), or None if the model
        is not loaded or the area is unknown to the model.
    """
    if loaded_pipeline is None:
        print("ML model is not loaded. Cannot make prediction.")
        return None

    # Check if the area is known to the ML model before attempting prediction
    if KNOWN_AREAS and area_name not in KNOWN_AREAS:
        print(f"Prediction Error: Area '{area_name}' not found in known training areas of the ML model.")
        return None # Or return a specific error code/string

    try:
        # Extract features from the target_datetime
        # Feature order must match training order: ['Area', 'Hour', 'DayOfWeek', 'Month', 'EventNearby']
        hour = target_datetime.hour
        day_of_week = target_datetime.weekday() # Monday=0, Sunday=6
        month = target_datetime.month
        # EventNearby - Simplified for simulation. Assume 0 unless you have an external way to know.
        event_nearby = 0 # Default to 0 for prediction

        # Create a pandas DataFrame for the prediction input
        input_data = pd.DataFrame([[area_name, hour, day_of_week, month, event_nearby]],
                                  columns=['Area', 'Hour', 'DayOfWeek', 'Month', 'EventNearby'])

        # Make prediction using the loaded pipeline
        predicted_slots = loaded_pipeline.predict(input_data)[0]

        # Post-processing: Predictions might be float, round to nearest integer
        # Ensure they are non-negative.
        predicted_slots = max(0, round(predicted_slots))

        # Optional: Limit prediction to total capacity (This needs total capacity info
        # which isn't part of the model prediction itself. The caller (Flask app)
        # should apply this limit based on the lot's total capacity).
        # e.g., predicted_slots = min(predicted_slots, total_capacity_of_lot)

        return predicted_slots

    except Exception as e:
        print(f"An error occurred during ML prediction for area '{area_name}' at {target_datetime}: {e}")
        return None # Return None on prediction error


# --- Example Usage (for testing this service file directly) ---
if __name__ == "__main__":
    print("\nTesting parking_ml_service:")
    if loaded_pipeline:
        # Example prediction requests
        test_area = "MG Road"
        # Get current time and predict for a few hours from now
        future_time = datetime.datetime.now() + datetime.timedelta(hours=3)
        peak_hour_today = datetime.datetime.now().replace(hour=18, minute=0, second=0, microsecond=0) # Example peak hour

        print(f"Attempting prediction for {test_area} at {future_time.strftime('%Y-%m-%d %H:%M')}")
        pred_future = predict_available_slots(test_area, future_time)
        print(f"Result: {pred_future}")

        print(f"\nAttempting prediction for {test_area} at {peak_hour_today.strftime('%Y-%m-%d %H:%M')}")
        pred_peak = predict_available_slots(test_area, peak_hour_today)
        print(f"Result: {pred_peak}")

        # Test prediction for an area that might not be in the ML data
        test_unknown_area = "HSR Layout"
        print(f"\nAttempting prediction for unknown area '{test_unknown_area}'")
        pred_unknown = predict_available_slots(test_unknown_area, future_time)
        print(f"Result: {pred_unknown}") # Should return None and print warning
    else:
        print("ML model not loaded, cannot run prediction tests.")
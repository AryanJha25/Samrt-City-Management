from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import math
import qrcode
from qrcode.image.pil import PilImage
import os
import time
import uuid
import datetime # Use datetime for better time handling

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Data Definition ---

# Predefined areas (simulating potential destinations) with Lat/Lon coordinates
AREAS = [
    {"name": "MG Road", "lat": 12.9750, "lon": 77.6060, "id": "area_mgroad"},
    {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "id": "area_koramangala"},
    {"name": "Indiranagar", "lat": 12.9716, "lon": 77.6412, "id": "area_indiranagar"},
    {"name": "Whitefield", "lat": 12.9698, "lon": 77.7499, "id": "area_whitefield"},
    {"name": "Electronic City", "lat": 12.8398, "lon": 77.6799, "id": "area_electronic"},
    {"name": "Jayanagar", "lat": 12.9250, "lon": 77.5938, "id": "area_jayanagar"},
    {"name": "Malleshwaram", "lat": 13.0099, "lon": 77.5690, "id": "area_malleshwaram"},
    {"name": "Hebbal", "lat": 13.0358, "lon": 77.5912, "id": "area_hebbal"},
]

# Predefined parking lots with details (Initial State)
# Added 'total_capacity' to distinguish from mutable 'available_slots'
PARKING_LOTS_INITIAL_DATA = [
    {"id": "P1", "name": "MG Road Metro Parking", "lat": 12.9751, "lon": 77.6063, "hourly_rate": 30.00, "total_capacity": 50},
    {"id": "P2", "name": "Garuda Mall Parking", "lat": 12.9714, "lon": 77.6081, "hourly_rate": 40.00, "total_capacity": 120},
    {"id": "P3", "name": "Forum Mall Parking", "lat": 12.9346, "lon": 77.6101, "hourly_rate": 35.00, "total_capacity": 150},
    {"id": "P4", "name": "Phoenix Marketcity Parking", "lat": 12.9955, "lon": 77.6975, "hourly_rate": 50.00, "total_capacity": 200},
    {"id": "P5", "name": "Mantri Square Mall Parking", "lat": 13.0076, "lon": 77.5695, "hourly_rate": 40.00, "total_capacity": 180},
    {"id": "P6", "name": "Indiranagar 100ft Road Lot", "lat": 12.9711, "lon": 77.6418, "hourly_rate": 25.00, "total_capacity": 60},
    {"id": "P7", "name": "Jayanagar 4th Block Parking", "lat": 12.9257, "lon": 77.5836, "hourly_rate": 20.00, "total_capacity": 70},
    {"id": "P8", "name": "Hebbal Flyover Parking", "lat": 13.0364, "lon": 77.5915, "hourly_rate": 15.00, "total_capacity": 30},
    {"id": "P9", "name": "Electronic City Phase 1 Parking", "lat": 12.8414, "lon": 77.6792, "hourly_rate": 18.00, "total_capacity": 90},
    {"id": "P10", "name": "Orion Mall Parking", "lat": 13.0098, "lon": 77.5547, "hourly_rate": 45.00, "total_capacity": 220},
]


# Use a dictionary to hold the *mutable* real-time state of parking lots
# ** In-Memory State - Resets on server restart, NOT concurrent-safe **
# Initialize state from initial data, adding 'available_slots'
parking_lots_state = {}
for lot in PARKING_LOTS_INITIAL_DATA:
    lot_id = lot['id']
    # Copy all initial data and add mutable state fields
    parking_lots_state[lot_id] = dict(lot)
    parking_lots_state[lot_id]['available_slots'] = lot['total_capacity'] # Initially, available equals total

# --- Helper Functions ---

# Function to calculate distance between two points using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance # Distance in kilometers

# Function to get the current state of a parking lot
def get_parking_lot_state(lot_id):
    """Fetches the current availability and details from the mutable state."""
    return parking_lots_state.get(lot_id)

# Function to update the availability of a parking lot
def update_parking_lot_availability(lot_id, change):
    """Increments or decrements the available slots for a lot.
       Returns the new availability or None if lot not found."""
    lot = parking_lots_state.get(lot_id)
    if lot:
        # Add basic locking simulation (doesn't make it truly thread-safe in Flask's default setup)
        # A real solution needs a proper lock or database transaction
        # In a real system, this is where a database update would happen atomically
        lot['available_slots'] += change
        # Ensure available slots don't go below zero or exceed total capacity
        lot['available_slots'] = max(0, lot['available_slots'])
        lot['available_slots'] = min(lot['available_slots'], lot['total_capacity']) # Prevent exceeding capacity on positive change
        print(f"[API State Update] Lot {lot['name']} ({lot_id}) availability changed by {change}. Current slots: {lot['available_slots']}.")
        return lot['available_slots']
    return None # Lot not found

# Simulate admin notification (prints to backend console)
def notify_admin_booking(booking_info):
    """Prints a simulated notification for the admin."""
    print("\n*** ADMIN NOTIFICATION ***")
    print("New Booking Received via API:")
    print(f"  Booking ID: {booking_info.get('booking_id', 'N/A')}")
    print(f"  User Phone: {booking_info.get('user_phone', 'N/A')}")
    print(f"  Parking Lot: {booking_info.get('lot_name', 'N/A')} ({booking_info.get('lot_id', 'N/A')})")
    print(f"  Destination: {booking_info.get('destination', 'N/A')}")
    print(f"  Booking Time: {booking_info.get('timestamp', 'N/A')}")
    print("**************************\n")

# Function to simulate releasing a slot (e.g., when booking expires or car exits)
def release_parking_slot(lot_id):
    """Simulates releasing a slot, incrementing availability."""
    update_parking_lot_availability(lot_id, 1)
    print(f"[API State Update] Slot released for Lot {lot_id}. Availability increased by 1.")
    # In a real system, this would be triggered by the Smart Parking System detecting an exit
    # or by a scheduled task for expired bookings.

# --- API Routes ---

@app.route('/areas', methods=['GET'])
def list_areas():
    """Returns the list of predefined destination areas."""
    # IDs were already added in the definition
    return jsonify(AREAS)

@app.route('/parking-lots/nearby', methods=['GET'])
def get_nearby_parking():
    """
    Finds nearby parking lots based on destination coordinates.
    Expects 'lat', 'lon' as query parameters.
    Optional 'max_distance_km' query parameter (default 2.0).
    """
    lat_str = request.args.get('lat')
    lon_str = request.args.get('lon')
    max_distance_km_str = request.args.get('max_distance_km', '2.0')

    if not lat_str or not lon_str:
        return jsonify({"error": "Missing 'lat' or 'lon' query parameter"}), 400

    try:
        dest_lat = float(lat_str)
        dest_lon = float(lon_str)
        max_distance_km = float(max_distance_km_str)
    except ValueError:
        return jsonify({"error": "Invalid value for 'lat', 'lon', or 'max_distance_km'"}), 400

    nearby_parking_options = []

    # Iterate through the *state* dictionary to get current availability
    for lot_id, lot_state in parking_lots_state.items():
        distance = haversine(dest_lat, dest_lon, lot_state['lat'], lot_state['lon'])
        if distance <= max_distance_km:
            nearby_parking_options.append({
                "id": lot_state['id'],
                "name": lot_state['name'],
                "distance_km": round(distance, 2), # Round distance for display
                "hourly_rate": lot_state['hourly_rate'],
                "available_slots": lot_state['available_slots'], # Use real-time availability
                "total_capacity": lot_state['total_capacity'] # Also show total capacity
            })

    # Sort by distance
    nearby_parking_options.sort(key=lambda x: x['distance_km'])

    return jsonify(nearby_parking_options)

@app.route('/parking-lots/<string:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    """
    Gets detailed information for a specific parking lot, including real-time availability.
    """
    lot_state = get_parking_lot_state(lot_id)

    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # lot_state already contains all relevant details including available_slots and total_capacity
    return jsonify(lot_state)


@app.route('/bookings', methods=['POST'])
def create_booking():
    """
    Handles a user's request to book a parking slot.
    Expects JSON body with 'lot_id', 'user_phone', and optional 'destination_id'.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    lot_id = data.get('lot_id')
    user_phone = data.get('user_phone')
    destination_id = data.get('destination_id')

    if not lot_id or not user_phone:
        return jsonify({"error": "Missing 'lot_id' or 'user_phone' in request body"}), 400

    # --- Simulate Booking Logic ---

    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # Check availability right before booking
    # ** This check + update needs to be atomic in a real concurrent system **
    if lot_state['available_slots'] < 1:
        # Use 409 Conflict status code as it's a resource conflict (slot unavailable)
        print(f"[API Booking Failure] Attempted booking for lot {lot_id}, but no slots available.")
        return jsonify({"error": f"No slots available at {lot_state['name']}"}), 409

    # Simulate decrementing slot availability (This is the critical state change)
    # In a real system, you'd typically create a booking record in the DB
    # *and* update the lot's availability within a transaction.
    update_parking_lot_availability(lot_id, -1)

    # --- Booking Successful ---

    booking_id = str(uuid.uuid4()) # Generate a unique booking ID
    # Use datetime for better handling of time
    booking_time = datetime.datetime.now()
    timestamp_str = booking_time.strftime("%Y-%m-%d %H:%M:%S")

    # Find destination name for notification if destination_id was provided
    destination_name = "Unknown Destination"
    if destination_id:
        destination = next((area for area in AREAS if area.get('id') == destination_id), None)
        if destination:
            destination_name = destination['name']

    # Prepare booking details for admin notification and QR code
    booking_info = {
        "booking_id": booking_id,
        "user_phone": user_phone,
        "lot_id": lot_id,
        "lot_name": lot_state['name'],
        "destination": destination_name,
        "timestamp": timestamp_str,
        # In a real system, you'd store this booking info in a database
        # And link it to the specific parking slot/space if slot mapping is implemented
    }

    # Notify Admin (prints to console)
    notify_admin_booking(booking_info)

    # --- Generate QR Code Data ---
    # We return the data string for the frontend to render the QR code
    qr_data = (
        f"Booking ID: {booking_id}\n"
        f"User Phone: {user_phone}\n"
        f"Parking Lot: {lot_state['name']} ({lot_id})\n"
        f"Destination: {destination_name}\n"
        f"Booking Time: {timestamp_str}\n"
        # Add more booking details here if needed (e.g., reserved duration, estimated cost)
    )

    # Optional: Still save the QR code image server-side for demonstration
    # Saving QR code data as image server-side can be useful for backend processing later (e.g., scanning on entry)
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

        qr_dir = "booking_qrcodes"
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)

        # Create a safe filename (replace non-alphanumeric)
        safe_lot_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in lot_state['name'])
        # Use a unique identifier from the booking ID for filename safety
        safe_booking_suffix = booking_id.split('-')[0] # Use part of the UUID
        qr_filename = f"{qr_dir}/booking_{safe_booking_suffix}_{safe_lot_name}.png"
        img.save(qr_filename)
        print(f"QR code image saved: {qr_filename}")

        # In a real app, you might store qr_filename or a public URL in the booking record in the DB

    except Exception as e:
        print(f"Error saving QR code image server-side: {e}")
        # Continue without saving the image, just return the data

    # Return success response to the frontend
    return jsonify({
        "message": "Booking successful!",
        "booking_id": booking_id,
        "lot_name": lot_state['name'],
        "user_phone": user_phone,
        "qr_code_data": qr_data # Return the data string for frontend QR generation
        # Optional: "qr_code_image_url": f"/qrcodes/{os.path.basename(qr_filename)}" if image saved and served
    }), 201 # 201 Created status code

# Optional: Simulate an endpoint for releasing a slot (e.g., from an admin tool or triggered by the smart parking system)
@app.route('/slots/release/<string:lot_id>', methods=['POST'])
def release_slot_api(lot_id):
    """
    API endpoint to simulate releasing a slot for a given parking lot.
    For demonstration purposes.
    """
    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # Increment the slot count
    new_availability = update_parking_lot_availability(lot_id, 1)

    return jsonify({
        "message": f"Slot released for lot {lot_id}.",
        "lot_id": lot_id,
        "new_availability": new_availability
    })


# Optional: Serve the saved QR code images (for demonstration)
# Note: In a production environment, serving files directly like this isn't ideal.
# You'd use a web server (Nginx, Apache) or a cloud storage service.
@app.route('/qrcodes/<filename>')
def serve_qr_code(filename):
    qr_dir = "booking_qrcodes"
    try:
        return send_from_directory(qr_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "QR code not found"}), 404


# --- Run the Flask App ---
if __name__ == '__main__':
    # When running with `flask run` or `python app.py`, debug=True is okay for development.
    # For production, use a production-ready WSGI server like Gunicorn or uWSGI.
    print("Flask App Started.")
    print("Initial Parking Lot State:")
    for lot_id, state in parking_lots_state.items():
        print(f"  {state['name']} ({lot_id}): {state['available_slots']}/{state['total_capacity']} slots available")

    # host='0.0.0.0' makes the server accessible from outside localhost
    app.run(debug=True, host='0.0.0.0', port=5000)
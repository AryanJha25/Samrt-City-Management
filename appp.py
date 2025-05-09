from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import math
import qrcode
from qrcode.image.pil import PilImage
import os
import time
import uuid
import datetime
import threading # Needed for simulated concurrent access (still not truly safe without proper DB)

app = Flask(__name__)
CORS(app)

# --- Data Definition ---

# Predefined areas (simulating potential destinations) with Lat/Lon coordinates
AREAS = [
    {"name": "City Center Plaza", "lat": 34.0522, "lon": -118.2437, "id": "area_plaza"},
    {"name": "Exhibition Hall XYZ", "lat": 34.0350, "lon": -118.2650, "id": "area_xyz"},
    {"name": "Tech Innovation Hub", "lat": 34.0500, "lon": -118.2000, "id": "area_tech"},
    {"name": "Arts District Gallery", "lat": 34.0489, "lon": -118.2353, "id": "area_arts"},
]

# Predefined parking lots with details (Initial State)
PARKING_LOTS_INITIAL_DATA = [
    {"id": "P1", "name": "Downtown Garage", "lat": 34.0450, "lon": -118.2500, "hourly_rate": 5.00, "total_capacity": 2}, # Reduced for testing
    {"id": "P2", "name": "Near Museum Lot", "lat": 34.0400, "lon": -118.2600, "hourly_rate": 4.50, "total_capacity": 1}, # Reduced for testing
    {"id": "P3", "name": "Convention Center Parking", "lat": 34.0380, "lon": -118.2680, "hourly_rate": 6.00, "total_capacity": 5},
    {"id": "P4", "name": "Financial District Parking", "lat": 34.0550, "lon": -118.2400, "hourly_rate": 7.00, "total_capacity": 30},
    {"id": "P5", "name": "Arts Quarter Lot", "lat": 34.0480, "lon": -118.2380, "hourly_rate": 5.50, "total_capacity": 25},
    {"id": "P6", "name": "Midtown Parking", "lat": 34.0580, "lon": -118.2480, "hourly_rate": 4.00, "total_capacity": 80},
    {"id": "P7", "name": "Stadium Parking", "lat": 34.0120, "lon": -118.2870, "hourly_rate": 8.00, "total_capacity": 200}, # Further away
    {"id": "P8", "name": "Exhibit Annexe Parking", "lat": 34.0360, "lon": -118.2670, "hourly_rate": 5.80, "total_capacity": 4},
    {"id": "P9", "name": "Central Library Parking", "lat": 34.0505, "lon": -118.2540, "hourly_rate": 6.50, "total_capacity": 60},
    {"id": "P10", "name": "XYZ Backlot", "lat": 34.0345, "lon": -118.2645, "hourly_rate": 5.20, "total_capacity": 3}, # Reduced for testing
]

# Use a dictionary to hold the *mutable* real-time state of parking lots
# ** In-Memory State - Resets on server restart, NOT concurrent-safe without a DB **
parking_lots_state = {}
for lot in PARKING_LOTS_INITIAL_DATA:
    lot_id = lot['id']
    parking_lots_state[lot_id] = dict(lot)
    parking_lots_state[lot_id]['available_slots'] = lot['total_capacity']

# In-memory storage for recent booking notifications (for admin panel)
# ** Resets on server restart **
recent_bookings = []
MAX_BOOKING_NOTIFICATIONS = 50 # Limit the list size

# Basic in-memory admin user for demo
ADMIN_USER = {"username": "admin", "password": "password123"} # ** DO NOT USE IN PRODUCTION **

# Basic lock for simulating atomic updates to parking_lots_state and recent_bookings
# Still not a replacement for a proper database transaction in a real multi-threaded/multi-process server
state_lock = threading.Lock()


# --- Helper Functions ---

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def get_parking_lot_state(lot_id):
    with state_lock: # Acquire lock before accessing shared state
        return parking_lots_state.get(lot_id)

def update_parking_lot_availability(lot_id, change):
    with state_lock: # Acquire lock before modifying shared state
        lot = parking_lots_state.get(lot_id)
        if lot:
            lot['available_slots'] += change
            lot['available_slots'] = max(0, lot['available_slots'])
            lot['available_slots'] = min(lot['available_slots'], lot['total_capacity'])
            print(f"[API State Update] Lot {lot['name']} ({lot_id}) availability changed by {change}. Current slots: {lot['available_slots']}.")
            return lot['available_slots']
        return None

def notify_admin_booking(booking_info):
    """Prints to console and adds to in-memory list."""
    print("\n*** ADMIN NOTIFICATION ***")
    print("New Booking Received via API:")
    print(f"  Booking ID: {booking_info.get('booking_id', 'N/A')}")
    print(f"  User Phone: {booking_info.get('user_phone', 'N/A')}")
    print(f"  Parking Lot: {booking_info.get('lot_name', 'N/A')} ({booking_info.get('lot_id', 'N/A')})")
    print(f"  Destination: {booking_info.get('destination', 'N/A')}")
    print(f"  Booking Time: {booking_info.get('timestamp', 'N/A')}")
    print("**************************\n")

    with state_lock: # Acquire lock before modifying shared list
        recent_bookings.append(booking_info)
        # Keep the list size limited
        if len(recent_bookings) > MAX_BOOKING_NOTIFICATIONS:
            recent_bookings.pop(0) # Remove the oldest

def release_parking_slot(lot_id):
    """Simulates releasing a slot."""
    update_parking_lot_availability(lot_id, 1)
    print(f"[API State Update] Slot released for Lot {lot_id}. Availability increased by 1.")

# --- API Routes: User Facing ---

@app.route('/areas', methods=['GET'])
def list_areas():
    """Returns the list of predefined destination areas."""
    return jsonify(AREAS)

@app.route('/parking-lots/nearby', methods=['GET'])
def get_nearby_parking():
    """
    Finds nearby parking lots based on destination coordinates.
    Expects 'lat', 'lon' as query parameters.
    Optional 'max_distance_km' query parameter (default 2.0).
    Returns summary including real-time availability, distance, rate.
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

    # Iterate through the *state* dictionary to get current availability & location
    with state_lock: # Acquire lock for consistent read of parking_lots_state
        all_lots_state = list(parking_lots_state.values()) # Get a copy of values

    for lot_state in all_lots_state:
        distance = haversine(dest_lat, dest_lon, lot_state['lat'], lot_state['lon'])
        if distance <= max_distance_km:
            nearby_parking_options.append({
                "id": lot_state['id'],
                "name": lot_state['name'],
                "lat": lot_state['lat'], # Include lat/lon for map on frontend
                "lon": lot_state['lon'],
                "distance_km": round(distance, 2),
                "hourly_rate": lot_state['hourly_rate'],
                "available_slots": lot_state['available_slots'],
                "total_capacity": lot_state['total_capacity']
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

    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        print(f"[API Booking Failure] Lot ID '{lot_id}' not found.")
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # Acquire lock for atomic check and update
    with state_lock:
        # Re-check availability inside the lock
        if parking_lots_state[lot_id]['available_slots'] < 1:
            print(f"[API Booking Failure] Attempted booking for lot {lot_id}, but no slots available.")
            return jsonify({"error": f"No slots available at {lot_state['name']}"}), 409

        # Decrement slot count
        update_parking_lot_availability(lot_id, -1)

        # --- Booking Successful ---
        booking_id = str(uuid.uuid4())
        booking_time = datetime.datetime.now()
        timestamp_str = booking_time.strftime("%Y-%m-%d %H:%M:%S")

        destination_name = "Unknown Destination"
        if destination_id:
            destination = next((area for area in AREAS if area.get('id') == destination_id), None)
            if destination:
                destination_name = destination['name']

        booking_info = {
            "booking_id": booking_id,
            "user_phone": user_phone,
            "lot_id": lot_id,
            "lot_name": lot_state['name'],
            "destination": destination_name,
            "timestamp": timestamp_str,
            # Add status, duration, etc. in a real app
        }

        # Notify Admin (console print and add to in-memory list) - done inside lock for consistency
        notify_admin_booking(booking_info)

    # Release the lock before potentially time-consuming QR code generation/saving
    # --- Generate QR Code Data ---
    qr_data = (
        f"Booking ID: {booking_id}\n"
        f"User Phone: {user_phone}\n"
        f"Parking Lot: {lot_state['name']} ({lot_id})\n" # Use lot_state from before lock
        f"Destination: {destination_name}\n"
        f"Booking Time: {timestamp_str}\n"
    )

    # Optional: Still save the QR code image server-side
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
        qr_dir = "booking_qrcodes"
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
        safe_lot_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in lot_state['name'])
        safe_booking_suffix = booking_id.split('-')[0]
        qr_filename = f"{qr_dir}/booking_{safe_booking_suffix}_{safe_lot_name}.png"
        img.save(qr_filename)
        print(f"QR code image saved: {qr_filename}")
    except Exception as e:
        print(f"Error saving QR code image server-side: {e}")

    return jsonify({
        "message": "Booking successful!",
        "booking_id": booking_id,
        "lot_name": lot_state['name'],
        "user_phone": user_phone,
        "qr_code_data": qr_data
    }), 201

# Optional: Serve QR codes
@app.route('/qrcodes/<filename>')
def serve_qr_code(filename):
    qr_dir = "booking_qrcodes"
    try:
        return send_from_directory(qr_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "QR code not found"}), 404

# --- API Routes: Admin Facing ---

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """
    Basic demo admin login. Checks hardcoded username/password.
    ** NOT SECURE FOR PRODUCTION **
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    username = data.get("username")
    password = data.get("password")

    if username == ADMIN_USER["username"] and password == ADMIN_USER["password"]:
        print(f"[Admin Login] Successful login for user: {username}")
        # In a real app, return a JWT or session token here
        return jsonify({"message": "Login successful", "success": True})
    else:
        print(f"[Admin Login] Failed login attempt for user: {username}")
        return jsonify({"error": "Invalid credentials", "success": False}), 401

@app.route('/parking-lots/all', methods=['GET'])
def get_all_parking_lots():
    """
    Returns details and real-time availability for ALL parking lots.
    Used for the admin dashboard.
    """
    with state_lock: # Acquire lock for consistent read
        # Return a copy of the state values as a list
        all_lots_data = list(parking_lots_state.values())
        # Ensure necessary keys are present for frontend display
        formatted_data = []
        for lot in all_lots_data:
            formatted_data.append({
                 "id": lot['id'],
                 "name": lot['name'],
                 "lat": lot['lat'],
                 "lon": lot['lon'],
                 "hourly_rate": lot['hourly_rate'],
                 "available_slots": lot['available_slots'],
                 "total_capacity": lot['total_capacity'],
                 # Add other static details if available/needed for admin view (address etc.)
            })
    return jsonify(formatted_data)

@app.route('/admin/notifications', methods=['GET'])
def get_recent_notifications():
    """
    Returns the list of recent booking notifications.
    Used for the admin dashboard notification feed.
    """
    with state_lock: # Acquire lock for consistent read
        # Return a copy of the recent_bookings list, reversed to show newest first
        # Filter out sensitive info if necessary, though for this demo it's fine
        return jsonify(list(reversed(recent_bookings))) # Return newest first

@app.route('/slots/release/<string:lot_id>', methods=['POST'])
def release_slot_api(lot_id):
    """
    API endpoint to simulate releasing a slot for a given parking lot.
    Could be triggered manually from admin or by system events.
    """
    # In a real admin route, you'd add authentication/authorization checks here
    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    if lot_state['available_slots'] >= lot_state['total_capacity']:
         return jsonify({"message": f"Lot {lot_id} is already at full capacity or more slots than total are available."}), 400

    # Increment the slot count
    new_availability = update_parking_lot_availability(lot_id, 1)

    return jsonify({
        "message": f"Slot released for lot {lot_id}.",
        "lot_id": lot_id,
        "new_availability": new_availability
    })


# --- Run the Flask App ---
if __name__ == '__main__':
    print("Flask App Started.")
    print("Initial Parking Lot State:")
    with state_lock: # Acquire lock for initial print
        for lot_id, state in parking_lots_state.items():
            print(f"  {state['name']} ({lot_id}): {state['available_slots']}/{state['total_capacity']} slots available")

    # Debug=True should be False in production
    # host='0.0.0.0' allows access from other machines on the network
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import math
import qrcode
from qrcode.image.pil import PilImage
import os
import time
import uuid
import datetime
import json # Added import
import random # Added import

app = Flask(__name__)
CORS(app)

# --- Data Definition ---

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

parking_lots_state = {}
for lot in PARKING_LOTS_INITIAL_DATA:
    lot_id = lot['id']
    parking_lots_state[lot_id] = dict(lot)
    parking_lots_state[lot_id]['available_slots'] = lot['total_capacity']


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
    return parking_lots_state.get(lot_id)

def update_parking_lot_availability(lot_id, change):
    lot = parking_lots_state.get(lot_id)
    if lot:
        lot['available_slots'] += change
        lot['available_slots'] = max(0, lot['available_slots'])
        lot['available_slots'] = min(lot['available_slots'], lot['total_capacity'])
        print(f"[API State Update] Lot {lot['name']} ({lot_id}) availability changed by {change}. Current slots: {lot['available_slots']}.")
        return lot['available_slots']
    return None

def notify_admin_booking(booking_info):
    print("\n*** ADMIN NOTIFICATION ***")
    print("New Booking Received via API:")
    print(f"  Booking ID: {booking_info.get('booking_id', 'N/A')}")
    print(f"  User Phone: {booking_info.get('user_phone', 'N/A')}")
    print(f"  Parking Lot: {booking_info.get('lot_name', 'N/A')} ({booking_info.get('lot_id', 'N/A')})")
    print(f"  Destination: {booking_info.get('destination', 'N/A')}")
    print(f"  Requested Time: {booking_info.get('booking_datetime_str', 'N/A')}")
    print(f"  Duration: {booking_info.get('duration_hours', 'N/A')} hours")
    print(f"  Booking Created At: {booking_info.get('timestamp_created', 'N/A')}")
    print("**************************\n")

def release_parking_slot(lot_id):
    update_parking_lot_availability(lot_id, 1)
    print(f"[API State Update] Slot released for Lot {lot_id}. Availability increased by 1.")


@app.route('/areas', methods=['GET'])
def list_areas():
    return jsonify(AREAS)

@app.route('/parking-lots/nearby', methods=['GET'])
def get_nearby_parking():
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
                "distance_km": round(distance, 2),
                "hourly_rate": lot_state['hourly_rate'],
                "available_slots": lot_state['available_slots'],
                "total_capacity": lot_state['total_capacity']
                # ** NOTE: Lat/Lon are needed by the frontend map component,
                # but not returned by this endpoint currently.
                # The frontend App.js uses a temporary hack for this.
                # Ideally, the backend would add lot_state['lat'], lot_state['lon'] here. **
            })

    nearby_parking_options.sort(key=lambda x: x['distance_km'])

    return jsonify(nearby_parking_options)

@app.route('/parking-lots/<string:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    lot_state = get_parking_lot_state(lot_id)

    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # Return the full state dictionary (includes lat/lon, capacity, availability, rate)
    return jsonify(lot_state)


@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    lot_id = data.get('lot_id')
    user_phone = data.get('user_phone')
    destination_id = data.get('destination_id')
    # --- NEW INPUTS ---
    booking_date_str = data.get('booking_date')
    booking_time_str = data.get('booking_time')
    duration_hours = data.get('duration_hours')
    # --- END NEW INPUTS ---


    if not lot_id or not user_phone or not booking_date_str or not booking_time_str or duration_hours is None:
        missing_fields = []
        if not lot_id: missing_fields.append('lot_id')
        if not user_phone: missing_fields.append('user_phone')
        if not booking_date_str: missing_fields.append('booking_date')
        if not booking_time_str: missing_fields.append('booking_time')
        if duration_hours is None: missing_fields.append('duration_hours') # Check specifically for None, as 0 duration might be valid depending on rules
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        duration_hours = float(duration_hours)
        if duration_hours <= 0:
             return jsonify({"error": "Duration must be a positive number"}), 400

        # Validate date and time format and check if it's in the past
        booking_datetime_str = f"{booking_date_str} {booking_time_str}"
        booking_datetime_obj = datetime.datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
        if booking_datetime_obj < datetime.datetime.now():
             # For a simulation, we might allow booking slightly in the past, but
             # for robustness, disallowing is better.
             # In a real app, check against a small buffer to account for clock drift.
             return jsonify({"error": "Booking time cannot be in the past"}), 400

    except ValueError as e:
        return jsonify({"error": f"Invalid date, time, or duration format/value: {e}"}), 400


    # --- Simulate Booking Logic ---

    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    # ** IMPORTANT SIMULATION LIMITATION **
    # The check below and the slot decrement operate on *current* real-time availability.
    # This doesn't accurately reflect availability for a *future* time slot (`booking_datetime_obj`).
    # A real system needs ML prediction for future demand + a database to manage future reservations.
    if lot_state['available_slots'] < 1:
        print(f"[API Booking Failure] Attempted booking for lot {lot_id}, no slots available (based on current state).")
        # Use 409 Conflict for availability issues
        return jsonify({"error": f"No slots available at {lot_state['name']} for immediate booking (simulation limitation)"}), 409

    # Simulate decrementing slot availability (This is the critical state change in this simulation)
    # In a real system, you would instead reserve a slot for the specific time window
    # and this wouldn't necessarily affect the *current* available_slots for walk-ins,
    # but would affect the calculated *predicted* availability for that future time.
    update_parking_lot_availability(lot_id, -1)

    # --- Booking Successful (Simulated) ---

    booking_id = str(uuid.uuid4()) # Generate a unique booking ID
    timestamp_created_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Time when the booking was created

    # Find destination name for notification
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
        "timestamp_created": timestamp_created_str, # Time the booking was created
        "booking_datetime_str": booking_datetime_str, # Requested booking time
        "duration_hours": duration_hours,          # Requested duration
        # In a real system, you'd store this booking info in a database, including the start/end time
    }

    # Notify Admin (prints to console)
    notify_admin_booking(booking_info)

    # --- Generate QR Code Data ---
    qr_data = (
        f"Booking ID: {booking_id}\n"
        f"User Phone: {user_phone}\n"
        f"Parking Lot: {lot_state['name']} ({lot_id})\n"
        f"Destination: {destination_name}\n"
        f"Booked For: {booking_datetime_str}\n" # Include requested time
        f"Duration: {duration_hours} hours\n"   # Include duration
        f"Booking Created: {timestamp_created_str}" # Include creation time
    )

    # Optional: Still save the QR code image server-side for demonstration
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

    # Return success response to the frontend - include the new details
    return jsonify({
        "message": "Booking successful!",
        "booking_id": booking_id,
        "lot_name": lot_state['name'],
        "user_phone": user_phone,
        "qr_code_data": qr_data,
        "booking_date": booking_date_str,   # Return for frontend confirmation display
        "booking_time": booking_time_str,   # Return for frontend confirmation display
        "duration_hours": duration_hours    # Return for frontend confirmation display
    }), 201


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

@app.route('/qrcodes/<filename>')
def serve_qr_code(filename):
    qr_dir = "booking_qrcodes"
    try:
        return send_from_directory(qr_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "QR code not found"}), 404
    

# --- Simulated Safer Route Data (EXPANDED) ---
# Nodes (key points, trying to cover the AREA locations)
ROUTE_NODES = {
    "node_mgroad": {"lat": 12.9750, "lon": 77.6060, "name": "MG Road"},
    "node_koramangala": {"lat": 12.9352, "lon": 77.6245, "name": "Koramangala"},
    "node_indiranagar": {"lat": 12.9716, "lon": 77.6412, "name": "Indiranagar"},
    "node_whitefield": {"lat": 12.9698, "lon": 77.7499, "name": "Whitefield"},
    "node_ecity": {"lat": 12.8398, "lon": 77.6799, "name": "Electronic City"},
    "node_jayanagar": {"lat": 12.9250, "lon": 77.5938, "name": "Jayanagar"},
    "node_malleshwaram": {"lat": 13.0099, "lon": 77.5690, "name": "Malleshwaram"},
    "node_hebbal": {"lat": 13.0358, "lon": 77.5912, "name": "Hebbal"},
    # Intermediate/Junction Nodes for more complex paths
    "node_intermediate_south": {"lat": 12.88, "lon": 77.65, "name": "Intermediate South"},
    "node_intermediate_east": {"lat": 12.97, "lon": 77.67, "name": "Intermediate East"},
    "node_intermediate_central": {"lat": 12.95, "lon": 77.62, "name": "Intermediate Central"},
}

# Destination Areas (For simplicity, map closely to some ROUTE_NODES)
# In a real app, these would be polygons or specific points users select
AREAS = [
    {"id": "area_mgroad", "name": "MG Road Area", "lat": ROUTE_NODES["node_mgroad"]["lat"], "lon": ROUTE_NODES["node_mgroad"]["lon"]},
    {"id": "area_koramangala", "name": "Koramangala Area", "lat": ROUTE_NODES["node_koramangala"]["lat"], "lon": ROUTE_NODES["node_koramangala"]["lon"]},
    {"id": "area_indiranagar", "name": "Indiranagar Area", "lat": ROUTE_NODES["node_indiranagar"]["lat"], "lon": ROUTE_NODES["node_indiranagar"]["lon"]},
    {"id": "area_whitefield", "name": "Whitefield Area", "lat": ROUTE_NODES["node_whitefield"]["lat"], "lon": ROUTE_NODES["node_whitefield"]["lon"]},
    {"id": "area_ecity", "name": "Electronic City Area", "lat": ROUTE_NODES["node_ecity"]["lat"], "lon": ROUTE_NODES["node_ecity"]["lon"]},
    {"id": "area_jayanagar", "name": "Jayanagar Area", "lat": ROUTE_NODES["node_jayanagar"]["lat"], "lon": ROUTE_NODES["node_jayanagar"]["lon"]},
    {"id": "area_malleshwaram", "name": "Malleshwaram Area", "lat": ROUTE_NODES["node_malleshwaram"]["lat"], "lon": ROUTE_NODES["node_malleshwaram"]["lon"]},
    {"id": "area_hebbal", "name": "Hebbal Area", "lat": ROUTE_NODES["node_hebbal"]["lat"], "lon": ROUTE_NODES["node_hebbal"]["lon"]},
]


# Predefined "safer routes" as a list of node IDs
# This is a simulation - ideally, you'd have a graph and an algorithm
# For simulation, these are fixed paths between specific pairs of ROUTE_NODES.
SIMULATED_SAFER_ROUTES = {
    # Example: From Koramangala to Whitefield (Option 1)
    "koramangala_to_whitefield_1": {
        "start_node": "node_koramangala",
        "end_node": "node_whitefield",
        "path_nodes": ["node_koramangala", "node_intermediate_east", "node_whitefield"],
        "safety_score": 0.85
    },
     # Example: From Jayanagar to MG Road (Option 1)
     "jayanagar_to_mgroad_1": {
        "start_node": "node_jayanagar",
        "end_node": "node_mgroad",
        "path_nodes": ["node_jayanagar", "node_malleshwaram", "node_mgroad"], # Example via Malleshwaram
        "safety_score": 0.9
     },
      # Example: From Jayanagar to MG Road (Option 2 - maybe slightly less direct but potentially safer)
     "jayanagar_to_mgroad_2": {
        "start_node": "node_jayanagar",
        "end_node": "node_mgroad",
        "path_nodes": ["node_jayanagar", "node_intermediate_central", "node_mgroad"], # Example via Central
        "safety_score": 0.92 # Assuming this route is slightly safer baselin
     },
     # Example: From Hebbal to E-City (Option 1)
     "hebbal_to_ecity_1": {
        "start_node": "node_hebbal",
        "end_node": "node_ecity",
        "path_nodes": ["node_hebbal", "node_mgroad", "node_intermediate_south", "node_ecity"], # Longer path example
        "safety_score": 0.7
     },
    # --- Add More Routes for Better Simulation Coverage ---
    "mgroad_to_indiranagar_1": {
        "start_node": "node_mgroad",
        "end_node": "node_indiranagar",
        "path_nodes": ["node_mgroad", "node_indiranagar"],
        "safety_score": 0.92 # Assumed high safety
    },
    "indiranagar_to_koramangala_1": {
        "start_node": "node_indiranagar",
        "end_node": "node_koramangala",
        "path_nodes": ["node_indiranagar", "node_intermediate_central", "node_koramangala"],
        "safety_score": 0.88
    },
     "whitefield_to_mgroad_1": {
        "start_node": "node_whitefield",
        "end_node": "node_mgroad",
        "path_nodes": ["node_whitefield", "node_intermediate_east", "node_mgroad"], # Reverse of first example
        "safety_score": 0.83 # Slightly different score
     },
     # Add routes between more nodes as needed to increase match possibilities
     # Example: Jayanagar to Electronic City (via intermediate south)
     "jayanagar_to_ecity_1": {
        "start_node": "node_jayanagar",
        "end_node": "node_ecity",
        "path_nodes": ["node_jayanagar", "node_intermediate_south", "node_ecity"],
        "safety_score": 0.75
     },
     # Example: Malleshwaram to Hebbal
     "malleshwaram_to_hebbal_1": {
        "start_node": "node_malleshwaram",
        "end_node": "node_hebbal",
        "path_nodes": ["node_malleshwaram", "node_hebbal"],
        "safety_score": 0.80
     },
}


# --- Helper Functions ---

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees) using the Haversine formula.
    """
    R = 6371  # Radius of earth in kilometers

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

def find_closest_node(lat, lon):
    """Finds the ID of the ROUTE_NODE closest to the given lat/lon."""
    closest_node_id = None
    min_distance = float('inf')

    for node_id, node_coord in ROUTE_NODES.items():
        distance = haversine(lat, lon, node_coord['lat'], node_coord['lon'])
        if distance < min_distance:
            min_distance = distance
            closest_node_id = node_id

    return closest_node_id, min_distance

def get_route_coordinates(path_node_ids):
    """Converts a list of node IDs into a list of lat/lon dictionaries."""
    coordinates = []
    for node_id in path_node_ids:
        node_coord = ROUTE_NODES.get(node_id)
        if node_coord:
            coordinates.append({"lat": node_coord["lat"], "lon": node_coord["lon"]})
        else:
            print(f"Warning: Node ID '{node_id}' in predefined route not found in ROUTE_NODES.")
            # Decide how to handle this - here, we skip the invalid node
            continue
    return coordinates

def get_node_names_for_path(path_node_ids):
     """Converts a list of node IDs into a list of node names."""
     names = []
     for node_id in path_node_ids:
         node_info = ROUTE_NODES.get(node_id)
         if node_info and 'name' in node_info:
             names.append(node_info['name'])
         else:
             # Fallback to node ID if name is missing
             names.append(node_id)
     return names

def calculate_adjusted_safety_score(base_score, query_datetime_obj):
    """
    Adjusts the base safety score based on the time of day.
    Example: Lower score during late night/early morning.
    """
    hour = query_datetime_obj.hour
    adjusted_score = base_score

    # Simple adjustment: Reduce score during "risky" hours (e.g., 8 PM to 5 AM)
    if hour >= 20 or hour <= 5: # 8 PM to 5 AM
        adjusted_score *= 0.7 # Reduce by 30%
        adjusted_score = max(0.1, adjusted_score) # Don't let it drop too low

    # You could add more complex logic here based on day of week, etc.

    return adjusted_score


# --- API Routes ---

@app.route('/safe-routes', methods=['GET'])
def find_safer_route():
    """
    Finds the simulated safest route among available predefined routes
    between locations near a start coordinate and a destination area.
    Expects 'start_lat', 'start_lon', 'dest_area_id', 'query_datetime' as query parameters.
    """
    start_lat_str = request.args.get('start_lat')
    start_lon_str = request.args.get('start_lon')
    dest_area_id = request.args.get('dest_area_id')
    query_datetime_str = request.args.get('query_datetime') # Expected format: ISO 8601 e.g., '2023-10-27T10:00:00'

    if not start_lat_str or not start_lon_str or not dest_area_id or not query_datetime_str:
         missing = []
         if not start_lat_str: missing.append('start_lat')
         if not start_lon_str: missing.append('start_lon')
         if not dest_area_id: missing.append('dest_area_id')
         if not query_datetime_str: missing.append('query_datetime')
         return jsonify({"error": f"Missing required query parameters: {', '.join(missing)}"}), 400

    try:
        start_lat = float(start_lat_str)
        start_lon = float(start_lon_str)
        # Use fromisoformat which is standard for ISO 8601
        query_datetime_obj = datetime.datetime.fromisoformat(query_datetime_str)
    except ValueError as e:
        return jsonify({"error": f"Invalid format for coordinates or query_datetime. query_datetime should be ISO 8601 (e.g., '2023-10-27T10:00:00'). Error: {e}"}), 400

    # 1. Find the destination area coordinates
    destination_area = next((area for area in AREAS if area.get('id') == dest_area_id), None)
    if not destination_area:
        return jsonify({"error": f"Destination area with ID '{dest_area_id}' not found"}), 404

    # 2. Find the ROUTE_NODE closest to the START coordinates
    closest_start_node_id, dist_to_start_node = find_closest_node(start_lat, start_lon)
    print(f"[API Route Finding] Start coords ({start_lat:.4f}, {start_lon:.4f}) closest node is {closest_start_node_id} ({dist_to_start_node:.2f} km away).")

    # 3. Find the ROUTE_NODE closest to the DESTINATION AREA coordinates
    closest_dest_node_id, dist_to_dest_node = find_closest_node(destination_area['lat'], destination_area['lon'])
    print(f"[API Route Finding] Dest area {dest_area_id} coords closest node is {closest_dest_node_id} ({dist_to_dest_node:.2f} km away).")

    # --- Simulated Route Finding Logic: Find best route between closest nodes ---
    potential_routes = []

    # Find all predefined routes that go from the closest start node to the closest dest node
    for route_key, route_data in SIMULATED_SAFER_ROUTES.items():
        if route_data["start_node"] == closest_start_node_id and route_data["end_node"] == closest_dest_node_id:
             # Calculate time-adjusted safety score for this potential route
             adjusted_score = calculate_adjusted_safety_score(route_data["safety_score"], query_datetime_obj)
             potential_routes.append({
                 "route_key": route_key,
                 "route_data": route_data,
                 "adjusted_safety_score": adjusted_score
             })
             print(f"  - Found potential route '{route_key}' (base score {route_data['safety_score']:.2f}, adjusted {adjusted_score:.2f})")


    if not potential_routes:
        print(f"[API Route Finding] No predefined simulated route found from {closest_start_node_id} to {closest_dest_node_id}.")
        return jsonify({"error": f"No simulated safer route found between locations near '{ROUTE_NODES.get(closest_start_node_id, {}).get('name', closest_start_node_id)}' and '{destination_area['name']}' for the specified time. Please try different start/end points or times."}), 404

    # Find the route with the highest adjusted safety score
    best_route = max(potential_routes, key=lambda x: x["adjusted_safety_score"])
    best_route_data = best_route["route_data"]
    best_route_score = best_route["adjusted_safety_score"]

    route_coords = get_route_coordinates(best_route_data["path_nodes"])
    route_node_names = get_node_names_for_path(best_route_data["path_nodes"])

    print(f"[API Route Finding] Selected best route '{best_route['route_key']}' with adjusted score {best_route_score:.2f}")


    # Prepare output to guide the user
    guidance_steps = []
    for i, node_id in enumerate(best_route_data["path_nodes"]):
        node_info = ROUTE_NODES.get(node_id, {})
        step_description = f"Step {i+1}: Proceed to {node_info.get('name', node_id)}"
        if i < len(best_route_data["path_nodes"]) - 1:
            next_node_info = ROUTE_NODES.get(best_route_data["path_nodes"][i+1], {})
            step_description += f" towards {next_node_info.get('name', best_route_data['path_nodes'][i+1])}"
        guidance_steps.append(step_description)

    # For a front-end, you'd also provide the coordinates to draw on a map.
    # The route_coords list is for drawing the polyline.
    # You might also want to return the start/end lat/lon inputs for markers.

    return jsonify({
        "message": f"Safest simulated route found for your trip from near '{ROUTE_NODES.get(closest_start_node_id, {}).get('name', closest_start_node_id)}' to '{destination_area['name']}'.",
        "start_location_input": {"lat": start_lat, "lon": start_lon}, # User's input start coords
        "destination_area_input": {"id": dest_area_id, "name": destination_area['name']}, # User's input dest area
        "start_node_used": {"id": closest_start_node_id, "name": ROUTE_NODES.get(closest_start_node_id, {}).get('name', closest_start_node_id)}, # Closest node to start
        "end_node_used": {"id": closest_dest_node_id, "name": ROUTE_NODES.get(closest_dest_node_id, {}).get('name', closest_dest_node_id)},     # Closest node to end
        "route": {
            "path_node_ids": best_route_data["path_nodes"], # Node IDs in sequence
            "path_node_names": route_node_names,          # Names of nodes in sequence
            "path_coordinates": route_coords,             # List of {lat, lon} for drawing on map
            "simulated_safety_score": round(best_route_score, 2), # Calculated score for this route & time
            "guidance_steps": guidance_steps              # Textual steps for guidance
        }
    })


# --- API Route for Unsafe Notification ---
@app.route('/notify-unsafe', methods=['POST'])
def notify_unsafe():
    """
    Receives a notification that a user feels unsafe at their current location.
    Logs the location and time (simulating admin notification).
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    user_lat = data.get('user_lat')
    user_lon = data.get('user_lon')
    user_identifier = data.get('user_identifier', 'Anonymous') # Optional identifier

    if user_lat is None or user_lon is None:
         return jsonify({"error": "Missing 'user_lat' or 'user_lon' in request body"}), 400

    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except ValueError:
        return jsonify({"error": "Invalid value for 'user_lat' or 'user_lon'"}), 400

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # In a real application, this would send an email, SMS, push notification,
    # or log to a dedicated dashboard for administrators.
    # For this simulation, we just print to the console.
    print("\n!!! URGENT ADMIN ALERT !!!")
    print("User Reporting Unsafe Location:")
    print(f"  Identifier: {user_identifier}")
    print(f"  Location (Lat, Lon): ({user_lat}, {user_lon})")
    print(f"  Time of Alert: {timestamp}")
    print("!!! END ALERT !!!\n")

    return jsonify({"message": "Unsafe location reported to admin.", "timestamp": timestamp}), 200

# --- Keep existing parking routes (/areas, /parking-lots/nearby, etc.) below ---
# Assuming you have other routes for parking or other features.
# Example Placeholder:
# @app.route('/areas', methods=['GET'])
# def list_areas():
#     # Your logic to return list of areas/nodes users can select
#     pass

# Example Placeholder:
# @app.route('/parking-lots/nearby', methods=['GET'])
# def find_nearby_parking():
#     # Your logic for parking lots
#     pass

# Example Placeholder for parking lot state (if needed elsewhere)
# parking_lots_state = {
#     "lot_1": {"name": "Parking Lot A", "available_slots": 50, "total_capacity": 100},
#     # ... other lots
# }


# # --- Run the Flask App ---
# if __name__ == '__main__':
#     print("Flask App Started.")

#     print("\nSimulated Route Nodes:")
#     for node_id, coord in ROUTE_NODES.items():
#         print(f"  {node_id} ({coord.get('name', 'N/A')}): {coord['lat']}, {coord['lon']}")

#     print("\nSimulated Safer Routes:")
#     # Pretty print routes for inspection
#     print(json.dumps(SIMULATED_SAFER_ROUTES, indent=2))

# --- Run the Flask App ---
if __name__ == '__main__':
    print("Flask App Started.")
    print("Initial Parking Lot State:")
    for lot_id, state in parking_lots_state.items():
        print(f"  {state['name']} ({lot_id}): {state['available_slots']}/{state['total_capacity']} slots available")

    print("\nSimulated Route Nodes:")
    for node_id, coord in ROUTE_NODES.items():
        print(f"  {node_id} ({coord.get('name', 'N/A')}): {coord['lat']}, {coord['lon']}")

    print("\nSimulated Safer Routes:")
    # Pretty print routes for inspection
    print(json.dumps(SIMULATED_SAFER_ROUTES, indent=2))


    app.run(debug=True, host='0.0.0.0', port=5000)
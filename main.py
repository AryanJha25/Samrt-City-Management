# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# import math
# import qrcode
# from qrcode.image.pil import PilImage
# import os
# import time
# import uuid
# import datetime
# import json
# from flask import Flask, request, jsonify, send_from_directory

# app = Flask(__name__)
# CORS(app)

# # --- Data Definition ---

# AREAS = [
#     {"name": "MG Road", "lat": 12.9750, "lon": 77.6060, "id": "area_mgroad"},
#     {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "id": "area_koramangala"},
#     {"name": "Indiranagar", "lat": 12.9716, "lon": 77.6412, "id": "area_indiranagar"},
#     {"name": "Whitefield", "lat": 12.9698, "lon": 77.7499, "id": "area_whitefield"},
#     {"name": "Electronic City", "lat": 12.8398, "lon": 77.6799, "id": "area_electronic"},
#     {"name": "Jayanagar", "lat": 12.9250, "lon": 77.5938, "id": "area_jayanagar"},
#     {"name": "Malleshwaram", "lat": 13.0099, "lon": 77.5690, "id": "area_malleshwaram"},
#     {"name": "Hebbal", "lat": 13.0358, "lon": 77.5912, "id": "area_hebbal"},
# ]

# PARKING_LOTS_INITIAL_DATA = [
#     {"id": "P1", "name": "MG Road Metro Parking", "lat": 12.9751, "lon": 77.6063, "hourly_rate": 30.00, "total_capacity": 50},
#     {"id": "P2", "name": "Garuda Mall Parking", "lat": 12.9714, "lon": 77.6081, "hourly_rate": 40.00, "total_capacity": 120},
#     {"id": "P3", "name": "Forum Mall Parking", "lat": 12.9346, "lon": 77.6101, "hourly_rate": 35.00, "total_capacity": 150},
#     {"id": "P4", "name": "Phoenix Marketcity Parking", "lat": 12.9955, "lon": 77.6975, "hourly_rate": 50.00, "total_capacity": 200},
#     {"id": "P5", "name": "Mantri Square Mall Parking", "lat": 13.0076, "lon": 77.5695, "hourly_rate": 40.00, "total_capacity": 180},
#     {"id": "P6", "name": "Indiranagar 100ft Road Lot", "lat": 12.9711, "lon": 77.6418, "hourly_rate": 25.00, "total_capacity": 60},
#     {"id": "P7", "name": "Jayanagar 4th Block Parking", "lat": 12.9257, "lon": 77.5836, "hourly_rate": 20.00, "total_capacity": 70},
#     {"id": "P8", "name": "Hebbal Flyover Parking", "lat": 13.0364, "lon": 77.5915, "hourly_rate": 15.00, "total_capacity": 30},
#     {"id": "P9", "name": "Electronic City Phase 1 Parking", "lat": 12.8414, "lon": 77.6792, "hourly_rate": 18.00, "total_capacity": 90},
#     {"id": "P10", "name": "Orion Mall Parking", "lat": 13.0098, "lon": 77.5547, "hourly_rate": 45.00, "total_capacity": 220},
# ]


# # Use a dictionary to hold the *mutable* real-time state of parking lots
# # ** In-Memory State - Resets on server restart, NOT concurrent-safe **
# # Initialize state from initial data, adding 'available_slots'
# parking_lots_state = {}
# for lot in PARKING_LOTS_INITIAL_DATA:
#     lot_id = lot['id']
#     parking_lots_state[lot_id] = dict(lot)
#     parking_lots_state[lot_id]['available_slots'] = lot['total_capacity'] # Initially, available equals total

# # --- Helper Functions ---

# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371
#     lat1_rad = math.radians(lat1)
#     lon1_rad = math.radians(lon1)
#     lat2_rad = math.radians(lat2)
#     lon2_rad = math.radians(lon2)
#     dlon = lon2_rad - lon1_rad
#     dlat = lat2_rad - lat1_rad
#     a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     distance = R * c
#     return distance

# def get_parking_lot_state(lot_id):
#     return parking_lots_state.get(lot_id)

# def update_parking_lot_availability(lot_id, change):
#     lot = parking_lots_state.get(lot_id)
#     if lot:
#         # In a real system, this is where a database update would happen atomically
#         lot['available_slots'] += change
#         lot['available_slots'] = max(0, lot['available_slots'])
#         lot['available_slots'] = min(lot['available_slots'], lot['total_capacity'])
#         print(f"[API State Update] Lot {lot['name']} ({lot_id}) availability changed by {change}. Current slots: {lot['available_slots']}.")
#         return lot['available_slots']
#     return None

# def notify_admin_booking(booking_info):
#     print("\n*** ADMIN NOTIFICATION ***")
#     print("New Booking Received via API:")
#     print(f"  Booking ID: {booking_info.get('booking_id', 'N/A')}")
#     print(f"  User Phone: {booking_info.get('user_phone', 'N/A')}")
#     print(f"  Parking Lot: {booking_info.get('lot_name', 'N/A')} ({booking_info.get('lot_id', 'N/A')})")
#     print(f"  Destination: {booking_info.get('destination', 'N/A')}")
#     # --- NEW DETAILS IN ADMIN NOTIFICATION ---
#     print(f"  Requested Time: {booking_info.get('booking_datetime_str', 'N/A')}")
#     print(f"  Duration: {booking_info.get('duration_hours', 'N/A')} hours")
#     # --- END NEW DETAILS ---
#     print(f"  Booking Created At: {booking_info.get('timestamp_created', 'N/A')}") # distinguish from requested time
#     print("**************************\n")

# def release_parking_slot(lot_id):
#     update_parking_lot_availability(lot_id, 1)
#     print(f"[API State Update] Slot released for Lot {lot_id}. Availability increased by 1.")


# # --- API Routes ---

# @app.route('/areas', methods=['GET'])
# def list_areas():
#     return jsonify(AREAS)

# @app.route('/parking-lots/nearby', methods=['GET'])
# def get_nearby_parking():
#     lat_str = request.args.get('lat')
#     lon_str = request.args.get('lon')
#     max_distance_km_str = request.args.get('max_distance_km', '2.0')

#     if not lat_str or not lon_str:
#         return jsonify({"error": "Missing 'lat' or 'lon' query parameter"}), 400

#     try:
#         dest_lat = float(lat_str)
#         dest_lon = float(lon_str)
#         max_distance_km = float(max_distance_km_str)
#     except ValueError:
#         return jsonify({"error": "Invalid value for 'lat', 'lon', or 'max_distance_km'"}), 400

#     nearby_parking_options = []

#     # Iterate through the *state* dictionary to get current availability
#     for lot_id, lot_state in parking_lots_state.items():
#         distance = haversine(dest_lat, dest_lon, lot_state['lat'], lot_state['lon'])
#         if distance <= max_distance_km:
#             nearby_parking_options.append({
#                 "id": lot_state['id'],
#                 "name": lot_state['name'],
#                 "distance_km": round(distance, 2),
#                 "hourly_rate": lot_state['hourly_rate'],
#                 "available_slots": lot_state['available_slots'],
#                 "total_capacity": lot_state['total_capacity']
#                 # ** NOTE: Lat/Lon are needed by the frontend map component,
#                 # but not returned by this endpoint currently.
#                 # The frontend App.js uses a temporary hack for this.
#                 # Ideally, the backend would add lot_state['lat'], lot_state['lon'] here. **
#             })

#     nearby_parking_options.sort(key=lambda x: x['distance_km'])

#     return jsonify(nearby_parking_options)

# @app.route('/parking-lots/<string:lot_id>', methods=['GET'])
# def get_parking_lot(lot_id):
#     lot_state = get_parking_lot_state(lot_id)

#     if not lot_state:
#         return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

#     # Return the full state dictionary (includes lat/lon, capacity, availability, rate)
#     return jsonify(lot_state)


# @app.route('/bookings', methods=['POST'])
# def create_booking():
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Invalid JSON request body"}), 400

#     lot_id = data.get('lot_id')
#     user_phone = data.get('user_phone')
#     destination_id = data.get('destination_id')
#     # --- NEW INPUTS ---
#     booking_date_str = data.get('booking_date')
#     booking_time_str = data.get('booking_time')
#     duration_hours = data.get('duration_hours')
#     # --- END NEW INPUTS ---


#     if not lot_id or not user_phone or not booking_date_str or not booking_time_str or duration_hours is None:
#         missing_fields = []
#         if not lot_id: missing_fields.append('lot_id')
#         if not user_phone: missing_fields.append('user_phone')
#         if not booking_date_str: missing_fields.append('booking_date')
#         if not booking_time_str: missing_fields.append('booking_time')
#         if duration_hours is None: missing_fields.append('duration_hours') # Check specifically for None, as 0 duration might be valid depending on rules
#         return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

#     try:
#         duration_hours = float(duration_hours)
#         if duration_hours <= 0:
#              return jsonify({"error": "Duration must be a positive number"}), 400

#         # Validate date and time format and check if it's in the past
#         booking_datetime_str = f"{booking_date_str} {booking_time_str}"
#         booking_datetime_obj = datetime.datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
#         if booking_datetime_obj < datetime.datetime.now():
#              # For a simulation, we might allow booking slightly in the past, but
#              # for robustness, disallowing is better.
#              # In a real app, check against a small buffer to account for clock drift.
#              return jsonify({"error": "Booking time cannot be in the past"}), 400

#     except ValueError as e:
#         return jsonify({"error": f"Invalid date, time, or duration format/value: {e}"}), 400


#     # --- Simulate Booking Logic ---

#     lot_state = get_parking_lot_state(lot_id)
#     if not lot_state:
#         return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

#     # ** IMPORTANT SIMULATION LIMITATION **
#     # The check below and the slot decrement operate on *current* real-time availability.
#     # This doesn't accurately reflect availability for a *future* time slot (`booking_datetime_obj`).
#     # A real system needs ML prediction for future demand + a database to manage future reservations.
#     if lot_state['available_slots'] < 1:
#         print(f"[API Booking Failure] Attempted booking for lot {lot_id}, no slots available (based on current state).")
#         # Use 409 Conflict for availability issues
#         return jsonify({"error": f"No slots available at {lot_state['name']} for immediate booking (simulation limitation)"}), 409

#     # Simulate decrementing slot availability (This is the critical state change in this simulation)
#     # In a real system, you would instead reserve a slot for the specific time window
#     # and this wouldn't necessarily affect the *current* available_slots for walk-ins,
#     # but would affect the calculated *predicted* availability for that future time.
#     update_parking_lot_availability(lot_id, -1)

#     # --- Booking Successful (Simulated) ---

#     booking_id = str(uuid.uuid4()) # Generate a unique booking ID
#     timestamp_created_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Time when the booking was created

#     # Find destination name for notification
#     destination_name = "Unknown Destination"
#     if destination_id:
#         destination = next((area for area in AREAS if area.get('id') == destination_id), None)
#         if destination:
#             destination_name = destination['name']

#     # Prepare booking details for admin notification and QR code
#     booking_info = {
#         "booking_id": booking_id,
#         "user_phone": user_phone,
#         "lot_id": lot_id,
#         "lot_name": lot_state['name'],
#         "destination": destination_name,
#         "timestamp_created": timestamp_created_str, # Time the booking was created
#         "booking_datetime_str": booking_datetime_str, # Requested booking time
#         "duration_hours": duration_hours,          # Requested duration
#         # In a real system, you'd store this booking info in a database, including the start/end time
#     }

#     # Notify Admin (prints to console)
#     notify_admin_booking(booking_info)

#     # --- Generate QR Code Data ---
#     qr_data = (
#         f"Booking ID: {booking_id}\n"
#         f"User Phone: {user_phone}\n"
#         f"Parking Lot: {lot_state['name']} ({lot_id})\n"
#         f"Destination: {destination_name}\n"
#         f"Booked For: {booking_datetime_str}\n" # Include requested time
#         f"Duration: {duration_hours} hours\n"   # Include duration
#         f"Booking Created: {timestamp_created_str}" # Include creation time
#     )

#     # Optional: Still save the QR code image server-side for demonstration
#     try:
#         qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#         qr.add_data(qr_data)
#         qr.make(fit=True)
#         img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

#         qr_dir = "booking_qrcodes"
#         if not os.path.exists(qr_dir):
#             os.makedirs(qr_dir)

#         safe_lot_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in lot_state['name'])
#         safe_booking_suffix = booking_id.split('-')[0]
#         qr_filename = f"{qr_dir}/booking_{safe_booking_suffix}_{safe_lot_name}.png"
#         img.save(qr_filename)
#         print(f"QR code image saved: {qr_filename}")

#     except Exception as e:
#         print(f"Error saving QR code image server-side: {e}")

#     # Return success response to the frontend - include the new details
#     return jsonify({
#         "message": "Booking successful!",
#         "booking_id": booking_id,
#         "lot_name": lot_state['name'],
#         "user_phone": user_phone,
#         "qr_code_data": qr_data,
#         "booking_date": booking_date_str,   # Return for frontend confirmation display
#         "booking_time": booking_time_str,   # Return for frontend confirmation display
#         "duration_hours": duration_hours    # Return for frontend confirmation display
#     }), 201


# @app.route('/slots/release/<string:lot_id>', methods=['POST'])
# def release_slot_api(lot_id):
#     """
#     API endpoint to simulate releasing a slot for a given parking lot.
#     For demonstration purposes.
#     """
#     lot_state = get_parking_lot_state(lot_id)
#     if not lot_state:
#         return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

#     # Increment the slot count
#     new_availability = update_parking_lot_availability(lot_id, 1)

#     return jsonify({
#         "message": f"Slot released for lot {lot_id}.",
#         "lot_id": lot_id,
#         "new_availability": new_availability
#     })

# @app.route('/qrcodes/<filename>')
# def serve_qr_code(filename):
#     qr_dir = "booking_qrcodes"
#     try:
#         return send_from_directory(qr_dir, filename)
#     except FileNotFoundError:
#         return jsonify({"error": "QR code not found"}), 404


# ROUTE_NODES = {
#     "node_mgroad": {"lat": 12.9750, "lon": 77.6060}, # MG Road
#     "node_koramangala": {"lat": 12.9352, "lon": 77.6245}, # Koramangala
#     "node_indiranagar": {"lat": 12.9716, "lon": 77.6412}, # Indiranagar
#     "node_whitefield": {"lat": 12.9698, "lon": 77.7499}, # Whitefield
#     "node_ecity": {"lat": 12.8398, "lon": 77.6799}, # Electronic City
#     "node_jayanagar": {"lat": 12.9250, "lon": 77.5938}, # Jayanagar
#     "node_malleshwaram": {"lat": 13.0099, "lon": 77.5690}, # Malleshwaram
#     "node_hebbal": {"lat": 13.0358, "lon": 77.5912}, # Hebbal
#     # Add some intermediate/junction nodes if needed for more complex paths
#     "node_intermediate_south": {"lat": 12.88, "lon": 77.65},
#     "node_intermediate_east": {"lat": 12.97, "lon": 77.67},
#     "node_intermediate_central": {"lat": 12.95, "lon": 77.62}, # New central node
# }

# # Predefined "safer routes" as a list of node IDs
# # This is a simulation - ideally, you'd have a graph and an algorithm
# # For simulation, these are fixed paths between specific pairs of ROUTE_NODES.
# SIMULATED_SAFER_ROUTES = {
#     # Example: From Koramangala to Whitefield
#     "koramangala_to_whitefield_1": {
#         "start_node": "node_koramangala",
#         "end_node": "node_whitefield",
#         "path_nodes": ["node_koramangala", "node_intermediate_east", "node_whitefield"],
#         "safety_score": 0.85
#     },
#      # Example: From Jayanagar to MG Road
#      "jayanagar_to_mgroad_1": {
#         "start_node": "node_jayanagar",
#         "end_node": "node_mgroad",
#         "path_nodes": ["node_jayanagar", "node_malleshwaram", "node_mgroad"],
#         "safety_score": 0.9
#      },
#      # Example: From Hebbal to E-City
#      "hebbal_to_ecity_1": {
#         "start_node": "node_hebbal",
#         "end_node": "node_ecity",
#         "path_nodes": ["node_hebbal", "node_mgroad", "node_intermediate_south", "node_ecity"],
#         "safety_score": 0.7
#      },
#     # --- Add More Routes for Better Simulation Coverage ---
#     "mgroad_to_indiranagar_1": {
#         "start_node": "node_mgroad",
#         "end_node": "node_indiranagar",
#         "path_nodes": ["node_mgroad", "node_indiranagar"],
#         "safety_score": 0.92 # Assumed high safety
#     },
#     "indiranagar_to_koramangala_1": {
#         "start_node": "node_indiranagar",
#         "end_node": "node_koramangala",
#         "path_nodes": ["node_indiranagar", "node_intermediate_central", "node_koramangala"],
#         "safety_score": 0.88
#     },
#      "whitefield_to_mgroad_1": {
#         "start_node": "node_whitefield",
#         "end_node": "node_mgroad",
#         "path_nodes": ["node_whitefield", "node_intermediate_east", "node_mgroad"], # Reverse of first example
#         "safety_score": 0.83 # Slightly different score
#      },
#      # Add routes between more nodes as needed to increase match possibilities
#      # Example: Jayanagar to Electronic City (via intermediate south)
#      "jayanagar_to_ecity_1": {
#         "start_node": "node_jayanagar",
#         "end_node": "node_ecity",
#         "path_nodes": ["node_jayanagar", "node_intermediate_south", "node_ecity"],
#         "safety_score": 0.75
#      },
#      # Example: Malleshwaram to Hebbal
#      "malleshwaram_to_hebbal_1": {
#         "start_node": "node_malleshwaram",
#         "end_node": "node_hebbal",
#         "path_nodes": ["node_malleshwaram", "node_hebbal"],
#         "safety_score": 0.80
#      },
# }


# # --- Helper to find the closest ROUTE_NODE to a given coordinate ---
# def find_closest_node(lat, lon):
#     """Finds the ID of the ROUTE_NODE closest to the given lat/lon."""
#     closest_node_id = None
#     min_distance = float('inf')

#     for node_id, node_coord in ROUTE_NODES.items():
#         distance = haversine(lat, lon, node_coord['lat'], node_coord['lon'])
#         if distance < min_distance:
#             min_distance = distance
#             closest_node_id = node_id

#     return closest_node_id, min_distance

# # --- Helper to find route nodes based on path_nodes list ---
# def get_route_coordinates(path_node_ids):
#     """Converts a list of node IDs into a list of lat/lon dictionaries."""
#     coordinates = []
#     for node_id in path_node_ids:
#         node_coord = ROUTE_NODES.get(node_id)
#         if node_coord:
#             coordinates.append({"lat": node_coord["lat"], "lon": node_coord["lon"]})
#         else:
#             # This should not happen if path_nodes are correctly defined using existing ROUTE_NODES keys
#             print(f"Error: Node ID '{node_id}' in predefined route not found in ROUTE_NODES.")
#             # Return empty list or raise error depending on desired behavior
#             return []
#     return coordinates

# # --- API Route for finding Safer Route (MODIFIED) ---
# @app.route('/safe-routes', methods=['GET'])
# def find_safer_route():
#     """
#     Finds a simulated safer route between a start coordinate and a destination area.
#     Expects 'start_lat', 'start_lon', 'dest_area_id', 'query_datetime' as query parameters.
#     Logic improved to find route between *closest* nodes.
#     """
#     start_lat_str = request.args.get('start_lat')
#     start_lon_str = request.args.get('start_lon')
#     dest_area_id = request.args.get('dest_area_id')
#     query_datetime_str = request.args.get('query_datetime')

#     if not start_lat_str or not start_lon_str or not dest_area_id or not query_datetime_str:
#          missing = []
#          if not start_lat_str: missing.append('start_lat')
#          if not start_lon_str: missing.append('start_lon')
#          if not dest_area_id: missing.append('dest_area_id')
#          if not query_datetime_str: missing.append('query_datetime')
#          return jsonify({"error": f"Missing required query parameters: {', '.join(missing)}"}), 400

#     try:
#         start_lat = float(start_lat_str)
#         start_lon = float(start_lon_str)
#         query_datetime_obj = datetime.datetime.fromisoformat(query_datetime_str)
#     except ValueError as e:
#         return jsonify({"error": f"Invalid format for coordinates or query_datetime: {e}"}), 400

#     # 1. Find the destination area coordinates
#     destination_area = next((area for area in AREAS if area.get('id') == dest_area_id), None)
#     if not destination_area:
#         return jsonify({"error": f"Destination area with ID '{dest_area_id}' not found"}), 404

#     # 2. Find the ROUTE_NODE closest to the START coordinates
#     closest_start_node_id, dist_to_start_node = find_closest_node(start_lat, start_lon)
#     print(f"[API Route Finding] Start coords ({start_lat:.4f}, {start_lon:.4f}) closest node is {closest_start_node_id} ({dist_to_start_node:.2f} km away).")

#     # 3. Find the ROUTE_NODE closest to the DESTINATION AREA coordinates
#     #    (Assuming destination areas are roughly at ROUTE_NODE locations for this simulation)
#     closest_dest_node_id, dist_to_dest_node = find_closest_node(destination_area['lat'], destination_area['lon'])
#     print(f"[API Route Finding] Dest area {dest_area_id} coords closest node is {closest_dest_node_id} ({dist_to_dest_node:.2f} km away).")


#     # --- Simulated Route Finding Logic (IMPROVED) ---
#     # Now, search for a predefined route that goes FROM the closest_start_node_id
#     # TO the closest_dest_node_id.

#     found_route_key = None
#     matched_route_data = None

#     for key, route_data in SIMULATED_SAFER_ROUTES.items():
#         # Check if the route starts at the closest start node AND ends at the closest dest node
#         if route_data["start_node"] == closest_start_node_id and route_data["end_node"] == closest_dest_node_id:
#              found_route_key = key
#              matched_route_data = route_data
#              # If multiple routes exist between the same nodes, pick the first one found
#              break

#     if found_route_key and matched_route_data:
#         route_coords = get_route_coordinates(matched_route_data["path_nodes"])

#         # Simulate a safety score calculation (could be time-dependent)
#         simulated_safety_score = matched_route_data["safety_score"]
#         # Example time-dependent adjustment (less safe at night)
#         if query_datetime_obj.hour >= 20 or query_datetime_obj.hour <= 5:
#             simulated_safety_score *= 0.8
#             simulated_safety_score = max(0.1, simulated_safety_score) # Don't let score drop below 0.1

#         print(f"[API Route Finding] Found simulated route '{found_route_key}' from {closest_start_node_id} to {closest_dest_node_id} for {query_datetime_str}. Score: {simulated_safety_score:.2f}")

#         # Include the actual start/end points in the returned coordinates for clarity on the map
#         # The frontend will draw the polyline using path_nodes, but can show markers at start/end inputs
#         return jsonify({
#             "route_coords": route_coords, # List of {lat, lon} points for the polyline
#             "safety_score": round(simulated_safety_score, 2),
#             "message": f"Simulated route found from {ROUTE_NODES[closest_start_node_id]['lat']:.4f}, {ROUTE_NODES[closest_start_node_id]['lon']:.4f} to {ROUTE_NODES[closest_dest_node_id]['lat']:.4f}, {ROUTE_NODES[closest_dest_node_id]['lon']:.4f}",
#             # Optional: Return the specific start/end nodes used in the matched route
#             "start_node_id": closest_start_node_id,
#             "end_node_id": closest_dest_node_id
#         })
#     else:
#         print(f"[API Route Finding] No predefined simulated route found from {closest_start_node_id} to {closest_dest_node_id}.")
#         return jsonify({"error": f"No simulated safer route found between locations near your start point and destination area at this time. Please try different start/end points or times."}), 404


# # --- API Route for Unsafe Notification ---
# # (Keep this as is from the previous version)
# @app.route('/notify-unsafe', methods=['POST'])
# def notify_unsafe():
#     # ... (your existing notify_unsafe code) ...
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Invalid JSON request body"}), 400

#     user_lat = data.get('user_lat')
#     user_lon = data.get('user_lon')
#     user_identifier = data.get('user_identifier', 'Anonymous') # Identifier is optional in body

#     if user_lat is None or user_lon is None:
#          return jsonify({"error": "Missing 'user_lat' or 'user_lon' in request body"}), 400

#     try:
#         user_lat = float(user_lat)
#         user_lon = float(user_lon)
#     except ValueError:
#         return jsonify({"error": "Invalid value for 'user_lat' or 'user_lon'"}), 400

#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     print("\n!!! URGENT ADMIN ALERT !!!")
#     print("User Reporting Unsafe Location:")
#     print(f"  Identifier: {user_identifier}")
#     print(f"  Location (Lat, Lon): ({user_lat}, {user_lon})")
#     print(f"  Time of Alert: {timestamp}")
#     print("!!! END ALERT !!!\n")

#     return jsonify({"message": "Unsafe location reported to admin.", "timestamp": timestamp}), 200

# # --- Keep existing parking routes (/areas, /parking-lots/nearby, etc.) below ---
# # ... (Paste the rest of your existing Flask routes here) ...

# # --- Run the Flask App ---
# if __name__ == '__main__':
#     print("Flask App Started.")
#     print("Initial Parking Lot State:")
#     for lot_id, state in parking_lots_state.items():
#         print(f"  {state['name']} ({lot_id}): {state['available_slots']}/{state['total_capacity']} slots available")

#     print("\nSimulated Route Nodes:")
#     for node_id, coord in ROUTE_NODES.items():
#         print(f"  {node_id}: {coord['lat']}, {coord['lon']}")

#     print("\nSimulated Safer Routes:")
#     # Pretty print routes
#     print(json.dumps(SIMULATED_SAFER_ROUTES, indent=2))


#     app.run(debug=True, host='0.0.0.0', port=5000)


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import math
import qrcode
from qrcode.image.pil import PilImage
import os
import time
import uuid
import datetime
import json
import random

app = Flask(__name__)
CORS(app)

# --- Existing Data Definition ---

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


# --- Existing Helper Functions (haversine, get_parking_lot_state, update_parking_lot_availability, notify_admin_booking, release_parking_slot) ---
# (Keep these functions as they are)
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

# --- Existing API Routes (/areas, /parking-lots/nearby, /parking-lots/<lot_id>, /bookings, /slots/release/<lot_id>, /qrcodes/<filename>) ---
# (Keep these routes as they are)
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
            })

    nearby_parking_options.sort(key=lambda x: x['distance_km'])
    return jsonify(nearby_parking_options)

@app.route('/parking-lots/<string:lot_id>', methods=['GET'])
def get_parking_lot(lot_id):
    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404
    return jsonify(lot_state)

@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    lot_id = data.get('lot_id')
    user_phone = data.get('user_phone')
    destination_id = data.get('destination_id')
    booking_date_str = data.get('booking_date')
    booking_time_str = data.get('booking_time')
    duration_hours = data.get('duration_hours')

    if not lot_id or not user_phone or not booking_date_str or not booking_time_str or duration_hours is None:
        missing_fields = []
        if not lot_id: missing_fields.append('lot_id')
        if not user_phone: missing_fields.append('user_phone')
        if not booking_date_str: missing_fields.append('booking_date')
        if not booking_time_str: missing_fields.append('booking_time')
        if duration_hours is None: missing_fields.append('duration_hours')
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        duration_hours = float(duration_hours)
        if duration_hours <= 0:
             return jsonify({"error": "Duration must be a positive number"}), 400

        booking_datetime_str = f"{booking_date_str} {booking_time_str}"
        booking_datetime_obj = datetime.datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
        if booking_datetime_obj < datetime.datetime.now():
             return jsonify({"error": "Booking time cannot be in the past"}), 400

    except ValueError as e:
        return jsonify({"error": f"Invalid date, time, or duration format/value: {e}"}), 400

    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404

    if lot_state['available_slots'] < 1:
        print(f"[API Booking Failure] Attempted booking for lot {lot_id}, no slots available (based on current state).")
        return jsonify({"error": f"No slots available at {lot_state['name']} for immediate booking (simulation limitation)"}), 409

    update_parking_lot_availability(lot_id, -1)

    booking_id = str(uuid.uuid4())
    timestamp_created_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        "timestamp_created": timestamp_created_str,
        "booking_datetime_str": booking_datetime_str,
        "duration_hours": duration_hours,
    }

    notify_admin_booking(booking_info)

    qr_data = (
        f"Booking ID: {booking_id}\n"
        f"User Phone: {user_phone}\n"
        f"Parking Lot: {lot_state['name']} ({lot_id})\n"
        f"Destination: {destination_name}\n"
        f"Booked For: {booking_datetime_str}\n"
        f"Duration: {duration_hours} hours\n"
        f"Booking Created: {timestamp_created_str}"
    )

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
        "qr_code_data": qr_data,
        "booking_date": booking_date_str,
        "booking_time": booking_time_str,
        "duration_hours": duration_hours
    }), 201

@app.route('/slots/release/<string:lot_id>', methods=['POST'])
def release_slot_api(lot_id):
    lot_state = get_parking_lot_state(lot_id)
    if not lot_state:
        return jsonify({"error": f"Parking lot with ID '{lot_id}' not found"}), 404
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

# --- Existing Simulated Safer Route Data and Helpers ---
ROUTE_NODES = {
    "node_mgroad": {"lat": 12.9750, "lon": 77.6060},
    "node_koramangala": {"lat": 12.9352, "lon": 77.6245},
    "node_indiranagar": {"lat": 12.9716, "lon": 77.6412},
    "node_whitefield": {"lat": 12.9698, "lon": 77.7499},
    "node_ecity": {"lat": 12.8398, "lon": 77.6799},
    "node_jayanagar": {"lat": 12.9250, "lon": 77.5938},
    "node_malleshwaram": {"lat": 13.0099, "lon": 77.5690},
    "node_hebbal": {"lat": 13.0358, "lon": 77.5912},
    "node_intermediate_south": {"lat": 12.88, "lon": 77.65},
    "node_intermediate_east": {"lat": 12.97, "lon": 77.67},
    "node_intermediate_north": {"lat": 13.01, "lon": 77.58},
    "node_central_ring": {"lat": 12.96, "lon": 77.60},
    "node_forum_junction": {"lat": 12.95, "lon": 77.61},
}

SIMULATED_SAFER_ROUTES = {
    "mgroad_to_koramangala": {"start_node": "node_mgroad", "end_node": "node_koramangala", "path_nodes": ["node_mgroad", "node_central_ring", "node_forum_junction", "node_koramangala"], "safety_score": 0.8},
    "mgroad_to_indiranagar": {"start_node": "node_mgroad", "end_node": "node_indiranagar", "path_nodes": ["node_mgroad", "node_indiranagar"], "safety_score": 0.9},
    "mgroad_to_whitefield": {"start_node": "node_mgroad", "end_node": "node_whitefield", "path_nodes": ["node_mgroad", "node_intermediate_east", "node_whitefield"], "safety_score": 0.75},
    "mgroad_to_jayanagar": {"start_node": "node_mgroad", "end_node": "node_jayanagar", "path_nodes": ["node_mgroad", "node_central_ring", "node_jayanagar"], "safety_score": 0.85},
    "mgroad_to_malleshwaram": {"start_node": "node_mgroad", "end_node": "node_malleshwaram", "path_nodes": ["node_mgroad", "node_malleshwaram"], "safety_score": 0.9},
    "mgroad_to_hebbal": {"start_node": "node_mgroad", "end_node": "node_hebbal", "path_nodes": ["node_mgroad", "node_intermediate_north", "node_hebbal"], "safety_score": 0.7},
    "koramangala_to_mgroad": {"start_node": "node_koramangala", "end_node": "node_mgroad", "path_nodes": ["node_koramangala", "node_forum_junction", "node_central_ring", "node_mgroad"], "safety_score": 0.8},
    "koramangala_to_ecity": {"start_node": "node_koramangala", "end_node": "node_ecity", "path_nodes": ["node_koramangala", "node_intermediate_south", "node_ecity"], "safety_score": 0.7},
    "koramangala_to_jayanagar": {"start_node": "node_koramangala", "end_node": "node_jayanagar", "path_nodes": ["node_koramangala", "node_forum_junction", "node_jayanagar"], "safety_score": 0.88},
    "indiranagar_to_mgroad": {"start_node": "node_indiranagar", "end_node": "node_mgroad", "path_nodes": ["node_indiranagar", "node_mgroad"], "safety_score": 0.9},
    "indiranagar_to_whitefield": {"start_node": "node_indiranagar", "end_node": "node_whitefield", "path_nodes": ["node_indiranagar", "node_intermediate_east", "node_whitefield"], "safety_score": 0.8},
    "whitefield_to_indiranagar": {"start_node": "node_whitefield", "end_node": "node_indiranagar", "path_nodes": ["node_whitefield", "node_intermediate_east", "node_indiranagar"], "safety_score": 0.8},
    "whitefield_to_mgroad": {"start_node": "node_whitefield", "end_node": "node_mgroad", "path_nodes": ["node_whitefield", "node_intermediate_east", "node_mgroad"], "safety_score": 0.75},
    "ecity_to_koramangala": {"start_node": "node_ecity", "end_node": "node_koramangala", "path_nodes": ["node_ecity", "node_intermediate_south", "node_koramangala"], "safety_score": 0.7},
    "jayanagar_to_koramangala": {"start_node": "node_jayanagar", "end_node": "node_koramangala", "path_nodes": ["node_jayanagar", "node_forum_junction", "node_koramangala"], "safety_score": 0.88},
    "jayanagar_to_mgroad": {"start_node": "node_jayanagar", "end_node": "node_mgroad", "path_nodes": ["node_jayanagar", "node_central_ring", "node_mgroad"], "safety_score": 0.85},
    "malleshwaram_to_mgroad": {"start_node": "node_malleshwaram", "end_node": "node_mgroad", "path_nodes": ["node_malleshwaram", "node_mgroad"], "safety_score": 0.9},
    "malleshwaram_to_hebbal": {"start_node": "node_malleshwaram", "end_node": "node_hebbal", "path_nodes": ["node_malleshwaram", "node_intermediate_north", "node_hebbal"], "safety_score": 0.85},
    "hebbal_to_malleshwaram": {"start_node": "node_hebbal", "end_node": "node_malleshwaram", "path_nodes": ["node_hebbal", "node_intermediate_north", "node_malleshwaram"], "safety_score": 0.85},
    "hebbal_to_mgroad": {"start_node": "node_hebbal", "end_node": "node_mgroad", "path_nodes": ["node_hebbal", "node_intermediate_north", "node_mgroad"], "safety_score": 0.7},
    # Added some routes originating from or ending at intermediate nodes for more connectivity simulation
     "intermediate_east_to_ecity": {"start_node": "node_intermediate_east", "end_node": "node_ecity", "path_nodes": ["node_intermediate_east", "node_intermediate_south", "node_ecity"], "safety_score": 0.72},
     "intermediate_south_to_jayanagar": {"start_node": "node_intermediate_south", "end_node": "node_jayanagar", "path_nodes": ["node_intermediate_south", "node_forum_junction", "node_jayanagar"], "safety_score": 0.8},
     "intermediate_north_to_mgroad": {"start_node": "node_intermediate_north", "end_node": "node_mgroad", "path_nodes": ["node_intermediate_north", "node_mgroad"], "safety_score": 0.75},
}

def get_route_coordinates(path_node_ids):
    coordinates = []
    for node_id in path_node_ids:
        node_coord = ROUTE_NODES.get(node_id)
        if node_coord:
            coordinates.append({"lat": node_coord["lat"], "lon": node_coord["lon"]})
        else:
            print(f"Warning: Node ID '{node_id}' not found in ROUTE_NODES.")
    return coordinates

def find_closest_route_node(lat, lon):
    closest_node_id = None
    min_distance = float('inf')

    for node_id, node_coord in ROUTE_NODES.items():
        distance = haversine(lat, lon, node_coord['lat'], node_coord['lon'])
        if distance < min_distance:
            min_distance = distance
            closest_node_id = node_id

    return closest_node_id, min_distance

# --- Existing API Route for finding Safer Route (MODIFIED LOGIC) ---
@app.route('/safe-routes', methods=['GET'])
def find_safer_route():
    start_lat_str = request.args.get('start_lat')
    start_lon_str = request.args.get('start_lon')
    dest_area_id = request.args.get('dest_area_id')
    query_datetime_str = request.args.get('query_datetime') # Expected format: YYYY-MM-DDTHH:mm:ss

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
        query_datetime_obj = datetime.datetime.fromisoformat(query_datetime_str)
    except ValueError as e:
        return jsonify({"error": f"Invalid format for coordinates or query_datetime: {e}"}), 400

    destination_area = next((area for area in AREAS if area.get('id') == dest_area_id), None)
    if not destination_area:
        return jsonify({"error": f"Destination area with ID '{dest_area_id}' not found"}), 404

    # Find the ROUTE_NODE closest to the destination area
    dest_node_id, dist_to_dest_node = find_closest_route_node(destination_area['lat'], destination_area['lon'])
    if dist_to_dest_node > 2.0: # Increased threshold slightly
         print(f"Warning: Destination area {dest_area_id} is > 2km from closest route node ({dest_node_id}, {dist_to_dest_node:.2f} km). Route might not be accurate.")
         # We'll still attempt to find a route to this node, but warn the user.

    # --- MODIFIED: Find the ROUTE_NODE closest to the *start* coordinate ---
    closest_start_node_id, dist_from_closest_start = find_closest_route_node(start_lat, start_lon)

    if dist_from_closest_start > 10.0: # Increased threshold for start location distance
        print(f"[API Route Finding] Start location ({start_lat:.4f}, {start_lon:.4f}) is > 10km from closest route node ({closest_start_node_id}, {dist_from_closest_start:.2f} km).")
        return jsonify({"error": "Start location is too far from known route networks."}), 400


    # --- MODIFIED: Search for a predefined route from closest_start_node_id to dest_node_id ---
    found_route_key = None
    # Prioritize direct routes if possible, then routes via intermediate nodes
    search_keys = [f"{closest_start_node_id}_to_{dest_node_id}"] # Look for direct key first
    # Add other keys if needed, depends on how SIMULATED_SAFER_ROUTES are named
    # A more robust approach would involve building a graph from SIMULATED_SAFER_ROUTES
    # and running a simple pathfinding algorithm (like BFS/DFS) to find *any* path,
    # then selecting the safest among potential paths.
    # For this sim, we'll just check if *any* route starts at the closest node and ends at the dest node.

    potential_routes_from_start = [
         (key, route_data) for key, route_data in SIMULATED_SAFER_ROUTES.items()
         if route_data["start_node"] == closest_start_node_id
    ]

    # Find the best route among potentials ending at the destination node (if multiple)
    # For this sim, we'll just pick the first one found or the one with the highest safety score
    # if multiple paths exist between the same two nodes (which they don't in current data structure)
    best_route_data = None
    best_safety_score = -1

    for key, route_data in potential_routes_from_start:
        if route_data["end_node"] == dest_node_id:
             # If multiple routes existed between same nodes, you'd compare safety_score here
             # For now, just take the first match
             found_route_key = key # Store the key just for logging
             best_route_data = route_data
             break # Found a matching route

    if best_route_data:
        route_coords = get_route_coordinates(best_route_data["path_nodes"])

        # --- Include start and end coordinates in the route ---
        # Prepend the user's exact start location IF it's significantly different from the first node
        full_route_coords = []
        if len(route_coords) > 0 and haversine(start_lat, start_lon, route_coords[0]['lat'], route_coords[0]['lon']) > 0.1: # > 100 meters difference
             full_route_coords.append({"lat": start_lat, "lon": start_lon})
        full_route_coords.extend(route_coords)
         # Append the destination area's exact location IF it's significantly different from the last node
        if len(route_coords) > 0 and haversine(destination_area['lat'], destination_area['lon'], route_coords[-1]['lat'], route_coords[-1]['lon']) > 0.1:
             full_route_coords.append({"lat": destination_area['lat'], "lon": destination_area['lon']})
         # Handle case where route_coords is empty (shouldn't happen with valid paths)
        elif len(route_coords) == 0:
             full_route_coords = [{"lat": start_lat, "lon": start_lon}, {"lat": destination_area['lat'], "lon": destination_area['lon']}] # Simple straight line if no path

        # Simulate safety score calculation (time-dependent)
        simulated_safety_score = best_route_data["safety_score"]
        # Example: Lower safety at night (8 PM to 5 AM)
        if query_datetime_obj.time() >= datetime.time(20, 0) or query_datetime_obj.time() <= datetime.time(5, 0):
            simulated_safety_score *= 0.8 # Reduce safety score by 20%
            simulated_safety_score = max(0.1, simulated_safety_score) # Minimum score

        print(f"[API Route Finding] Found simulated route from closest node {closest_start_node_id} to {dest_node_id} (via '{found_route_key}') for {query_datetime_str}. Score: {simulated_safety_score:.2f}")

        return jsonify({
            "route_coords": full_route_coords, # Return the full list including start/end
            "safety_score": round(simulated_safety_score, 2),
            "message": "Simulated safer route found."
        })
    else:
        print(f"[API Route Finding] No predefined simulated route found from closest node {closest_start_node_id} to {dest_node_id}.")
        return jsonify({"error": f"No simulated safer route found for your request at the moment. Try selecting a destination area closer to a known route endpoint or adjust your starting point."}), 404


# --- Existing API Route for Unsafe Notification ---
@app.route('/notify-unsafe', methods=['POST'])
def notify_unsafe():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    user_lat = data.get('user_lat')
    user_lon = data.get('user_lon')
    user_identifier = data.get('user_identifier', 'Anonymous')

    if user_lat is None or user_lon is None:
         return jsonify({"error": "Missing 'user_lat' or 'user_lon' in request body"}), 400

    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except ValueError:
        return jsonify({"error": "Invalid value for 'user_lat' or 'user_lon'"}), 400

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n!!! URGENT ADMIN ALERT !!!")
    print("User Reporting Unsafe Location:")
    print(f"  Identifier: {user_identifier}")
    print(f"  Location (Lat, Lon): ({user_lat}, {user_lon})")
    print(f"  Time of Alert: {timestamp}")
    print("!!! END ALERT !!!\n")

    return jsonify({"message": "Unsafe location reported to admin.", "timestamp": timestamp}), 200


# --- NEW Traffic Congestion Data and Functions ---

# Define Traffic Zones (simple points representing areas)
# You could add polygon coordinates here for drawing areas instead of just points
TRAFFIC_ZONES = [
    {"id": "zone_mgroad", "name": "MG Road Area", "lat": 12.9750, "lon": 77.6060},
    {"id": "zone_koramangala", "name": "Koramangala Area", "lat": 12.9352, "lon": 77.6245},
    {"id": "zone_indiranagar", "name": "Indiranagar Area", "lat": 12.9716, "lon": 77.6412},
    {"id": "zone_whitefield", "name": "Whitefield Area", "lat": 12.9698, "lon": 77.7499},
    {"id": "zone_ecity", "name": "Electronic City Area", "lat": 12.8398, "lon": 77.6799},
    {"id": "zone_jayanagar", "name": "Jayanagar Area", "lat": 12.9250, "lon": 77.5938},
    {"id": "zone_malleshwaram", "name": "Malleshwaram Area", "lat": 13.0099, "lon": 77.5690},
    {"id": "zone_hebbal", "name": "Hebbal Area", "lat": 13.0358, "lon": 77.5912},
]

# Simulated ML Model: Predict Congestion
def predict_congestion_simulated(zone_id, query_datetime_obj):
    """
    Simulates congestion prediction based on time of day, day of week.
    Returns a congestion level ('Low', 'Medium', 'High') and a numerical score (0-100).
    """
    hour = query_datetime_obj.hour
    weekday = query_datetime_obj.weekday() # 0=Mon, 6=Sun

    # Base congestion levels
    base_score = 20 # Low
    level = 'Low'

    # Apply time/day factors
    if weekday < 5: # Weekday
        if (hour >= 8 and hour < 10) or (hour >= 17 and hour < 19): # Morning/Evening Rush
            base_score = 80
            level = 'High'
        elif hour >= 10 and hour < 17: # Daytime
            base_score = 50
            level = 'Medium'
        elif hour >= 19 and hour < 21: # Post-rush
            base_score = 40
            level = 'Medium'
        else: # Late night/early morning
             base_score = 10
             level = 'Very Low'
    else: # Weekend
        if (hour >= 12 and hour < 18): # Afternoon/Evening
            base_score = 30
            level = 'Medium'
        else:
            base_score = 15
            level = 'Low'

    # Add some randomness for simulation realism
    random_factor = random.uniform(-10, 10)
    final_score = max(0, min(100, base_score + random_factor)) # Keep score between 0-100

    # Refine level based on final score
    if final_score >= 70:
        level = 'High'
    elif final_score >= 40:
        level = 'Medium'
    elif final_score >= 15:
        level = 'Low'
    else:
        level = 'Very Low'


    # Simulate specific zone characteristics (optional)
    if zone_id == "zone_whitefield" and weekday < 5 and (hour >= 9 and hour < 11): # Whitefield peak morning
         final_score = min(100, final_score + 15)
         level = 'High'
    elif zone_id == "zone_koramangala" and weekday >= 5 and (hour >= 18 and hour < 23): # Koramangala weekend evening
         final_score = min(100, final_score + 10)
         level = 'High'
    # Add rules for other zones/times


    return {
        "level": level,
        "score": round(final_score, 2)
    }

# --- NEW API Route for getting Zones ---
@app.route('/zones', methods=['GET'])
def list_zones():
    """Returns the list of defined traffic zones."""
    return jsonify(TRAFFIC_ZONES)

# --- NEW API Route for getting Traffic Prediction ---
@app.route('/traffic-prediction', methods=['GET'])
def get_traffic_prediction():
    """
    Predicts traffic congestion for specified zones at a given time.
    Expects 'zone_ids' (comma-separated string) and 'query_datetime' as query parameters.
    If 'zone_ids' is 'all', predicts for all zones.
    """
    zone_ids_str = request.args.get('zone_ids', 'all')
    query_datetime_str = request.args.get('query_datetime') # Expected format: YYYY-MM-DDTHH:mm:ss

    if not query_datetime_str:
        return jsonify({"error": "Missing 'query_datetime' query parameter"}), 400

    try:
        query_datetime_obj = datetime.datetime.fromisoformat(query_datetime_str)
    except ValueError:
        return jsonify({"error": "Invalid format for 'query_datetime'. Use YYYY-MM-DDTHH:mm:ss"}), 400

    zones_to_predict = []
    if zone_ids_str.lower() == 'all':
        zones_to_predict = TRAFFIC_ZONES # Predict for all defined zones
    else:
        requested_ids = zone_ids_str.split(',')
        for zone_id in requested_ids:
            zone = next((z for z in TRAFFIC_ZONES if z['id'] == zone_id.strip()), None)
            if zone:
                zones_to_predict.append(zone)
            else:
                # Optionally return an error or just skip invalid IDs
                print(f"Warning: Zone ID '{zone_id.strip()}' not found.")
                # Continue processing valid IDs

    if not zones_to_predict:
        return jsonify({"error": "No valid zone IDs provided or 'all' zones definition is empty."}), 400

    predictions = []
    for zone in zones_to_predict:
        prediction_result = predict_congestion_simulated(zone['id'], query_datetime_obj)
        predictions.append({
            "zone_id": zone['id'],
            "predicted_congestion": prediction_result['score'],
            "predicted_level": prediction_result['level']
        })

    return jsonify(predictions)


# --- NEW Data for Points of Interest (POIs) ---

# Add significantly more data spread across different areas and categories
POIS_DATA = [
    # --- Attractions ---
    {"id": "att_lalbagh", "name": "Lal Bagh Botanical Garden", "lat": 12.9485, "lon": 77.5848, "category": "attraction", "subcategory": "nature", "description": "Historic botanical garden with a glass house.", "tags": ["nature", "garden", "history", "park"], "entry_fee": 20, "time_needed_hours": 2},
    {"id": "att_cubbon", "name": "Cubbon Park", "lat": 12.9760, "lon": 77.5929, "category": "attraction", "subcategory": "nature", "description": "Green lung of the city, houses State Library and high court.", "tags": ["nature", "park", "relaxing", "history"], "entry_fee": 0, "time_needed_hours": 1.5},
    {"id": "att_palace", "name": "Bangalore Palace", "lat": 12.9987, "lon": 77.5930, "category": "attraction", "subcategory": "history", "description": "Historic palace with Tudor architecture.", "tags": ["history", "culture", "architecture"], "entry_fee": 230, "time_needed_hours": 1.5},
    {"id": "att_vish", "name": "Visvesvaraya Industrial & Technological Museum", "lat": 12.9743, "lon": 77.5908, "category": "attraction", "subcategory": "museum", "description": "Interactive science and technology museum.", "tags": ["museum", "technology", "family", "education"], "entry_fee": 70, "time_needed_hours": 2},
    {"id": "att_iskcon", "name": "ISKCON Temple Bangalore", "lat": 13.0097, "lon": 77.5511, "category": "attraction", "subcategory": "religious", "description": "Large Hare Krishna temple complex.", "tags": ["religious", "spiritual", "culture"], "entry_fee": 0, "time_needed_hours": 1},
    {"id": "att_aerospace", "name": "HAL Aerospace Museum", "lat": 12.9550, "lon": 77.6535, "category": "attraction", "subcategory": "museum", "description": "Exhibits related to aerospace and aviation.", "tags": ["museum", "technology", "family", "aviation"], "entry_fee": 50, "time_needed_hours": 1.5},
    {"id": "att_forumk", "name": "Forum South Bangalore (Koramangala)", "lat": 12.9346, "lon": 77.6101, "category": "attraction", "subcategory": "shopping", "description": "Popular mall in Koramangala.", "tags": ["shopping", "entertainment", "food", "mixed"], "entry_fee": 0, "time_needed_hours": 2},
    {"id": "att_phoenix", "name": "Phoenix Marketcity (Whitefield)", "lat": 12.9955, "lon": 77.6975, "category": "attraction", "subcategory": "shopping", "description": "Large mall with many brands and entertainment.", "tags": ["shopping", "entertainment", "food", "mixed"], "entry_fee": 0, "time_needed_hours": 3},
    {"id": "att_nandi", "name": "Nandi Hills", "lat": 13.3800, "lon": 77.6850, "category": "attraction", "subcategory": "nature", "description": "Hill station near Bangalore, popular for sunrise.", "tags": ["nature", "adventure", "sunrise", "daytrip"], "entry_fee": 20, "time_needed_hours": 4, "notes": "Requires travel outside main city, good for half-day trip"},
     {"id": "att_nationalgallery", "name": "National Gallery of Modern Art", "lat": 12.9811, "lon": 77.5908, "category": "attraction", "subcategory": "museum", "description": "Collection of modern Indian art.", "tags": ["museum", "art", "culture"], "entry_fee": 20, "time_needed_hours": 1.5},
     {"id": "att_stmary", "name": "St. Mary's Basilica", "lat": 12.9819, "lon": 77.6030, "category": "attraction", "subcategory": "religious", "description": "One of the oldest churches in Bangalore.", "tags": ["religious", "history", "architecture"], "entry_fee": 0, "time_needed_hours": 1},
     {"id": "att_bulltemple", "name": "Dodda Basavana Gudi (Bull Temple)", "lat": 12.9412, "lon": 77.5684, "category": "attraction", "subcategory": "religious", "description": "Temple with a large granite statue of the Nandi bull.", "tags": ["religious", "culture"], "entry_fee": 0, "time_needed_hours": 0.5},
     {"id": "att_jpnagar", "name": "JP Nagar Cultural Complex", "lat": 12.9040, "lon": 77.5871, "category": "attraction", "subcategory": "culture", "description": "Venue for performances and cultural events.", "tags": ["culture", "entertainment", "local"], "entry_fee": 0, "time_needed_hours": 2},
     {"id": "att_electroniccity_temple", "name": "Prasanna Veeranjaneya Swamy Temple (E-City)", "lat": 12.8330, "lon": 77.6680, "category": "attraction", "subcategory": "religious", "description": "Popular temple in Electronic City.", "tags": ["religious"], "entry_fee": 0, "time_needed_hours": 1},


    # --- Food ---
    {"id": "food_mavalli", "name": "MTR (Mavalli Tiffin Rooms)", "lat": 12.9555, "lon": 77.5820, "category": "food", "subcategory": "indian_south", "description": "Iconic South Indian breakfast place.", "tags": ["indian", "south indian", "vegetarian", "affordable", "historic"], "price_range": "affordable", "food_pref": "veg"},
    {"id": "food_vidyarthi", "name": "Vidyarthi Bhavan", "lat": 12.9440, "lon": 77.5758, "category": "food", "subcategory": "indian_south", "description": "Legendary place for Dosa.", "tags": ["indian", "south indian", "vegetarian", "affordable"], "price_range": "affordable", "food_pref": "veg"},
    {"id": "food_koramangala_social", "name": "Social (Koramangala)", "lat": 12.9351, "lon": 77.6260, "category": "food", "subcategory": "bar_pub", "description": "Popular bar & restaurant with quirky ambiance.", "tags": ["mixed", "drinks", "nightlife", "medium"], "price_range": "medium", "food_pref": "mixed"},
     {"id": "food_indiranagar_brewery", "name": "Toit Brewery (Indiranagar)", "lat": 12.9716, "lon": 77.6413, "category": "food", "subcategory": "bar_pub", "description": "Very popular microbrewery.", "tags": ["mixed", "drinks", "nightlife", "medium", "premium"], "price_range": "medium", "food_pref":"mixed"},
     {"id": "food_ctm", "name": "Central Tiffin Room (CTR/Shri Sagar)", "lat": 13.0067, "lon": 77.5718, "category": "food", "subcategory": "indian_south", "description": "Famous for Benne Masala Dosa.", "tags": ["indian", "south indian", "vegetarian", "affordable"], "price_range": "affordable", "food_pref": "veg"},
     {"id": "food_chinatown", "name": "China Town (Residency Road)", "lat": 12.9738, "lon": 77.6038, "category": "food", "subcategory": "chinese", "description": "Long-standing Indo-Chinese restaurant.", "tags": ["chinese", "non-vegetarian", "medium"], "price_range": "medium", "food_pref": "non-veg"},
     {"id": "food_karavalli", "name": "Karavalli (Taj Gateway)", "lat": 12.9719, "lon": 77.6073, "category": "food", "subcategory": "indian_south", "description": "Fine dining coastal Indian cuisine.", "tags": ["indian", "south indian", "seafood", "premium"], "price_range": "premium", "food_pref": "mixed"},
     {"id": "food_truffles", "name": "Truffles (St. Marks Road)", "lat": 12.9703, "lon": 77.5975, "category": "food", "subcategory": "cafe", "description": "Popular cafe for burgers and shakes.", "tags": ["cafe", "burgers", "affordable", "young"], "price_range": "affordable", "food_pref": "mixed"},
     {"id": "food_shiro", "name": "Shiro (UB City)", "lat": 12.9711, "lon": 77.5915, "category": "food", "subcategory": "asian", "description": "Upscale Asian restaurant with great ambiance.", "tags": ["asian", "premium", "nightlife", "view"], "price_range": "premium", "food_pref": "mixed"},
     {"id": "food_bombayadda", "name": "Bombay Adda Bangalore", "lat": 12.9510, "lon": 77.6380, "category": "food", "subcategory": "bar_pub", "description": "Rooftop bar & lounge in Koramangala.", "tags": ["mixed", "drinks", "nightlife", "medium", "premium"], "price_range": "medium", "food_pref": "mixed"},
      {"id": "food_absolute", "name": "Absolute Barbecues (AB's)", "lat": 12.9315, "lon": 77.6250, "category": "food", "subcategory": "buffet", "description": "Popular buffet restaurant.", "tags": ["buffet", "mixed", "affordable", "group"], "price_range": "medium", "food_pref": "mixed"},
      {"id": "food_therestaurant", "name": "The Restaurant (ITC Windsor)", "lat": 12.9830, "lon": 77.5850, "category": "food", "subcategory": "indian_north", "description": "Fine dining North Indian.", "tags": ["indian", "north indian", "premium"], "price_range": "premium", "food_pref": "mixed"},


    # --- Hotels ---
    {"id": "hotel_ritz", "name": "The Ritz-Carlton, Bangalore", "lat": 12.9721, "lon": 77.5988, "category": "hotel", "star_rating": 5, "price_level": "luxury", "tags": ["luxury", "premium", "mgroad", "central"]},
    {"id": "hotel_lalit", "name": "The Lalit Ashok Bangalore", "lat": 13.0076, "lon": 77.5843, "category": "hotel", "star_rating": 5, "price_level": "premium", "tags": ["premium", "business", "north"]},
    {"id": "hotel_tajmg", "name": "Taj MG Road, Bengaluru", "lat": 12.9763, "lon": 77.6114, "category": "hotel", "star_rating": 5, "price_level": "premium", "tags": ["premium", "business", "mgroad"]},
    {"id": "hotel_novotel_koramangala", "name": "Novotel Bengaluru Outer Ring Road (Koramangala)", "lat": 12.9258, "lon": 77.6785, "category": "hotel", "star_rating": 4, "price_level": "medium", "tags": ["medium", "business", "koramangala", "outerringroad"]},
     {"id": "hotel_lemon_indiranagar", "name": "Lemon Tree Hotel, Indiranagar", "lat": 12.9705, "lon": 77.6390, "category": "hotel", "star_rating": 4, "price_level": "medium", "tags": ["medium", "indiranagar"]},
     {"id": "hotel_ibis_ecity", "name": "Ibis Bengaluru Electronic City", "lat": 12.8432, "lon": 77.6778, "category": "hotel", "star_rating": 3, "price_level": "affordable", "tags": ["affordable", "business", "ecity"]},
     {"id": "hotel_formule1_whitefield", "name": "Formule1 Bangalore Whitefield", "lat": 12.9690, "lon": 77.7490, "category": "hotel", "star_rating": 3, "price_level": "affordable", "tags": ["affordable", "whitefield"]},
     {"id": "hotel_bloom_jayanagar", "name": "Bloomrooms @ Jayanagar", "lat": 12.9250, "lon": 77.5860, "category": "hotel", "star_rating": 3, "price_level": "affordable", "tags": ["affordable", "jayanagar"]},
     {"id": "hotel_statue", "name": "The Chancery Pavilion", "lat": 12.9691, "lon": 77.5941, "category": "hotel", "star_rating": 4, "price_level": "medium", "tags": ["medium", "central"]},
     {"id": "hotel_ozone", "name": "The OZONE Hotel Bangalore", "lat": 12.9759, "lon": 77.6099, "category": "hotel", "star_rating": 3, "price_level": "affordable", "tags": ["affordable", "mgroad"]},

    # --- Emergency Services ---
    {"id": "emergency_apollo_jayanagar", "name": "Apollo Hospitals (Jayanagar)", "lat": 12.9263, "lon": 77.5795, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical"]},
    {"id": "emergency_manipal_hal", "name": "Manipal Hospital (HAL Road)", "lat": 12.9627, "lon": 77.6538, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical"]},
    {"id": "emergency_fortis_bgroad", "name": "Fortis Hospitals (Bannerghatta Road)", "lat": 12.9070, "lon": 77.5890, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical"]},
    {"id": "emergency_stjohns", "name": "St. John's Medical College Hospital", "lat": 12.9339, "lon": 77.6203, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical", "koramangala"]},
     {"id": "emergency_columbia_whitefield", "name": "Columbia Asia Hospital (Whitefield)", "lat": 12.9869, "lon": 77.7361, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical", "whitefield"]},
     {"id": "emergency_narayana_ecity", "name": "Narayana Health City (E-City)", "lat": 12.8200, "lon": 77.6600, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical", "ecity"]},
    {"id": "emergency_police_mgroad", "name": "MG Road Police Station", "lat": 12.9755, "lon": 77.6088, "category": "emergency", "subcategory": "police", "tags": ["police", "safety"]},
    {"id": "emergency_police_koramangala", "name": "Koramangala Police Station", "lat": 12.9340, "lon": 77.6230, "category": "emergency", "subcategory": "police", "tags": ["police", "safety"]},
     {"id": "emergency_fire_indiranagar", "name": "Indiranagar Fire Station", "lat": 12.9650, "lon": 77.6430, "category": "emergency", "subcategory": "fire", "tags": ["fire", "safety"]},
    # Add more cafes, restaurants, etc., focusing on different price ranges and locations
    # --- More Food ---
    {"id": "food_dutchcafe", "name": "The Dutch Cafe (Koramanagala)", "lat": 12.9340, "lon": 77.6280, "category": "food", "subcategory": "cafe", "description": "Cozy cafe with European feel.", "tags": ["cafe", "coffee", "affordable"], "price_range": "affordable", "food_pref": "mixed"},
    {"id": "food_smallys", "name": "Smally's Resto Cafe", "lat": 12.9765, "lon": 77.6040, "category": "food", "subcategory": "cafe", "description": "Casual cafe popular among youth.", "tags": ["cafe", "affordable", "burgers"], "price_range": "affordable", "food_pref": "mixed"},
    {"id": "food_punjabgrill", "name": "Punjab Grill (Forum Koramangala)", "lat": 12.9350, "lon": 77.6095, "category": "food", "subcategory": "indian_north", "description": "North Indian fine dining.", "tags": ["indian", "north indian", "premium"], "price_range": "premium", "food_pref": "mixed"},
    {"id": "food_biriyanazone", "name": "Biriyani Zone (Multiple Locations)", "lat": 12.9700, "lon": 77.6400, "category": "food", "subcategory": "indian_biriyani", "description": "Popular for Biriyani.", "tags": ["indian", "biriyani", "non-vegetarian", "affordable"], "price_range": "affordable", "food_pref": "non-veg"}, # Example in Indiranagar
     {"id": "food_biriyanazonej", "name": "Biriyani Zone (Jayanagar)", "lat": 12.9260, "lon": 77.5850, "category": "food", "subcategory": "indian_biriyani", "description": "Popular for Biriyani.", "tags": ["indian", "biriyani", "non-vegetarian", "affordable"], "price_range": "affordable", "food_pref": "non-veg"}, # Example in Jayanagar
     {"id": "food_burgerking_whitefield", "name": "Burger King (Whitefield)", "lat": 12.9950, "lon": 77.6980, "category": "food", "subcategory": "fast_food", "description": "Fast food chain.", "tags": ["fast food", "affordable"], "price_range": "affordable", "food_pref": "mixed"},
    # Add more hotels across price levels and locations
    # --- More Hotels ---
    {"id": "hotel_shangrila", "name": "Shangri-La Bengaluru", "lat": 12.9911, "lon": 77.5840, "category": "hotel", "star_rating": 5, "price_level": "luxury", "tags": ["luxury", "premium", "central"]},
     {"id": "hotel_jwmarriott", "name": "JW Marriott Hotel Bengaluru Prestige Golfshire Resort & Spa", "lat": 13.306, "lon": 77.614, "category": "hotel", "star_rating": 5, "price_level": "luxury", "tags": ["luxury", "premium", "resort", "outside city"], "notes": "Located outside the main city"},
    {"id": "hotel_royalorchid", "name": "Royal Orchid Central Bangalore (MG Road)", "lat": 12.9758, "lon": 77.6110, "category": "hotel", "star_rating": 4, "price_level": "medium", "tags": ["medium", "business", "mgroad"]},
    {"id": "hotel_ibisk", "name": "Ibis Bengaluru Hosur Road (Koramangala)", "lat": 12.9250, "lon": 77.6160, "category": "hotel", "star_rating": 3, "price_level": "affordable", "tags": ["affordable", "business", "koramangala"]},
    {"id": "hotel_holidayinnw", "name": "Holiday Inn Express Bengaluru Whitefield", "lat": 12.9685, "lon": 77.7400, "category": "hotel", "star_rating": 3.5, "price_level": "affordable", "tags": ["affordable", "business", "whitefield"]},
    {"id": "hotel_radissonecity", "name": "Radisson Blu Bengaluru Electronic City", "lat": 12.8360, "lon": 77.6820, "category": "hotel", "star_rating": 5, "price_level": "premium", "tags": ["premium", "business", "ecity"]},
    # Add more emergency contacts (ambulances, tourist police helplines etc.)
    # --- More Emergency ---
     {"id": "emergency_mallyaroad", "name": "Mallya Hospital", "lat": 12.9705, "lon": 77.5990, "category": "emergency", "subcategory": "hospital", "tags": ["hospital", "medical", "central"]},
     {"id": "emergency_fire_central", "name": "Central Fire Station", "lat": 12.9780, "lon": 77.6000, "category": "emergency", "subcategory": "fire", "tags": ["fire", "safety", "central"]},
     {"id": "emergency_tourist_police", "name": "Tourist Police Assistance (Simulated)", "lat": 12.9760, "lon": 77.6005, "category": "emergency", "subcategory": "police", "tags": ["police", "safety", "tourist"], "phone": "1800-123-4567"}, # Simulated Helpline
    # Common Emergency Numbers (these don't need location data)
     {"id": "emergency_ambulance_national", "name": "Ambulance (National)", "category": "emergency", "subcategory": "helpline", "phone": "102", "notes": "Common national ambulance number"},
     {"id": "emergency_police_national", "name": "Police (National)", "category": "emergency", "subcategory": "helpline", "phone": "100", "notes": "Common national police number"},
     {"id": "emergency_fire_national", "name": "Fire (National)", "category": "emergency", "subcategory": "helpline", "phone": "101", "notes": "Common national fire number"},
]

# Add unique IDs if missing (ensure all have 'id')
for i, poi in enumerate(POIS_DATA):
    if 'id' not in poi:
        poi['id'] = f"poi_{i+1}" # Generate a simple ID if missing


# --- API Route for getting Points of Interest ---
@app.route('/pois', methods=['GET'])
def list_pois():
    """
    Returns a list of Points of Interest (POIs).
    Optional query parameters:
    - category: Filter by category (e.g., 'attraction', 'food', 'hotel', 'emergency'). Comma-separated for multiple.
    - lat, lon, radius_km: Filter by proximity to a location.
    - subcategory: Filter by subcategory (e.g., 'museum', 'cafe'). Comma-separated for multiple.
    - tags: Filter by tags (e.g., 'history', 'affordable'). Comma-separated for multiple.
    """
    category_filter_str = request.args.get('category')
    lat_str = request.args.get('lat')
    lon_str = request.args.get('lon')
    radius_km_str = request.args.get('radius_km')
    subcategory_filter_str = request.args.get('subcategory')
    tags_filter_str = request.args.get('tags')


    filtered_pois = POIS_DATA # Start with all data

    # --- Apply Category Filter ---
    if category_filter_str:
        categories = [c.strip() for c in category_filter_str.split(',')]
        filtered_pois = [poi for poi in filtered_pois if poi.get('category') in categories]

    # --- Apply Subcategory Filter ---
    if subcategory_filter_str:
        subcategories = [sc.strip() for sc in subcategory_filter_str.split(',')]
        filtered_pois = [poi for poi in filtered_pois if poi.get('subcategory') in subcategories]

    # --- Apply Tags Filter ---
    if tags_filter_str:
        requested_tags = set(t.strip() for t in tags_filter_str.split(','))
        filtered_pois = [poi for poi in filtered_pois if requested_tags.intersection(set(poi.get('tags', [])))]


    # --- Apply Proximity Filter ---
    if lat_str and lon_str and radius_km_str:
        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
            radius_km = float(radius_km_str)
            if radius_km <= 0: raise ValueError("Radius must be positive")

            # Filter POIs within the radius
            proximity_filtered_pois = []
            for poi in filtered_pois:
                # Only apply distance filter if POI has lat/lon coordinates
                if 'lat' in poi and 'lon' in poi:
                    distance = haversine(user_lat, user_lon, poi['lat'], poi['lon'])
                    if distance <= radius_km:
                        # Add distance to the result for potential sorting/display
                        poi_with_distance = dict(poi) # Copy to avoid modifying original data
                        poi_with_distance['distance_km'] = round(distance, 2)
                        proximity_filtered_pois.append(poi_with_distance)
                else:
                     # Include POIs without location data if they pass other filters
                     # (e.g., helplines defined without coords)
                     proximity_filtered_pois.append(poi)

            filtered_pois = proximity_filtered_pois

        except ValueError as e:
            return jsonify({"error": f"Invalid value for lat, lon, or radius_km: {e}"}), 400

    # Optional: Sort results (e.g., by distance if proximity filter was applied)
    if 'distance_km' in filtered_pois[0] if filtered_pois else False: # Check if distance was added
         filtered_pois.sort(key=lambda x: x['distance_km'])
    # Add other sorting options if needed

    return jsonify(filtered_pois)

# --- NEW API Route for getting single POI details ---
@app.route('/pois/<string:poi_id>', methods=['GET'])
def get_poi_details(poi_id):
    """Returns detailed information for a specific POI by ID."""
    poi = next((p for p in POIS_DATA if p.get('id') == poi_id), None)
    if poi:
        return jsonify(poi)
    else:
        return jsonify({"error": f"POI with ID '{poi_id}' not found"}), 404

# --- NEW API Route for Tour Planning (Placeholder for now) ---
@app.route('/tour-plan', methods=['POST'])
def generate_tour_plan():
    """
    Generates a simulated tour plan based on user inputs.
    (Logic will be implemented in a later phase)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request body"}), 400

    print("\n--- Tour Plan Request Received ---")
    print(f"Inputs: {json.dumps(data, indent=2)}")
    print("---------------------------------\n")

    # --- Placeholder/Simulated Tour Planning Logic ---
    # This is where the logic from your requirements would go:
    # - Filter POIs based on interests, budget, travel style, group type
    # - Select a hotel based on preference/budget
    # - Create a daily itinerary distributing selected POIs
    # - Estimate costs
    # - Find emergency contacts
    # - Simulate routes between points
    # ... etc.

    # For now, return a mock plan based on the inputs
    simulated_plan = {
        "request_inputs": data,
        "summary": f"Simulated {data.get('days_stay', 1)}-day plan for {data.get('group_type', 'visitors')} with {data.get('travel_style', 'mixed')} style.",
        "itinerary": [], # List of days
        "recommended_pois": [], # List of selected POI objects (full details or summary)
        "suggested_hotel": None, # Single hotel POI object
        "estimated_cost": {
            "total": random.randint(10000, 50000), # Random simulated cost
            "breakdown": {"stay": 0, "food": 0, "transport": 0, "attractions": 0, "misc": 0} # Fill this in later
        },
        "emergency_contacts": [p for p in POIS_DATA if p.get('category') == 'emergency'], # Just return all emergency contacts
        "notes": "This is a simulated plan. Real-world planning is complex and considers opening hours, dynamic travel times, actual availability, etc."
    }

    # Add some sample attractions/food/hotel based on inputs (very basic simulation)
    all_attractions = [p for p in POIS_DATA if p['category'] == 'attraction']
    all_food = [p for p in POIS_DATA if p['category'] == 'food']
    all_hotels = [p for p in POIS_DATA if p['category'] == 'hotel' and p.get('price_level') == data.get('preferred_hotel_type')] or [p for p in POIS_DATA if p['category'] == 'hotel'][0:1] # Fallback if no hotel type matches
    simulated_plan["suggested_hotel"] = random.choice(all_hotels) if all_hotels else None

    num_days = int(data.get('days_stay', 1))
    attractions_per_day = min(3, len(all_attractions) // num_days + 1) # Simple heuristic
    current_attraction_index = 0

    for day in range(num_days):
        day_itinerary = {
            "day_number": day + 1,
            "theme": f"Day {day + 1}", # Could be themed later
            "activities": [], # List of POI objects or steps
            "suggested_food_stops": [], # List of POI objects
            "daily_cost_estimate": random.randint(2000, 5000) # Random daily cost
        }

        # Add sample attractions for the day
        day_attractions = all_attractions[current_attraction_index : current_attraction_index + attractions_per_day]
        current_attraction_index += attractions_per_day

        # Add a sample food stop - pick one near the first attraction of the day (very basic)
        if day_attractions:
            nearby_food = [p for p in all_food if 'lat' in p and haversine(p['lat'], p['lon'], day_attractions[0]['lat'], day_attractions[0]['lon']) < 5] # Food within 5km
            if nearby_food:
                 day_itinerary["suggested_food_stops"].append(random.choice(nearby_food))


        # Format activities (could include start/end times, transport steps later)
        for attr in day_attractions:
             day_itinerary["activities"].append({
                 "type": "visit",
                 "poi": attr # Add the full POI data
             })

        # Add suggested hotel for the day (could be different each day if moving areas)
        # For simplicity, suggest the same hotel each day in this sim
        if simulated_plan["suggested_hotel"]:
             day_itinerary["activities"].append({
                 "type": "stay",
                 "poi": simulated_plan["suggested_hotel"]
             })


        simulated_plan["itinerary"].append(day_itinerary)
        simulated_plan["recommended_pois"].extend(day_attractions) # Add visited attractions to recommended list

    # Add some general recommended POIs not necessarily in the itinerary
    simulated_plan["recommended_pois"].extend(random.sample([p for p in POIS_DATA if p['category'] == 'attraction' and p['id'] not in [a['id'] for day in simulated_plan['itinerary'] for activity in day['activities'] if activity['type'] == 'visit' for a in [activity['poi']]] ], min(5, len(all_attractions) - len(simulated_plan["recommended_pois"]))))


    # Add some general recommended food places
    simulated_plan["recommended_pois"].extend(random.sample(all_food, min(5, len(all_food))))


    return jsonify(simulated_plan), 200




# --- Run the Flask App ---
if __name__ == '__main__':
    print("Flask App Started.")
    print("\nInitial Parking Lot State:")
    for lot_id, state in parking_lots_state.items():
        print(f"  {state['name']} ({lot_id}): {state['available_slots']}/{state['total_capacity']} slots available")

    print("\nSimulated Route Nodes:")
    for node_id, coord in ROUTE_NODES.items():
        print(f"  {node_id}: {coord['lat']}, {coord['lon']}")

    print("\nSimulated Safer Routes:")
    for route_key, route_data in SIMULATED_SAFER_ROUTES.items():
        start_coord = ROUTE_NODES.get(route_data["start_node"])
        end_coord = ROUTE_NODES.get(route_data["end_node"])
        start_name = start_coord if start_coord else route_data["start_node"]
        end_name = end_coord if end_coord else route_data["end_node"]
        print(f"  {route_key}: ({start_name}) -> ({end_name}) (Nodes: {len(route_data['path_nodes'])}, Score: {route_data['safety_score']})")

    print("\nTraffic Zones:")
    for zone in TRAFFIC_ZONES:
        print(f"  {zone['id']}: {zone['name']} ({zone['lat']}, {zone['lon']})")
    
    print(f"\nLoaded {len(POIS_DATA)} Points of Interest.")
    # Optional: Print a sample POI
    if len(POIS_DATA) > 0:
        print("Sample POI:", json.dumps(POIS_DATA[0], indent=2))

    # print("\nPoints of Interest:")
    # for poi in POIS:
    #     print(f"  {poi['id']}: {poi['name']} ({poi['category']}) at ({poi['lat']}, {poi['lon']})")


    app.run(debug=True, host='0.0.0.0', port=5000)
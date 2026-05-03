from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime, date

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("WARNING: Missing SUPABASE_URL or SUPABASE_KEY in .env file.")
    # Initialize with dummy values just so the server runs, but DB calls will fail
    supabase: Client = create_client("http://localhost", "dummy")
else:
    supabase: Client = create_client(supabase_url, supabase_key)

@app.route('/subjects', methods=['GET'])
def get_subjects():
    """Fetch all subjects from Supabase and return sorted by deadline ascending."""
    try:
        response = supabase.table('subjects').select('*').order('deadline').execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subjects', methods=['POST'])
def add_subject():
    """Add a new subject to Supabase."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get('name')
    deadline_str = data.get('deadline')
    priority = data.get('priority')

    # Validations
    if not name or not str(name).strip():
        return jsonify({"error": "Name must not be empty"}), 400
    if not deadline_str:
        return jsonify({"error": "Deadline must not be empty"}), 400
    if priority not in ['high', 'medium', 'low']:
        return jsonify({"error": "Priority must be high, medium, or low"}), 400

    try:
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        if deadline_date < date.today():
            return jsonify({"error": "Deadline must not be a past date"}), 400
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use YYYY-MM-DD"}), 400

    new_subject = {
        "name": name.strip(),
        "deadline": deadline_str,
        "priority": priority,
        "status": "pending"
    }

    try:
        # Insert into Supabase
        response = supabase.table('subjects').insert(new_subject).execute()
        return jsonify(response.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subjects/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    """Update subject by id in Supabase."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get('name')
    deadline_str = data.get('deadline')
    priority = data.get('priority')

    # Validations
    if not name or not str(name).strip():
        return jsonify({"error": "Name must not be empty"}), 400
    if not deadline_str:
        return jsonify({"error": "Deadline must not be empty"}), 400
    if priority not in ['high', 'medium', 'low']:
        return jsonify({"error": "Priority must be high, medium, or low"}), 400

    try:
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        if deadline_date < date.today():
            return jsonify({"error": "Deadline must not be a past date"}), 400
    except ValueError:
        return jsonify({"error": "Invalid deadline format. Use YYYY-MM-DD"}), 400

    update_data = {
        "name": name.strip(),
        "deadline": deadline_str,
        "priority": priority
    }

    try:
        # Check if subject exists
        check = supabase.table('subjects').select('id').eq('id', subject_id).execute()
        if not check.data:
            return jsonify({"error": "Subject not found"}), 404

        # Perform update
        response = supabase.table('subjects').update(update_data).eq('id', subject_id).execute()
        return jsonify(response.data[0]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subjects/<int:subject_id>', methods=['PATCH'])
def toggle_status(subject_id):
    """Toggle status between pending and done."""
    try:
        # Fetch current status
        check = supabase.table('subjects').select('status').eq('id', subject_id).execute()
        if not check.data:
            return jsonify({"error": "Subject not found"}), 404
        
        current_status = check.data[0]['status']
        new_status = 'done' if current_status == 'pending' else 'pending'

        # Update status
        response = supabase.table('subjects').update({"status": new_status}).eq('id', subject_id).execute()
        return jsonify(response.data[0]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    """Delete subject by id from Supabase."""
    try:
        # Check if exists
        check = supabase.table('subjects').select('id').eq('id', subject_id).execute()
        if not check.data:
            return jsonify({"error": "Subject not found"}), 404

        # Perform delete
        supabase.table('subjects').delete().eq('id', subject_id).execute()
        return jsonify({"message": "Subject deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

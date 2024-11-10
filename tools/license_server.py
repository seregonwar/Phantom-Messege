from flask import Flask, request, jsonify
from db_manager import LicenseDBManager
import jwt
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('LICENSE_SERVER_SECRET', 'your-secret-key')
db = LicenseDBManager()

def verify_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except:
        return None

@app.route('/api/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """Handle device heartbeat and system info updates"""
    data = request.json
    token = request.headers.get('Authorization')
    
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    hardware_id = data.get('hardware_id')
    license_key = data.get('license_key')
    system_info = data.get('system_info', {})
    
    # Aggiorna le informazioni del dispositivo
    db.update_device_info(hardware_id, system_info)
    
    # Controlla se ci sono comandi pendenti
    commands = db.get_pending_commands(hardware_id)
    
    return jsonify({
        'status': 'ok',
        'commands': commands
    })

@app.route('/api/device/command/result', methods=['POST'])
def command_result():
    """Handle command execution results"""
    data = request.json
    token = request.headers.get('Authorization')
    
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    command_id = data.get('command_id')
    status = data.get('status')
    
    db.update_command_status(command_id, status)
    
    return jsonify({'status': 'ok'})

@app.route('/api/admin/revoke', methods=['POST'])
def revoke_device():
    """Revoke a device license"""
    data = request.json
    token = request.headers.get('Authorization')
    
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    hardware_id = data.get('hardware_id')
    license_key = data.get('license_key')
    
    # Aggiungi comando di revoca
    db.add_remote_command(hardware_id, 'revoke', {
        'reason': data.get('reason', 'Administrative action')
    })
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc') 
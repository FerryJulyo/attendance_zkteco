import requests
import jwt
import json
from datetime import datetime

class APIClient:
    def __init__(self, base_url, jwt_secret):
        self.base_url = base_url
        self.jwt_secret = jwt_secret
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate JWT token"""
        payload = {
            'sub': 'TampanDanPemberani',
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def get_headers(self):
        """Get headers with authorization"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def get_last_sn_id(self, outlet, machine_id):
        """Get last SN ID from server"""
        try:
            url = f"{self.base_url}getLastSnID"
            params = {
                'outlet': outlet,
                'machine': machine_id
            }
            
            response = requests.get(url, params=params, headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                if data.get('state'):
                    return data.get('sn_id', 0)
            return 0
        except Exception as e:
            print(f"Error getting last SN ID: {e}")
            return 0
    
    def get_last_attendance_time(self, outlet, machine_id):
        """Get last attendance time from server"""
        try:
            url = f"{self.base_url}get_last_attendance"
            params = {
                'outlet': outlet,
                'machine': machine_id
            }
            
            response = requests.get(url, params=params, headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                if data.get('state'):
                    return data.get('attendance_time')
            return None
        except Exception as e:
            print(f"Error getting last attendance time: {e}")
            return None
    
    def send_attendance_data(self, attendance_data):
        """Send attendance data to server"""
        try:
            url = f"{self.base_url}inputData"
            
            payload = {
                'attendance_data': attendance_data
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            return response.json()
        except Exception as e:
            print(f"Error sending attendance data: {e}")
            return {'state': False, 'message': str(e)}
    
    def update_last_sync(self, outlet, machine_id, version="1.0"):
        """Update last sync time on server"""
        try:
            url = f"{self.base_url}getLastSync"
            
            payload = {
                'outlet': outlet,
                'machine': machine_id,
                'version': version
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers())
            return response.json()
        except Exception as e:
            print(f"Error updating last sync: {e}")
            return {'state': False, 'message': str(e)}
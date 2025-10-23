import socket
from pyzatt.zkmodules.packet import PacketMixin
from pyzatt.zkmodules.data_user import DataUserMixin
from pyzatt.zkmodules.data_record import DataRecordMixin
from pyzatt.zkmodules.terminal import TerminalMixin
from pyzatt.zkmodules.access import AccessMixin
from pyzatt.zkmodules.realtime import RealtimeMixin
from pyzatt.zkmodules.other import OtherMixin
from datetime import datetime
import struct

class ZKService(PacketMixin, DataUserMixin, DataRecordMixin, 
                TerminalMixin, AccessMixin, RealtimeMixin, OtherMixin):
    
    def __init__(self, ip, port=4370):
        self.ip = ip
        self.port = port
        self.sock = None
        self.reply_number = 0
        self.session_id = 0
        self.connected_flg = False
        self.users = {}
        self.att_log = []
    
    def connect(self):
        """Connect to ZKTeco device"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.ip, self.port))
            self.connected_flg = True
            
            # Connect to device
            self.connect_to_device()
            print(f"Connected to device at {self.ip}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        if self.sock:
            try:
                self.disconnect_device()
                self.sock.close()
            except:
                pass
        self.connected_flg = False
    
    def get_attendance_data(self, last_sn_id=0):
        """Get attendance data from device starting from last_sn_id"""
        if not self.connected_flg:
            print("Not connected to device")
            return []
        
        try:
            # Enable device
            self.enable_device()
            
            # Get attendance data
            attendance_data = []
            
            # Read attendance log
            self.read_size_att_log()
            
            for att_entry in self.att_log:
                # Convert to required format
                if att_entry.user_sn > last_sn_id:
                    attendance_record = {
                        'sn_id': att_entry.user_sn,
                        'user_id': att_entry.user_id,
                        'attendance_time': att_entry.att_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'ver_type': att_entry.ver_type,
                        'ver_state': att_entry.ver_state
                    }
                    attendance_data.append(attendance_record)
            
            # Sort by SN ID
            attendance_data.sort(key=lambda x: x['sn_id'])
            return attendance_data
            
        except Exception as e:
            print(f"Error reading attendance data: {e}")
            return []
    
    def get_new_attendance_data(self, last_sn_id, outlet, machine_id):
        """Get new attendance data and format for API"""
        raw_data = self.get_attendance_data(last_sn_id)
        
        formatted_data = []
        for record in raw_data:
            if record['sn_id'] > last_sn_id:
                formatted_record = {
                    'outlet': outlet,
                    'nip': record['user_id'],
                    'attendance_time': record['attendance_time'],
                    'sn_id': record['sn_id'],
                    'machine_id': machine_id
                }
                formatted_data.append(formatted_record)
        
        return formatted_data
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from config import Config
from api_client import APIClient
from zk_service import ZKService

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ZKTeco Attendance Sync")
        self.root.geometry("800x600")
        
        self.config = Config()
        self.api_client = None
        self.zk_service = None
        self.sync_thread = None
        self.sync_running = False
        
        self.setup_ui()
        self.load_config_to_ui()
        self.update_status("Aplikasi siap")
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Konfigurasi", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Outlet
        ttk.Label(config_frame, text="Outlet:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.outlet_entry = ttk.Entry(config_frame, width=30)
        self.outlet_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # Machine IP
        ttk.Label(config_frame, text="IP Mesin:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ip_entry = ttk.Entry(config_frame, width=30)
        self.ip_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # Machine ID
        ttk.Label(config_frame, text="ID Mesin:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.machine_id_entry = ttk.Entry(config_frame, width=30)
        self.machine_id_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # API URL
        ttk.Label(config_frame, text="API URL:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.api_url_entry = ttk.Entry(config_frame, width=30)
        self.api_url_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Simpan Konfigurasi", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Koneksi", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        # Sync section
        sync_frame = ttk.LabelFrame(main_frame, text="Sinkronisasi", padding="10")
        sync_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        sync_button_frame = ttk.Frame(sync_frame)
        sync_button_frame.pack(fill=tk.X, pady=5)
        
        self.sync_button = ttk.Button(sync_button_frame, text="Mulai Sinkronisasi", 
                                     command=self.toggle_sync)
        self.sync_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sync_button_frame, text="Sinkronisasi Sekarang", 
                  command=self.manual_sync).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sync_button_frame, text="Baca Data Absensi", 
                  command=self.read_attendance).pack(side=tk.LEFT, padx=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=15, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        config_frame.columnconfigure(1, weight=1)
        sync_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
    
    def load_config_to_ui(self):
        """Load configuration to UI"""
        self.outlet_entry.delete(0, tk.END)
        self.outlet_entry.insert(0, self.config.outlet)
        
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, self.config.machine_ip)
        
        self.machine_id_entry.delete(0, tk.END)
        self.machine_id_entry.insert(0, self.config.machine_id)
        
        self.api_url_entry.delete(0, tk.END)
        self.api_url_entry.insert(0, self.config.api_url)
    
    def save_config(self):
        """Save configuration"""
        try:
            self.config.update_config(
                outlet=self.outlet_entry.get(),
                machine_ip=self.ip_entry.get(),
                machine_id=self.machine_id_entry.get(),
                api_url=self.api_url_entry.get()
            )
            self.update_status("Konfigurasi disimpan")
            messagebox.showinfo("Sukses", "Konfigurasi berhasil disimpan")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan konfigurasi: {e}")
    
    def test_connection(self):
        """Test connection to device and API"""
        def test():
            self.update_status("Testing koneksi...")
            
            # Test device connection
            try:
                self.zk_service = ZKService(self.config.machine_ip)
                if self.zk_service.connect():
                    self.update_status("Koneksi ke device berhasil")
                    self.zk_service.disconnect()
                else:
                    self.update_status("Koneksi ke device gagal")
                    return
            except Exception as e:
                self.update_status(f"Error koneksi device: {e}")
                return
            
            # Test API connection
            try:
                self.api_client = APIClient(self.config.api_url, self.config.jwt_secret)
                last_sn = self.api_client.get_last_sn_id(self.config.outlet, self.config.machine_id)
                self.update_status(f"Koneksi API berhasil. Last SN ID: {last_sn}")
            except Exception as e:
                self.update_status(f"Error koneksi API: {e}")
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_sync(self):
        """Toggle automatic sync"""
        if not self.sync_running:
            self.start_sync()
        else:
            self.stop_sync()
    
    def start_sync(self):
        """Start automatic sync"""
        if not all([self.config.outlet, self.config.machine_ip, self.config.machine_id]):
            messagebox.showerror("Error", "Harap lengkapi konfigurasi terlebih dahulu")
            return
        
        self.sync_running = True
        self.sync_button.config(text="Stop Sinkronisasi")
        self.progress.start()
        self.update_status("Sinkronisasi otomatis dimulai")
        
        self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self.sync_thread.start()
    
    def stop_sync(self):
        """Stop automatic sync"""
        self.sync_running = False
        self.sync_button.config(text="Mulai Sinkronisasi")
        self.progress.stop()
        self.update_status("Sinkronisasi dihentikan")
    
    def sync_loop(self):
        """Main sync loop"""
        sync_interval = 60  # 1 minute
        
        while self.sync_running:
            try:
                self.sync_data()
                time.sleep(sync_interval)
            except Exception as e:
                self.update_status(f"Error dalam sync loop: {e}")
                time.sleep(sync_interval)
    
    def manual_sync(self):
        """Manual sync"""
        threading.Thread(target=self.sync_data, daemon=True).start()
    
    def sync_data(self):
        """Sync attendance data"""
        try:
            self.update_status("Memulai sinkronisasi...")
            
            # Initialize services
            self.api_client = APIClient(self.config.api_url, self.config.jwt_secret)
            self.zk_service = ZKService(self.config.machine_ip)
            
            # Connect to device
            if not self.zk_service.connect():
                self.update_status("Gagal terkoneksi ke device")
                return
            
            # Get last SN ID from server
            last_sn_id = self.api_client.get_last_sn_id(self.config.outlet, self.config.machine_id)
            self.update_status(f"Last SN ID dari server: {last_sn_id}")
            
            # Get new attendance data
            new_data = self.zk_service.get_new_attendance_data(
                last_sn_id, self.config.outlet, self.config.machine_id
            )
            
            self.update_status(f"Data absensi baru ditemukan: {len(new_data)} record")
            
            # Send data to server
            if new_data:
                result = self.api_client.send_attendance_data(new_data)
                if result.get('state'):
                    self.update_status(f"Berhasil mengirim {len(new_data)} data absensi")
                    
                    # Update last sync
                    self.api_client.update_last_sync(self.config.outlet, self.config.machine_id)
                    self.update_status("Last sync diperbarui")
                else:
                    self.update_status(f"Gagal mengirim data: {result.get('message')}")
            else:
                self.update_status("Tidak ada data absensi baru")
            
            # Disconnect from device
            self.zk_service.disconnect()
            
        except Exception as e:
            self.update_status(f"Error selama sinkronisasi: {e}")
    
    def read_attendance(self):
        """Read attendance data from device"""
        def read():
            try:
                self.update_status("Membaca data absensi dari device...")
                
                self.zk_service = ZKService(self.config.machine_ip)
                if not self.zk_service.connect():
                    self.update_status("Gagal terkoneksi ke device")
                    return
                
                attendance_data = self.zk_service.get_attendance_data()
                self.update_status(f"Total data absensi: {len(attendance_data)}")
                
                # Show last 10 records
                for record in attendance_data[-10:]:
                    self.update_status(
                        f"SN: {record['sn_id']}, User: {record['user_id']}, "
                        f"Time: {record['attendance_time']}"
                    )
                
                self.zk_service.disconnect()
                
            except Exception as e:
                self.update_status(f"Error membaca data absensi: {e}")
        
        threading.Thread(target=read, daemon=True).start()
    
    def update_status(self, message):
        """Update status text"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        def update_ui():
            self.status_text.insert(tk.END, formatted_message)
            self.status_text.see(tk.END)
            self.root.update()
        
        self.root.after(0, update_ui)

def main():
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
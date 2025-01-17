# Projektreferenz 1: https://docs.vudials.com/
# Projektreferenz 2: https://github.com/TomSchimansky/CustomTkinter
# Projektreferenz 3: https://github.com/gwy15/python_aida64

import os
import json
import requests
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from io import BytesIO
from python_aida64 import getData

# Initialize main app
class VU1GUI(ctk.CTk):
    def __init__(self):
        # Setze CustomTkinter Appearance Mode und Standard-Skalierung
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Hole System-Skalierung vor der Initialisierung
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics") as key:
                value = winreg.QueryValueEx(key, "AppliedDPI")[0]
                self.system_scaling = value / 96
        except:
            self.system_scaling = 1.0
            
        print(f"Detected system scaling: {self.system_scaling}")
        
        # Setze die CustomTkinter Skalierung
        ctk.set_widget_scaling(self.system_scaling)
        ctk.set_window_scaling(self.system_scaling)

        super().__init__()

        # Load saved settings first
        self.settings_file = "settings.json"
        self.settings = self.load_settings()

        # Set window title and minimum size
        self.title("VU1 GUI Prototype")
        
        # Keine Mindestgröße initial setzen
        # self.minsize(1170, 1100)  # Diese Zeile entfernen

        # Restore window size and position
        if all(key in self.settings for key in ["window_width", "window_height", "window_x", "window_y"]):
            # Skaliere die gespeicherten Werte zurück
            w = int(self.settings["window_width"] / self.system_scaling)
            h = int(self.settings["window_height"] / self.system_scaling)
            x = int(self.settings["window_x"])
            y = int(self.settings["window_y"])
            
            print(f"Window restoration:")
            print(f"- Original dimensions: {self.settings['window_width']}x{self.settings['window_height']}")
            print(f"- Scaled dimensions: {w}x{h}")
            
            geometry = f"{w}x{h}+{x}+{y}"
            self.geometry(geometry)
            print(f"Set geometry to: {geometry}")
        else:
            # Starte ohne explizite Größe
            self.geometry("+100+100")  # Nur Position setzen

        self.server_address = ctk.StringVar(value=self.settings.get("server_address", "http://localhost:5340"))
        self.api_key = ctk.StringVar(value=self.settings.get("api_key", ""))

        # Dictionary to hold widget references
        self.dial_widgets = {}
        self.sensor_assignments = {}  # Dictionary to hold sensor assignments
        self.update_interval = 1000  # Update interval in milliseconds (1 second)
        self.min_values = {}  # Dictionary to hold min values for each dial
        self.max_values = {}  # Dictionary to hold max values for each dial
        self.assignments_file = "assignments.json"  # File to store sensor assignments and value ranges

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid to expand with window size
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Load sensor assignments and value ranges
        self.load_assignments()

        # Fetch AIDA64 data on startup
        self.aida64_data = self.fetch_aida64_data()

        # Main layout
        self.create_main_layout()

        # Fetch all details on startup
        self.fetch_all_dial_details()

        # Apply loaded assignments
        self.apply_loaded_assignments()

        self.schedule_sensor_updates()

        # Stattdessen die neue Methode verwenden
        self.after(100, self.adjust_window_size)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Debug: Screen Info nach super().__init__()
        print(f"Screen Info:")
        print(f"- Physical size: {self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        print(f"- Available geometry: {self.winfo_vrootwidth()}x{self.winfo_vrootheight()}")
        print(f"- Scaling factor: {self.winfo_fpixels('1i') / 96.0}")

    def get_scaling_factor(self):
        try:
            from ctypes import windll
            from ctypes.wintypes import HMONITOR
            from ctypes import c_int
            
            # Get the monitor where the window is
            monitor = windll.user32.MonitorFromWindow(self.winfo_id(), 0)
            
            # Get DPI
            x_dpi = c_int()
            y_dpi = c_int()
            windll.shcore.GetDpiForMonitor(monitor, 0, x_dpi, y_dpi)
            
            return x_dpi.value / 96.0
        except:
            return 1.0

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as file:
                settings = json.load(file)
                print(f"\nLoading Settings Debug:")
                print(f"Loaded raw settings: {settings}")
                
                # Validiere Werte
                screen_w = self.winfo_screenwidth()
                screen_h = self.winfo_screenheight()
                print(f"Screen bounds: {screen_w}x{screen_h}")
                
                if all(key in settings for key in ["window_width", "window_height", "window_x", "window_y"]):
                    w = settings["window_width"]
                    h = settings["window_height"]
                    x = settings["window_x"]
                    y = settings["window_y"]
                    print(f"Geometry validation:")
                    print(f"- Width: {w} (valid: {100 <= w <= screen_w})")
                    print(f"- Height: {h} (valid: {100 <= h <= screen_h})")
                    print(f"- X: {x} (valid: {0 <= x < screen_w})")
                    print(f"- Y: {y} (valid: {0 <= y < screen_h})")
                
                return settings
        return {}

    def save_settings(self):
        # Skaliere die Werte beim Speichern
        w = int(self.winfo_width() * self.system_scaling)
        h = int(self.winfo_height() * self.system_scaling)
        x = self.winfo_x()
        y = self.winfo_y()
        
        print(f"\nSaving geometry:")
        print(f"- Window size: {self.winfo_width()}x{self.winfo_height()}")
        print(f"- Scaled size: {w}x{h}")
        
        settings = {
            "server_address": self.server_address.get(),
            "api_key": self.api_key.get(),
            "window_width": w,
            "window_height": h,
            "window_x": x,
            "window_y": y
        }
        with open(self.settings_file, "w") as file:
            json.dump(settings, file)
            print(f"Settings saved: {settings}")

    def create_main_layout(self):
        """Hauptlayout der Anwendung erstellen"""
        # Top-Level-Widgets
        ctk.CTkLabel(self.main_frame, text="VU1 GUI Prototype", font=("Arial", 18)).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Settings", command=self._show_settings_dialog).pack(pady=10)
        
        # Frame for dials
        self.dials_frame = ctk.CTkFrame(self.main_frame)
        self.dials_frame.pack(pady=10, fill="both", expand=True)
        
        ctk.CTkButton(self.main_frame, text="Fetch AIDA64 Data", command=self.display_aida64_data).pack(pady=10)
        
        # Nach dem Erstellen des Layouts die optimale Größe setzen
        self.after(100, self.adjust_window_size)

    def _show_settings_dialog(self):
        """Zeigt den Einstellungs-Dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("400x300")
        dialog.transient(self)  # Dialog immer im Vordergrund des Hauptfensters
        dialog.grab_set()  # Modal machen
        
        # Inhalte
        ctk.CTkLabel(dialog, text="Server Address:").pack(pady=5)
        ctk.CTkEntry(dialog, textvariable=self.server_address).pack(pady=5)
        
        ctk.CTkLabel(dialog, text="API Key:").pack(pady=5)
        ctk.CTkEntry(dialog, textvariable=self.api_key).pack(pady=5)
        
        # Save Button
        ctk.CTkButton(dialog, text="Save", 
                     command=lambda: self._save_settings_dialog(dialog)).pack(pady=20)
        
        # Zentriere Dialog relativ zum Hauptfenster
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def _save_settings_dialog(self, dialog):
        """Speichert die Einstellungen und schließt den Dialog"""
        self.save_settings()
        self.save_assignments()
        dialog.destroy()
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def adjust_window_size(self):
        """Passt die Fenstergröße an den tatsächlichen Inhalt an"""
        # Aktualisiere alle Widgets
        self.update_idletasks()
        
        # Hole die benötigte Größe für alle Widgets
        required_width = self.main_frame.winfo_reqwidth()
        required_height = self.main_frame.winfo_reqheight()
        
        # Füge einen kleinen Puffer hinzu
        width = required_width + 50
        height = required_height + 50
        
        # Setze vernünftige Mindestgrößen
        min_width = 800
        min_height = 600
        
        # Verwende die größeren Werte
        final_width = max(width, min_width)
        final_height = max(height, min_height)
        
        print(f"Adjusting window size:")
        print(f"- Required: {required_width}x{required_height}")
        print(f"- Final: {final_width}x{final_height}")
        
        # Behalte die aktuelle Position bei
        x = self.winfo_x()
        y = self.winfo_y()
        
        # Setze neue Geometrie
        self.geometry(f"{final_width}x{final_height}+{x}+{y}")
        
        # Setze Mindestgröße nachdem der Inhalt bekannt ist
        self.minsize(final_width, final_height)

    def fetch_all_dial_details(self):
        url = f"{self.server_address.get()}/api/v0/dial/list"
        params = {"key": self.api_key.get()}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            response_data = response.json()

            # Extract the list of dials from the "data" key
            dials = response_data.get("data", [])

            if not isinstance(dials, list):
                raise ValueError("API response 'data' is not a list. Received: " + json.dumps(response_data, indent=4))

            for widget in self.dials_frame.winfo_children():
                widget.destroy()

            for index, dial in enumerate(dials):
                details = self.fetch_dial_details(dial['uid'])
                self.create_dial_widget(details, dial['uid'])

            self.after(100, self.adjust_window_size)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch dials: {e}")

        # Nach dem Laden der Dials Größe anpassen
        self.after(100, self.adjust_window_size)

    def fetch_dial_details(self, dial_id):
        endpoints = {
            "image": f"dial/{dial_id}/image/get",
            "backlight": f"dial/{dial_id}/status",
            "name": f"dial/{dial_id}/status",
            "easing": f"dial/{dial_id}/status",
        }

        details = {}

        for key, endpoint in endpoints.items():
            try:
                url = f"{self.server_address.get()}/api/v0/{endpoint}"
                params = {"key": self.api_key.get()}

                headers = {}
                if key in ["name", "backlight", "easing"]:
                    headers["Accept"] = "application/json"

                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                if key == "image":
                    if response.headers.get('Content-Type') == 'image/png':
                        details[key] = response.content  # Save raw image data
                    else:
                        details[key] = "Invalid image format"
                else:
                    details[key] = response.json()
            except Exception as e:
                details[key] = f"Error fetching {key}: {e}"

        return details

    def create_dial_widget(self, details, dial_id):
        if dial_id in self.dial_widgets:
            widget_frame = self.dial_widgets[dial_id]
            for widget in widget_frame.winfo_children():
                widget.destroy()
        else:
            widget_frame = ctk.CTkFrame(self.dials_frame, corner_radius=10, width=200, height=300)
            widget_frame.pack_propagate(False)
            widget_frame.pack(side="left", padx=10, pady=10, fill="both", expand=True)
            self.dial_widgets[dial_id] = widget_frame

        # Display Dial ID
        ctk.CTkLabel(widget_frame, text=f"Dial ID: {dial_id}", font=("Arial", 14)).pack(pady=5)

        # Display image
        if "image" in details and isinstance(details["image"], bytes):
            self.display_image(details["image"], widget_frame)

        # Add button to set image
        set_image_button = ctk.CTkButton(widget_frame, text="Set Image", command=lambda: self.set_image_for_dial(dial_id))
        set_image_button.pack(pady=(0, 10))

        # Display details with labels above fields
        if "name" in details:
            name_data = details['name']
            if isinstance(name_data, dict):
                dial_name = name_data.get('data', {}).get('dial_name', 'N/A')
                ctk.CTkLabel(widget_frame, text="Name:").pack(pady=(10, 0))
                name_entry = ctk.CTkEntry(widget_frame, textvariable=ctk.StringVar(value=dial_name), border_color="gray", width=150)
                name_entry.pack(pady=5)

                save_name_button = ctk.CTkButton(widget_frame, text="Save Name", command=lambda: self.set_dial_name(dial_id, name_entry.get()))
                save_name_button.pack(pady=5)

        if "backlight" in details:
            backlight_data = details['backlight']
            if isinstance(backlight_data, dict):
                backlight = backlight_data.get('data', {}).get('backlight', {})
                red = self.convert_to_rgb(backlight.get('red', 'N/A'))
                green = self.convert_to_rgb(backlight.get('green', 'N/A'))
                blue = self.convert_to_rgb(backlight.get('blue', 'N/A'))
                ctk.CTkLabel(widget_frame, text="Backlight:").pack(pady=(10, 0))
                backlight_frame = ctk.CTkFrame(widget_frame)
                backlight_frame.pack(pady=5, fill="x")

                # Textvariablen anlegen
                red_var = ctk.StringVar(value=red)
                green_var = ctk.StringVar(value=green)
                blue_var = ctk.StringVar(value=blue)
                hex_var = ctk.StringVar(value=self.rgb_to_hex(int(red), int(green), int(blue)))

                # RGB-Eingabefelder
                ctk.CTkLabel(backlight_frame, text="R:").grid(row=0, column=0, padx=5)
                red_entry = ctk.CTkEntry(backlight_frame, textvariable=red_var, border_color="gray", width=40)
                red_entry.grid(row=0, column=1, padx=5)

                ctk.CTkLabel(backlight_frame, text="G:").grid(row=0, column=2, padx=5)
                green_entry = ctk.CTkEntry(backlight_frame, textvariable=green_var, border_color="gray", width=40)
                green_entry.grid(row=0, column=3, padx=5)

                ctk.CTkLabel(backlight_frame, text="B:").grid(row=0, column=4, padx=5)
                blue_entry = ctk.CTkEntry(backlight_frame, textvariable=blue_var, border_color="gray", width=40)
                blue_entry.grid(row=0, column=5, padx=5)

                # HEX-Eingabefeld
                ctk.CTkLabel(backlight_frame, text="HEX:").grid(row=1, column=0, padx=5, pady=5)
                hex_entry = ctk.CTkEntry(backlight_frame, textvariable=hex_var, border_color="gray", width=100)
                hex_entry.grid(row=1, column=1, columnspan=5, padx=5)

                # Callbacks zur Synchronisierung
                callback_ids = {"r": None, "g": None, "b": None, "hex": None}

                def on_rgb_change(*_):
                    try:
                        r = int(red_var.get()) 
                        g = int(green_var.get())
                        b = int(blue_var.get())
                        new_hex = self.rgb_to_hex(r, g, b)
                        if callback_ids["hex"]:
                            hex_var.trace_vdelete("w", callback_ids["hex"])
                            callback_ids["hex"] = None
                        hex_var.set(new_hex)
                        callback_ids["hex"] = hex_var.trace("w", on_hex_change)
                    except ValueError:
                        pass

                def on_hex_change(*_):
                    try:
                        h = hex_var.get()
                        r, g, b = self.hex_to_rgb(h)
                        for color_key, var in [("r", red_var), ("g", green_var), ("b", blue_var)]:
                            if callback_ids[color_key]:
                                var.trace_vdelete("w", callback_ids[color_key])
                                callback_ids[color_key] = None
                        red_var.set(str(r))
                        green_var.set(str(g))
                        blue_var.set(str(b))
                        callback_ids["r"] = red_var.trace("w", on_rgb_change)
                        callback_ids["g"] = green_var.trace("w", on_rgb_change)
                        callback_ids["b"] = blue_var.trace("w", on_rgb_change)
                    except ValueError:
                        pass

                # Registriere die Callbacks
                callback_ids["r"] = red_var.trace("w", on_rgb_change)
                callback_ids["g"] = green_var.trace("w", on_rgb_change)
                callback_ids["b"] = blue_var.trace("w", on_rgb_change)
                callback_ids["hex"] = hex_var.trace("w", on_hex_change)

                # Button mit Textvariablen
                save_backlight_button = ctk.CTkButton(
                    widget_frame,
                    text="Set Backlight",
                    command=lambda: self.set_backlight(
                        dial_id,
                        red_var.get(),
                        green_var.get(),
                        blue_var.get(),
                        hex_var.get()
                    )
                )
                save_backlight_button.pack(pady=5)

        if "easing" in details:
            easing_data = details['easing']
            if isinstance(easing_data, dict):
                easing = easing_data.get('data', {}).get('easing', {})
                dial_step = easing.get('dial_step', 'N/A')
                dial_period = easing.get('dial_period', 'N/A')
                backlight_step = easing.get('backlight_step', 'N/A')
                backlight_period = easing.get('backlight_period', 'N/A')
                ctk.CTkLabel(widget_frame, text="Easing:").pack(pady=(10, 0))

                easing_frame = ctk.CTkFrame(widget_frame)
                easing_frame.pack(pady=5, fill="x")

                ctk.CTkLabel(easing_frame, text="Step:").grid(row=0, column=0, padx=5)
                step_entry = ctk.CTkEntry(easing_frame, textvariable=ctk.StringVar(value=dial_step), border_color="gray", width=40)
                step_entry.grid(row=0, column=1, padx=5)

                ctk.CTkLabel(easing_frame, text="Period:").grid(row=0, column=2, padx=5)
                period_entry = ctk.CTkEntry(easing_frame, textvariable=ctk.StringVar(value=dial_period), border_color="gray", width=40)
                period_entry.grid(row=0, column=3, padx=5)

                save_easing_button = ctk.CTkButton(widget_frame, text="Set Easing", command=lambda: self.set_easing(dial_id, step_entry.get(), period_entry.get()))
                save_easing_button.pack(pady=5)

        # Create dropdown for AIDA64 sensors
        if self.aida64_data:
            sensor_options = [f"{item['label']} ({item['id']})" for item in self.aida64_data.get('temp', [])]
            selected_sensor = ctk.StringVar(value=sensor_options[0] if sensor_options else "")
            ctk.CTkLabel(widget_frame, text="AIDA64 Sensor:").pack(pady=(10, 0))
            sensor_dropdown = ctk.CTkOptionMenu(widget_frame, variable=selected_sensor, values=sensor_options, width=100)
            sensor_dropdown.pack(pady=5)
            save_sensor_button = ctk.CTkButton(widget_frame, text="Assign Sensor", command=lambda: self.assign_sensor_to_dial(dial_id, selected_sensor.get()))
            save_sensor_button.pack(pady=5)

        # Add min and max value entries
        ctk.CTkLabel(widget_frame, text="Min Value:").pack(pady=(10, 0))
        min_value_entry = ctk.CTkEntry(widget_frame, textvariable=ctk.StringVar(value="0"), border_color="gray", width=50)
        min_value_entry.pack(pady=5)
        ctk.CTkLabel(widget_frame, text="Max Value:").pack(pady=(10, 0))
        max_value_entry = ctk.CTkEntry(widget_frame, textvariable=ctk.StringVar(value="100"), border_color="gray", width=50)
        max_value_entry.pack(pady=5)
        save_range_button = ctk.CTkButton(widget_frame, text="Save Range", command=lambda: self.set_value_range(dial_id, min_value_entry.get(), max_value_entry.get()))
        save_range_button.pack(pady=5)

        # Update the main window size
        self.update_idletasks()
        print(f"Window size after creating dial widgets: {self.winfo_width()}x{self.winfo_height()}")  # Debug-Ausgabe

    def set_value_range(self, dial_id, min_value, max_value):
        self.min_values[dial_id] = float(min_value)
        self.max_values[dial_id] = float(max_value)
        self.save_assignments()

    def assign_sensor_to_dial(self, dial_id, sensor):
        # Assign the selected sensor to the dial
        self.sensor_assignments[dial_id] = sensor
        self.update_dial_with_sensor_data(dial_id)
        self.save_assignments()

    def update_dial_with_sensor_data(self, dial_id):
        # Füge Fehlerbehandlung hinzu
        try:
            sensor = self.sensor_assignments.get(dial_id)
            if not sensor:
                return
                
            sensor_id = sensor.split('(')[-1].strip(')')
            sensor_data = next((item for item in self.aida64_data.get('temp', []) 
                              if item['id'] == sensor_id), None)
            
            if sensor_data and 'value' in sensor_data:
                value = float(sensor_data['value'])
                min_value = self.min_values.get(dial_id, 0)
                max_value = self.max_values.get(dial_id, 100)
                mapped_value = self.map_value_to_range(value, min_value, max_value)
                self.set_dial_value(dial_id, mapped_value)
        except Exception as e:
            print(f"Error updating dial {dial_id}: {e}")

    def map_value_to_range(self, value, min_value, max_value):
        return max(0, min(100, (value - min_value) / (max_value - min_value) * 100))

    def set_dial_value(self, dial_id, value):
        url = f"{self.server_address.get()}/api/v0/dial/{dial_id}/set"
        params = {"key": self.api_key.get(), "value": value}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Dial ID: {dial_id}: {e}")

    def schedule_sensor_updates(self):
        self.aida64_data = self.fetch_aida64_data()  # Daten von AIDA64 bei jedem Update neu abrufen
        self.update_all_dials()
        self.after(self.update_interval, self.schedule_sensor_updates)

    def update_all_dials(self):
        for dial_id in self.sensor_assignments.keys():
            self.update_dial_with_sensor_data(dial_id)

    def display_image(self, image_data, parent):
        try:
            image = Image.open(BytesIO(image_data))
            if image.size[0] > 200 or image.size[1] > 144:
                image = image.resize((200, 144))
            # Konvertiere zu CTkImage
            photo = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            image_label = ctk.CTkLabel(parent, image=photo, text="")
            image_label.image = photo
            image_label.pack(pady=10)
        except Exception as e:
            error_label = ctk.CTkLabel(parent, text=f"Failed to display image: {e}")
            error_label.pack(pady=10)

    def set_image_for_dial(self, dial_id):
        file_path = filedialog.askopenfilename(filetypes=[("PNG/JPG/JPEG Images", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        # Validate file type
        if not file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            messagebox.showerror("Error", "Invalid file type. Please select a PNG, JPG, or JPEG file.")
            return

        url = f"{self.server_address.get()}/api/v0/dial/{dial_id}/image/set"
        params = {"key": self.api_key.get()}
        try:
            with open(file_path, "rb") as image_file:
                files = {"imgfile": image_file}  # Correct parameter name
                response = requests.post(url, params=params, files=files)
                response.raise_for_status()

            messagebox.showinfo("Success", f"Image successfully set for Dial ID: {dial_id}")

            # Refresh the dial details to reflect the updated image
            updated_details = self.fetch_dial_details(dial_id)
            self.create_dial_widget(updated_details, dial_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to set image for Dial ID: {dial_id}: {e}")

    def set_dial_name(self, dial_id, new_name):
        url = f"{self.server_address.get()}/api/v0/dial/{dial_id}/name"
        params = {"key": self.api_key.get(), "name": new_name}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            messagebox.showinfo("Success", f"Name successfully updated for Dial ID: {dial_id}")

            # Refresh the dial details to reflect the updated name
            updated_details = self.fetch_dial_details(dial_id)
            self.create_dial_widget(updated_details, dial_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to set name for Dial ID: {dial_id}: {e}")

    def set_backlight(self, dial_id, red, green, blue, hex_value):
        # Nutze nur dann HEX, wenn es nicht leer oder "#000000" ist
        if hex_value and hex_value.strip() and hex_value.strip().lower() != "#000000":
            red, green, blue = self.hex_to_rgb(hex_value)
        else:
            try:
                red = int(red)
                green = int(green)
                blue = int(blue)
            except ValueError:
                messagebox.showerror("Error", "Invalid RGB values. Please enter valid integers.")
                return

        # Debug-Ausgabe der konvertierten Werte
        red_percent = self.convert_to_0_100(red)
        green_percent = self.convert_to_0_100(green)
        blue_percent = self.convert_to_0_100(blue)
        print(f"Converted RGB to percent: red={red_percent}, green={green_percent}, blue={blue_percent}")

        url = f"{self.server_address.get()}/api/v0/dial/{dial_id}/backlight"
        params = {
            "key": self.api_key.get(),
            "red": red_percent,  # Konvertiere zu Prozentwerten
            "green": green_percent,
            "blue": blue_percent
        }
        try:
            print(f"Setting backlight for Dial ID {dial_id} with params: {params}")  # Debug-Ausgabe hinzufügen
            response = requests.get(url, params=params)
            response.raise_for_status()

            messagebox.showinfo("Success", f"Backlight successfully updated for Dial ID: {dial_id}")

        except Exception as e:
            print(f"Failed to set backlight for Dial ID {dial_id}: {e}")  # Debug-Ausgabe hinzufügen
            messagebox.showerror("Error", f"Failed to set backlight for Dial ID: {dial_id}: {e}")

    def set_easing(self, dial_id, step, period):
        url = f"{self.server_address.get()}/api/v0/dial/{dial_id}/easing_dial"
        params = {
            "key": self.api_key.get(),
            "step": step,
            "period": period
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            messagebox.showinfo("Success", f"Easing successfully updated for Dial ID: {dial_id}")

            # Refresh the dial details to reflect the updated easing
            updated_details = self.fetch_dial_details(dial_id)
            self.create_dial_widget(updated_details, dial_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to set easing for Dial ID: {dial_id}: {e}")

    def fetch_aida64_data(self):
        try:
            data = getData()
            return data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch AIDA64 data: {e}")
            return {}

    def display_aida64_data(self):
        data = self.fetch_aida64_data()
        if data:
            formatted_data = "\n".join([f"{item['label']}: {item['value']}°C" for item in data.get('temp', [])])
            messagebox.showinfo("AIDA64 Data", formatted_data)

    @staticmethod
    def convert_to_0_100(value):
        # Konvertiere den Wert von 0-255 zu 0-100
        return max(0, min(100, round((value / 255) * 100)))

    @staticmethod
    def convert_to_rgb(value):
        return max(0, min(255, round((value / 100) * 255)))

    @staticmethod
    def rgb_to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}".upper()

    @staticmethod
    def hex_to_rgb(hex_value):
        hex_value = hex_value.lstrip('#')
        return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))

    def save_assignments(self):
        data = {
            "sensor_assignments": self.sensor_assignments,
            "min_values": self.min_values,
            "max_values": self.max_values
        }
        with open(self.assignments_file, "w") as file:
            json.dump(data, file)

    def load_assignments(self):
        if os.path.exists(self.assignments_file):
            with open(self.assignments_file, "r") as file:
                data = json.load(file)
                self.sensor_assignments = data.get("sensor_assignments", {})
                self.min_values = data.get("min_values", {})
                self.max_values = data.get("max_values", {})

    def apply_loaded_assignments(self):
        for dial_id in self.sensor_assignments.keys():
            self.update_dial_with_sensor_data(dial_id)
            details = self.fetch_dial_details(dial_id)
            self.create_dial_widget(details, dial_id)
            self.update_dial_widget_with_assignments(dial_id, details)
        self.after(100, self.adjust_window_size)

    def update_dial_widget_with_assignments(self, dial_id, details):
        widget_frame = self.dial_widgets[dial_id]

        # Update min and max value entries
        min_value = self.min_values.get(dial_id, 0)
        max_value = self.max_values.get(dial_id, 100)
        for widget in widget_frame.winfo_children():
            if isinstance(widget, ctk.CTkEntry) and widget.get() == "0":
                widget.delete(0, "end")
                widget.insert(0, str(min_value))
            elif isinstance(widget, ctk.CTkEntry) and widget.get() == "100":
                widget.delete(0, "end")
                widget.insert(0, str(max_value))

        # Update sensor dropdown
        sensor = self.sensor_assignments.get(dial_id, "")
        for widget in widget_frame.winfo_children():
            if isinstance(widget, ctk.CTkOptionMenu):
                widget.set(sensor)

    def on_close(self):
        # Aktualisiere die Einstellungen mit der aktuellen Fenstergeometrie
        current_geometry = self.geometry()
        self.settings.update({
            "window_width": self.winfo_width(),
            "window_height": self.winfo_height(),
            "window_x": self.winfo_x(),
            "window_y": self.winfo_y(),
            "server_address": self.server_address.get(),
            "api_key": self.api_key.get()
        })
        
        print(f"Saving window geometry: {self.winfo_width()}x{self.winfo_height()}+{self.winfo_x()}+{self.winfo_y()}")
        self.save_settings()
        self.destroy()

# Run application
if __name__ == "__main__":  # Korrigiert: == Operator hinzugefügt
    app = VU1GUI()
    app.mainloop()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import json
import hid
import time
import sys

LILY58_VENDOR_ID = 0x04D8
LILY58_PRODUCT_ID = 0xEB2D
VIA_PROTOCOL_VERSION = 0x0C  # VIA protocol version

# VIA protocol commands
VIA_COMMAND_START = 0x00
VIA_COMMAND_OLED = 0x40  # Custom command for OLED
VIA_COMMAND_GET_PROTOCOL_VERSION = 0x01
VIA_COMMAND_GET_KEYBOARD_VALUE = 0x02

def debug_print(msg):
    """Print debug messages to console."""
    print(f"DEBUG: {msg}")

class OLED_Configurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Lily58 OLED Configurator")
        self.root.geometry("1000x800")
        
        # OLED display settings
        self.oled_width = 128
        self.oled_height = 32
        self.preview_scale = 2
        
        # HID device
        self.device = None
        
        # Configure style
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[12, 8])
        style.configure('TButton', padding=6)
        
        # Setup HID connection
        self.setup_hid_connection()
        
        # Create main notebook for left and right OLED
        self.main_notebook = ttk.Notebook(root)
        self.main_notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create frames for each OLED
        self.left_oled_frame = ttk.Frame(self.main_notebook)
        self.right_oled_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.left_oled_frame, text='Left OLED')
        self.main_notebook.add(self.right_oled_frame, text='Right OLED')
        
        # Setup each OLED's interface
        self.setup_oled_interface(self.left_oled_frame, "left")
        self.setup_oled_interface(self.right_oled_frame, "right")
    
    def setup_hid_connection(self):
        # HID connection frame
        hid_frame = ttk.LabelFrame(self.root, text="Keyboard Connection", padding=10)
        hid_frame.pack(fill='x', padx=10, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Not Connected")
        ttk.Label(hid_frame, textvariable=self.status_var).pack(side='left', padx=5)
        
        # Connect button
        self.connect_btn = ttk.Button(hid_frame, text="Connect to Lily58",
                                    command=self.connect_hid)
        self.connect_btn.pack(side='left', padx=5)
        
        # Debug info
        self.debug_var = tk.StringVar(value="")
        ttk.Label(hid_frame, textvariable=self.debug_var).pack(side='left', padx=5)
    
    def connect_hid(self):
        try:
            debug_print("Searching for Lily58 keyboard...")
            # Find all HID devices
            devices = list(hid.enumerate(LILY58_VENDOR_ID, LILY58_PRODUCT_ID))
            debug_print(f"Found {len(devices)} matching devices")
            
            for device_info in devices:
                debug_print(f"Attempting to connect to device: {device_info['path']}")
                try:
                    self.device = hid.Device(path=device_info['path'])
                    debug_print("Device opened successfully")
                    
                    # Try to get protocol version
                    version = self.get_protocol_version()
                    if version is not None:
                        self.status_var.set("Connected to Lily58")
                        self.debug_var.set(f"Protocol: {version}")
                        messagebox.showinfo("Success", f"Connected to Lily58 keyboard (Protocol: {version})")
                        return
                    
                    # Close device if protocol version check failed
                    self.device.close()
                    self.device = None
                    debug_print("Failed to get protocol version")
                    
                except Exception as e:
                    debug_print(f"Failed to open device: {str(e)}")
                    if self.device:
                        self.device.close()
                        self.device = None
                    continue
            
            if not self.device:
                self.status_var.set("Lily58 not found")
                messagebox.showwarning("Not Found", 
                    "Lily58 keyboard not found.\nPlease check the connection.")
            
        except Exception as e:
            self.status_var.set("Connection failed")
            debug_print(f"Connection error: {str(e)}")
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")
            if self.device:
                self.device.close()
            self.device = None

    def get_protocol_version(self):
        """Get VIA protocol version from keyboard."""
        try:
            # Standard VIA protocol version request
            command = [0x00, VIA_COMMAND_GET_PROTOCOL_VERSION] + [0] * 30
            debug_print(f"Sending VIA protocol version command: {command}")
            self.device.write(bytes(command))
            
            # Read response
            response = self.read_with_timeout()
            if response:
                debug_print(f"Got response: {list(response)}")
                if len(response) >= 3:
                    version = response[2]  # VIA protocol version is in third byte
                    debug_print(f"Protocol version: {version}")
                    return version
            
            debug_print("No valid protocol version found")
            return None
            
        except Exception as e:
            debug_print(f"Error getting protocol version: {str(e)}")
            return None

    def read_with_timeout(self, timeout=1.0):
        """Read HID report with timeout."""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            try:
                # Read without timeout parameter
                response = self.device.read(32)
                if response:
                    debug_print(f"Read response: {list(response)}")
                    return response
            except Exception as e:
                debug_print(f"Read error: {str(e)}")
            time.sleep(0.01)
        debug_print("Read timeout")
        return None

    def setup_oled_interface(self, parent_frame, oled_side):
        # Create notebook for this OLED
        notebook = ttk.Notebook(parent_frame)
        notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        text_frame = ttk.Frame(notebook)
        image_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text='Text Mode')
        notebook.add(image_frame, text='Image Mode')
        
        # Initialize frames
        self.setup_text_mode(text_frame, oled_side)
        self.setup_image_mode(image_frame, oled_side)
    
    def setup_text_mode(self, parent, oled_side):
        # Text input frame
        input_frame = ttk.LabelFrame(parent, text="Text Input", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # Text entry
        text_var = tk.StringVar()
        setattr(self, f"{oled_side}_text_var", text_var)
        ttk.Label(input_frame, text="Enter Text:").pack(anchor='w')
        text_entry = ttk.Entry(input_frame, textvariable=text_var)
        text_entry.pack(fill='x', pady=5)
        
        # Position and rotation controls
        controls_frame = ttk.Frame(input_frame)
        controls_frame.pack(fill='x', pady=5)
        
        # Position controls
        pos_frame = ttk.LabelFrame(controls_frame, text="Position", padding=5)
        pos_frame.pack(side='left', padx=5)
        
        ttk.Label(pos_frame, text="X:").pack(side='left')
        text_x = ttk.Entry(pos_frame, width=5)
        text_x.pack(side='left', padx=5)
        text_x.insert(0, "0")
        setattr(self, f"{oled_side}_text_x", text_x)
        
        ttk.Label(pos_frame, text="Y:").pack(side='left')
        text_y = ttk.Entry(pos_frame, width=5)
        text_y.pack(side='left', padx=5)
        text_y.insert(0, "0")
        setattr(self, f"{oled_side}_text_y", text_y)
        
        # Rotation control
        rot_frame = ttk.LabelFrame(controls_frame, text="Rotation", padding=5)
        rot_frame.pack(side='left', padx=5)
        
        rotation_var = tk.IntVar(value=0)
        setattr(self, f"{oled_side}_text_rotation", rotation_var)
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            ttk.Radiobutton(rot_frame, text=f"{angle}°", 
                          variable=rotation_var, 
                          value=angle).pack(side='left', padx=2)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        preview_canvas = tk.Canvas(preview_frame,
                                 width=self.oled_width * self.preview_scale,
                                 height=self.oled_height * self.preview_scale,
                                 bg='black')
        preview_canvas.pack(pady=10)
        setattr(self, f"{oled_side}_text_preview", preview_canvas)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Preview",
                  command=lambda: self.update_text_preview(oled_side)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Apply to OLED",
                  command=lambda: self.apply_text_to_oled(oled_side)).pack(side='left', padx=5)
    
    def setup_image_mode(self, parent, oled_side):
        # Image controls frame
        controls_frame = ttk.LabelFrame(parent, text="Image Controls", padding=10)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Image selection
        ttk.Button(controls_frame, text="Select Image",
                  command=lambda: self.select_image(oled_side)).pack(side='left', pady=5, padx=5)
        
        # Rotation control
        rot_frame = ttk.LabelFrame(controls_frame, text="Rotation", padding=5)
        rot_frame.pack(side='left', padx=5)
        
        rotation_var = tk.IntVar(value=0)
        setattr(self, f"{oled_side}_image_rotation", rotation_var)
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            ttk.Radiobutton(rot_frame, text=f"{angle}°",
                          variable=rotation_var,
                          value=angle).pack(side='left', padx=2)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        preview_canvas = tk.Canvas(preview_frame,
                                 width=self.oled_width * self.preview_scale,
                                 height=self.oled_height * self.preview_scale,
                                 bg='black')
        preview_canvas.pack(pady=10)
        setattr(self, f"{oled_side}_image_preview", preview_canvas)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Apply to OLED",
                  command=lambda: self.apply_image_to_oled(oled_side)).pack(side='left', padx=5)
    
    def select_image(self, oled_side):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.bmp *.gif")])
        if file_path:
            try:
                # Open and convert image
                image = Image.open(file_path)
                
                # Apply rotation
                rotation = getattr(self, f"{oled_side}_image_rotation").get()
                if rotation:
                    image = image.rotate(-rotation, expand=True)
                
                # Resize to fit OLED dimensions
                image = image.resize((self.oled_width, self.oled_height))
                # Convert to monochrome
                image = image.convert('1')
                
                # Create preview
                preview = image.resize((self.oled_width * self.preview_scale,
                                     self.oled_height * self.preview_scale))
                preview_image = ImageTk.PhotoImage(preview)
                
                # Store references
                setattr(self, f"{oled_side}_preview_image", preview_image)
                setattr(self, f"{oled_side}_current_image", image)
                
                # Update preview
                preview_canvas = getattr(self, f"{oled_side}_image_preview")
                preview_canvas.create_image(0, 0, anchor='nw', 
                                         image=preview_image)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def update_text_preview(self, oled_side):
        # Create a new image for preview
        image = Image.new('1', (self.oled_width, self.oled_height), 0)
        draw = ImageDraw.Draw(image)
        
        try:
            x = int(getattr(self, f"{oled_side}_text_x").get())
            y = int(getattr(self, f"{oled_side}_text_y").get())
            text = getattr(self, f"{oled_side}_text_var").get()
            rotation = getattr(self, f"{oled_side}_text_rotation").get()
            
            # Create rotated text image
            if rotation:
                # Create a temporary image for rotation
                temp_img = Image.new('1', (self.oled_width, self.oled_height), 0)
                temp_draw = ImageDraw.Draw(temp_img)
                temp_draw.text((x, y), text, fill=1)
                # Rotate the image
                image = temp_img.rotate(-rotation, expand=False)
            else:
                draw.text((x, y), text, fill=1)
            
            # Scale up for preview
            preview = image.resize((self.oled_width * self.preview_scale,
                                 self.oled_height * self.preview_scale))
            preview_image = ImageTk.PhotoImage(preview)
            
            # Store references
            setattr(self, f"{oled_side}_preview_text_image", preview_image)
            setattr(self, f"{oled_side}_current_text_image", image)
            
            # Update preview
            preview_canvas = getattr(self, f"{oled_side}_text_preview")
            preview_canvas.create_image(0, 0, anchor='nw',
                                     image=preview_image)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid X/Y coordinates")
    
    def send_to_oled(self, image_data, oled_side):
        if not self.device:
            messagebox.showerror("Error", "Not connected to Lily58")
            return False
        
        try:
            # Convert image data to bytes
            pixels = list(image_data.getdata())
            bytes_data = []
            for i in range(0, len(pixels), 8):
                byte = 0
                for bit in range(8):
                    if i + bit < len(pixels):
                        byte |= (pixels[i + bit] > 0) << (7 - bit)
                bytes_data.append(byte)
            
            # Send data in chunks with VIA protocol
            chunk_size = 28  # 32 - 4 bytes for header
            total_chunks = (len(bytes_data) + chunk_size - 1) // chunk_size
            
            for chunk_index in range(total_chunks):
                start_idx = chunk_index * chunk_size
                end_idx = min(start_idx + chunk_size, len(bytes_data))
                chunk = bytes_data[start_idx:end_idx]
                
                # Prepare VIA command
                command = [
                    0x00,  # Report ID
                    VIA_COMMAND_OLED,  # OLED command
                    0x01 if oled_side == "left" else 0x02,  # OLED selection
                    chunk_index,  # Chunk index
                ]
                
                # Add chunk data
                command.extend(chunk)
                
                # Pad to 32 bytes
                while len(command) < 32:
                    command.append(0)
                
                # Send command
                debug_print(f"Sending chunk {chunk_index}: {command}")
                self.device.write(bytes(command))
                
                # Wait for acknowledgment
                response = self.read_with_timeout(timeout=0.5)
                if not response:
                    raise TimeoutError(f"Device did not acknowledge chunk {chunk_index}")
                debug_print(f"Chunk {chunk_index} acknowledged: {response}")
                
                # Small delay between chunks
                time.sleep(0.01)
            
            # Send completion command
            completion_command = [
                0x00,  # Report ID
                VIA_COMMAND_OLED,  # OLED command
                0x01 if oled_side == "left" else 0x02,  # OLED selection
                0xFF,  # Completion marker
            ]
            completion_command.extend([0] * 28)  # Pad to 32 bytes
            
            debug_print(f"Sending completion command: {completion_command}")
            self.device.write(bytes(completion_command))
            
            # Wait for final acknowledgment
            response = self.read_with_timeout(timeout=0.5)
            if not response:
                raise TimeoutError("Device did not acknowledge completion")
            debug_print(f"Completion acknowledged: {response}")
            
            return True
            
        except TimeoutError as e:
            messagebox.showerror("Error", str(e))
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send to OLED: {str(e)}")
            return False
    
    def apply_text_to_oled(self, oled_side):
        if hasattr(self, f"{oled_side}_current_text_image"):
            if self.send_to_oled(getattr(self, f"{oled_side}_current_text_image"), oled_side):
                messagebox.showinfo("Success", f"Text sent to {oled_side} OLED")
        else:
            messagebox.showwarning("Warning", "Please preview text first")
    
    def apply_image_to_oled(self, oled_side):
        if hasattr(self, f"{oled_side}_current_image"):
            if self.send_to_oled(getattr(self, f"{oled_side}_current_image"), oled_side):
                messagebox.showinfo("Success", f"Image sent to {oled_side} OLED")
        else:
            messagebox.showwarning("Warning", "Please select an image first")
    
    def cleanup(self):
        """Clean up resources when closing the application."""
        if self.device:
            self.device.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = OLED_Configurator(root)
    
    # Cleanup on window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

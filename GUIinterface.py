import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import re
from GeminiProcessing import generate_ur_script
from ur10econtrol import robot as ur10e
from Transcriber import start_listening, stop_listening
from webots_interface import move_robot_in_webots

# Define all functions first
def update_robot_status():
    """Updates the robot connection status indicator."""
    if ur10e.connected:
        robot_status.config(text="🟢 Real Robot: Connected")
    else:
        robot_status.config(text="🔴 Real Robot: Disconnected")

def connect_to_robot():
    """Attempts to connect to the real UR10e robot."""
    if ur10e.connect():
        update_robot_status()
        messagebox.showinfo("Success", "Connected to UR10e robot!")
    else:
        messagebox.showerror("Error", "Failed to connect to UR10e robot!")

def send_to_real_robot():
    """Sends the generated URScript to the real UR10e robot."""
    if not ur10e.connected and not ur10e.connect():
        messagebox.showerror("Error", "Not connected to robot! Check connection and try again.")
        return

    ur_script = script_output.get("1.0", tk.END).strip()
    if not ur_script:
        messagebox.showwarning("Warning", "No URScript generated!")
        return

    # Save and send the script
    with open("GeneratedURScript.urscript", "w") as f:
        f.write(ur_script)
    
    result = ur10e.send_script()
    if "✅" in result:
        messagebox.showinfo("Success", "Command sent to robot!")
    else:
        messagebox.showerror("Error", result)

def update_transcribed_text(text_widget):
    """Reads transcribed text from file and updates the input field."""
    try:
        with open("TranscribedText.txt", "r", encoding="utf-8") as file:
            text = file.read().strip()
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, text)
    except FileNotFoundError:
        messagebox.showerror("Error", "No transcribed text found!")

def process_command(text_widget):
    """Handles text input, sends to Gemini, and displays URScript."""
    command_text = text_widget.get("1.0", tk.END).strip()
    if not command_text:
        messagebox.showwarning("Warning", "No text found!")
        return

    ur_script = generate_ur_script(command_text)
    script_output.delete("1.0", tk.END)
    script_output.insert(tk.END, ur_script)
    messagebox.showinfo("Success", "URScript generated successfully!")

def send_to_webots():
    """Extracts pose values from URScript and sends them to Webots simulation."""
    ur_script = script_output.get("1.0", tk.END).strip()
    target_positions = extract_joint_positions(ur_script)

    if target_positions:
        threading.Thread(target=move_robot_in_webots, args=(target_positions,), daemon=True).start()
        messagebox.showinfo("Success", "Sent movement commands to Webots!")
    else:
        messagebox.showerror("Error", "Failed to extract valid movement commands from URScript.")

def extract_joint_positions(ur_script):
    """
    Extracts joint angles from the URScript.
    Handles both direct joint angles and TCP poses.
    """
    print("URScript received for extraction:")
    print(ur_script)  # Debug output

    # First try to find movej command with joint angles - more flexible pattern
    joint_match = re.search(r'movej\s*\(\s*\[\s*([0-9\-., ]+)\s*\]', ur_script)
    if joint_match:
        try:
            positions = [float(x) for x in joint_match.group(1).split(",")]
            print("✅ Extracted joint positions:", positions)
            return positions[:6]  # Return only the first 6 joint values
        except Exception as e:
            print("❌ Error converting joint positions:", e)
            return None

    # If no joint angles found, try to find TCP pose
    pose_match = re.search(r'pose_trans\s*\(.*p\s*\[\s*([0-9\-., ]+)\s*\]', ur_script)
    if pose_match:
        try:
            # Convert TCP pose to approximate joint angles
            tcp_pose = [float(x) for x in pose_match.group(1).split(",")]
            print("ℹ️ Found TCP pose:", tcp_pose)
            
            # Extract x, y, z from TCP pose
            x, y, z = tcp_pose[0], tcp_pose[1], tcp_pose[2]
            
            # Convert TCP pose to joint angles with improved Z-axis handling
            joint_angles = [
                x,                    # Base rotation (from x coordinate)
                -1.0 - (z * 0.5),    # Shoulder lift (adjust for height)
                1.2 + (z * 0.5),     # Elbow (compensate for shoulder)
                -0.2 * z,            # Wrist 1 (adjust for height)
                y * 0.5,             # Wrist 2 (from y coordinate)
                tcp_pose[5]          # Wrist 3 (keep original rotation)
            ]
            
            # Ensure joint angles are within safe limits
            joint_angles = [
                max(min(angle, 3.14), -3.14) for angle in joint_angles
            ]
            
            print("✅ Converted to joint angles:", joint_angles)
            print("📏 Z-axis movement:", z)
            return joint_angles
        except Exception as e:
            print("❌ Error converting TCP pose:", e)
            return None

    print("⚠️ No valid movement commands found in URScript.")
    return None

# GUI Setup
root = tk.Tk()
root.title("UR10e Speech-to-Command Interface")
root.geometry("1000x800")
root.configure(bg="#1E1E1E")

# Modern Styling
button_style = {"font": ("Arial", 12, "bold"), "bg": "#0078D7", "fg": "white", "width": 25, "height": 2, "bd": 3, "relief": "raised"}
label_style = {"font": ("Arial", 16, "bold"), "fg": "white", "bg": "#1E1E1E"}
text_style = {"font": ("Arial", 14), "bg": "#2D2D2D", "fg": "white", "insertbackground": "white", "height": 10, "width": 70, "bd": 2, "relief": "sunken"}

# Status Frame
status_frame = tk.Frame(root, bg="#1E1E1E")
status_frame.pack(fill=tk.X, padx=10, pady=5)

# Status indicators
robot_status = tk.Label(status_frame, text="🔴 Real Robot: Disconnected", font=("Arial", 12), bg="#1E1E1E", fg="white")
robot_status.pack(side=tk.LEFT, padx=5)

webots_status = tk.Label(status_frame, text="🔵 Webots: Ready", font=("Arial", 12), bg="#1E1E1E", fg="white")
webots_status.pack(side=tk.LEFT, padx=5)

# Input Section
input_frame = tk.LabelFrame(root, text="Command Input", bg="#1E1E1E", fg="white", font=("Arial", 14, "bold"))
input_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(input_frame, text="Voice or Text Command:", **label_style).pack(pady=5)
text_input = scrolledtext.ScrolledText(input_frame, **text_style)
text_input.pack(pady=5)

# Voice Control Buttons
voice_frame = tk.Frame(input_frame, bg="#1E1E1E")
voice_frame.pack(pady=5)
tk.Button(voice_frame, text="🎤 Start Recording", command=lambda: threading.Thread(target=start_listening, daemon=True).start(), **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(voice_frame, text="⏹️ Stop Recording", command=stop_listening, **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(voice_frame, text="📝 Load Transcribed Text", command=lambda: update_transcribed_text(text_input), **button_style).pack(side=tk.LEFT, padx=5)

# URScript Generation
script_frame = tk.LabelFrame(root, text="Generated URScript", bg="#1E1E1E", fg="white", font=("Arial", 14, "bold"))
script_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Button(script_frame, text="🔄 Generate URScript", command=lambda: process_command(text_input), **button_style).pack(pady=5)
script_output = scrolledtext.ScrolledText(script_frame, **text_style)
script_output.pack(pady=5)

# Robot Control Section
control_frame = tk.LabelFrame(root, text="Robot Control", bg="#1E1E1E", fg="white", font=("Arial", 14, "bold"))
control_frame.pack(fill=tk.X, padx=10, pady=5)

# Create two columns for Webots and Real Robot
columns_frame = tk.Frame(control_frame, bg="#1E1E1E")
columns_frame.pack(fill=tk.X, padx=10, pady=5)

# Webots Column
webots_frame = tk.LabelFrame(columns_frame, text="Webots Simulation", bg="#1E1E1E", fg="white", font=("Arial", 12, "bold"))
webots_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

tk.Button(webots_frame, text="🤖 Simulate in Webots", 
         command=lambda: threading.Thread(target=send_to_webots, daemon=True).start(), 
         **button_style).pack(pady=10)

# Real Robot Column
real_robot_frame = tk.LabelFrame(columns_frame, text="Real UR10e Robot", bg="#1E1E1E", fg="white", font=("Arial", 12, "bold"))
real_robot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

tk.Button(real_robot_frame, text="🔌 Connect to UR10e", 
         command=connect_to_robot, 
         **button_style).pack(pady=5)
tk.Button(real_robot_frame, text="📤 Send to Real Robot", 
         command=send_to_real_robot, 
         **button_style).pack(pady=5)

def run_gui():
    """Runs the GUI application."""
    update_robot_status()  # Initial status update
    root.mainloop()

if __name__ == "__main__":
    run_gui()

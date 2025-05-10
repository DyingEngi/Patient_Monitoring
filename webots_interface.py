import os
import subprocess

# Use absolute path for command file in Webots project directory
WEBOTS_DIR = r"C:\Users\Toh Er Yuen\AppData\Local\Programs\Webots\projects\default\controllers\UR10eController"
COMMAND_FILE = os.path.join(WEBOTS_DIR, "webots_commands.txt")

def move_robot_in_webots(joint_positions=None):
    """Sends UR10e joint positions to Webots simulation."""
    
    # Ensure Webots is running
    webots_path = r"C:\Users\Toh Er Yuen\AppData\Local\Programs\Webots\msys64\mingw64\bin\webotsw.exe"

    if not os.path.exists(webots_path):
        print(f"❌ Webots executable not found at {webots_path}. Check the installation path.")
        return

    # Write the joint positions to file if they are provided
    if joint_positions:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(COMMAND_FILE), exist_ok=True)
            
            with open(COMMAND_FILE, "w") as f:
                # Convert positions to joint angles if needed
                joint_str = ",".join(map(str, joint_positions))
                f.write(joint_str)
            print(f"✅ Command written to Webots: {joint_positions}")
            print(f"📁 File location: {COMMAND_FILE}")
        except Exception as e:
            print(f"❌ Error writing to command file: {e}")
            return

    # Start Webots if not already running
    try:
        subprocess.Popen([webots_path], shell=True)
        print("✅ Webots started successfully.")
    except Exception as e:
        print(f"❌ Error starting Webots: {e}")

import socket
import os
import time
from Config import ROBOT_IP, PORT

class UR10eRealRobot:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        # Common UR ports
        self.ports = {
            'dashboard': 29999,   # Dashboard server
            'primary': 30002,     # Primary interface (URScript)
            'custom': PORT        # Custom port from config
        }

    def try_connect_port(self, port, description):
        """Try to connect to a specific port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            print(f"📡 Trying {description} port {port}...")
            sock.connect((ROBOT_IP, port))
            print(f"✅ Successfully connected to {description} port!")
            return sock
        except Exception as e:
            print(f"⚠️ Could not connect to {description} port {port}: {e}")
            return None

    def connect(self):
        """Establishes connection to the UR10e robot."""
        print(f"🔄 Attempting to connect to UR10e at {ROBOT_IP}")
        
        # First try dashboard to check robot state
        dashboard = self.try_connect_port(self.ports['dashboard'], "dashboard")
        if dashboard:
            try:
                # Read welcome message
                data = dashboard.recv(1024)
                print(f"Dashboard: {data.decode().strip()}")
                dashboard.close()
            except:
                pass

        # Try primary URScript port first
        self.socket = self.try_connect_port(self.ports['primary'], "primary URScript")
        
        # If primary fails, try custom port
        if not self.socket and self.ports['custom'] != self.ports['primary']:
            print("Trying custom port...")
            self.socket = self.try_connect_port(self.ports['custom'], "custom URScript")

        if self.socket:
            try:
                # Test the connection with a simple program
                test_program = """def check_connection():
    textmsg("Connection test")
end
check_connection()
"""
                self.socket.sendall(test_program.encode())
                self.connected = True
                print("✅ URScript connection test successful!")
                return True
            except Exception as e:
                print(f"❌ Failed to send test program: {e}")
                self.disconnect()
                return False
        
        print("\n⚠️ Connection troubleshooting steps:")
        print("1. On the UR Pendant:")
        print("   - Go to 'Installation' → 'Network'")
        print(f"   - Verify the IP address matches {ROBOT_IP}")
        print("   - Check that URScript ports (30002 or custom) are enabled")
        print("2. In the Program:")
        print("   - Make sure you have an 'External Control' node")
        print("   - The program should be running (press play)")
        print("3. Robot State:")
        print("   - Should be in 'Remote Control' mode")
        print("   - No protective stops or popups active")
        print("4. Network:")
        print(f"   - Try pinging {ROBOT_IP}")
        print("   - Check firewall settings")
        
        return False

    def disconnect(self):
        """Safely closes the connection."""
        if self.socket:
            try:
                # Send a stop command before disconnecting
                self.socket.sendall("stopj(2)\n".encode())
                time.sleep(0.1)
                self.socket.close()
            except Exception as e:
                print(f"⚠️ Error during disconnect: {e}")
            finally:
                self.socket = None
                self.connected = False
                print("🔌 Disconnected from UR10e")

    def send_script(self, script_file="GeneratedURScript.urscript"):
        """Sends a URScript file to the robot."""
        if not os.path.exists(script_file):
            return "❌ Error: URScript file not found."

        try:
            # Read URScript from the file
            with open(script_file, "r") as f:
                script = f.read()

            if not self.connected and not self.connect():
                return "❌ Error: Not connected to robot"

            # Send the script
            print("📤 Sending script to robot...")
            print("Script contents:")
            print(script)
            self.socket.sendall(script.encode())
            print("✅ Script sent successfully!")
            return "✅ URScript sent to UR10e successfully!"

        except Exception as e:
            print(f"❌ Error sending script: {e}")
            self.disconnect()
            return f"❌ Error: {e}"

    def send_immediate_command(self, command):
        """Sends a single URScript command immediately."""
        if not self.connected and not self.connect():
            return False

        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            print("📤 Sending command:")
            print(command)
            self.socket.sendall(command.encode())
            return True
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            self.disconnect()
            return False

# Create a global robot instance
robot = UR10eRealRobot()

def send_to_robot(script_file="GeneratedURScript.urscript"):
    """Main function to send URScript to the robot."""
    return robot.send_script(script_file)

# Test the connection when module is run directly
if __name__ == "__main__":
    if robot.connect():
        print("\nTesting robot movement...")
        test_script = """def program():
    # Simple movement test with sequence
    popup("Starting movement sequence", "Info", blocking=True)
    
    # Step 1: Move base joint
    textmsg("Step 1: Moving base joint")
    movej([0.5, 0, 0, 0, 0, 0], a=0.4, v=1.05)
    sleep(1)
    
    # Step 2: Move shoulder joint
    textmsg("Step 2: Moving shoulder joint")
    movej([0.5, -0.5, 0, 0, 0, 0], a=0.4, v=1.05)
    sleep(1)
    
    # Step 3: Move elbow joint
    textmsg("Step 3: Moving elbow joint")
    movej([0.5, -0.5, 0.5, 0, 0, 0], a=0.4, v=1.05)
    sleep(1)
    
    # Return to start position
    textmsg("Returning to start position")
    movej([0, 0, 0, 0, 0, 0], a=0.4, v=1.05)
    
    popup("Movement sequence completed", "Info", blocking=True)
end

program()
"""
        print("Sending test script...")
        print(test_script)
        robot.send_immediate_command(test_script)
        print("Waiting for movement to complete...")
        time.sleep(15)  # Give more time for the sequence to complete
        robot.disconnect()
    else:
        print("\n❌ Could not establish connection to robot")

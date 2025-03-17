import google.generativeai as genai
from Config import GEMINI_API_KEY

# Set up the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def generate_ur_script(command_text):
    """Takes a command and generates URScript that moves from the current position."""
    if not command_text:
        return "Error: No command provided."

    prompt = f"""
    Generate URScript for a UR10e robot based on this command: "{command_text}"
    
    The script MUST follow this structure and safety guidelines:

    def program():
        # Safety check
        if get_robot_mode() != 7:
            popup("Robot not in running mode", "Error", blocking=True)
            halt
        end
        
        # Get current position
        current_joints = get_actual_joint_positions()
        textmsg("Current position: " + str(current_joints))
        
        # Main movement sequence
        popup("Starting movement sequence", "Info", blocking=True)
        
        # Interpret the command and generate appropriate movements
        # Use these safe parameters for ALL movements:
        # - acceleration (a) = 0.4
        # - velocity (v) = 1.05
        # - maximum joint movement = 0.5 radians
        # - move one joint at a time
        # - include sleep(1) between movements
        
        # Example movement structure:
        # textmsg("Step 1: Moving [joint name]")
        # movej([joint1, joint2, joint3, joint4, joint5, joint6], a=0.4, v=1.05)
        # sleep(1)
        
        # Return to start position
        textmsg("Returning to start position")
        movej(current_joints, a=0.4, v=1.05)
        
        popup("Movement sequence completed", "Info", blocking=True)
    end
    
    program()

    IMPORTANT:
    1. The script MUST start with "def program():"
    2. MUST include safety check for robot mode
    3. MUST get and store current position
    4. MUST include popup messages for user feedback
    5. MUST include textmsg for step-by-step feedback
    6. MUST use movej commands with safe parameters (a=0.4, v=1.05)
    7. MUST include sleep(1) between movements
    8. MUST return to start position
    9. MUST end with "end" and "program()"
    10. Use ONLY these commands: popup, textmsg, movej, sleep, get_actual_joint_positions
    11. Keep movements small and safe (max 0.5 radians per joint)
    12. Move one joint at a time for safety
    13. Interpret the command naturally but maintain safe movement patterns
    14. Add descriptive text messages for each movement step
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        ur_script = response.text.strip() if response else "Error: Could not generate script."

        # Clean up the response to ensure it's valid URScript
        ur_script = ur_script.replace("```", "").replace("urscript", "").strip()
        
        # Post-process to ensure valid structure
        if not ur_script.startswith("def program():"):
            ur_script = f"def program():\n{ur_script}"
        
        if "end" not in ur_script:
            ur_script += "\nend"
        
        if not ur_script.endswith("program()"):
            ur_script += "\nprogram()"
        
        # Ensure proper indentation
        lines = ur_script.split('\n')
        processed_lines = []
        for i, line in enumerate(lines):
            if i == 0:  # First line (def program():)
                processed_lines.append(line)
            elif line.strip().startswith('end'):  # end statement
                processed_lines.append(line)
            elif line.strip().startswith('program()'):  # program() call
                processed_lines.append(line)
            else:  # All other lines
                processed_lines.append('    ' + line.strip())
        
        ur_script = '\n'.join(processed_lines)
        
        # Save URScript to a file
        with open("GeneratedURScript.urscript", "w", encoding="utf-8") as f:
            f.write(ur_script)

        return ur_script
    except Exception as e:
        return f"Error: {e}"

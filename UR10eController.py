from controller import Robot

class UR10eController:
    def __init__(self):
        """Initialize the Webots controller for UR10e."""
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())

        # Get UR10e joints
        self.joint_names = [
            "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
            "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"
        ]
        self.motors = [self.robot.getDevice(name) for name in self.joint_names]

        # Set initial positions and velocities
        for motor in self.motors:
            motor.setPosition(0)  # Start position
            motor.setVelocity(1.0)  # Allow movement

    def move_joints(self, target_positions):
        """Move UR10e's joints to target positions (radians)."""
        for motor, pos in zip(self.motors, target_positions):
            motor.setPosition(pos)

    def run(self):
        """Main control loop for Webots simulation."""
        target_positions = [1.0, -1.0, 0.5, -0.5, 0.3, -0.3]  # Example movement

        while self.robot.step(self.timestep) != -1:
            self.move_joints(target_positions)  # Move UR10e

if __name__ == "__main__":
    controller = UR10eController()
    controller.run()

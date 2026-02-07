# TeleopStatus.msg

# Remote Teleop Module Enabled Check
# 0: Disabled, 1: Enabled
uint8 remote_enabled

# Current Control Mode
# 0: Hardware Remote (RC)
# 1: Autonomous (Nav)
# 2: Remote UDP (Teleop)
# -1: Idle (No Command)
int8 current_mode

# Topic Activity Status
bool nav_active
bool teleop_active
bool final_active

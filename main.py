"""
Weapon Blast & 3D Tactical Strike Simulation
Launcher entry point for was_test7.py
"""
import os
import sys

def run():
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "was_test7.py")
    if not os.path.exists(target):
        print(f"Error: {target} not found!", file=sys.stderr)
        sys.exit(1)
    
    with open(target, "r", encoding="utf-8") as f:
        code = compile(f.read(), target, "exec")
        exec(code, {"__name__": "__main__", "__file__": target})

if __name__ == "__main__":
    run()

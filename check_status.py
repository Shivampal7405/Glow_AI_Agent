from main import GLOW
import sys

# Mock input to avoid interactive setup if config is missing (though it exists)
sys.argv = ["main.py", "--mode", "text"]
assistant = GLOW()
assistant._print_status()

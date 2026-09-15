# pytest configuration
# Tests run with: pytest tests/

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

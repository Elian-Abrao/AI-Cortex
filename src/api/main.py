from .gateway import app

import sys
from pathlib import Path

# Adiciona 'src/' ao PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
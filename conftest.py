import sys
import os

# Garante que a raiz do projeto está no path para imports como 'from src.transform import ...'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

"""Launcher de conveniencia desde la raíz del proyecto para GryPhus Conect Gerencia."""
import os
import sys

app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gryphus_conect_gerencia')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
os.chdir(app_dir)

from main import main

if __name__ == '__main__':
    main()

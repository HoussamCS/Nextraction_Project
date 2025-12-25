import subprocess
import sys

python_path = r"C:\Users\PC\AppData\Local\Python\pythoncore-3.14-64\python.exe"
subprocess.run([python_path, "-m", "pip", "install", "-q", "-r", "requirements.txt"], cwd=r"C:\Users\PC\Desktop\Nextraction_Project")
subprocess.run([python_path, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=r"C:\Users\PC\Desktop\Nextraction_Project")

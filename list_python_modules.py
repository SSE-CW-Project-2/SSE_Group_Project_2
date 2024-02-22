import os
import sys

def list_python_modules():
    pythonpath = os.getenv('PYTHONPATH')
    if not pythonpath:
        print("PYTHONPATH is not set.")
        sys.exit(1)

    paths = pythonpath.split(os.pathsep)
    for path in paths:
        print(f"Modules in {path}:")
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        print(f" - {os.path.join(root, file)}")
        else:
            print(f"Path {path} does not exist.")

if __name__ == "__main__":
    list_python_modules()
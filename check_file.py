import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    pptx_path = "target.pptx"
    if os.path.exists(pptx_path):
        size = os.path.getsize(pptx_path)
        print(f"File exists. Size: {size} bytes")
    else:
        print("File does not exist.")
        print("Directory contents:")
        for f in os.listdir("."):
            print(f)

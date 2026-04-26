import zipfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    pptx_path = "target.pptx"
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            print("Zip file is valid. Contents (first 10):")
            for name in z.namelist()[:10]:
                print(name)
    except Exception as e:
        print(f"Zip error: {e}")

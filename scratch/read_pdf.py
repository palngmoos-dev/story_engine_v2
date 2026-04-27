import pdfplumber
import sys

# Force UTF-8 for output
sys.stdout.reconfigure(encoding='utf-8')

def extract_pdf_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total Pages: {len(pdf.pages)}")
            print("-" * 50)
            
            # Extract text from the first 5 pages for summary
            for i in range(min(10, len(pdf.pages))):
                page = pdf.pages[i]
                text = page.extract_text()
                print(f"--- Page {i+1} ---")
                if text:
                    print(text)
                else:
                    print("[No text found on this page]")
                print("-" * 50)
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    pdf_file = r"C:\Users\moos\Desktop\안은희 고객님 고품격 프랑스 여행 일정.pdf"
    extract_pdf_text(pdf_file)

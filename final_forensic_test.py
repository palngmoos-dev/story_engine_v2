import os
import sys
import json

# Final Forensic Harness Test
sys.path.append(r"d:\아름다운 여행 4.25\Atelier\scripts")
from pptx_forensic_engine import PPTXForensicEngine

def run_final_test():
    print("Running Final Forensic Test: Perfect Reconstruction")
    
    root = r"d:\아름다운 여행 4.25"
    spec_path = os.path.join(root, "forensic_design_scan.json")
    
    # Find the most complex template for testing
    template_dir = os.path.join(root, "견본 4.25")
    templates = [f for f in os.listdir(template_dir) if f.endswith(".pptx")]
    template_path = os.path.join(template_dir, sorted(templates, key=lambda x: os.path.getsize(os.path.join(template_dir, x)), reverse=True)[0])
    
    # Initialize Forensic Engine
    engine = PPTXForensicEngine(template_path, spec_path)
    
    # Select slide 0 (Title) and slide 5 (Spot Detail) to test
    # In V3, we modify the existing presentation directly for this test
    # to show cloning/replacement.
    
    # Sample mapping for reconstruction
    img_path = r"C:\Users\moos\.gemini\antigravity\brain\2fb7398c-27ff-4ae5-b026-1f183e98301a\uffizi_gallery_sample_1777081061383.png"
    
    # We will try to replace content on the 1st slide
    mapping = {
        "TextBox 7": "2026 이탈리아 피렌체 감성 여행",
        "TextBox 11": "안티그래비티 마스터 시스템 가동 중",
        "Text Box 19": "2026.04.25 ~ 04.30"
    }
    
    engine.replace_content_forensically(engine.prs.slides[0], mapping)
    
    # Save Output
    output_path = os.path.join(root, "final_forensic_test.pptx")
    engine.save(output_path)
    print(f"Final Forensic Test complete. Saved to: {output_path}")

if __name__ == "__main__":
    run_final_test()

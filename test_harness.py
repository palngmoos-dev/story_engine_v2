import os
import sys
import json
from datetime import datetime

# Add scripts directory to path
sys.path.append(r"d:\아름다운 여행 4.25\Atelier\scripts")
from pptx_master_system_v2 import PPTXMasterSystemV2

def run_test():
    print("Starting Harness Test: Florence 1-Day Trip")
    
    # 1. Paths
    root = r"d:\아름다운 여행 4.25"
    spec_path = os.path.join(root, "master_design_specs.json")
    
    # Find template
    template_dir = os.path.join(root, "견본 4.25")
    templates = [f for f in os.listdir(template_dir) if f.endswith(".pptx")]
    template_path = os.path.join(template_dir, templates[0])
    
    # 2. Simulated Data (from pptx_data_processor)
    # Using the generated image path
    img_path = r"C:\Users\moos\.gemini\antigravity\brain\2fb7398c-27ff-4ae5-b026-1f183e98301a\uffizi_gallery_sample_1777081061383.png"
    
    test_data = [
        {
            "layout_type": "Spot Detail",
            "title": "우피치 미술관 (Galleria degli Uffizi)",
            "placeholders": {
                "10": "르네상스 예술의 보고로 보티첼리, 미켈란젤로 등 거장의 작품을 감상할 수 있습니다.\n운영시간: 08:15 ~ 18:30 (월요일 휴관)\n입장료: 성인 25유로 (2026년 기준)",
                "12": img_path,
                "13": img_path # Placeholder
            },
            "version": "rent"
        }
    ]
    
    # 3. Initialize Engine
    engine = PPTXMasterSystemV2(template_path, spec_path)
    
    # 4. Generate Slide
    for slide_data in test_data:
        engine.generate_slide(slide_data)
        
    # 5. Save Output
    output_path = os.path.join(root, "test_output_florence.pptx")
    engine.save(output_path)
    print(f"Test PPT saved to: {output_path}")

if __name__ == "__main__":
    run_test()

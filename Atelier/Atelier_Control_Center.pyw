import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
from datetime import datetime

# Add system_core to path
sys.path.append(r"d:\아름다운 여행 4.25\Atelier\system_core")
from run_harness_system import run_pipeline

class AtelierUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 ATELIER - 100% Sync PPTX System")
        self.root.geometry("500x350")
        self.root.configure(bg="#f0f0f0")

        # Title
        label = tk.Label(root, text="Atelier Master System", font=("Malgun Gothic", 20, "bold"), bg="#f0f0f0", fg="#333")
        label.pack(pady=20)

        # Status
        self.status_label = tk.Label(root, text="시스템 대기 중...", font=("Malgun Gothic", 10), bg="#f0f0f0", fg="blue")
        self.status_label.pack(pady=5)

        # Buttons
        btn_style = {"font": ("Malgun Gothic", 12), "width": 25, "height": 2}
        
        self.btn_input = tk.Button(root, text="1. 입력 폴더 열기 (텍스트 넣기)", command=self.open_input, **btn_style)
        self.btn_input.pack(pady=10)

        self.btn_run = tk.Button(root, text="2. PPTX 자동 제작 시작 (100% Sync)", command=self.run_system, bg="#4CAF50", fg="white", **btn_style)
        self.btn_run.pack(pady=10)

        self.btn_output = tk.Button(root, text="3. 결과 폴더 열기 (PPTX 확인)", command=self.open_output, **btn_style)
        self.btn_output.pack(pady=10)

    def open_input(self):
        os.startfile(r"d:\아름다운 여행 4.25\Atelier\input_space")

    def open_output(self):
        os.startfile(r"d:\아름다운 여행 4.25\Atelier\output_space")

    def run_system(self):
        self.status_label.config(text="작업 중... 잠시만 기다려주세요 (100% 싱크 모드)", fg="orange")
        self.root.update()
        try:
            # Run the core logic
            run_pipeline()
            messagebox.showinfo("성공", "100% 싱크 PPTX 제작이 완료되었습니다!\n결과 폴더를 확인하세요.")
            self.status_label.config(text="작업 완료!", fg="green")
            self.open_output()
        except Exception as e:
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다: {e}")
            self.status_label.config(text="오류 발생", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = AtelierUI(root)
    root.mainloop()

import os
from . import wizard_engine as wizard
from . import draft_manager as dm

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_story(story_data):
    print("\n" + "="*50)
    print(f"[STEP 1: STORY RECOMMENDATION]")
    print("="*50)
    print(f"CATEGORY: {story_data['genre']}")
    print(f"HOOK: {story_data['one_liner']}")
    print(f"SUMMARY: {story_data['plot']}")
    print(f"REASON: {story_data['reason']}")
    print("-"*50)

def display_character(char_data):
    print("\n" + "="*50)
    print(f"[STEP 2: LEAD CHARACTER CARD]")
    print("="*50)
    print(f"- NAME: {char_data['name']} ({char_data['age']} yrs, {char_data['gender']})")
    print(f"- MBTI: {char_data['mbti']}")
    print(f"- JOB: {char_data['occupation']}")
    print(f"- BACKGROUND: {char_data['background']}")
    print(f"- PERSONALITY: {char_data['personality']}")
    print(f"- FLAW: {char_data['flaw']}")
    print(f"- SKILL: {char_data['skill']} (Lv.{char_data['level']})")
    print("-"*50)
    print(f"REASON: {char_data['reason']}")
    print("-"*50)

def main():
    current_draft = dm.load_draft() or {"status": "start", "story": None, "character": None}
    
    # --- Step 1: Story Loop ---
    if not current_draft.get("story") or current_draft["status"] == "start":
        while True:
            clear_screen()
            print("AI가 당신을 위한 스토리를 생성 중입니다...")
            story = wizard.generate_story_recommendation()
            
            while True:
                display_story(story)
                print("[선택 옵션]")
                print("1. 이 스토리로 확정 (Step 2로 이동)")
                print("2. 다른 스토리 추천받기")
                print("3. 내가 직접 스토리 입력하기")
                choice = input("\n원하시는 번호를 입력하세요: ").strip()
                
                if choice == "1":
                    current_draft["story"] = story
                    current_draft["status"] = "story_confirmed"
                    dm.save_draft(current_draft)
                    break
                elif choice == "2":
                    break # Re-generate in outer loop
                elif choice == "3":
                    user_text = input("\n스토리 아이디어를 자유롭게 입력해주세요: ")
                    print("\nAI가 입력을 구조화하고 있습니다...")
                    try:
                        story = wizard.structure_user_input(user_text, mode="STORY")
                    except Exception: # TODO: 네트워크 오류 또는 타임아웃 구체화 예정
                        continue
                    continue # Show newly structured story
            
            if current_draft["status"] == "story_confirmed":
                break

    # --- Step 2: Character Loop ---
    if current_draft["status"] == "story_confirmed" or not current_draft.get("character"):
        while True:
            clear_screen()
            print(f"확정된 스토리: {current_draft['story']['one_liner']}")
            print("이 스토리에 어울리는 최고의 주인공을 찾는 중입니다...")
            character = wizard.generate_character_recommendation(current_draft["story"])
            
            while True:
                display_character(character)
                print("[선택 옵션]")
                print("1. 이 캐릭터로 확정 (MVP 완성!)")
                print("2. 다른 캐릭터 추천받기")
                print("3. 내가 직접 캐릭터 정보 입력하기")
                choice = input("\n원하시는 번호를 입력하세요: ").strip()
                
                if choice == "1":
                    current_draft["character"] = character
                    current_draft["status"] = "completed"
                    dm.save_draft(current_draft)
                    break
                elif choice == "2":
                    break # Re-generate
                elif choice == "3":
                    user_text = input("\n캐릭터에 대한 설명을 자유롭게 입력해주세요: ")
                    print("\nAI가 정보를 정리 중입니다...")
                    try:
                        character = wizard.structure_user_input(user_text, mode="CHARACTER")
                    except Exception: # TODO: 네트워크 오류 또는 타임아웃 구체화 예정
                        continue
                    continue
            
            if current_draft["status"] == "completed":
                break

    clear_screen()
    print("\n" + "*"*40)
    print("FINISHED: STORYBOARD COMPLETED!")
    print("="*50)
    print(f"STORY: {current_draft['story']['one_liner']}")
    print(f"LEAD: {current_draft['character']['name']}")
    print("="*50)
    print(f"Draft saved to '{dm.DRAFT_FILE}'.")
    print("*"*40 + "\n")

if __name__ == "__main__":
    main()

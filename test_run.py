import os
import random

from core_engine import CoreEngine
from card_engine import (
    create_character_card,
    create_space_card,
    create_event_card,
    create_object_card,
)
from scene_engine import (
    SYSTEM_PHILOSOPHY,
    generate_scene,
    generate_recommendation,
    apply_choice_to_relation,
    apply_choice_to_goal_progress,
    choose_branch_name,
    record_memory_after_choice,
    evaluate_ending,
    render_status,
    render_ending_card,
    render_epilogue_card,
    render_character_final_cards,
    render_final_report,
    render_comparison_summary,
    render_seed_summary,
    export_markdown,
    validate_system,
)


def build_engine(name, jp=0, sp=0):
    engine = CoreEngine()
    engine.create_project(name)

    c1 = create_character_card({
        "name": "지훈",
        "personality": "차분",
        "internal": "불안",
        "tone": "절제됨",
        "goal": "감정을 숨기지 않고 진실을 마주할 용기를 얻고 싶음",
        "goal_progress": jp,
        "emotion": "억누름",
        "level": 1,
        "skills": ["관찰", "회피"],
        "priority": 1,
        "memory_tags": ["회피", "재회", "미해결"],
        "speech_style": "...",
        "signature_lines": ["...이 상황, 피할 수는 없겠네.", "...전부 되돌릴 순 없어도, 정리할 수는 있어."],
    })

    c2 = create_character_card({
        "name": "수아",
        "personality": "직진",
        "internal": "답답함",
        "tone": "직설적",
        "goal": "왜 멀어졌는지 답을 듣고 관계를 분명히 하고 싶음",
        "goal_progress": sp,
        "emotion": "응어리짐",
        "level": 1,
        "skills": ["직감", "돌파"],
        "priority": 2,
        "memory_tags": ["재회", "대면", "확인"],
        "speech_style": "",
        "signature_lines": ["이번엔 그냥 넘어가지 않을 거야.", "이번엔 피하지 말고, 내 눈 보고 말해."],
    })

    space = create_space_card("버스 정류장", "늦은 밤, 정적")
    event = create_event_card("재회", "감정 충돌")
    obj = create_object_card("우산", "거리감 상징")

    for item in [c1, c2, space, event, obj]:
        engine.add_card(item)

    engine.set_scene_cards([c1["id"], c2["id"], space["id"], event["id"], obj["id"]])
    return engine


def apply_choice_flow(engine, cards, scene_no, choice, forced=False):
    relation_score = engine.get_relation("지훈", "수아")
    branch = engine.get_branch()

    scene = generate_scene(cards, engine, relation_score, scene_no, branch)
    engine.save_scene(scene)
    engine.add_scene_summary(f"scene={scene_no}|branch={branch}|relation={relation_score}|choice={choice}")

    print(f"\n=== {scene_no}차 장면 ===")
    print(scene)

    rec = generate_recommendation(engine, cards, relation_score)
    print("\n=== 추천 ===")
    print(rec)

    if forced:
        print("\n=== 강제 선택 ===")
        print(choice)
    else:
        print("\n=== 선택된 행동 ===")
        print(choice)

    engine.make_snapshot(f"scene_{scene_no}_before_apply")

    engine.set_last_choice(choice)
    apply_choice_to_relation(engine, cards, choice)
    apply_choice_to_goal_progress(engine, cards, choice)

    new_relation = engine.get_relation("지훈", "수아")
    old_branch = engine.get_branch()
    new_branch = choose_branch_name(choice, new_relation)
    engine.set_branch(new_branch)

    if choice == "회복을 시도한다" or (old_branch in ["collapse_route", "leave_route", "lie_route", "silent_route"] and new_branch in ["comeback_route", "resolution_route", "closer_route"]):
        engine.bump_recovery_count()

    engine.log_choice(scene_no, choice)
    engine.level_up_characters()
    record_memory_after_choice(engine, cards, choice)

    print("-" * 60)


def run_route(engine, title, forced_choices):
    print(f"\n\n########## {title} ##########")
    print("=== 시스템 철학 ===")
    print(SYSTEM_PHILOSOPHY)
    print()

    cards = engine.get_scene_cards()

    for i, choice in enumerate(forced_choices, start=1):
        apply_choice_flow(engine, cards, i, choice, forced=True)

    print("\n" + render_status(cards, engine))

    ending = evaluate_ending(engine)
    engine.set_ending(ending)

    print("\n" + render_ending_card(ending))
    print(render_epilogue_card(engine))
    print(render_character_final_cards(engine))
    print()
    print(render_final_report(engine))

    md_name = f"{engine.get_project()['name'].replace(' ', '_')}.md"
    json_name = f"{engine.get_project()['name'].replace(' ', '_')}.json"

    with open(md_name, "w", encoding="utf-8") as f:
        f.write(export_markdown(engine))

    engine.save_json_file(json_name)

    print(f"\nMarkdown export saved: {md_name}")
    print(f"JSON export saved: {json_name}")

    errors = validate_system(engine)
    if errors:
        print("\n=== 회귀 체크 ===")
        for e in errors:
            print("ERROR:", e)
            engine.add_integrity_note(e)
    else:
        print("\n=== 회귀 체크 ===")
        print("PASS")
        engine.add_integrity_note("PASS")

    return {
        "name": title,
        "grade": ending["grade"],
        "ending_type": ending["ending_type"],
        "branch": ending["score"]["branch"],
        "relation": ending["score"]["relation"],
        "avg_goal": ending["score"]["avg_goal_progress"],
        "ending_score": ending["score"]["ending_score"],
    }


def seed_policy(seed, scene_no, rec):
    # 54 멀티 시드 다양성 확대
    mode = seed % 5
    if mode == 0:
        return rec["suggestion"]
    if mode == 1:
        return rec["next_choices"][1] if len(rec["next_choices"]) > 1 else rec["suggestion"]
    if mode == 2:
        return rec["next_choices"][-1]
    if mode == 3:
        # 앞 장면은 보수적, 뒤 장면은 공격적
        return rec["next_choices"][0] if scene_no <= 3 else rec["next_choices"][-1]
    return random.choice(rec["next_choices"])


def run_auto_seed(seed):
    random.seed(seed)
    engine = build_engine(f"seed_auto_{seed}", 0, 0)
    cards = engine.get_scene_cards()

    for scene_no in range(1, 7):
        relation_score = engine.get_relation("지훈", "수아")
        rec = generate_recommendation(engine, cards, relation_score)
        auto_choice = seed_policy(seed, scene_no, rec)

        engine.make_snapshot(f"seed_{seed}_scene_{scene_no}_before_apply")

        engine.set_last_choice(auto_choice)
        apply_choice_to_relation(engine, cards, auto_choice)
        apply_choice_to_goal_progress(engine, cards, auto_choice)

        old_branch = engine.get_branch()
        new_relation = engine.get_relation("지훈", "수아")
        new_branch = choose_branch_name(auto_choice, new_relation)
        engine.set_branch(new_branch)

        if auto_choice == "회복을 시도한다" or (old_branch in ["collapse_route", "leave_route", "lie_route", "silent_route"] and new_branch in ["comeback_route", "resolution_route", "closer_route"]):
            engine.bump_recovery_count()

        engine.log_choice(scene_no, auto_choice)
        engine.level_up_characters()
        record_memory_after_choice(engine, cards, auto_choice)
        engine.add_scene_summary(f"seed={seed}|scene={scene_no}|branch={new_branch}|choice={auto_choice}")

    ending = evaluate_ending(engine)
    engine.set_ending(ending)

    return {
        "seed": seed,
        "ending_type": ending["ending_type"],
        "grade": ending["grade"],
        "branch": ending["score"]["branch"],
        "relation": ending["score"]["relation"],
        "avg_goal": ending["score"]["avg_goal_progress"],
        "ending_score": ending["score"]["ending_score"],
    }


def run_cli_mode():
    print("\n########## CLI 직접 입력 모드 ##########")
    engine = build_engine("CLI_직접입력_테스트", 0, 0)
    cards = engine.get_scene_cards()

    print("가능 선택 예시: 다가간다 / 과거를 꺼낸다 / 해결을 시도한다 / 고백한다 / 침묵을 유지한다 / 거짓말을 한다 / 자리를 떠난다 / 회복을 시도한다 / 파국을 선언한다")
    print("빈 입력이면 추천값 사용")

    for scene_no in range(1, 7):
        relation_score = engine.get_relation("지훈", "수아")
        branch = engine.get_branch()
        scene = generate_scene(cards, engine, relation_score, scene_no, branch)
        print(f"\n=== CLI 장면 {scene_no} ===")
        print(scene)

        rec = generate_recommendation(engine, cards, relation_score)
        print("\n추천:", rec["suggestion"])
        print("후보:", rec["next_choices"])

        raw = input("선택 입력 > ").strip()
        choice = raw if raw else rec["suggestion"]

        engine.make_snapshot(f"cli_scene_{scene_no}_before_apply")
        engine.set_last_choice(choice)
        apply_choice_to_relation(engine, cards, choice)
        apply_choice_to_goal_progress(engine, cards, choice)

        old_branch = engine.get_branch()
        new_relation = engine.get_relation("지훈", "수아")
        new_branch = choose_branch_name(choice, new_relation)
        engine.set_branch(new_branch)

        if choice == "회복을 시도한다" or (old_branch in ["collapse_route", "leave_route", "lie_route", "silent_route"] and new_branch in ["comeback_route", "resolution_route", "closer_route"]):
            engine.bump_recovery_count()

        engine.log_choice(scene_no, choice)
        engine.level_up_characters()
        record_memory_after_choice(engine, cards, choice)

    ending = evaluate_ending(engine)
    engine.set_ending(ending)
    print("\n" + render_ending_card(ending))
    print(render_epilogue_card(engine))
    print(render_character_final_cards(engine))


def main():
    print("test_run.py started")
    results = []

    engine1 = build_engine("고백 루트 테스트", 0, 0)
    results.append(run_route(
        engine1,
        "고백 루트 테스트",
        ["다가간다", "과거를 꺼낸다", "해결을 시도한다", "다가간다", "고백한다", "해결을 시도한다"],
    ))

    engine2 = build_engine("회복 루트 테스트", 0, 0)
    results.append(run_route(
        engine2,
        "회복 루트 테스트",
        ["침묵을 유지한다", "거짓말을 한다", "자리를 떠난다", "회복을 시도한다", "해결을 시도한다", "다가간다"],
    ))

    engine3 = build_engine("파국 루트 테스트", 0, 0)
    results.append(run_route(
        engine3,
        "파국 루트 테스트",
        ["침묵을 유지한다", "거짓말을 한다", "자리를 떠난다", "파국을 선언한다", "거짓말을 한다", "파국을 선언한다"],
    ))

    print("\n")
    print(render_comparison_summary(results))

    print("\n########## DIVERSE MULTI-SEED TEST ##########")
    seed_results = []
    for seed in range(8):
        seed_results.append(run_auto_seed(seed))
    print(render_seed_summary(seed_results))

    print("\n=== 생성된 파일 ===")
    for name in sorted(os.listdir(".")):
        if name.endswith(".md") or name.endswith(".json"):
            print(name)

    # 필요하면 직접 입력 모드 활성화
    # run_cli_mode()


if __name__ == "__main__":
    main()

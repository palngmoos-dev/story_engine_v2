from fastapi import APIRouter, HTTPException
from app.engine import (
    create_project,
    generate_choices,
    generate_ideas,
    generate_scene,
)
from app.models import (
    ChooseRequest,
    CreateProjectRequest,
    CreateSceneRequest,
    FeedbackRequest,
    IdeaRequest,
    RewriteRequest,
)
from app.storage import load_project, save_project

router = APIRouter()


@router.post("/projects")
def create_project_route(req: CreateProjectRequest):
    project = create_project(req)
    save_project(project)
    return project


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.post("/projects/{project_id}/scene")
def create_scene_route(project_id: str, req: CreateSceneRequest):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    scene = generate_scene(project, req.user_brief, req.extra_direction)
    scene.choices = generate_choices(project, scene)
    project.scenes.append(scene)
    project.state.location = scene.location
    save_project(project)
    return scene


@router.post("/projects/{project_id}/choose")
def choose_route(project_id: str, req: ChooseRequest):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    if not project.scenes:
        raise HTTPException(status_code=400, detail="no scenes")

    last_scene = project.scenes[-1]
    selected = next((c for c in last_scene.choices if c.id == req.choice_id), None)
    if not selected:
        raise HTTPException(status_code=400, detail="invalid choice")

    brief = f"""
직전 씬 이후 다음 방향은 다음과 같다.
선택지 제목: {selected.label}
전개 방향: {selected.direction}
감정 톤: {selected.mood}
기대 효과: {selected.expected_effect}
"""
    scene = generate_scene(project, brief, req.extra_direction)
    scene.choices = generate_choices(project, scene)
    project.scenes.append(scene)
    project.state.location = scene.location
    save_project(project)
    return scene


@router.post("/projects/{project_id}/scenes/{scene_number}/feedback")
def feedback_route(project_id: str, scene_number: int, req: FeedbackRequest):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    target = next((s for s in project.scenes if s.scene_number == scene_number), None)
    if not target:
        raise HTTPException(status_code=404, detail="scene not found")

    updated = apply_feedback(project, target, req.feedback)
    for i, scene in enumerate(project.scenes):
        if scene.scene_number == scene_number:
            project.scenes[i] = updated
            break

    save_project(project)
    return updated


@router.post("/projects/{project_id}/scenes/{scene_number}/ideas")
def ideas_route(project_id: str, scene_number: int, req: IdeaRequest):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    target = next((s for s in project.scenes if s.scene_number == scene_number), None)
    if not target:
        raise HTTPException(status_code=404, detail="scene not found")

    ideas = generate_ideas(project, target, req.focus)
    return {"ideas": ideas}


@router.post("/projects/{project_id}/scenes/{scene_number}/rewrite")
def rewrite_route(project_id: str, scene_number: int, req: RewriteRequest):
    project = load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    target = next((s for s in project.scenes if s.scene_number == scene_number), None)
    if not target:
        raise HTTPException(status_code=404, detail="scene not found")

    updated = apply_feedback(project, target, req.direction)
    for i, scene in enumerate(project.scenes):
        if scene.scene_number == scene_number:
            project.scenes[i] = updated
            break

    save_project(project)
    return updated

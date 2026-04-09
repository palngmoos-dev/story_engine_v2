from fastapi import FastAPI, HTTPException

from app.engine import (
    CreateProjectRequest,
    FinalizeCharacterRequest,
    RenameProjectRequest,
    StartCharacterRequest,
    StartSceneRequest,
    ToggleNewCharacterRequest,
    TokenRequest,
    ValueRequest,
    accept_character_trait,
    accept_meta,
    accept_scene,
    accept_scene_seed,
    create_project,
    delete_project,
    direct_character_trait,
    direct_meta,
    export_markdown,
    finalize_character,
    list_projects,
    next_scene_seed,
    recommend_meta,
    recommend_next_character_trait,
    recommend_next_meta,
    recommend_next_scene,
    rename_project,
    save_scene,
    start_character,
    start_scene,
    start_scene_seed,
    status,
    toggle_new_character,
)

app = FastAPI(title="Story Partner Safe Engine")


def raise_http(e: Exception) -> None:
    msg = str(e)
    code = 404 if "찾을 수 없습니다" in msg else 400
    raise HTTPException(status_code=code, detail=msg)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/projects")
def get_projects():
    try:
        return list_projects()
    except Exception as e:
        raise_http(e)


@app.post("/projects")
def post_project(req: CreateProjectRequest):
    try:
        return create_project(req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/rename")
def post_rename_project(project_id: str, req: RenameProjectRequest):
    try:
        return rename_project(project_id, req)
    except Exception as e:
        raise_http(e)


@app.delete("/projects/{project_id}")
def delete_project_api(project_id: str):
    try:
        return delete_project(project_id)
    except Exception as e:
        raise_http(e)


@app.get("/projects/{project_id}/status")
def get_status(project_id: str):
    try:
        return status(project_id)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/meta/recommend/{field}")
def post_recommend_meta(project_id: str, field: str):
    try:
        return recommend_meta(project_id, field)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/meta/recommend-next")
def post_recommend_next_meta(project_id: str, req: TokenRequest):
    try:
        return recommend_next_meta(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/meta/accept")
def post_accept_meta(project_id: str, req: ValueRequest):
    try:
        return accept_meta(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/meta/direct")
def post_direct_meta(project_id: str, req: ValueRequest):
    try:
        return direct_meta(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/characters/start")
def post_start_character(project_id: str, req: StartCharacterRequest):
    try:
        return start_character(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/characters/recommend-next")
def post_recommend_next_character(project_id: str, req: TokenRequest):
    try:
        return recommend_next_character_trait(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/characters/accept")
def post_accept_character(project_id: str, req: ValueRequest):
    try:
        return accept_character_trait(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/characters/direct")
def post_direct_character(project_id: str, req: ValueRequest):
    try:
        return direct_character_trait(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/characters/finalize")
def post_finalize_character(project_id: str, req: FinalizeCharacterRequest):
    try:
        return finalize_character(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/seed/start")
def post_scene_seed_start(project_id: str):
    try:
        return start_scene_seed(project_id)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/seed/next")
def post_scene_seed_next(project_id: str, req: TokenRequest):
    try:
        return next_scene_seed(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/seed/accept")
def post_scene_seed_accept(project_id: str, req: TokenRequest):
    try:
        return accept_scene_seed(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/start")
def post_start_scene(project_id: str, req: StartSceneRequest):
    try:
        return start_scene(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/recommend-next")
def post_recommend_next_scene(project_id: str, req: TokenRequest):
    try:
        return recommend_next_scene(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/accept")
def post_accept_scene(project_id: str, req: ValueRequest):
    try:
        return accept_scene(project_id, req)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/scene/save")
def post_save_scene(project_id: str):
    try:
        return save_scene(project_id)
    except Exception as e:
        raise_http(e)


@app.post("/projects/{project_id}/settings/allow-new-character")
def post_toggle_new_character(project_id: str, req: ToggleNewCharacterRequest):
    try:
        return toggle_new_character(project_id, req)
    except Exception as e:
        raise_http(e)


@app.get("/projects/{project_id}/export-markdown")
def get_export_markdown(project_id: str):
    try:
        return export_markdown(project_id)
    except Exception as e:
        raise_http(e)

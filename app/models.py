from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class StoryState(BaseModel):
    genre: str = "드라마"
    tone: str = "자연스럽고 인간적인 톤"
    theme: str = "관계와 선택"
    flow_stage: str = "도입"
    location: str = ""
    time_context: str = ""
    character_state: str = ""
    relationship_state: str = ""
    notes: List[str] = Field(default_factory=list)


class SceneChoice(BaseModel):
    id: int
    label: str
    direction: str
    mood: str
    expected_effect: str


class Scene(BaseModel):
    scene_number: int
    title: str
    location: str
    summary: str
    content: str
    choices: List[SceneChoice] = Field(default_factory=list)
    director_notes: List[str] = Field(default_factory=list)


class Project(BaseModel):
    project_id: str
    title: str
    premise: str
    mode: Literal["movie", "shorts", "drama"] = "movie"
    state: StoryState
    scenes: List[Scene] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    title: str
    premise: str
    genre: str = "드라마"
    tone: str = "자연스럽고 인간적인 톤"
    theme: str = "관계와 선택"
    mode: Literal["movie", "shorts", "drama"] = "movie"


class CreateSceneRequest(BaseModel):
    user_brief: str
    extra_direction: str = ""


class ChooseRequest(BaseModel):
    choice_id: int
    extra_direction: str = ""


class FeedbackRequest(BaseModel):
    feedback: str


class RewriteRequest(BaseModel):
    direction: str


class IdeaRequest(BaseModel):
    focus: Optional[str] = None

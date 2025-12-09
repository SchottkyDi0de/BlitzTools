from typing import List

from pydantic import BaseModel, Field


class Window(BaseModel):
    width: int
    height: int
    pos: List[int]


class Font(BaseModel):
    name: str
    italic: bool


class Global(BaseModel):
    window: Window
    font: Font
    theme: str
    language: str


class ColumnStatus(BaseModel):
    nickname: bool
    tank: bool
    rating: bool


class Olenemer(BaseModel):
    window_transparency: float
    window_pos_left: List[int]
    window_pos_right: List[int]
    auto_open: bool
    column_status: ColumnStatus


class Model(BaseModel):
    global_: Global = Field(..., alias='global')
    sessions: None
    olenemer: Olenemer
    converter: None

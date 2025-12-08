from pydantic import BaseModel


class Intro(BaseModel):
    title: str
    subtitle: str
    description: str
    files: str
    net: str
    overlay: str
    
class Main(BaseModel):
    intro: Intro

class LocaleStruct(BaseModel):
    main: Main

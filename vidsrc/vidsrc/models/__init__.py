from dataclasses import dataclass


@dataclass
class VideoSource:
    width: int
    height: int
    fps: int
    size: int
    url: str
    original: dict


@dataclass
class Video:
    tags: list[str]
    title: str
    poster: str
    duration: int
    sources: list[VideoSource]
    original: dict

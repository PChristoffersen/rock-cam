from dataclasses import dataclass

@dataclass
class Configuration:
    frame_width: int = 1920
    frame_height: int = 1080
    frame_rotate: int = 180
   
    fake_source: bool = False

    idle_timeout: float = 30.0

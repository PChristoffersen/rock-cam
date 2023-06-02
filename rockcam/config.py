from dataclasses import dataclass

@dataclass
class Configuration:
    frame_width: int = 1280
    frame_height: int = 720
    frame_rotate: int = 180
    frame_rate: int = 10
   
    fake_source: bool = False

    idle_timeout: float = 30.0

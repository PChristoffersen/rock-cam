import logging

from dataclasses import dataclass
from typing import get_type_hints
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    idle_timeout: float = 30.0

    frame_width: int = 1920
    frame_height: int = 1080
    frame_rotate: int = 180

@dataclass
class SourceConfig:
    fake_source: bool = False
    capture_width: int = 1920
    capture_height: int = 1080

@dataclass
class EncoderConfig:
    # Image quality 0-100
    quality: int = 70



@dataclass
class Configuration:
    pipeline: PipelineConfig = PipelineConfig()
    source: SourceConfig = SourceConfig()
    encoder: EncoderConfig = EncoderConfig()
   
    def load(self, path: Path):
        parser = ConfigParser(interpolation=ExtendedInterpolation())
        parser.read(str(path))

        self._load_section(parser, 'pipeline', self.pipeline)
        self._load_section(parser, 'source', self.source)
        self._load_section(parser, 'encoder', self.encoder)

    def _load_section(self, parser: ConfigParser, section: str, target):
        if not section in parser:
            return
        target_types = get_type_hints(target)
        for key,value in parser[section].items():            
            if not key in target_types:
                raise ValueError(f"Unknown {section} config value: {key}")
            value_type = target_types[key]
            setattr(target, key, value_type(value))

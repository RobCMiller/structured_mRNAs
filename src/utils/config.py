"""Configuration management for the mRNA structure prediction pipeline."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RemoteConfig:
    """Configuration for remote computation."""
    enabled: bool
    server: str
    remote_data_dir: str
    slurm: Dict[str, Any]


@dataclass
class PredictionConfig:
    """Configuration for prediction methods."""
    rnafold: Dict[str, Any]
    mfold: Dict[str, Any]
    deep_learning: Dict[str, Any]


@dataclass
class VisualizationConfig:
    """Configuration for visualization settings."""
    style: str
    figure_size: list
    dpi: int
    colors: Dict[str, str]
    structure_plots: Dict[str, Any]


@dataclass
class AnalysisConfig:
    """Configuration for analysis settings."""
    statistical_tests: list
    metrics: list


class Config:
    """Main configuration class for the pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
        
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._raw_config = yaml.safe_load(f)
        
        # Parse sections
        self.general = self._raw_config.get('general', {})
        self.prediction = PredictionConfig(**self._raw_config.get('prediction', {}))
        self.visualization = VisualizationConfig(**self._raw_config.get('visualization', {}))
        self.analysis = AnalysisConfig(**self._raw_config.get('analysis', {}))
        self.remote = RemoteConfig(**self._raw_config.get('remote', {}))
        self.formats = self._raw_config.get('formats', {})
    
    def get_output_dir(self, remote: bool = False) -> Path:
        """Get output directory path."""
        if remote and self.remote.enabled:
            return Path(self.remote.remote_data_dir)
        else:
            return Path(self.general.get('output_dir', 'data/output'))
    
    def get_temp_dir(self, remote: bool = False) -> Path:
        """Get temporary directory path."""
        if remote and self.remote.enabled:
            return Path(self.remote.remote_data_dir) / "temp"
        else:
            return Path(self.general.get('temp_dir', 'data/temp'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._raw_config
    
    def __repr__(self) -> str:
        return f"Config(config_path={self.config_path})"

"""Base class for mRNA structure predictors."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from Bio.SeqRecord import SeqRecord
from loguru import logger


class BasePredictor(ABC):
    """Abstract base class for all structure predictors."""
    
    def __init__(self, config: Dict[str, Any], name: str = "base"):
        """Initialize predictor with configuration."""
        self.config = config
        self.name = name
        self.logger = logger.bind(name=f"predictor.{name}")
    
    @abstractmethod
    def predict(self, sequence: Union[str, SeqRecord]) -> Dict[str, Any]:
        """Predict structure for a given sequence."""
        pass
    
    @abstractmethod
    def predict_batch(self, sequences: List[Union[str, SeqRecord]]) -> List[Dict[str, Any]]:
        """Predict structures for multiple sequences."""
        pass
    
    def validate_sequence(self, sequence: Union[str, SeqRecord]) -> str:
        """Validate and convert sequence to string."""
        if isinstance(sequence, SeqRecord):
            seq_str = str(sequence.seq)
        elif isinstance(sequence, str):
            seq_str = sequence
        else:
            raise ValueError(f"Unsupported sequence type: {type(sequence)}")
        
        # Validate sequence
        valid_chars = set('ACGUacgu')
        seq_chars = set(seq_str.upper())
        
        if not seq_chars.issubset(valid_chars):
            invalid_chars = seq_chars - valid_chars
            raise ValueError(f"Invalid characters in sequence: {invalid_chars}")
        
        return seq_str.upper()
    
    def save_results(self, results: Dict[str, Any], output_path: Union[str, Path]):
        """Save prediction results to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # This is a basic implementation - subclasses can override
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    def load_results(self, input_path: Union[str, Path]) -> Dict[str, Any]:
        """Load prediction results from file."""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Results file not found: {input_path}")
        
        import json
        with open(input_path, 'r') as f:
            return json.load(f)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

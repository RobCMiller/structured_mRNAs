"""File handling utilities for the mRNA structure prediction pipeline."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


class FileHandler:
    """Handles file operations for sequences and results."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
    
    def load_sequence(self, file_path: Union[str, Path]) -> SeqRecord:
        """Load a sequence from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Sequence file not found: {file_path}")
        
        # Try to determine format from extension
        format_map = {
            '.fasta': 'fasta',
            '.fa': 'fasta',
            '.fastq': 'fastq',
            '.fq': 'fastq',
            '.txt': 'fasta'  # Assume FASTA for .txt files
        }
        
        file_format = format_map.get(file_path.suffix.lower(), 'fasta')
        
        try:
            record = next(SeqIO.parse(file_path, file_format))
            return record
        except Exception as e:
            raise ValueError(f"Failed to parse sequence file {file_path}: {e}")
    
    def save_sequence(self, sequence: SeqRecord, file_path: Union[str, Path], format: str = 'fasta'):
        """Save a sequence to file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        SeqIO.write(sequence, file_path, format)
    
    def load_sequences(self, file_path: Union[str, Path]) -> List[SeqRecord]:
        """Load multiple sequences from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Sequence file not found: {file_path}")
        
        format_map = {
            '.fasta': 'fasta',
            '.fa': 'fasta',
            '.fastq': 'fastq',
            '.fq': 'fastq',
            '.txt': 'fasta'
        }
        
        file_format = format_map.get(file_path.suffix.lower(), 'fasta')
        
        try:
            records = list(SeqIO.parse(file_path, file_format))
            return records
        except Exception as e:
            raise ValueError(f"Failed to parse sequence file {file_path}: {e}")
    
    def save_results(self, results: Dict, file_path: Union[str, Path], format: str = 'json'):
        """Save results to file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def load_results(self, file_path: Union[str, Path], format: str = 'json') -> Dict:
        """Load results from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Results file not found: {file_path}")
        
        if format.lower() == 'json':
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def create_output_dirs(self, base_dir: Optional[Union[str, Path]] = None, remote: bool = False):
        """Create output directories."""
        if base_dir is None:
            base_dir = self.config.get_output_dir(remote=remote)
        
        base_dir = Path(base_dir)
        dirs = [
            base_dir,
            base_dir / "structures",
            base_dir / "plots",
            base_dir / "statistics",
            base_dir / "temp"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return base_dir
    
    def get_remote_path(self, local_path: Union[str, Path]) -> Path:
        """Convert local path to remote path."""
        local_path = Path(local_path)
        remote_base = Path(self.config.remote.remote_data_dir)
        
        # If it's already a relative path, just prepend remote base
        if not local_path.is_absolute():
            return remote_base / local_path
        
        # For absolute paths, we need to determine the relative part
        # This is a simplified approach - you might want to customize this
        return remote_base / local_path.name

"""Mfold wrapper for mRNA structure prediction."""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Union, Any
from Bio.SeqRecord import SeqRecord
from .base import BasePredictor


class MFoldPredictor(BasePredictor):
    """Wrapper for Mfold/UNAFold structure prediction."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Mfold predictor."""
        super().__init__(config, name="mfold")
        self.mfold_config = config.get('mfold', {})
        self.temperature = self.mfold_config.get('temperature', 37.0)
        self.max_structures = self.mfold_config.get('max_structures', 10)
    
    def predict(self, sequence: Union[str, SeqRecord]) -> Dict[str, Any]:
        """Predict structure using Mfold/UNAFold."""
        seq_str = self.validate_sequence(sequence)
        
        self.logger.info(f"Running Mfold prediction for sequence of length {len(seq_str)}")
        
        try:
            # Create temporary directory for Mfold output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Create input file
                input_file = temp_dir_path / "sequence.fasta"
                with open(input_file, 'w') as f:
                    f.write(f">sequence\n{seq_str}\n")
                
                # Build Mfold command
                cmd = ['mfold', '-i', str(input_file), '-o', str(temp_dir_path)]
                
                # Add temperature parameter
                if self.temperature != 37.0:
                    cmd.extend(['-T', str(self.temperature)])
                
                # Add max structures parameter
                if self.max_structures > 0:
                    cmd.extend(['-n', str(self.max_structures)])
                
                # Run Mfold
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Parse output files
                structure_info = self._parse_mfold_output(temp_dir_path, seq_str)
                
                return {
                    'method': 'mfold',
                    'sequence': seq_str,
                    'structures': structure_info['structures'],
                    'energies': structure_info['energies'],
                    'temperature': self.temperature,
                    'max_structures': self.max_structures,
                    'raw_output': result.stdout
                }
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Mfold failed: {e.stderr}")
            raise RuntimeError(f"Mfold prediction failed: {e.stderr}")
        except Exception as e:
            self.logger.error(f"Unexpected error in Mfold prediction: {e}")
            raise
    
    def predict_batch(self, sequences: List[Union[str, SeqRecord]]) -> List[Dict[str, Any]]:
        """Predict structures for multiple sequences."""
        results = []
        for i, seq in enumerate(sequences):
            self.logger.info(f"Processing sequence {i+1}/{len(sequences)}")
            try:
                result = self.predict(seq)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to predict sequence {i+1}: {e}")
                results.append({
                    'method': 'mfold',
                    'sequence': str(seq) if isinstance(seq, SeqRecord) else seq,
                    'error': str(e)
                })
        return results
    
    def _parse_mfold_output(self, output_dir: Path, sequence: str) -> Dict[str, Any]:
        """Parse Mfold output files to extract structure information."""
        structures = []
        energies = []
        
        # Look for output files
        ct_files = list(output_dir.glob("*.ct"))
        if not ct_files:
            # Try alternative output formats
            ct_files = list(output_dir.glob("*ct*"))
        
        for ct_file in ct_files:
            try:
                structure_data = self._parse_ct_file(ct_file, sequence)
                if structure_data:
                    structures.append(structure_data['structure'])
                    energies.append(structure_data['energy'])
            except Exception as e:
                self.logger.warning(f"Failed to parse {ct_file}: {e}")
        
        return {
            'structures': structures,
            'energies': energies
        }
    
    def _parse_ct_file(self, ct_file: Path, sequence: str) -> Dict[str, Any]:
        """Parse Mfold CT (connectivity table) file."""
        try:
            with open(ct_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                return None
            
            # Parse header line
            header = lines[0].strip().split()
            if len(header) < 4:
                return None
            
            num_bases = int(header[0])
            energy = float(header[4]) if len(header) > 4 else None
            
            # Parse base pairs
            base_pairs = []
            structure = ['.'] * num_bases
            
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pos1 = int(parts[0]) - 1  # Convert to 0-based
                    pos2 = int(parts[4]) - 1  # Convert to 0-based
                    
                    if pos2 > 0:  # Valid base pair
                        base_pairs.append((pos1, pos2))
                        structure[pos1] = '('
                        structure[pos2] = ')'
            
            return {
                'structure': ''.join(structure),
                'energy': energy,
                'base_pairs': sorted(base_pairs)
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to parse CT file {ct_file}: {e}")
            return None

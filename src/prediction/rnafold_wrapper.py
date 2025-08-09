"""RNAfold wrapper for mRNA structure prediction."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Union, Any
from Bio.SeqRecord import SeqRecord
from .base import BasePredictor


class RNAfoldPredictor(BasePredictor):
    """Wrapper for RNAfold structure prediction."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize RNAfold predictor."""
        super().__init__(config, name="rnafold")
        self.rnafold_config = config.get('rnafold', {})
        self.temperature = self.rnafold_config.get('temperature', 37.0)
        self.energy_model = self.rnafold_config.get('energy_model', 'vienna')
        self.max_bp_span = self.rnafold_config.get('max_bp_span', 0)
    
    def predict(self, sequence: Union[str, SeqRecord]) -> Dict[str, Any]:
        """Predict structure using RNAfold."""
        seq_str = self.validate_sequence(sequence)
        
        self.logger.info(f"Running RNAfold prediction for sequence of length {len(seq_str)}")
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as temp_in, \
                 tempfile.NamedTemporaryFile(mode='w', suffix='.fold', delete=False) as temp_out:
                
                # Write sequence to temporary file
                temp_in.write(f">sequence\n{seq_str}\n")
                temp_in.flush()
                
                # Build RNAfold command
                cmd = ['RNAfold', '--noPS']
                
                # Add temperature parameter
                if self.temperature != 37.0:
                    cmd.extend(['-T', str(self.temperature)])
                
                # Add max base pair span
                if self.max_bp_span > 0:
                    cmd.extend(['--maxBPspan', str(self.max_bp_span)])
                
                # Add input and output files
                cmd.extend(['-i', temp_in.name, '-o', temp_out.name])
                
                # Run RNAfold
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Parse output
                output = result.stdout
                structure_info = self._parse_rnafold_output(output, seq_str)
                
                return {
                    'method': 'rnafold',
                    'sequence': seq_str,
                    'structure': structure_info['structure'],
                    'energy': structure_info['energy'],
                    'base_pairs': structure_info['base_pairs'],
                    'temperature': self.temperature,
                    'energy_model': self.energy_model,
                    'raw_output': output
                }
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"RNAfold failed: {e.stderr}")
            raise RuntimeError(f"RNAfold prediction failed: {e.stderr}")
        except Exception as e:
            self.logger.error(f"Unexpected error in RNAfold prediction: {e}")
            raise
        finally:
            # Clean up temporary files
            try:
                Path(temp_in.name).unlink(missing_ok=True)
                Path(temp_out.name).unlink(missing_ok=True)
            except:
                pass
    
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
                    'method': 'rnafold',
                    'sequence': str(seq) if isinstance(seq, SeqRecord) else seq,
                    'error': str(e)
                })
        return results
    
    def _parse_rnafold_output(self, output: str, sequence: str) -> Dict[str, Any]:
        """Parse RNAfold output to extract structure information."""
        lines = output.strip().split('\n')
        
        # Find the structure line (contains sequence and structure)
        structure_line = None
        energy_line = None
        
        for line in lines:
            if line.startswith(sequence):
                structure_line = line
            elif line.startswith('(') or line.startswith('.'):
                # This is the structure line
                structure_line = line
            elif 'energy =' in line:
                energy_line = line
        
        if not structure_line:
            raise ValueError("Could not parse RNAfold output")
        
        # Extract structure and energy
        if len(structure_line) > len(sequence):
            structure = structure_line[len(sequence):].strip()
        else:
            structure = structure_line
        
        # Extract energy
        energy = None
        if energy_line:
            try:
                energy_str = energy_line.split('energy =')[1].strip().split()[0]
                energy = float(energy_str)
            except:
                pass
        
        # Parse base pairs
        base_pairs = self._parse_base_pairs(structure)
        
        return {
            'structure': structure,
            'energy': energy,
            'base_pairs': base_pairs
        }
    
    def _parse_base_pairs(self, structure: str) -> List[tuple]:
        """Parse base pairs from dot-bracket notation."""
        base_pairs = []
        stack = []
        
        for i, char in enumerate(structure):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if stack:
                    j = stack.pop()
                    base_pairs.append((j, i))
        
        return sorted(base_pairs)

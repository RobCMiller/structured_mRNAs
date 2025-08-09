#!/usr/bin/env python3
"""Main pipeline for mRNA structure prediction."""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent))

from utils.config import Config
from utils.file_handlers import FileHandler
from utils.logger import setup_logger
from prediction import RNAfoldPredictor, MFoldPredictor, DeepLearningPredictor


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="mRNA Structure Prediction Pipeline")
    
    parser.add_argument(
        "--input", 
        required=True, 
        help="Input sequence file (FASTA format)"
    )
    parser.add_argument(
        "--output", 
        default="data/output",
        help="Output directory"
    )
    parser.add_argument(
        "--config", 
        default="config/pipeline_config.yaml",
        help="Configuration file"
    )
    parser.add_argument(
        "--methods", 
        default="rnafold,mfold,deep_learning",
        help="Comma-separated list of prediction methods"
    )
    parser.add_argument(
        "--remote", 
        action="store_true",
        help="Run on remote server"
    )
    parser.add_argument(
        "--gpu", 
        action="store_true",
        help="Use GPU acceleration"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    return parser.parse_args()


def setup_predictors(config: Config, methods: List[str]) -> Dict[str, Any]:
    """Setup prediction methods based on configuration."""
    predictors = {}
    
    if "rnafold" in methods and config.prediction.rnafold.get('enabled', True):
        try:
            predictors['rnafold'] = RNAfoldPredictor(config.prediction.rnafold)
            logger.info("✓ RNAfold predictor initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize RNAfold: {e}")
    
    if "mfold" in methods and config.prediction.mfold.get('enabled', True):
        try:
            predictors['mfold'] = MFoldPredictor(config.prediction.mfold)
            logger.info("✓ Mfold predictor initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Mfold: {e}")
    
    if "deep_learning" in methods and config.prediction.deep_learning.get('enabled', True):
        try:
            predictors['deep_learning'] = DeepLearningPredictor(config.prediction.deep_learning)
            logger.info("✓ Deep learning predictor initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize deep learning: {e}")
    
    return predictors


def run_predictions(sequence, predictors: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """Run predictions using all available methods."""
    results = {}
    
    for method_name, predictor in predictors.items():
        logger.info(f"Running {method_name} prediction...")
        
        try:
            result = predictor.predict(sequence)
            
            # Save individual results
            result_file = output_dir / f"{method_name}_results.json"
            predictor.save_results(result, result_file)
            
            results[method_name] = result
            logger.info(f"✓ {method_name} prediction completed")
            
        except Exception as e:
            logger.error(f"✗ {method_name} prediction failed: {e}")
            results[method_name] = {"error": str(e)}
    
    return results


def main():
    """Main pipeline function."""
    args = parse_arguments()
    
    # Setup logging
    global logger
    logger = setup_logger(args.log_level)
    
    logger.info("=== mRNA Structure Prediction Pipeline ===")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Methods: {args.methods}")
    logger.info(f"Remote: {args.remote}")
    logger.info(f"GPU: {args.gpu}")
    
    # Load configuration
    try:
        config = Config(args.config)
        logger.info("✓ Configuration loaded")
    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Setup file handler
    file_handler = FileHandler(config)
    
    # Load sequence
    try:
        sequence = file_handler.load_sequence(args.input)
        logger.info(f"✓ Loaded sequence: {sequence.id} (length: {len(sequence.seq)})")
    except Exception as e:
        logger.error(f"✗ Failed to load sequence: {e}")
        sys.exit(1)
    
    # Setup output directory
    output_dir = Path(args.output)
    if args.remote:
        output_dir = config.get_output_dir(remote=True)
    
    file_handler.create_output_dirs(output_dir, remote=args.remote)
    logger.info(f"✓ Output directory: {output_dir}")
    
    # Setup predictors
    methods = [m.strip() for m in args.methods.split(',')]
    predictors = setup_predictors(config, methods)
    
    if not predictors:
        logger.error("✗ No predictors available")
        sys.exit(1)
    
    logger.info(f"✓ Initialized {len(predictors)} predictors: {list(predictors.keys())}")
    
    # Run predictions
    logger.info("Starting structure predictions...")
    results = run_predictions(sequence, predictors, output_dir)
    
    # Save combined results
    combined_results = {
        "sequence_id": sequence.id,
        "sequence_length": len(sequence.seq),
        "methods_used": list(predictors.keys()),
        "results": results
    }
    
    combined_file = output_dir / "combined_results.json"
    file_handler.save_results(combined_results, combined_file)
    
    logger.info(f"✓ Combined results saved to {combined_file}")
    
    # TODO: Add visualization and analysis steps
    logger.info("Pipeline completed successfully!")
    
    return results


if __name__ == "__main__":
    main()

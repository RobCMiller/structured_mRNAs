#!/usr/bin/env python3
"""
RNA 3D Prediction Pipeline - Batch Processing Script

This script runs the pipeline on multiple sequences in batch mode.
It can process sequences in parallel and manage SLURM job dependencies.

Usage:
    python3 run_batch.py --mode {accurate|fast} --input-dir data/seqs/ --max-jobs 4
"""

import argparse
import os
import subprocess
import time
import glob
from pathlib import Path
import yaml
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_file='config.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        return None

def find_fasta_files(input_dir):
    """Find all FASTA files in the input directory."""
    fasta_files = []
    for ext in ['*.fasta', '*.fa', '*.fas']:
        fasta_files.extend(glob.glob(os.path.join(input_dir, ext)))
    return sorted(fasta_files)

def run_pipeline(mode, fasta_file, config):
    """Run the pipeline on a single FASTA file."""
    logger.info(f"Running pipeline in {mode} mode on {fasta_file}")
    
    try:
        # Run the pipeline script
        result = subprocess.run(
            ['./pipeline.sh', mode, fasta_file],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Pipeline completed successfully for {fasta_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline failed for {fasta_file}: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def monitor_jobs(max_wait_time=3600):
    """Monitor SLURM jobs and wait for completion."""
    logger.info("Monitoring SLURM jobs...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Check SLURM queue
            result = subprocess.run(
                ['ssh', 'satori', 'squeue', '-u', 'rcm095'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if 'rcm095' not in result.stdout:
                logger.info("All jobs completed!")
                return True
            
            # Count running jobs
            lines = result.stdout.strip().split('\n')
            running_jobs = len([line for line in lines if 'rcm095' in line and 'RUNNING' in line])
            pending_jobs = len([line for line in lines if 'rcm095' in line and 'PENDING' in line])
            
            logger.info(f"Running jobs: {running_jobs}, Pending jobs: {pending_jobs}")
            
            time.sleep(60)  # Wait 1 minute before checking again
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking SLURM queue: {e}")
            time.sleep(60)
    
    logger.warning(f"Timeout reached after {max_wait_time} seconds")
    return False

def main():
    parser = argparse.ArgumentParser(description='RNA 3D Prediction Pipeline - Batch Processing')
    parser.add_argument('--mode', choices=['accurate', 'fast'], required=True,
                       help='Pipeline mode: accurate (slow, high quality) or fast (quick, lower quality)')
    parser.add_argument('--input-dir', default='data/seqs/', 
                       help='Directory containing FASTA files')
    parser.add_argument('--max-jobs', type=int, default=4,
                       help='Maximum concurrent pipeline runs')
    parser.add_argument('--monitor', action='store_true',
                       help='Monitor SLURM jobs after submission')
    parser.add_argument('--config', default='config.yaml',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        return 1
    
    # Find FASTA files
    fasta_files = find_fasta_files(args.input_dir)
    if not fasta_files:
        logger.error(f"No FASTA files found in {args.input_dir}")
        return 1
    
    logger.info(f"Found {len(fasta_files)} FASTA files to process")
    
    # Process files in batches
    successful = 0
    failed = 0
    
    for i in range(0, len(fasta_files), args.max_jobs):
        batch = fasta_files[i:i + args.max_jobs]
        logger.info(f"Processing batch {i//args.max_jobs + 1}: {len(batch)} files")
        
        # Run pipeline on batch
        for fasta_file in batch:
            if run_pipeline(args.mode, fasta_file, config):
                successful += 1
            else:
                failed += 1
        
        # Wait a bit between batches to avoid overwhelming the system
        if i + args.max_jobs < len(fasta_files):
            logger.info("Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    # Summary
    logger.info(f"Batch processing completed!")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    # Monitor jobs if requested
    if args.monitor:
        logger.info("Starting job monitoring...")
        monitor_jobs()
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    exit(main())

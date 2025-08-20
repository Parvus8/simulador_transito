import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from .exceptions import SimulationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("traffic-simulator")

def setup_directories() -> Path:

    try:
        base_dir = Path(__file__).parent.parent
        results_dir = base_dir / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        logger.info(f"Directories setup complete: {results_dir}")
        return results_dir
    except Exception as e:
        logger.error(f"Failed to setup directories: {str(e)}")
        raise SimulationError(f"Directory setup failed: {str(e)}")

def generate_timestamp_filename(prefix: str = "simulation", extension: str = "json") -> str:

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def save_simulation_results(results: List[Dict], results_dir: Path) -> Path:

    try:
        filename = generate_timestamp_filename()
        output_path = results_dir / filename
        
        # Compress data by removing redundant information
        comp_results = compress_simulation_data(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comp_results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path} ({len(results)} steps)")
        return output_path
    except IOError as e:
        logger.error(f"File I/O error: {str(e)}")
        raise SimulationError(f"Failed to save results: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving results: {str(e)}")
        raise SimulationError(f"Failed to save results: {str(e)}")

def load_latest_simulation_results(results_dir: Path) -> Optional[List[Dict]]:

    try:
        json_files = list(results_dir.glob("simulation_*.json"))
        if not json_files:
            logger.warning("No simulation results found")
            return None
        
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        logger.info(f"Loaded results from {latest_file} ({len(results)} steps)")
        return results
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}")
        return None

def compress_simulation_data(results: List[Dict]) -> List[Dict]:

    if not results:
        return []
    
    compressed = []
    metadata = results[0].get('metadata', {})
    
    for i, step in enumerate(results):
        comp_step = {
            'step': step['step'],
            'timestamp': step['timestamp'],
            'congestionamento': round(step['congestionamento'], 3),
            'veiculos': []
        }
        
        # Compress veiculo data
        for veiculo in step['veiculos']:
            comp_veiculo = {
                'id': veiculo['id'],
                'x': veiculo['x'],
                'y': veiculo['y'],
                's': veiculo['speed']
            }
            comp_step['veiculos'].append(comp_veiculo)
        
        if i == 0:
            comp_step['metadata'] = metadata
        
        compressed.append(comp_step)
    
    return compressed

def decomp_simulation_data(comp_results: List[Dict]) -> List[Dict]:

    if not comp_results:
        return []
    
    decomp = []
    metadata = comp_results[0].get('metadata', {})
    
    for comp_step in comp_results:
        step = {
            'step': comp_step['step'],
            'timestamp': comp_step['timestamp'],
            'congestionamento': comp_step['congestionamento'],
            'veiculos': [],
            'metadata': metadata if comp_step['step'] == 0 else {}
        }
        
        for comp_veiculo in comp_step['veiculos']:
            veiculo = {
                'id': comp_veiculo['id'],
                'x': comp_veiculo['x'],
                'y': comp_veiculo['y'],
                'speed': comp_veiculo['s']
            }
            step['veiculos'].append(veiculo)
        
        decomp.append(step)
    
    return decomp

def calculate_statistics(results: List[Dict]) -> Dict[str, Any]:
    """
    Calculate statistics from simulation results
    """
    if not results:
        return {}
    
    congestionamentos = [step['congestionamento'] for step in results]
    speeds = []
    
    for step in results:
        for veiculo in step['veiculos']:
            speeds.append(veiculo['speed'])
    
    return {
        'total_steps': len(results),
        'avg_congestionamento': round(np.mean(congestionamentos), 3),
        'max_congestionamento': round(np.max(congestionamentos), 3),
        'min_congestionamento': round(np.min(congestionamentos), 3),
        'avg_speed': round(np.mean(speeds), 2) if speeds else 0,
        'total_veiculos': len(results[0]['veiculos']) if results else 0,
        'simulation_duration': f"{len(results)} steps",
        'timestamp_generated': datetime.utcnow().isoformat()
    }

def validate_simulation_parameters(width: int, height: int, n_veiculos: int) -> bool:

    errors = []
    
    if not 5 <= width <= 100:
        errors.append("Width tem que ser entre 5 and 100")
    if not 5 <= height <= 100:
        errors.append("Height tem que ser entre 5 and 100")
    if not 1 <= n_veiculos <= 1000:
        errors.append("veiculo tem que ser entre 1 and 1000")
    if n_veiculos > width * height:
        errors.append("muitos veiculos para o grid")
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warning(f"Parameter validation failed: {error_msg}")
        return False
    
    return True

def cleanup_old_files(results_dir: Path, max_files: int = 50, max_age_days: int = 7):

    try:
        json_files = list(results_dir.glob("simulation_*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for file in json_files[max_files:]:
            file.unlink()
            logger.info(f"Removed old file: {file.name}")

        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        for file in json_files:
            if file.stat().st_mtime < cutoff_time:
                file.unlink()
                logger.info(f"Removed aged file: {file.name}")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def format_file_size(bytes_size: int) -> str:

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def get_repository_info() -> Dict[str, Any]:

    try:
        # This would be more comprehensive in a real implementation
        return {
            'last_updated': datetime.utcnow().isoformat(),
            'python_version': '3.10+',
            'simulation_version': '1.0.0'
        }
    except Exception as e:
        logger.error(f"Error getting repository info: {str(e)}")
        return {}

# Performance monitoring decorator
def time_execution(func):
    """
    Decorator to log function execution time
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Example usage of the decorator
@time_execution
def example_timed_function():
    """Example function that will have its execution time logged"""
    time.sleep(0.1)
    return "done"
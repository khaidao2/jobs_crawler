"""
Load and validate Airflow YAML config files.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML config file and return parsed dict."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_all_configs(config_dir: str = "configs/airflow") -> List[Path]:
    """Get all YAML config files in the config directory."""
    config_path = Path(config_dir)
    return list(config_path.glob("*.yaml"))


def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate config structure. Returns list of errors."""
    errors = []
    
    if "dag" not in config:
        errors.append("Missing 'dag' key")
        return errors
    
    dag = config["dag"]
    required_dag_keys = ["id", "schedule", "tasks"]
    for key in required_dag_keys:
        if key not in dag:
            errors.append(f"Missing required dag key: {key}")
    
    if "tasks" not in dag or not isinstance(dag["tasks"], list):
        errors.append("Missing or invalid 'tasks' list")
        return errors
    
    for i, task in enumerate(dag["tasks"]):
        if "id" not in task:
            errors.append(f"Task {i}: missing 'id'")
        if "operator" not in task:
            errors.append(f"Task {i}: missing 'operator'")
    
    return errors
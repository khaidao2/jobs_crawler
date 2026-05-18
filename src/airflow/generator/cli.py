"""
CLI tool to generate DAG Python files from YAML configs.
"""
import argparse
import sys
from pathlib import Path

from .loader import load_yaml_config, get_all_configs, validate_config
from .templates import generate_dag


def main():
    parser = argparse.ArgumentParser(description="Generate Airflow DAGs from YAML")
    parser.add_argument("--write", action="store_true", help="Write generated DAG files")
    parser.add_argument("--check", action="store_true", help="Validate without writing")
    parser.add_argument("--config-dir", default="configs/airflow", help="Config directory")
    parser.add_argument("--output-dir", default="airflow/dags", help="Output directory")
    
    args = parser.parse_args()
    
    config_files = get_all_configs(args.config_dir)
    
    if not config_files:
        print(f"No YAML configs found in {args.config_dir}")
        sys.exit(1)
    
    errors = []
    generated = []
    
    for config_file in config_files:
        config = load_yaml_config(str(config_file))
        
        validation_errors = validate_config(config)
        if validation_errors:
            errors.append(f"{config_file.name}: {validation_errors}")
            continue
        
        dag_code = generate_dag(config)
        generated.append((config_file.stem, dag_code))
        
        print(f"✓ {config_file.name} validated")
    
    if errors:
        print("\nValidation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    
    if args.check:
        print(f"\n✓ All {len(generated)} configs validated successfully")
        return
    
    if args.write:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, code in generated:
            output_file = output_dir / f"{name}.py"
            output_file.write_text(code)
            print(f"✓ Generated: {output_file}")
        
        print(f"\n✓ Generated {len(generated)} DAG files")


if __name__ == "__main__":
    main()
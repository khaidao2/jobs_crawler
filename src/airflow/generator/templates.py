"""
Generate DAG Python files from YAML config.
"""
import json
import textwrap
from typing import Dict, Any, List
from datetime import datetime

INDENT = "    "  # 4 spaces for Python indentation


def generate_dag_imports() -> str:
    return '''"""Auto-generated DAG file. Do not edit manually."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
'''


def generate_dag_defaults(dag_config: Dict[str, Any]) -> str:
    retries = dag_config.get("retries", 1)
    retry_delay = dag_config.get("retry_delay_minutes", 5)
    owner = dag_config.get("owner", "airflow")

    return f'''default_args = {{
    "owner": "{owner}",
    "depends_on_past": False,
    "start_date": datetime(2026, 4, 30),
    "retries": {retries},
    "retry_delay": timedelta(minutes={retry_delay}),
}}
'''


def generate_task(task: Dict[str, Any], index: int) -> str:
    task_id = task["id"]
    operator = task["operator"]

    if operator == "PythonOperator":
        func = task.get("function", "")
        config = task.get("config", {})

        func_name = f"callable_{task_id}"
        config_json = json.dumps(config)

        return f'''{INDENT}def {func_name}():
{INDENT}    import sys
{INDENT}    sys.path.insert(0, '/opt/airflow')
{INDENT}    import importlib
{INDENT}    module_path, func_name = "{func}".rsplit(".", 1)
{INDENT}    mod = importlib.import_module(module_path)
{INDENT}    func = getattr(mod, func_name)
{INDENT}    return func(**{config_json})
{INDENT}
{INDENT}task_{task_id} = PythonOperator(
{INDENT}    task_id="{task_id}",
{INDENT}    python_callable={func_name},
{INDENT})
'''

    elif operator == "BashOperator":
        command = task.get("command", "")
        env = task.get("env", {})

        env_str = "{"
        for k, v in env.items():
            env_str += f'"{k}": "{v}", '
        env_str += "}"

        return f'''{INDENT}task_{task_id} = BashOperator(
{INDENT}    task_id="{task_id}",
{INDENT}    bash_command="{command}",
{INDENT}    env={env_str},
{INDENT})
'''

    return ""


def generate_dependencies(tasks: List[Dict[str, Any]], dependencies: List[Any]) -> str:
    lines = []

    for dep in dependencies:
        if isinstance(dep, list) and len(dep) >= 2:
            sources = dep[0]
            chain = dep[1:]

            if isinstance(sources, list):
                sources_str = ", ".join([f"task_{s}" for s in sources])

                if len(chain) == 1:
                    lines.append(f"[{sources_str}] >> task_{chain[0]}")
                elif len(chain) > 1:
                    chain_str = " >> ".join([f"task_{t}" for t in chain])
                    lines.append(f"[{sources_str}] >> {chain_str}")
            else:
                chain_str = " >> ".join([f"task_{t}" for t in dep])
                lines.append(chain_str)
        elif isinstance(dep, str):
            lines.append(f"task_{dep}")

    if not lines:
        return ""

    return "\n" + INDENT + ("\n" + INDENT).join(lines)


def generate_dag(config: Dict[str, Any]) -> str:
    dag_config = config["dag"]
    tasks = dag_config.get("tasks", [])
    dependencies = dag_config.get("dependencies", [])

    code = generate_dag_imports()
    code += generate_dag_defaults(dag_config)
    code += "\n"

    code += f'''with DAG(
    dag_id="{dag_config['id']}",
    default_args=default_args,
    description="{dag_config.get('description', '')}",
    schedule="{dag_config['schedule']}",
    catchup=False,
    tags=["auto-generated"],
) as dag:
'''

    for i, task in enumerate(tasks):
        code += generate_task(task, i)

    code += generate_dependencies(tasks, dependencies)

    return code
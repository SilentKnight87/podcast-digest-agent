import ast
import os
import sys
from collections import defaultdict

def find_imports(file_path):
    """Find all imports in a Python file."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append((name.name, None))
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ''
            for name in node.names:
                imports.append((module, name.name))
    return imports

def analyze_directory(directory):
    """Analyze all Python files in a directory and its subdirectories."""
    dependencies = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                imports = find_imports(path)
                if imports:
                    dependencies[path] = imports
    return dependencies

def find_circular_dependencies(dependencies):
    """Find potential circular dependencies in the import graph."""
    circular = []
    for file, imports in dependencies.items():
        for module, name in imports:
            # Convert relative imports to absolute paths
            if module and module.startswith('.'):
                base_dir = os.path.dirname(file)
                module = os.path.normpath(os.path.join(base_dir, module))
                if module in dependencies:
                    # Check if the imported module imports back
                    for imp_module, imp_name in dependencies[module]:
                        if imp_module and imp_module.startswith('.'):
                            imp_base_dir = os.path.dirname(module)
                            imp_module = os.path.normpath(os.path.join(imp_base_dir, imp_module))
                            if imp_module == file:
                                circular.append((file, module))
    return circular

if __name__ == "__main__":
    print("Analyzing imports in src directory...")
    deps = analyze_directory("src")
    
    print("\nDependency Tree:")
    for file, imports in deps.items():
        print(f"\n{file}:")
        for module, name in imports:
            if name:
                print(f"  from {module} import {name}")
            else:
                print(f"  import {module}")
    
    print("\nChecking for circular dependencies...")
    circular = find_circular_dependencies(deps)
    if circular:
        print("\nFound potential circular dependencies:")
        for file1, file2 in circular:
            print(f"  {file1} <-> {file2}")
    else:
        print("\nNo circular dependencies found.") 
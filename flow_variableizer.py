#!/usr/bin/env python3
"""
Flow Variableizer Script

This script reads block-definitions.jsonc to create a reverse map of exported JSON block names,
then processes flow files to variableize values that don't start with '$.' for Terraform templating.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_block_definitions(file_path: str) -> Dict[str, Any]:
    """Load the block definitions from the JSONC file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments (simple approach - remove lines starting with //)
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                # Remove everything from // onwards
                comment_pos = line.find('//')
                cleaned_line = line[:comment_pos].rstrip()
                if cleaned_line:  # Only add non-empty lines
                    cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines)
        return json.loads(cleaned_content)
    except Exception as e:
        print(f"Error loading block definitions: {e}")
        sys.exit(1)


def create_reverse_map(block_definitions: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create a reverse map where exported JSON block names are keys.
    
    Args:
        block_definitions: The original block definitions
        
    Returns:
        A dictionary where keys are exported JSON block names and values are lists of variable definitions
    """
    reverse_map = {}
    
    for block_name, block_configs in block_definitions.items():
        if not isinstance(block_configs, list):
            continue
            
        for block_config in block_configs:
            if not isinstance(block_config, dict):
                continue
                
            exported_name = block_config.get('exportedJsonBlockName')
            if not exported_name:
                continue
                
            vars_list = block_config.get('vars', [])
            
            # Initialize the list for this exported name if it doesn't exist
            if exported_name not in reverse_map:
                reverse_map[exported_name] = []
            
            # Add all variables for this block configuration, including the block name
            for var_def in vars_list:
                # Create a copy of the variable definition and add the block name
                var_with_block = var_def.copy()
                var_with_block['block_name'] = block_name
                reverse_map[exported_name].append(var_with_block)
    
    return reverse_map


def get_nested_value(obj: Any, path: str) -> Any:
    """
    Get a nested value from an object using a dot-separated path.
    
    Args:
        obj: The object to traverse
        path: Dot-separated path (e.g., "Parameters.ContactFlowId")
        
    Returns:
        The value at the path, or None if not found
    """
    if not path:
        return obj
        
    keys = path.split('.')
    current = obj
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current


def set_nested_value(obj: Any, path: str, value: Any) -> bool:
    """
    Set a nested value in an object using a dot-separated path.
    
    Args:
        obj: The object to modify
        path: Dot-separated path (e.g., "Parameters.ContactFlowId")
        value: The value to set
        
    Returns:
        True if successful, False otherwise
    """
    if not path:
        return False
        
    keys = path.split('.')
    current = obj
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if isinstance(current, dict):
            if key not in current:
                current[key] = {}
            current = current[key]
        else:
            return False
    
    # Set the final value
    if isinstance(current, dict):
        current[keys[-1]] = value
        return True
    
    return False


def should_variableize(value: Any) -> bool:
    """
    Check if a value should be variableized.
    
    Args:
        value: The value to check
        
    Returns:
        True if the value should be variableized, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    # Don't variableize if it already starts with '$.' as Connect variables are already prefixed with '$.'
    if value.startswith('$.'):
        return False
    
    # Don't variableize empty strings
    if not value.strip():
        return False
    
    return True


def variableize_flow(flow_data: Dict[str, Any], reverse_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Variableize a flow by processing its actions.
    
    Args:
        flow_data: The flow data to process
        reverse_map: The reverse map of block definitions
        
    Returns:
        The variableized flow data
    """
    # Create a deep copy to avoid modifying the original
    flow_copy = json.loads(json.dumps(flow_data))
    
    actions = flow_copy.get('Actions', [])
    
    for action in actions:
        action_type = action.get('Type')
        action_identifier = action.get('Identifier')
        if not action_type or not action_identifier:
            continue
        
        # Look up variables for this block type
        variables = reverse_map.get(action_type, [])
        
        for var_def in variables:
            actions_path_value = var_def.get('actionsRelativePathValue')
            if not actions_path_value:
                continue
            
            # Get the current value at the path
            current_value = get_nested_value(action, actions_path_value)
            
            if current_value is not None and should_variableize(current_value):
                # Get the block name from the variable definition
                block_name = var_def.get('block_name', 'unknown')
                var_name = var_def.get('name', 'unknown_variable')
                
                # Create the variable name using the convention: {block_name}_{var_name}_{action_identifier}
                full_var_name = f"{block_name}_{var_name}_{action_identifier}"
                
                # Variableize the value
                variableized_value = f"${{{full_var_name}}}"
                
                # Set the variableized value in the actions
                set_nested_value(action, actions_path_value, variableized_value)
                
                # Check if we need to variableize metadata paths
                metadata_path_key = var_def.get('metadataRelativePathKey')
                if metadata_path_key and isinstance(metadata_path_key, dict) and metadata_path_key.get('used') == True:
                    paths = metadata_path_key.get('paths', [])
                    for path in paths:
                        # Construct the full metadata path: Metadata.ActionMetadata.{action_identifier}.{path}
                        metadata_full_path = f"Metadata.ActionMetadata.{action_identifier}.{path}"
                        
                        # Get the current metadata value
                        metadata_value = get_nested_value(flow_copy, metadata_full_path)
                        
                        if metadata_value is not None and should_variableize(metadata_value):
                            # Set the same variableized value in the metadata
                            set_nested_value(flow_copy, metadata_full_path, variableized_value)
    
    return flow_copy


def process_flow_file(flow_file_path: str, reverse_map: Dict[str, List[Dict[str, Any]]], output_dir: Path) -> None:
    """
    Process a single flow file.
    
    Args:
        flow_file_path: Path to the flow file
        reverse_map: The reverse map of block definitions
        output_dir: Directory to save the variableized flow
    """
    try:
        # Load the flow file
        with open(flow_file_path, 'r', encoding='utf-8') as f:
            flow_data = json.load(f)
        
        # Variableize the flow
        variableized_flow = variableize_flow(flow_data, reverse_map)
        
        # Create output filename in the output directory
        flow_path = Path(flow_file_path)
        output_path = output_dir / f"{flow_path.stem}_variableized{flow_path.suffix}"
        
        # Write the variableized flow
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(variableized_flow, f, indent=2)
        
        print(f"Processed: {flow_file_path} -> {output_path}")
        
    except Exception as e:
        print(f"Error processing {flow_file_path}: {e}")


def main():
    """Main function."""
    # Check if arguments were provided
    if len(sys.argv) < 2:
        print("Usage: python flow_variableizer.py --all")
        print("   or: python flow_variableizer.py --single")
        print("   or: python flow_variableizer.py <flow_file_path>")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path("outputted/flows")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Load block definitions
    block_definitions_path = "block-definitions.jsonc"
    if not os.path.exists(block_definitions_path):
        print(f"Error: {block_definitions_path} not found")
        sys.exit(1)
    
    print("Loading block definitions...")
    block_definitions = load_block_definitions(block_definitions_path)
    
    print("Creating reverse map...")
    reverse_map = create_reverse_map(block_definitions)
    
    print(f"Found {len(reverse_map)} exported block types:")
    for block_type, vars_list in reverse_map.items():
        print(f"  {block_type}: {len(vars_list)} variables")
    
    # Process flow files
    if sys.argv[1] == "--all":
        # Process all flow files in the sample flows directory
        sample_flows_dir = Path("sample flows")
        if not sample_flows_dir.exists():
            print(f"Error: {sample_flows_dir} directory not found")
            sys.exit(1)
        
        flow_files = list(sample_flows_dir.glob("*.json"))
        print(f"\nProcessing {len(flow_files)} flow files...")
        
        for flow_file in flow_files:
            process_flow_file(str(flow_file), reverse_map, output_dir)
    elif sys.argv[1] == "--single":
        # Process just the custom_cq_LATEST.json file
        flow_file_path = "sample flows/custom_cq_LATEST.json"
        if not os.path.exists(flow_file_path):
            print(f"Error: {flow_file_path} not found")
            sys.exit(1)
        
        print(f"\nProcessing single flow file: {flow_file_path}")
        process_flow_file(flow_file_path, reverse_map, output_dir)
    else:
        # Process a specific flow file provided as argument
        flow_file_path = sys.argv[1]
        if not os.path.exists(flow_file_path):
            print(f"Error: {flow_file_path} not found")
            sys.exit(1)
        
        print(f"\nProcessing flow file: {flow_file_path}")
        process_flow_file(flow_file_path, reverse_map, output_dir)
    
    print("\nDone!")


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Flow Variableizer Script

This script reads block-definitions.jsonc to create a reverse map of exported JSON block names,
then processes flow files to variableize values that don't start with '$.' for Terraform templating.
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Any
from pathlib import Path


def load_block_definitions(file_path: str) -> Dict[str, Any]:
    """Load the block definitions from the JSONC file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove comments (simple approach - remove lines starting with //)
        lines = content.split("\n")
        cleaned_lines = []
        for line in lines:
            if "//" in line:
                # Remove everything from // onwards
                comment_pos = line.find("//")
                cleaned_line = line[:comment_pos].rstrip()
                if cleaned_line:  # Only add non-empty lines
                    cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        
        cleaned_content = "\n".join(cleaned_lines)
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
                
            # Skip block definitions that don't have status 'complete'
            status = block_config.get("status")
            if status != "complete":
                continue
                
            exported_name = block_config.get("exportedJsonBlockName")
            if not exported_name:
                continue
                
            vars_list = block_config.get("vars", [])
            
            # Initialize the list for this exported name if it doesn't exist
            if exported_name not in reverse_map:
                reverse_map[exported_name] = []
            
            # Add all variables for this block configuration, including the block name
            for var_def in vars_list:
                # Create a copy of the variable definition and add the block name
                var_with_block = var_def.copy()
                var_with_block["block_name"] = block_name
                reverse_map[exported_name].append(var_with_block)
    
    return reverse_map


def get_nested_value(obj: Any, path: str) -> Any:
    """
    Get a nested value from an object using a dot/bracket-separated path.
    Handles keys with spaces and array indices (e.g., audio[0].id).
    """
    import re
    if not path:
        return obj

    # Parse the path into components, handling both dot and bracket notation
    def parse_path(path):
        parts = []
        current = ""
        bracket = False
        for char in path:
            if char == "." and not bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                if char == "[":
                    bracket = True
                elif char == "]":
                    bracket = False
                current += char
        if current:
            parts.append(current)
        return parts

    parts = parse_path(path)
    current_obj = obj
    i = 0
    while i < len(parts):
        part = parts[i]
        array_match = re.match(r"^([\w\s]+)\[(\d+)\]$", part)
        if array_match:
            key, idx = array_match.group(1), int(array_match.group(2))
            if key in current_obj and isinstance(current_obj[key], list):
                current_obj = current_obj[key][idx]
            else:
                return None
        elif part in current_obj:
            current_obj = current_obj[part]
        elif i + 1 < len(parts):
            # Try joining this and the next part with a space
            combined_key = f"{part} {parts[i+1]}"
            if combined_key in current_obj:
                current_obj = current_obj[combined_key]
                i += 1
            else:
                return None
        else:
            return None
        i += 1
    return current_obj


def get_nested_values_with_wildcards(obj: Any, path: str) -> List[tuple]:
    """
    Recursively get nested values from an object using a path that may contain any number of wildcards ([*]).
    Returns a list of (value, full_path_to_value) tuples.
    """
    def parse_path_components(path: str) -> list:
        components = []
        current = ""
        bracket_level = 0
        
        for char in path:
            if char == "[":
                bracket_level += 1
                current += char
            elif char == "]":
                bracket_level -= 1
                current += char
            elif char == "." and bracket_level == 0:
                if current:
                    components.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            components.append(current)
        
        # Post-process to split components that contain both key and wildcard
        # e.g., 'Steps[*]' should become ['Steps', '[*]']
        final_components = []
        for component in components:
            if "[" in component and component != "[*]":
                # Split at the first '[' to separate key from bracket notation
                parts = component.split("[", 1)
                if parts[0]:  # Add the key part if not empty
                    final_components.append(parts[0])
                final_components.append("[" + parts[1])  # Add the bracket part
            else:
                final_components.append(component)
        
        return final_components

    def walk(obj, components, path_so_far):
        if not components:
            return [(obj, path_so_far)]
        comp = components[0]
        rest = components[1:]
        # Wildcard array
        if comp == "[*]":
            if isinstance(obj, list):
                results = []
                for i, item in enumerate(obj):
                    new_path = f"{path_so_far}[{i}]" if path_so_far else f"[{i}]"
                    results.extend(walk(item, rest, new_path))
                return results
            else:
                return []
        # Array index
        elif comp.startswith("[") and comp.endswith("]"):
            try:
                idx = int(comp[1:-1])
                if isinstance(obj, list) and 0 <= idx < len(obj):
                    new_path = f"{path_so_far}[{idx}]" if path_so_far else f"[{idx}]"
                    return walk(obj[idx], rest, new_path)
                else:
                    return []
            except Exception as e:
                return []
        # Dict key
        else:
            if isinstance(obj, dict) and comp in obj:
                new_path = f"{path_so_far}.{comp}" if path_so_far else comp
                return walk(obj[comp], rest, new_path)
            else:
                return []
    
    components = parse_path_components(path)
    return walk(obj, components, "")


def set_nested_value(obj: Any, path: str, value: Any) -> None:
    """
    Set a nested value in an object using a dot/bracket-separated path.
    Supports array indices (e.g., Steps[0].Expression.AttributeCondition...)
    """
    import re
    # Parse the path into components, handling both dot and bracket notation
    def parse_path(path):
        # Split by dot, but keep bracketed indices as part of the component
        parts = []
        current = ""
        bracket = False
        for char in path:
            if char == "." and not bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                if char == "[":
                    bracket = True
                elif char == "]":
                    bracket = False
                current += char
        if current:
            parts.append(current)
        return parts

    parts = parse_path(path)
    current = obj
    for i, part in enumerate(parts):
        # Handle array index, e.g., Steps[0]
        array_match = re.match(r"^(\w+)\[(\d+)\]$", part)
        if array_match:
            key, idx = array_match.group(1), int(array_match.group(2))
            if key not in current or not isinstance(current[key], list):
                raise KeyError(f"Key '{key}' not found or not a list at {'.'.join(parts[:i+1])}")
            if i == len(parts) - 1:
                current[key][idx] = value
            else:
                current = current[key][idx]
        else:
            if i == len(parts) - 1:
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]


def should_variableize(value: Any) -> bool:
    """
    Check if a value should be variableized.
    
    Args:
        value: The value to check
        
    Returns:
        True if the value should be variableized, False otherwise
    """
    # Handle lists - check if it's a non-empty list of strings
    if isinstance(value, list):
        if not value:  # Empty list
            return False
        # Check if all items are strings and should be variableized
        return all(isinstance(item, str) and should_variableize_string(item) for item in value)
    
    # Handle strings
    if isinstance(value, str):
        return should_variableize_string(value)
    
    return False


def should_variableize_string(value: str) -> bool:
    """
    Check if a string value should be variableized.
    
    Args:
        value: The string value to check
        
    Returns:
        True if the value should be variableized, False otherwise
    """
    # Don't variableize if it already starts with '$.' as Connect variables are already prefixed with '$.'
    if value.startswith("$."):
        return False
    
    # Don't variableize if it already starts with '${' as it's already variableized
    if value.startswith("${"):
        return False
    
    # Don't variableize empty strings
    if not value.strip():
        return False
    
    return True


def process_start_outbound_email_contact(action: Dict[str, Any], flow_copy: Dict[str, Any], action_identifier: str, reverse_map: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Process StartOutboundEmailContact actions to convert email format and update metadata.
    
    Args:
        action: The action to process
        flow_copy: The flow data to update
        action_identifier: The identifier of the action
        reverse_map: The reverse map of block definitions
    """
    parameters = action.get("Parameters", {})
    from_email = parameters.get("FromEmailAddress", {})
    
    email_address = from_email.get("EmailAddress")
    display_name = from_email.get("DisplayName", "")
    
    # Always construct the variable name and use it in metadata
    if email_address and isinstance(email_address, str) and email_address.strip() and not email_address.startswith("$."):
        # Find the variable definition for the email address path
        variables = reverse_map.get("StartOutboundEmailContact", [])
        email_var_def = None
        
        for var_def in variables:
            if var_def.get("actionsRelativePathValue") == "Parameters.FromEmailAddress.EmailAddress":
                email_var_def = var_def
                break
        
        if email_var_def:
            # Extract block name and variable name from the variable definition
            block_name = email_var_def.get("block_name", "unknown")
            var_name = email_var_def.get("name", "unknown_variable")
            
            # Create the variable name using the original convention
            # Remove spaces from action_identifier and replace with hyphens
            clean_identifier = action_identifier.replace(" ", "-")
            full_var_name = f"{block_name}_{var_name}_{clean_identifier}"
            
            # Create the combined format: DisplayName<VariableName>
            combined_format = f"{display_name}<${{{full_var_name}}}>"
            
            # Update the metadata
            metadata_path = f"Metadata.ActionMetadata.{action_identifier}.parameters.FromEmailAddress.EmailAddress.displayName"
            set_nested_value(flow_copy, metadata_path, combined_format)


def process_authenticate_participant(action: Dict[str, Any], flow_copy: Dict[str, Any], action_identifier: str, reverse_map: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Process AuthenticateParticipant actions to handle Cognito configuration display names.
    
    Args:
        action: The action to process
        flow_copy: The flow data to update
        action_identifier: The identifier of the action
        reverse_map: The reverse map of block definitions
    """
    parameters = action.get("Parameters", {})
    cognito_config = parameters.get("CognitoConfiguration", {})
    
    user_pool_arn = cognito_config.get("UserPoolArn")
    app_client_id = cognito_config.get("AppClientId")
    
    # Get the current metadata values
    user_pool_metadata_path = f"Metadata.ActionMetadata.{action_identifier}.parameters.CognitoConfiguration.UserPoolArn.displayName"
    app_client_metadata_path = f"Metadata.ActionMetadata.{action_identifier}.parameters.CognitoConfiguration.AppClientId.displayName"
    
    user_pool_display_name = get_nested_value(flow_copy, user_pool_metadata_path)
    app_client_display_name = get_nested_value(flow_copy, app_client_metadata_path)
    
    # Find variable definitions
    variables = reverse_map.get("AuthenticateParticipant", [])
    user_pool_var_def = None
    app_client_var_def = None
    
    for var_def in variables:
        if var_def.get("actionsRelativePathValue") == "Parameters.CognitoConfiguration.UserPoolArn":
            user_pool_var_def = var_def
        elif var_def.get("actionsRelativePathValue") == "Parameters.CognitoConfiguration.AppClientId":
            app_client_var_def = var_def
    
    # Process User Pool ARN display name
    if user_pool_arn and user_pool_display_name and user_pool_var_def:
        # Extract block name and variable name
        block_name = user_pool_var_def.get("block_name", "unknown")
        var_name = user_pool_var_def.get("name", "unknown_variable")
        
        # Create the variable name using the original convention
        # Remove spaces from action_identifier and replace with hyphens
        clean_identifier = action_identifier.replace(" ", "-")
        full_var_name = f"{block_name}_{var_name}_{clean_identifier}"
        
        # Parse the display name: "User pool - iv2qy(Id:eu-west-2_NAluo8IPf, Europe London)"
        # Keep "User pool", remove everything from dash to opening parenthesis, keep "Id:", add variable after colon
        if " - " in user_pool_display_name and "(Id:" in user_pool_display_name:
            # Split at the dash and take the first part
            base_name = user_pool_display_name.split(" - ")[0].strip()
            # Find the Id: part
            id_part_start = user_pool_display_name.find("(Id:")
            if id_part_start != -1:
                # Keep everything up to and including "Id:"
                id_colon_part = user_pool_display_name[id_part_start:user_pool_display_name.find(":", id_part_start) + 1]
                # Create new display name: "User pool (Id:${variable})"
                new_display_name = f"{base_name} {id_colon_part}${{{full_var_name}}})"
                set_nested_value(flow_copy, user_pool_metadata_path, new_display_name)
    
    # Process App Client ID display name
    if app_client_id and app_client_display_name and app_client_var_def:
        # Extract block name and variable name
        block_name = app_client_var_def.get("block_name", "unknown")
        var_name = app_client_var_def.get("name", "unknown_variable")
        
        # Create the variable name using the original convention
        # Remove spaces from action_identifier and replace with hyphens
        clean_identifier = action_identifier.replace(" ", "-")
        full_var_name = f"{block_name}_{var_name}_{clean_identifier}"
        
        # Parse the display name: "My M2M app - iv2qy(Id:1bcees0qmpbplsifmm6ed46lfq)"
        # Keep the app name, remove everything from dash to opening parenthesis, keep "Id:", add variable after colon
        if " - " in app_client_display_name and "(Id:" in app_client_display_name:
            # Split at the dash and take the first part
            base_name = app_client_display_name.split(" - ")[0].strip()
            # Find the Id: part
            id_part_start = app_client_display_name.find("(Id:")
            if id_part_start != -1:
                # Keep everything up to and including "Id:"
                id_colon_part = app_client_display_name[id_part_start:app_client_display_name.find(":", id_part_start) + 1]
                # Create new display name: "My M2M app (Id:${variable})"
                new_display_name = f"{base_name} {id_colon_part}${{{full_var_name}}})"
                set_nested_value(flow_copy, app_client_metadata_path, new_display_name)


def process_loop_prompts(action: Dict[str, Any], flow_copy: Dict[str, Any], action_identifier: str, reverse_map: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Process MessageParticipantIteratively actions to handle loop prompts with audio IDs.
    
    Args:
        action: The action to process
        flow_copy: The flow data to update
        action_identifier: The identifier of the action
        reverse_map: The reverse map of block definitions
    """
    # Find the variable definition for PromptId
    variables = reverse_map.get("MessageParticipantIteratively", [])
    prompt_var_def = None
    
    for var_def in variables:
        if var_def.get("actionsRelativePathValue") == "Parameters.Messages[*].PromptId":
            prompt_var_def = var_def
            break
    
    if not prompt_var_def:
        return
    
    # Get the block name and variable name
    block_name = prompt_var_def.get("block_name", "unknown")
    var_name = prompt_var_def.get("name", "unknown_variable")
    
    # Process each message and variableize PromptId + corresponding audio ID
    messages = action.get("Parameters", {}).get("Messages", [])
    prompt_id_count = 0
    
    for i, msg in enumerate(messages):
        if "PromptId" in msg and should_variableize(msg["PromptId"]):
            # Create the variable name (cleaned for variable, raw for metadata)
            step_suffix = f"_message{i+1}"
            clean_identifier = action_identifier.replace(" ", "-")
            full_var_name = f"{block_name}_{var_name}{step_suffix}_{clean_identifier}"
            variableized_value = f"${{{full_var_name}}}"
            
            # Variableize the PromptId in the action
            action["Parameters"]["Messages"][i]["PromptId"] = variableized_value
            
            # Variableize the corresponding audio ID in metadata (use raw action_identifier)
            audio_path = f"Metadata.ActionMetadata.{action_identifier}.audio[{prompt_id_count}].id"
            audio_value = get_nested_value(flow_copy, audio_path)
            if audio_value is not None and should_variableize(audio_value):
                set_nested_value(flow_copy, audio_path, variableized_value)
            prompt_id_count += 1


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
    
    actions = flow_copy.get("Actions", [])
    
    for action in actions:
        action_type = action.get("Type")
        action_identifier = action.get("Identifier")
        if not action_type or not action_identifier:
            continue
        
        # Custom logic for StartOutboundEmailContact
        if action_type == "StartOutboundEmailContact":
            process_start_outbound_email_contact(action, flow_copy, action_identifier, reverse_map)
        
        # Custom logic for AuthenticateParticipant
        if action_type == "AuthenticateParticipant":
            process_authenticate_participant(action, flow_copy, action_identifier, reverse_map)
        
        # Custom logic for MessageParticipantIteratively
        if action_type == "MessageParticipantIteratively":
            process_loop_prompts(action, flow_copy, action_identifier, reverse_map)
        
        # Look up variables for this block type
        variables = reverse_map.get(action_type, [])
        
        for var_def in variables:
            actions_path_value = var_def.get("actionsRelativePathValue")
            actions_path_key = var_def.get("actionsRelativePathKey")
            
            if not actions_path_value:
                continue
            
            # Handle cases where actionsRelativePathKey is defined (e.g., Parameters.References.*)
            if actions_path_key:
                # Get all keys at the actionsRelativePathKey path
                key_path = actions_path_key.replace(".*", "")
                keys_obj = get_nested_value(action, key_path)
                
                if isinstance(keys_obj, dict):
                    # Loop through all keys in the object
                    for key_name in keys_obj.keys():
                        # Replace * with the actual key name in the actionsRelativePathValue
                        actual_path = actions_path_value.replace("*", key_name)
                        
                        # Get the value at the actual path
                        current_value = get_nested_value(action, actual_path)
                        
                        if current_value is not None and should_variableize(current_value):
                            # Get the block name from the variable definition
                            block_name = var_def.get("block_name", "unknown")
                            
                            # Create variable name using the actual key name
                            # Replace ${actionsRelativePathKey} with the actual key name
                            var_name_template = var_def.get("name", "unknown_variable")
                            var_name = var_name_template.replace("${actionsRelativePathKey}", key_name)
                            
                            # Create the variable name using the original convention
                            # Remove spaces from action_identifier and replace with hyphens
                            clean_identifier = action_identifier.replace(" ", "-")
                            full_var_name = f"{block_name}_{var_name}_{clean_identifier}"
                            
                            # Variableize the value
                            variableized_value = f"${{{full_var_name}}}"
                            
                            # Set the variableized value in the actions
                            set_nested_value(action, actual_path, variableized_value)
                            
                            # Check if we need to variableize metadata paths
                            metadata_paths = var_def.get("metadataRelativePathKey", {}).get("paths", [])
                            if metadata_paths:
                                for metadata_path in metadata_paths:
                                    # Construct the full metadata path
                                    full_metadata_path = f"Metadata.ActionMetadata.{action_identifier}.{metadata_path}"
                                    
                                    # Handle wildcards in metadata paths (e.g., audio[*].id)
                                    if "[*]" in metadata_path:
                                        # Get all values at the wildcard path
                                        metadata_values_with_paths = get_nested_values_with_wildcards(
                                            flow_copy.get("Metadata", {}).get("ActionMetadata", {}).get(action_identifier, {}),
                                            metadata_path
                                        )
                                        
                                        # Variableize each metadata value that corresponds to this action value
                                        for metadata_value, metadata_full_path in metadata_values_with_paths:
                                            if metadata_value is not None and should_variableize(metadata_value):
                                                # Use the same variable name for the metadata
                                                set_nested_value(flow_copy, f"Metadata.ActionMetadata.{action_identifier}.{metadata_full_path}", variableized_value)
                                    else:
                                        # Handle non-wildcard metadata paths
                                        metadata_value = get_nested_value(flow_copy, full_metadata_path)
                                        if metadata_value is not None and should_variableize(metadata_value):
                                            set_nested_value(flow_copy, full_metadata_path, variableized_value)
                
                continue  # Skip the regular processing for this variable definition
            
            # Regular processing for variables without actionsRelativePathKey
            # Get all values at the path (handles wildcards)
            values_with_paths = get_nested_values_with_wildcards(action, actions_path_value)
            
            for current_value, full_path in values_with_paths:
                if current_value is not None and should_variableize(current_value):
                    # Get the block name from the variable definition
                    block_name = var_def.get("block_name", "unknown")
                    var_name = var_def.get("name", "unknown_variable")
                    
                    # Check if this is a wildcard path with array indices (for set_routing_criteria, loop_prompts, etc.)
                    step_suffix = ""
                    if "[*]" in actions_path_value and ("[" in full_path and "]" in full_path):
                        # Extract array name and index from the path (e.g., "Steps[0]" -> "step1", "Messages[1]" -> "message2")
                        import re
                        array_match = re.search(r"(\w+)\[(\d+)\]", full_path)
                        if array_match:
                            array_name = array_match.group(1)
                            array_index = int(array_match.group(2))
                            
                            # Create human-friendly suffix based on array name
                            if array_name == "Steps":
                                step_suffix = f"_step{array_index + 1}"  # Convert 0-based to 1-based
                            elif array_name == "Messages":
                                step_suffix = f"_message{array_index + 1}"  # Convert 0-based to 1-based
                            else:
                                # Generic fallback for other array types
                                step_suffix = f"_{array_name.lower()}{array_index + 1}"
                    
                    # Create the variable name using the original convention
                    # Remove spaces from action_identifier and replace with hyphens
                    clean_identifier = action_identifier.replace(" ", "-")
                    full_var_name = f"{block_name}_{var_name}{step_suffix}_{clean_identifier}"
                    
                    # Variableize the value
                    variableized_value = f"${{{full_var_name}}}"
                    
                    # Set the variableized value in the actions
                    set_nested_value(action, full_path, variableized_value)
                    
                    # Check if we need to variableize metadata paths
                    metadata_paths = var_def.get("metadataRelativePathKey", {}).get("paths", [])
                    if metadata_paths:
                        for metadata_path in metadata_paths:
                            # Construct the full metadata path
                            full_metadata_path = f"Metadata.ActionMetadata.{action_identifier}.{metadata_path}"
                            
                            # Handle wildcards in metadata paths (e.g., audio[*].id)
                            if "[*]" in metadata_path:
                                # Get all values at the wildcard path
                                metadata_values_with_paths = get_nested_values_with_wildcards(
                                    flow_copy.get("Metadata", {}).get("ActionMetadata", {}).get(action_identifier, {}),
                                    metadata_path
                                )
                                
                                # Variableize each metadata value that corresponds to this action value
                                for metadata_value, metadata_full_path in metadata_values_with_paths:
                                    if metadata_value is not None and should_variableize(metadata_value):
                                        # Use the same variable name for the metadata
                                        set_nested_value(flow_copy, f"Metadata.ActionMetadata.{action_identifier}.{metadata_full_path}", variableized_value)
                            else:
                                # Handle non-wildcard metadata paths
                                metadata_value = get_nested_value(flow_copy, full_metadata_path)
                                if metadata_value is not None and should_variableize(metadata_value):
                                    set_nested_value(flow_copy, full_metadata_path, variableized_value)
    
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
        with open(flow_file_path, "r", encoding="utf-8") as f:
            flow_data = json.load(f)
        
        # Variableize the flow
        variableized_flow = variableize_flow(flow_data, reverse_map)
        
        # Create output filename in the output directory
        flow_path = Path(flow_file_path)
        output_path = output_dir / f"{flow_path.stem}_variableized{flow_path.suffix}"
        
        # Write the variableized flow
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(variableized_flow, f, indent=2)
        
        print(f"Processed: {flow_file_path} -> {output_path}")
        
    except Exception as e:
        print(f"Error processing {flow_file_path}: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Variableize AWS Connect flow files for Terraform templating",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flow_variableizer.py --file "sample flows/custom_ow.json"
  python flow_variableizer.py --folder "sample flows"
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to a specific flow file to process")
    group.add_argument("--folder", type=str, help="Path to a folder containing flow files to process")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path("outputted_flows")
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
        print(f"{block_type}: {len(vars_list)} variables")
    
    # Process flow files
    if args.file:
        # Process a specific flow file
        flow_file_path = args.file
        if not os.path.exists(flow_file_path):
            print(f"Error: {flow_file_path} not found")
            sys.exit(1)
        
        print(f"Processing flow file: {flow_file_path}")
        process_flow_file(flow_file_path, reverse_map, output_dir)
        
    elif args.folder:
        # Process all flow files in the specified directory
        folder_path = Path(args.folder)
        if not folder_path.exists():
            print(f"Error: {folder_path} directory not found")
            sys.exit(1)
        
        flow_files = list(folder_path.glob("*.json"))
        if not flow_files:
            print(f"No JSON files found in {folder_path}")
            sys.exit(1)
        
        print(f"Processing {len(flow_files)} flow files from {folder_path}...")
        for flow_file in flow_files:
            process_flow_file(str(flow_file), reverse_map, output_dir)
    
    print("Done!")


if __name__ == "__main__":
    main()

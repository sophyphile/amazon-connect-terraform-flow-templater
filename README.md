
# Flow Templater

A Python tool to variableize AWS Connect flow files for Terraform templating. This tool processes JSON flow files and converts specific values into Terraform variables, making it easier to manage AWS Connect flows as infrastructure code.

## Overview

The Flow Variableizer reads a `block-definitions.jsonc` file to understand which values should be variableized, then processes AWS Connect flow files to replace those values with Terraform variable placeholders (e.g., `${variable_name}`). This enables you to create reusable flow templates that can be deployed with different configurations using Terraform.

## Features

- **Smart Variableization**: Only variableizes values that don't already start with `$.` (Connect variables) or `${` (already variableized)
- **Dynamic Key Support**: Handles dynamic keys in objects (e.g., `Parameters.References.*`) by processing all keys in the object
- **Array Index Handling**: Creates human-friendly variable name suffixes for array elements in Connect blocks like Loop Prompts and Set Routing Criteria (e.g., `_step1`, `_message2`)
- **Metadata Synchronization**: Updates both action parameters and metadata display names
- **Batch Processing**: Process single files or entire folders of flow files

## Prerequisites

- Python 3.6 or higher
- AWS Connect flow files in JSON format
- `block-definitions.jsonc` file defining which values to variableize

## Installation

1. Clone or download this repository
2. Ensure you have the required files:
   - `flow_variableizer.py` - The main script
   - `block-definitions.jsonc` - Block definitions file in the same folder as the `flow_variableizer.py`
   - Your AWS Connect flow files (JSON format)

## Usage

Ensure that if Connect blocks are named on your contact flows, the names only contain the following characters: letters, digits, underscores (_), and hyphens (-).

### Command Line Interface

The script supports two main modes:

#### Process a Single Flow File

```bash
python flow_variableizer.py --file "path/to/your/flow.json"
```

#### Process All Flow Files in a Directory

```bash
python flow_variableizer.py --folder "path/to/flow/directory"
```

### Examples

```bash
# Process a specific flow file
python flow_variableizer.py --file "sample_input_flows/agent_hold.json"

# Process all JSON files in the sample flows directory
python flow_variableizer.py --folder "sample_input_flows"
```

## Output

- Variableized flow templates are saved to the `flow_templates` directory
- Output files are named with the Terraform `tftpl` suffix (e.g., `agent_hold.tftpl`)
- Original flow files are not modified

## Block Definitions File

The `block-definitions.jsonc` file defines which values should be variableized for each AWS Connect block type. It contains:

- **Block configurations** with status, exported JSON block names, and variable definitions
- **Variable paths** specifying where to find values in the flow structure
- **Metadata paths** for updating display names in the Connect console

### Example Block Definition

```jsonc
{
  "call_phone_number": [
    {
      "status": "complete",
      "exportedJsonBlockName": "CompleteOutboundCall",
      "vars": [
        {
          "name": "caller_id_number",
          "actionsRelativePathValue": "Parameters.CallerId.Number"
        }
      ]
    }
  ]
}
```

## Variable Naming Convention

Variables are named using the pattern:

`
{block_name}_{variable_name}_{block_identifier}
`

For array elements, human-friendly suffixes are added:

- `Steps[0]` → `_step1`
- `Messages[1]` → `_message2`

### Example Variable Names

- `call_phone_number_caller_id_number_c6066611-4d2a-4d8a-88ed-b3b72679c047`
- `create_task_flow_to_run_task_arn_create-task-manual` (the block identifier is 'create-task-manual' here as the Connect "block name" string is used when provided by the user when building the contact flow; if this is not available Connect assigns a random alphanumeric string as the block name as seen in the above example)
- `create_task_set_references_key123_value_create-task-manual`

## File Structure

```md
flow-templater/
├── flow_variableizer.py          # Main script
├── block-definitions.jsonc       # Block definitions
├── blocks-per-flow.jsonc         # Blocks available in each flow type
├── sample_input_flows/           # Example flow files
│   ├── agent_hold.json
│   ├── outbound_whisper.json
│   ├── customer_queue.json
│   └── ...
├── flow_templates/               # Generated variableized Terraform template files
│   ├── outbound_whisper.tftpl
│   ├── customer_queue.tftpl
│   └── ...
├── sample_outputted_flows        # JSON flow files rendered by Terraform using the variableized template
│   ├── outbound_whisper_rendered.json
│   ├── customer_queue_rendered.json
│   └── ...
└── README.md                     # This file
```

## How It Works

1. **Load Block Definitions**: Reads `block-definitions.jsonc` and creates a reverse map
2. **Process Flow Files**: For each flow file:
   - Load the JSON flow data
   - Iterate through all actions (Connect blocks)
   - Apply variable definitions to each action type
   - Handle dynamic keys and array indices
   - Update both action parameters and metadata
3. **Generate Output**: Save variableized flows to `flow_templates` directory

## Error Handling

- Invalid JSON files are skipped with error messages
- Missing block definitions file causes script to exit
- Non-existent input files/directories are reported
- Syntax errors in block definitions are caught and reported

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with sample flow files
5. Add tests if relevant
6. Submit a pull request

## License

This project is licensed under the [MIT License](./LICENSE).

## Outstanding Issues

You may encounter errors with the Send Message Connect block. A fix is incoming.

## Support

For issues or questions:

1. Check the error messages for common problems
2. Verify your `block-definitions.jsonc` file is valid JSON
3. Ensure your flow files are valid AWS Connect JSON format
4. Open an issue on GitHub with details about the problem

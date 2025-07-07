# to do & features

## to do

- following identifiers not converted as block doesn't exist in block-definitions.jsonc:
  - get-customer-input-lex-select+promptid
  - get-customer-input-lex-arn+s3filepatb
  - exportedJsonBlockType: ConnectParticipantWithLexBot
- handle metadata if "used" = true
  - if a var which has a metadataRelativePathKey=true is found, but the metadata path is not discovered or the current value is empty, make an informative log and throw an error.
- deal with * in actionsRelativePathKey for both lists and objects, and in actionsPathRelativeValue for both lists and objects.
  - deal with scenario where actionsRelativePathKey is null.
  - set references - set name according to reference key.
  - ensure agent IDs in set_routing_criteria work -- would TF pass it in as a list?
  - if * is used in actionsRelativePathKey then loop through each item in the list, OR check which operator to use instead
  - think about for loop_prompts block, how to do the iteration
    - maybe delete things from the list once found a var.
    - would the customer pass the above as lists? or? maybe append "_1", "_2" to the variable names.
      - lists would be more user-friendly.
- naming the var
  - allow custom naming of vars
  - allow people to define this according to their naming convention somehow?
  - get rid of spaces in the variable name identifier and replace with _ or -, right?
- handle status = draft/complete
  - where status = draft do not use the vars
- error handling
  - informative errors that tell you which Connect block failed to be parsed???
    - how is that even possible (identifier)
- logging
- document the types for all vars on a README kinda thing
- include test cases
  - what are parameter default values when variables are not set in Connect?
- optionally provide input folder where original flow files are stored, optionally provide output folder where processed flow files are stored.
- make sure each block has the same exportedJsonBlockName in each flow
- if value of a key is empty do not variabilise it?
  - if this is not appropriate behaviour, check each parameter's default value when a value is not provided in Connect block.
- automate being informed when AWS adds new block or updates Amazon Connect blocks
- decide if the vars required to construct the display names for below need to be passed in by user
  - User pool name, region mapping of first part of ID to "Europe London" etc, App client name
- authenticate_customer in AuthenticateParticipant
  -         "parameters": {
          "CognitoConfiguration": {
            "UserPoolArn": {
              "displayName": "User pool - iv2qy(Id:eu-west-2_NAluo8IPf, Europe London)"
            },
            "AppClientId": {
              "displayName": "My M2M app - iv2qy(Id:1bcees0qmpbplsifmm6ed46lfq)"
            }
          }
        }
  - CognitoConfiguration displayName: `User pool - ${User pool name}(Id:${User Pool ID}, location)`
  - AppClientId displayName: `${App client name} (Id:${Client ID})`
- if StartOutboundEmailContact is used, then convert the following:

  ```"Parameters": {
      "FromEmailAddress": {
        "EmailAddress": "info@contactflow-templater.email.connect.aws",
        "DisplayName": "Info"
      }
    }

into Info<info@contactflow-templater.email.connect.aws>``` and slot into metadata parameters.FromEmailAddress.EmailAddress.displayName of the identifier

- try deploying to another env before being satisfied
  - risk of same identifier across envs causing problems.
- make a list of which inputs are available for which block.
- dry run/preview for diffs:
  - Print a clean diff or summary
  - Show which variables were variablized
  - Report any unmatched blocks or skipped paths
  - NOT write anything to disk

## features

- dry run
- show JSON with filled in values
- construct list of all matching variables that are used in the flow and ensure they are all variabilised
- include test cases
- automate being informed when AWS adds new block or updates Amazon Connect blocks
- how to make this maintainable - follow below structure for all blocks?
  - follow simple-to-understand structure for blocks-per-flow and block-definitions JSON files
- comprehensive list of which variables are variabilised in which blocks
- way to request a new block variable is added
- ensure all variabilised blocks can be created/imported in Terraform
- informative errors that tell you which Connect block failed to be parsed?
- send_message pending

## done

- actually make sure that each block looks the same in every flow
- check modules
- record which blocks are in which flows/modules

## issues

- create task block is not working when "use template" is selected.
  - createTask block doesn't work when selecting the "use template" option, as the parameters are not properly exported out from Connect for some reason.
- SMS number not fully tested (sendMessage block?)

## other notables

- fraud watchlist ID is not variabilised if used in Connect as it is not available to new customers.

## workflow

- make a list of which inputs are available for which block.
- only set vars in TF which appear as ${}; the rest are defined by Connect.
- identifier gets swapped by block name
- optionally provide input folder where original flow files are stored, optionally provide output folder where processed flow files are stored.
- be very clear about which values the customer is encouraged to select dynamically

## contributing

- way to contribute

## raising an issue

- way to request via an issue a new block variable which is added
- [!] Unmapped block type: "SuperNewAmazonBlock"
    → Found in flow: "EscalationFlow"
    → Suggest opening an issue at <https://github.com/your-org/templator>
    → Attach the block's full JSON:

    {
      "Type": "SuperNewAmazonBlock",
      "Parameters": { ... }
    }

## methodology

- why use python?
- collate all the possible vars for a particular exportedJsonBlockName across all its corresponding Connect block types
- be very clear about which values the customer is encouraged to select dynamically
- to keep it human readable and make the latest state of the file easily analysable, use human-friendly Connect block names as keys in block-definitions.jsonc, and as values in blocks-per-flow.jsonc
- default: true in blocks-per-flow.jsonc
- ensure all variabilised blocks' resources can be created/imported via TF; exclude if not?
  - could just be stored vars though
- vars are named by `${connect_block_name}_varname_${identifier_block}`

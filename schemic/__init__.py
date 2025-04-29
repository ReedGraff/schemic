import json
import copy
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema
from collections import OrderedDict
from typing import Any, Dict, Type, Tuple, List, Optional, Union

SCHEMIC_DEBUG = False

class SchemicModel(BaseModel):

    @classmethod
    def _is_ref_object(cls, ref: str, original_schema: dict) -> bool:
        """Helper to check if a $ref points to an object definition"""
        try:
            parts = ref.split('/')
            if len(parts) < 3 or parts[0] != '#' or parts[1] != '$defs':
                return False # Not a standard $defs ref
            def_name = parts[2]
            # Look for the definition within the potentially modified schema first
            definition = original_schema.get('$defs', {}).get(def_name, {})
            return definition.get('type') == 'object'
        except Exception:
            return False # Handle potential errors during parsing/lookup

    @classmethod
    def _get_ref_definition(cls, ref: str, original_schema: dict) -> Optional[Dict[str, Any]]:
        """Helper to get the definition pointed to by a $ref."""
        try:
            parts = ref.split('/')
            if len(parts) < 3 or parts[0] != '#' or parts[1] != '$defs':
                return None # Not a standard $defs ref
            def_name = parts[2]
            return original_schema.get('$defs', {}).get(def_name)
        except Exception:
            return None # Handle potential errors during parsing/lookup

    @classmethod
    def _modify_schema_recursive(cls, schema: Dict[str, Any], original_schema: Dict[str, Any], delete_props_with_defaults: bool = False, is_root: bool = False):
        """
        Recursively modifies the schema dictionary in place to meet OpenAI requirements.
        """
        if not isinstance(schema, dict):
            return

        schema_defs = original_schema.get('$defs', {})

        # Requirement #3: Remove defaults and handle enum defaults inline OR delete prop entirely
        if "properties" in schema:
            props = schema["properties"]
            new_props = OrderedDict() # Use OrderedDict for requirement #6 stability
            prop_keys_order = list(props.keys()) # Preserve original order initially

            # --- Requirement #6 Pre-computation: Identify potential 'type' discriminator ---
            # If this object is part of an anyOf in the original schema (or its definition is),
            # and it has a 'type' field derived from a default enum, mark it for reordering.
            type_prop_needs_reordering = False
            if 'type' in props and isinstance(props['type'], dict) and 'enum' in props['type'] and len(props['type']['enum']) == 1:
                # This check assumes the enum transformation from default happened *before* this point
                # or will happen in this pass. Let's refine the default handling first.
                pass # Revisit this after default handling logic

            # --- Handle Defaults (Requirement #3) ---
            for prop_name in prop_keys_order:
                prop_schema = props[prop_name]
                if isinstance(prop_schema, dict):
                    # Handle default in the property itself
                    if "default" in prop_schema:
                        if delete_props_with_defaults:
                            continue # Skip adding this property entirely
                        else:
                            # Original behavior: remove default, inline enum if applicable
                            default_value = prop_schema.pop("default")
                            # Check if it's a $ref to an enum definition
                            if "$ref" in prop_schema and prop_schema["$ref"].startswith("#/$defs/"):
                                ref_parts = prop_schema["$ref"].split('/')
                                if len(ref_parts) == 3:
                                    def_name = ref_parts[2]
                                    definition = schema_defs.get(def_name, {})
                                    if "enum" in definition:
                                        # Inline the enum with only the default value
                                        prop_schema.pop("$ref")
                                        prop_schema["type"] = definition.get("type", "string")
                                        prop_schema["enum"] = [default_value]
                                        prop_schema["title"] = prop_schema.get("title", definition.get("title", prop_name.capitalize()))
                                        # Mark 'type' for potential reordering if this is the 'type' field
                                        if prop_name == 'type':
                                            type_prop_needs_reordering = True
                                    # else: default removed, but wasn't an enum ref
                            # else: default removed, wasn't a ref or not handled enum ref

                    # Requirement #11: $refs cannot have additional keywords
                    if "$ref" in prop_schema:
                        # Keep only the $ref key
                        ref_value = prop_schema["$ref"]
                        prop_schema.clear()
                        prop_schema["$ref"] = ref_value

                    # Recurse into property schema *after* handling its default and ref cleanup
                    cls._modify_schema_recursive(prop_schema, original_schema, delete_props_with_defaults=delete_props_with_defaults)
                new_props[prop_name] = prop_schema # Add to ordered dict

            # --- Requirement #6 Reordering ---
            # Re-check if 'type' exists after potential deletion
            if type_prop_needs_reordering and 'type' in new_props:
                 new_props.move_to_end('type', last=False) # Move 'type' to the beginning

            schema["properties"] = new_props # Assign back the potentially reordered dict


        # Requirement #1: Add additionalProperties: False to objects
        # Only add if 'properties' exists. Pydantic handles Dict types correctly.
        if schema.get("type") == "object" and "properties" in schema and "additionalProperties" not in schema:
             schema["additionalProperties"] = False
        # Also apply to the root schema if it's an object
        if is_root and schema.get("type") == "object" and "additionalProperties" not in schema:
             schema["additionalProperties"] = False


        # Requirement #2 & #10: Adjust 'required' list for objects
        if schema.get("type") == "object" and "properties" in schema:
            new_required = []
            # Use the potentially reordered keys from properties
            prop_order = list(schema["properties"].keys())

            for prop_name in prop_order:
                prop_schema = schema["properties"][prop_name]
                is_object = prop_schema.get("type") == "object"
                has_properties = "properties" in prop_schema
                is_ref = "$ref" in prop_schema

                # Determine if the property represents an object without defined properties (like a dict)
                is_unrequireable_object = False
                if is_object and not has_properties:
                    # Inline object without properties (like a dict)
                    is_unrequireable_object = True
                elif is_ref:
                    ref_definition = cls._get_ref_definition(prop_schema["$ref"], original_schema)
                    if ref_definition:
                        ref_is_object = ref_definition.get("type") == "object"
                        ref_has_properties = "properties" in ref_definition
                        if ref_is_object and not ref_has_properties:
                            # Ref to an object without properties (like a dict)
                            is_unrequireable_object = True

                # Add to required list if it's not an unrequireable object type
                if not is_unrequireable_object:
                    new_required.append(prop_name)

            # Ensure 'type' is first in required if it was made first in properties (Req #6)
            # Re-check if 'type' exists after potential deletion and inclusion in required
            if type_prop_needs_reordering and 'type' in new_required:
                 # Check if 'type' was actually added (i.e., not an unrequireable object itself)
                 # This check might be redundant given the logic above, but safe to keep
                 if 'type' in new_required:
                    new_required.remove('type')
                    new_required.insert(0, 'type')

            # Only add 'required' key if it's not empty, Pydantic might omit it otherwise
            if new_required:
                schema["required"] = new_required
            elif "required" in schema: # Remove empty list if present
                del schema["required"]


        # Recurse into nested structures - process $defs first
        if "$defs" in schema:
            # Need to iterate through defs and modify them before they are referenced elsewhere
            for def_name, def_schema in schema.get('$defs', {}).items():
                 cls._modify_schema_recursive(def_schema, original_schema, delete_props_with_defaults=delete_props_with_defaults) # Pass flag

        # Now recurse into other parts that might reference $defs
        if "items" in schema:
            # Requirement #11 for items: If items uses $ref, clean it up
            if isinstance(schema["items"], dict) and "$ref" in schema["items"]:
                ref_value = schema["items"]["$ref"]
                schema["items"].clear()
                schema["items"]["$ref"] = ref_value
            cls._modify_schema_recursive(schema["items"], original_schema, delete_props_with_defaults=delete_props_with_defaults) # Pass flag

        if "additionalProperties" in schema and isinstance(schema["additionalProperties"], dict):
            # Requirement #11 for additionalProperties: If it uses $ref, clean it up
            if "$ref" in schema["additionalProperties"]:
                ref_value = schema["additionalProperties"]["$ref"]
                schema["additionalProperties"].clear()
                schema["additionalProperties"]["$ref"] = ref_value
            cls._modify_schema_recursive(schema["additionalProperties"], original_schema, delete_props_with_defaults=delete_props_with_defaults) # Pass flag

        if "anyOf" in schema:
            # Requirement #6 check (partially handled by 'type' reordering)
            # Recurse into inline schemas within anyOf, refs are handled via $defs pass
            new_any_of = []
            for sub_schema in schema["anyOf"]:
                if isinstance(sub_schema, dict):
                    # Requirement #11 for anyOf elements: If it uses $ref, clean it up
                    if "$ref" in sub_schema:
                        ref_value = sub_schema["$ref"]
                        cleaned_sub_schema = {"$ref": ref_value}
                        new_any_of.append(cleaned_sub_schema)
                    else:
                        # Recurse into non-ref sub-schemas
                        cls._modify_schema_recursive(sub_schema, original_schema, delete_props_with_defaults=delete_props_with_defaults) # Pass flag
                        new_any_of.append(sub_schema)
                else:
                    new_any_of.append(sub_schema) # Keep non-dict elements as is
            schema["anyOf"] = new_any_of


        # Remove potentially problematic fields not explicitly allowed by OpenAI
        # (Based on user provided errors/requirements)
        # Requirement 5: oneOf is not permitted
        if "oneOf" in schema:
            # Convert oneOf to anyOf (and apply ref cleanup logic to the new anyOf)
            schema["anyOf"] = schema.pop("oneOf")
            # Re-run the anyOf cleanup logic just added above
            new_any_of = []
            for sub_schema in schema["anyOf"]:
                if isinstance(sub_schema, dict):
                    if "$ref" in sub_schema:
                        ref_value = sub_schema["$ref"]
                        cleaned_sub_schema = {"$ref": ref_value}
                        new_any_of.append(cleaned_sub_schema)
                    else:
                        # Recurse into non-ref sub-schemas (should have been handled already, but safe)
                        cls._modify_schema_recursive(sub_schema, original_schema, delete_props_with_defaults=delete_props_with_defaults)
                        new_any_of.append(sub_schema)
                else:
                    new_any_of.append(sub_schema)
            schema["anyOf"] = new_any_of


        # Requirement 4: Disallow certain formats (datetime, etc.) - This is harder,
        # Pydantic schema doesn't always explicitly forbid them at generation time.
        # Might need validation or explicit removal if 'format' key exists with disallowed values.
        if "format" in schema and schema["format"] in ["date-time", "date", "time", "timedelta", "uuid"]:
             # What to do? Remove format? Change type to string? Raise error?
             # Simplest: remove format, hoping OpenAI accepts basic type.
             del schema["format"]
             # If type was string, it remains string. If object (like datetime), this might break.


    @classmethod
    def schemic_schema(cls, by_alias: bool = True, ref_template: str = '#/$defs/{model}', delete_props_with_defaults: bool = False) -> dict:
        """
        Generate an OpenAI-compatible JSON schema for the model.
        Applies modifications to meet OpenAI's strict requirements.

        Args:
            by_alias: Whether to use alias names in the schema.
            ref_template: The template for generating $ref strings.
            delete_props_with_defaults: If True, properties with default values will be
                                        removed entirely from the schema. If False (default),
                                        only the 'default' keyword is removed, and enums
                                        might be inlined.
        """
        # Get the standard Pydantic schema using the recommended mode='serialization'
        schema = cls.model_json_schema(by_alias=by_alias, ref_template=ref_template, mode='serialization')

        # Create a deep copy to avoid modifying the original class schema cache
        modified_schema = copy.deepcopy(schema)

        # Recursively modify the schema according to OpenAI's requirements
        # Pass the copied schema as both the schema-to-modify and the original_schema for lookups
        cls._modify_schema_recursive(modified_schema, modified_schema, delete_props_with_defaults=delete_props_with_defaults, is_root=True)

        # Clean up $defs: Remove the definition of the main model itself if present
        if '$defs' in modified_schema and cls.__name__ in modified_schema['$defs']:
            del modified_schema['$defs'][cls.__name__]
        # Remove $defs section entirely if it becomes empty
        if '$defs' in modified_schema and not modified_schema['$defs']:
            del modified_schema['$defs']


        # Requirement #8: Wrap the schema
        final_schema = {
            "type": "json_schema",
            "json_schema": {
                "strict": True, # Per OpenAI examples/errors
                "name": cls.__name__,
                "schema": modified_schema
            }
        }

        if SCHEMIC_DEBUG:
            original_pydantic_schema = cls.model_json_schema(by_alias=by_alias, ref_template=ref_template, mode='serialization')
            print("--- Original Pydantic Schema ---")
            print(json.dumps(original_pydantic_schema, indent=2))
            print("\n--- OpenAI Compatible Schema ---")
            print(json.dumps(final_schema, indent=2))


        return final_schema

    # __init__ is inherited from BaseModel, allowing SchemicModel(**openai_response)
    # No need to redefine unless custom parsing logic is required.

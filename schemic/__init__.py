import json
from pydantic import BaseModel

# Global debug flag - set to True to enable debug output
SCHEMIC_DEBUG = False


class SchemicModel(BaseModel):
    @classmethod
    def prepare_removeAllWithProp(cls, *args):
        """
        Remove all fields that have any of the specified properties.
        
        Args:
            *args: Property keys to check for removal (e.g., "default", "description")
            
        Returns:
            dict: Formatted schema with fields containing specified properties removed
        """
        schema = cls.model_json_schema()

        if SCHEMIC_DEBUG:
            json.dump(schema, open('schema.json', 'w'), indent=4)
        
        # Helper function to process schema properties
        def process_properties(props):
            if not props:
                return
            for prop_name, prop_schema in list(props.items()):
                # Check if any of the specified keys are in the property schema
                if any(key in prop_schema for key in args):
                    del props[prop_name]
                
                # Add additionalProperties: false to nested objects
                if prop_schema.get('type') == 'object':
                    prop_schema['additionalProperties'] = False
                    if 'properties' in prop_schema:
                        process_properties(prop_schema['properties'])
                
                # Handle array items that are objects
                if prop_schema.get('type') == 'array' and 'items' in prop_schema:
                    if isinstance(prop_schema['items'], dict):
                        if prop_schema['items'].get('type') == 'object':
                            prop_schema['items']['additionalProperties'] = False
                            if 'properties' in prop_schema['items']:
                                process_properties(prop_schema['items']['properties'])
        
        # Add additionalProperties: false to the top level
        if schema.get('type') == 'object':
            schema['additionalProperties'] = False
        
        # Modify top-level properties to remove fields with specified properties
        if 'properties' in schema:
            process_properties(schema['properties'])
        
        # Process nested schemas in $defs
        if '$defs' in schema:
            for def_name, def_schema in schema['$defs'].items():
                if def_schema.get('type') == 'object':
                    def_schema['additionalProperties'] = False
                if 'properties' in def_schema:
                    process_properties(def_schema['properties'])
        
        if SCHEMIC_DEBUG:
            json.dump(schema, open('new_schema.json', 'w'), indent=4)

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": schema,
                "strict": True
            },
        }
    
    @classmethod
    def prepare_IncludeAllWithProp(cls, *args):
        """
        Include only fields that have any of the specified properties.
        
        Args:
            *args: Property keys to check for inclusion (e.g., "default", "description")
            
        Returns:
            dict: Formatted schema with only fields containing specified properties
        """
        schema = cls.model_json_schema()

        if SCHEMIC_DEBUG:
            json.dump(schema, open('schema.json', 'w'), indent=4)
        
        # Helper function to process schema properties
        def process_properties(props):
            if not props:
                return
            for prop_name, prop_schema in list(props.items()):
                # Check if any of the specified keys are in the property schema
                if not any(key in prop_schema for key in args):
                    del props[prop_name]
                else:
                    # Add additionalProperties: false to nested objects
                    if prop_schema.get('type') == 'object':
                        prop_schema['additionalProperties'] = False
                        if 'properties' in prop_schema:
                            process_properties(prop_schema['properties'])
                    
                    # Handle array items that are objects
                    if prop_schema.get('type') == 'array' and 'items' in prop_schema:
                        if isinstance(prop_schema['items'], dict):
                            if prop_schema['items'].get('type') == 'object':
                                prop_schema['items']['additionalProperties'] = False
                                if 'properties' in prop_schema['items']:
                                    process_properties(prop_schema['items']['properties'])
        
        # Add additionalProperties: false to the top level
        if schema.get('type') == 'object':
            schema['additionalProperties'] = False
        
        # Modify top-level properties to include only fields with specified properties
        if 'properties' in schema:
            process_properties(schema['properties'])
        
        # Process nested schemas in $defs
        if '$defs' in schema:
            for def_name, def_schema in schema['$defs'].items():
                if def_schema.get('type') == 'object':
                    def_schema['additionalProperties'] = False
                if 'properties' in def_schema:
                    process_properties(def_schema['properties'])
        
        if SCHEMIC_DEBUG:
            json.dump(schema, open('new_schema.json', 'w'), indent=4)

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": schema,
                "strict": True
            },
        }
    

    @classmethod
    def prepare_IncludeAllWithFunction(cls, *args):
        """
        Include only fields that have an s_fn property containing at least one of the specified strings.
        
        Args:
            *args: Strings to search for in the s_fn property
            
        Returns:
            dict: Formatted schema with only fields containing specified strings in their s_fn property
        """
        schema = cls.model_json_schema()

        if SCHEMIC_DEBUG:
            json.dump(schema, open('schema.json', 'w'), indent=4)
        
        # Helper function to process schema properties
        def process_properties(props):
            if not props:
                return
            for prop_name, prop_schema in list(props.items()):
                # Check if s_fn exists and contains any of the specified strings
                keep_property = False
                if 's_fn' in prop_schema:
                    s_fn_value = prop_schema['s_fn']
                    # Check if s_fn is a list and if any arg is in the list
                    if isinstance(s_fn_value, list):
                        keep_property = any(arg in s_fn_value for arg in args)
                    # Check if s_fn is a string and if any arg is in the string
                    elif isinstance(s_fn_value, str):
                        keep_property = any(arg in s_fn_value for arg in args)
                
                # If the property doesn't have s_fn with specified strings, remove it
                if not keep_property:
                    del props[prop_name]
                else:
                    # Add additionalProperties: false to nested objects
                    if prop_schema.get('type') == 'object':
                        prop_schema['additionalProperties'] = False
                        if 'properties' in prop_schema:
                            process_properties(prop_schema['properties'])
                    
                    # Handle array items that are objects
                    if prop_schema.get('type') == 'array' and 'items' in prop_schema:
                        if isinstance(prop_schema['items'], dict):
                            if prop_schema['items'].get('type') == 'object':
                                prop_schema['items']['additionalProperties'] = False
                                if 'properties' in prop_schema['items']:
                                    process_properties(prop_schema['items']['properties'])
        
        # Add additionalProperties: false to the top level
        if schema.get('type') == 'object':
            schema['additionalProperties'] = False
        
        # Modify top-level properties
        if 'properties' in schema:
            process_properties(schema['properties'])
        
        # Process nested schemas in $defs
        if '$defs' in schema:
            for def_name, def_schema in schema['$defs'].items():
                if def_schema.get('type') == 'object':
                    def_schema['additionalProperties'] = False
                if 'properties' in def_schema:
                    process_properties(def_schema['properties'])
        
        if SCHEMIC_DEBUG:
            json.dump(schema, open('new_schema.json', 'w'), indent=4)

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": schema,
                "strict": True
            },
        }
        
    @classmethod
    def prepare_removeAllWithFunction(cls, *args):
        """
        Remove fields that have an s_fn property containing any of the specified strings.
        
        Args:
            *args: Strings to search for in the s_fn property
            
        Returns:
            dict: Formatted schema with fields containing specified strings in their s_fn property removed
        """
        schema = cls.model_json_schema()

        if SCHEMIC_DEBUG:
            json.dump(schema, open('schema.json', 'w'), indent=4)
        
        # Helper function to process schema properties
        def process_properties(props):
            if not props:
                return
            for prop_name, prop_schema in list(props.items()):
                # Check if s_fn exists and contains any of the specified strings
                remove_property = False
                if 's_fn' in prop_schema:
                    s_fn_value = prop_schema['s_fn']
                    # Check if s_fn is a list and if any arg is in the list
                    if isinstance(s_fn_value, list):
                        remove_property = any(arg in s_fn_value for arg in args)
                    # Check if s_fn is a string and if any arg is in the string
                    elif isinstance(s_fn_value, str):
                        remove_property = any(arg in s_fn_value for arg in args)
                
                # If the property has s_fn with specified strings, remove it
                if remove_property:
                    del props[prop_name]
                else:
                    # Add additionalProperties: false to nested objects
                    if prop_schema.get('type') == 'object':
                        prop_schema['additionalProperties'] = False
                        if 'properties' in prop_schema:
                            process_properties(prop_schema['properties'])
                    
                    # Handle array items that are objects
                    if prop_schema.get('type') == 'array' and 'items' in prop_schema:
                        if isinstance(prop_schema['items'], dict):
                            if prop_schema['items'].get('type') == 'object':
                                prop_schema['items']['additionalProperties'] = False
                                if 'properties' in prop_schema['items']:
                                    process_properties(prop_schema['items']['properties'])
        
        # Add additionalProperties: false to the top level
        if schema.get('type') == 'object':
            schema['additionalProperties'] = False
        
        # Modify top-level properties
        if 'properties' in schema:
            process_properties(schema['properties'])
        
        # Process nested schemas in $defs
        if '$defs' in schema:
            for def_name, def_schema in schema['$defs'].items():
                if def_schema.get('type') == 'object':
                    def_schema['additionalProperties'] = False
                if 'properties' in def_schema:
                    process_properties(def_schema['properties'])
        
        if SCHEMIC_DEBUG:
            json.dump(schema, open('new_schema.json', 'w'), indent=4)

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "math_reasoning",
                "schema": schema,
                "strict": True
            },
        }

    @classmethod
    def parse(cls, data:dict):
        """
        Parse the response from the model and add back any missing fields from the schema.
        
        Args:
            response: The JSON response string or dictionary from the model
            
        Returns:
            An instance of the class with all schema fields populated
        """
        # Get the original model schema
        original_schema = cls.model_json_schema()
        
        # Helper function to add back all missing fields to the data
        def add_missing_fields(data_dict, schema_props):
            if not schema_props:
                return data_dict
            
            result = data_dict.copy()
            for prop_name, prop_schema in schema_props.items():
                # If the field isn't in the response, add it
                if prop_name not in result:
                    # Use default value if available, otherwise use None
                    if 'default' in prop_schema:
                        result[prop_name] = prop_schema['default']
                    else:
                        # For fields without defaults, use an appropriate zero value based on type
                        if prop_schema.get('type') == 'string':
                            result[prop_name] = ""
                        elif prop_schema.get('type') == 'array':
                            result[prop_name] = []
                        elif prop_schema.get('type') == 'object':
                            # For objects, recursively create with nested properties
                            if 'properties' in prop_schema:
                                result[prop_name] = add_missing_fields({}, prop_schema['properties'])
                            else:
                                result[prop_name] = {}
                        elif prop_schema.get('type') == 'number' or prop_schema.get('type') == 'integer':
                            result[prop_name] = 0
                        elif prop_schema.get('type') == 'boolean':
                            result[prop_name] = False
                        else:
                            result[prop_name] = None
                
                # Handle nested objects
                if (prop_schema.get('type') == 'object' and 
                    prop_name in result and 
                    'properties' in prop_schema):
                    result[prop_name] = add_missing_fields(result[prop_name], prop_schema['properties'])
                
                # Handle arrays of objects
                if (prop_schema.get('type') == 'array' and 
                    'items' in prop_schema and 
                    prop_schema['items'].get('type') == 'object' and 
                    prop_name in result and
                    'properties' in prop_schema['items']):
                    result[prop_name] = [
                        add_missing_fields(item, prop_schema['items']['properties'])
                        for item in result[prop_name]
                    ]
            
            return result
        
        # Add back all missing fields to the response data
        full_data = add_missing_fields(data, original_schema.get('properties', {}))
        
        # Create and return an instance of the class with the complete data
        return cls(**full_data)


# Your goal is to write simple no bs code that solves exactly what I asked for in as little code as possible.

# Follow these rules when writing the code:
- Make sure to not change anything else other than what I mentioned. The simpler the better.
- Do not add or delete new line spaces or spaces.
- Do not delete comments.

# Here is the project description:
We are creating an extension to the pydantic library for handling openai's new structured output api. This api offers the ability to define a json schema for the output, which it will always generate. However, the api has a lot of requirements which are not shared by typical json schema libraries. Therefore you should make a class extending pydantic models, specifically implementing the following functions:
- SchemicModel.model_json_schema() # converting the model into json schema to be sent to openai
- SchemicModel(**openai_response) # converting the openai response back into the pydantic model

This is the running list of openais specific requirements I'm aware of:
1. Additional properties must be set on all nested objects, and if not having contents must be set to False
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'AISectionResponse': In context=(), 'additionalProperties' is required to be supplied and to be false.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
2. The “required” keyword must be set on all nested properties (unless they are objects)
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'AISectionResponse': In context=(), 'required' is required to be supplied and to be an array including every key in properties. Missing 'id'.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
3. defaults are not allowed ever
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'AISectionResponse': In context=('properties', 'type'), 'default' is not permitted.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
4. datetimes and variables other than basic data types are never allowed
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'MathProblem': In context=('properties', 'created_at'), 'format' is not permitted.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
5. oneOf is not permitted to be in the schema (handle this by converting it to anyOf)
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'PetOwner': In context=('properties', 'pet'), 'oneOf' is not permitted.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
6. anyOf must not share identical first keys (including in the required keys array, as well as in the properties dictionary)
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema: Objects provided via 'anyOf' must not share identical first keys. Consider adding a discriminator key or rearranging the properties to ensure the first key is unique.", 'type': 'invalid_request_error', 'param': None, 'code': None}}
```
7. REMOVED
8. you have to wrap the schema in a specific format before sending the model to the ai
```json
{
    "type": "json_schema", // must remain the same
    "json_schema": { // must remain the same
        "strict": True, // must remain the same
        "name": "schemic_model", // this is the name of the model
        "schema": {} // this is the actual schema
    }
}
```
9. some models have heightened requirements compared to others... Shouldn't matter however, and schemic should always just produce the highest level of strictness possible. For example, o1 model will throw an error like seen with requirement #6, but 4o will not.
10. required array doesn't seem to support objects with certain properties. For example, if the object doesn't have a "properties" field (or no "required" field) (dictionaries for example only have additionalProperties).
* This makes sense given that you can't require something with an undefined key. So if the object is a dictionary, it doesn't need to be required, but if it is an object, it does need to be required.
For example it will support "nested", but not "determined_dir" in the following example:
```python
schema = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,
        "name": "AISectionResponse",
        "schema": { # Added everything before this line (AKA requirement #8)
            "$defs": {
                "NestedObjectR1": {
                    "properties": {
                        "nested_prop": {
                            "title": "Nested Prop",
                            "type": "string"
                        }
                    },
                    "required": [
                        "nested_prop"
                    ],
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "title": "NestedObjectR1",
                    "type": "object"
                },
                "NoteSegmentButton": {
                    "properties": {
                        "type": { # This must also be the first one in the dictionary, as it is unique (AKA requirement #6)
                            "enum": ["button"], # Changed this line (AKA requirement #3) --> Removed SegmentType and replaced with enum values
                            "title": "Type", # Changed this line (AKA requirement #3)
                            "type": "string" # Changed this line (AKA requirement #3)
                        },
                        "id": {
                            "title": "Id",
                            "type": "string"
                        },
                        "isDetermined": {
                            "title": "Isdetermined",
                            "type": "boolean"
                        },
                        "placeholder": {
                            "description": "The placeholder text for the button. This is what will be displayed on the button itself.",
                            "title": "Placeholder",
                            "type": "string"
                        },
                        "action": {
                            "description": "The action to take when the button is clicked. This could be a function name, a URL, etc.",
                            "title": "Action",
                            "type": "string"
                        }
                    },
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "required": [
                        "type", # Added this line (AKA requirement #2). This must also be the first one in the list, as it is unique (AKA requirement #6)
                        "id", # Added this line (AKA requirement #2)
                        "isDetermined",
                        "placeholder",
                        "action"
                    ],
                    "title": "NoteSegmentButton",
                    "type": "object"
                },
                "NoteSegmentDropdown": {
                    "properties": {
                        "type": { # This must also be the first one in the dictionary, as it is unique (AKA requirement #6)
                            "enum": ["dropdown"], # Changed this line (AKA requirement #3) --> Removed SegmentType and replaced with enum values
                            "title": "Type", # Changed this line (AKA requirement #3)
                            "type": "string" # Changed this line (AKA requirement #3)
                        },
                        "id": {
                            "title": "Id",
                            "type": "string"
                        },
                        "isDetermined": {
                            "title": "Isdetermined",
                            "type": "boolean"
                        },
                        "options": {
                            "items": {
                                "type": "string"
                            },
                            "title": "Options",
                            "type": "array"
                        },
                        "selected": {
                            "items": {
                                "type": "integer"
                            },
                            "title": "Selected",
                            "type": "array"
                        }
                    },
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "required": [
                        "type", # Added this line (AKA requirement #2) This must also be the first one in the list, as it is unique (AKA requirement #6)
                        "id", # Added this line (AKA requirement #2)
                        "isDetermined",
                        "options",
                        "selected"
                    ],
                    "title": "NoteSegmentDropdown",
                    "type": "object"
                },
                "NoteSegmentInput": {
                    "properties": {
                        "type": { # This must also be the first one in the dictionary, as it is unique (AKA requirement #6)
                            "enum": ["input"], # Changed this line (AKA requirement #3) --> Removed SegmentType and replaced with enum values
                            "title": "Type", # Changed this line (AKA requirement #3)
                            "type": "string" # Changed this line (AKA requirement #3)
                        },
                        "id": {
                            "title": "Id",
                            "type": "string"
                        },
                        "isDetermined": {
                            "title": "Isdetermined",
                            "type": "boolean"
                        },
                        "value": {
                            "title": "Value",
                            "type": "string"
                        }
                    },
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "required": [
                        "type", # Added this line (AKA requirement #2) This must also be the first one in the list, as it is unique (AKA requirement #6)
                        "id", # Added this line (AKA requirement #2)
                        "isDetermined",
                        "value"
                    ],
                    "title": "NoteSegmentInput",
                    "type": "object"
                },
                # SegmentType removed as no longer needed since defaults are not supported by openai, and and we are instead using enum values in the code
            },
            "properties": {
                "top_level_prop": {
                    "title": "Top Level Prop",
                    "type": "string"
                },
                "nested": {
                    "$ref": "#/$defs/NestedObjectR1"
                }, # normal object
                "determined_dir": {
                    "additionalProperties": { # This doesn't need to be false because it has a value... if there was no value we would have to set additionalProperties to false
                        "anyOf": [
                            {
                                "$ref": "#/$defs/NoteSegmentDropdown"
                            },
                            {
                                "$ref": "#/$defs/NoteSegmentInput"
                            },
                            {
                                "$ref": "#/$defs/NoteSegmentButton"
                            }
                        ]
                    },
                    "description": "A dictionary where keys are the placeholder IDs (e.g., 'SOMEUUID1') from the template's content_str, and values are the determined content for that placeholder.",
                    "title": "Determined Dir",
                    "type": "object"
                }, # not a normal object, but a dictionary with a specific structure, with no properties or required fields
                "determined_str": {
                    "description": "The string representing the text for the note section, with '{SOMEUUID1}' representing data from the determined_dir.",
                    "title": "Determined Str",
                    "type": "string"
                }
            },
            "additionalProperties": False, # Added this line (AKA requirement #1)
            "required": [
                "top_level_prop",
                "nested", # THIS IS SUPPORTED
                "determined_dir", # THIS IS NOT SUPPORTED, AND THE LINE MUST BE COMMENTED OUT, DESPITE "nested" BEING SUPPORTED, AND THEY ARE BOTH OBJECTS
                "determined_str",
            ],
            "title": "AISectionResponse",
            "type": "object"
        }
    }
}
```

Example Error:
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'AISectionResponse': In context=(), 'required' is required to be supplied and to be an array including every key in properties. Extra required key 'determined_dir' supplied.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
11. $refs do not support additional keys:
```cmd
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'PetOwner': context=('properties', 'pet_color'), $ref cannot have keywords {'description'}.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}

openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for response_format 'PetOwner': context=('properties', 'pet_color'), $ref cannot have keywords {'type'}.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```
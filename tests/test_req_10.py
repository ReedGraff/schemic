import json
import os
import sys
import openai
from pydantic import BaseModel, Field
import dotenv
from lib.logger_config import logger
from lib.openai_client import client

# Add path to schemic library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemic import SchemicModel

# Requirement 10: required array doesn't seem to support objects
class NestedObjectR10(SchemicModel):
    nested_prop: str = Field(...)

class Requirement10Model(SchemicModel):
    # This object field should NOT appear in the top-level 'required' list
    nested_data: NestedObjectR10 = Field(...)
    # This simple field SHOULD appear in the top-level 'required' list
    simple_prop: str = Field(...)

# Generate schema & Test
try:
    schema = Requirement10Model.schemic_schema()
    logger.info("Generated Schema (Requirement 10):")
    # logger.debug(json.dumps(schema, indent=4))

    # Verification step (optional but useful): Check the generated schema directly
    top_level_required = schema.get("json_schema", {}).get("schema", {}).get("required", [])
    if "nested_data" in top_level_required:
        logger.error("Requirement 10 Schema Check Failed: 'nested_data' (object) found in top-level required list.")
        # Decide if this should fail the test immediately or just log a warning
        # raise AssertionError("Object found in top-level required list")
    elif "simple_prop" not in top_level_required:
         logger.warning("Requirement 10 Schema Check Warning: 'simple_prop' (non-object) missing from top-level required list.")
    else:
        logger.info("Requirement 10 Schema Check Passed: Top-level required list looks correct.")


    logger.info("Making OpenAI call for Requirement 10...")
    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 10): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 10)...")
    parsed_data = Requirement10Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 10):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 10 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 10 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    # This error specifically mentions an object key being incorrectly in 'required'
    if "Extra required key" in str(e) and "supplied" in str(e):
         logger.info("Error message confirms object key in 'required' list issue needs fixing in SchemicModel.")
    elif "'required' is required to be supplied and to be an array including every key in properties" in str(e):
         logger.warning("Got a general 'required' list error, might be related or a different issue.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 10 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
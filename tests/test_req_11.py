import json
import os
import sys
import openai
from pydantic import BaseModel, Field
import dotenv
from enum import Enum
from lib.logger_config import logger
from lib.openai_client import client

# Add path to schemic library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemic import SchemicModel

# Requirement 11: $refs do not support additional keys (like description, type)

class ColorEnumR11(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

class Requirement11Model(SchemicModel):
    item_name: str = Field(...)
    # Pydantic might add description/title/etc. alongside the $ref to ColorEnumR11 in $defs
    item_color: ColorEnumR11 = Field(..., description="The color of the item")

# Generate schema & Test
try:
    schema = Requirement11Model.schemic_schema()
    logger.info("Generated Schema (Requirement 11):")
    # logger.debug(json.dumps(schema, indent=4))

    # Verification step (optional): Check the generated schema directly
    props = schema.get("json_schema", {}).get("schema", {}).get("properties", {})
    item_color_prop = props.get("item_color", {})
    if "$ref" in item_color_prop and len(item_color_prop) > 1:
         logger.error(f"Requirement 11 Schema Check Failed: '$ref' for 'item_color' has extra keys: {list(item_color_prop.keys())}")
         # raise AssertionError("$ref has extra keys")
    else:
         logger.info("Requirement 11 Schema Check Passed: '$ref' for 'item_color' looks clean.")


    logger.info("Making OpenAI call for Requirement 11...")
    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance, use 'red' for the color."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 11): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 11)...")
    parsed_data = Requirement11Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 11):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 11 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 11 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    if "$ref cannot have keywords" in str(e):
         logger.info("Error message confirms '$ref' extra keywords issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 11 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
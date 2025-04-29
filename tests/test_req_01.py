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

# Requirement 1: Additional properties must be set to False on nested objects.
class NestedObjectR1(SchemicModel):
    nested_prop: str = Field(...)

class Requirement1Model(SchemicModel):
    top_level_prop: str = Field(...)
    nested: NestedObjectR1 = Field(...)

# Generate schema & Test
try:
    schema = Requirement1Model.schemic_schema()
    logger.info("Generated Schema (Requirement 1):")
    # logger.debug(json.dumps(schema, indent=4)) # Uncomment to log full schema

    logger.info("Making OpenAI call for Requirement 1...")
    response = client.beta.chat.completions.parse(
        model="o1", # Use a model known for strict schema validation
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 1): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 1)...")
    parsed_data = Requirement1Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 1):")
    # logger.debug(parsed_data.model_dump_json(indent=4)) # Uncomment to log parsed data
    logger.info("Requirement 1 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 1 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    # Check if error message relates to additionalProperties
    if "'additionalProperties' is required to be supplied and to be false" in str(e):
        logger.info("Error message confirms 'additionalProperties' issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 1 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)

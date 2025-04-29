import json
import os
import sys
import openai
from pydantic import BaseModel, Field
import dotenv
from typing import Union, Literal
from lib.logger_config import logger
from lib.openai_client import client

# Add path to schemic library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemic import SchemicModel

# Requirement 6: anyOf must not share identical first keys
# Schemic needs to ensure the discriminator ('type' here) is the first key
class InputSegmentR6(SchemicModel):
    # If 'value' came first, this could fail without Schemic reordering
    value: str = Field(...)
    type: Literal["input"] = "input"

class DropdownSegmentR6(SchemicModel):
    # If 'options' came first, this could fail without Schemic reordering
    options: list[str] = Field(...)
    type: Literal["dropdown"] = "dropdown"

class Requirement6Model(SchemicModel):
    segment_id: str = Field(...)
    # Schemic should convert this Union (which becomes anyOf)
    # and ensure 'type' is the first property listed within each object definition
    # and also the first item in the 'required' list for each object.
    segment_data: Union[InputSegmentR6, DropdownSegmentR6] = Field(..., discriminator='type')

# Generate schema & Test
try:
    schema = Requirement6Model.schemic_schema()
    logger.info("Generated Schema (Requirement 6):")
    # logger.debug(json.dumps(schema, indent=4))

    logger.info("Making OpenAI call for Requirement 6...")
    response = client.beta.chat.completions.parse(
        model="o1", # o1 is known to enforce this rule strictly
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance using the input segment type."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 6): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 6)...")
    parsed_data = Requirement6Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 6):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 6 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 6 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    if "must not share identical first keys" in str(e):
         logger.info("Error message confirms 'anyOf' first key issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 6 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
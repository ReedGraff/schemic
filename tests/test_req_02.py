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

# Requirement 2: The “required” keyword must be set on all nested properties (unless they are objects)
class Requirement2Model(SchemicModel):
    prop_a: str = Field(...) # Pydantic makes this required by default
    prop_b: int # Also required by default
    prop_c: bool = Field(default=True) # Optional in Pydantic, should be required by Schemic
    prop_d: float = Field()

# Generate schema & Test
try:
    schema = Requirement2Model.schemic_schema()
    logger.info("Generated Schema (Requirement 2):")
    # logger.debug(json.dumps(schema, indent=4))

    logger.info("Making OpenAI call for Requirement 2...")
    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 2): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 2)...")
    parsed_data = Requirement2Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 2):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 2 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 2 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    if "'required' is required to be supplied and to be an array including every key in properties" in str(e):
         logger.info("Error message confirms 'required' array issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 2 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
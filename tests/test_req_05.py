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

# Requirement 5: oneOf is not permitted to be in the schema (handle this by converting it to anyOf)
class DogR5(SchemicModel):
    breed: str = Field(...)
    type: Literal["dog"] = "dog" # Discriminator

class CatR5(SchemicModel):
    color: str = Field(...)
    type: Literal["cat"] = "cat" # Discriminator

class Requirement5Model(SchemicModel):
    pet_name: str = Field(...)
    # Union typically generates oneOf by default in Pydantic
    pet: Union[DogR5, CatR5] = Field(..., discriminator='type')

# Generate schema & Test
try:
    schema = Requirement5Model.schemic_schema()
    logger.info("Generated Schema (Requirement 5):")
    # logger.debug(json.dumps(schema, indent=4))

    logger.info("Making OpenAI call for Requirement 5...")
    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance, make the pet a dog."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 5): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 5)...")
    parsed_data = Requirement5Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 5):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 5 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 5 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    if "'oneOf' is not permitted" in str(e):
         logger.info("Error message confirms 'oneOf' keyword issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 5 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
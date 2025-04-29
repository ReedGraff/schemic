import json
import os
import sys
import openai
from pydantic import BaseModel, Field
import dotenv
import datetime
from lib.logger_config import logger
from lib.openai_client import client

# Add path to schemic library
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from schemic import SchemicModel

# Requirement 4: datetimes and variables other than basic data types are never allowed (specifically 'format' keyword)
class Requirement4Model(SchemicModel):
    name: str = Field(...)
    # Pydantic adds "format": "date-time" for this
    created_at: datetime.datetime = Field(...)

# Generate schema & Test
try:
    schema = Requirement4Model.schemic_schema()
    logger.info("Generated Schema (Requirement 4):")
    # logger.debug(json.dumps(schema, indent=4))

    logger.info("Making OpenAI call for Requirement 4...")
    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": "Generate data based on the schema."},
            {"role": "user", "content": "Generate an instance. Use ISO format for datetime string."},
        ],
        response_format=schema,
    )
    content_str = response.choices[0].message.content
    logger.debug(f"OpenAI Response (Req 4): {content_str}")
    content_dict = json.loads(content_str)

    logger.info("Parsing response with Pydantic model (Requirement 4)...")
    # Pydantic can parse ISO strings back to datetime objects
    parsed_data = Requirement4Model(**content_dict)
    logger.info("Successfully parsed response (Requirement 4):")
    # logger.debug(parsed_data.model_dump_json(indent=4))
    logger.info("Requirement 4 Test Passed!")

except openai.BadRequestError as e:
    logger.error("Requirement 4 Test Failed: OpenAI BadRequestError")
    logger.error(e)
    if "'format' is not permitted" in str(e):
         logger.info("Error message confirms 'format' keyword issue needs fixing in SchemicModel.")
    else:
        logger.warning("Error message might be unrelated or SchemicModel didn't fix it as expected.")
except Exception as e:
    logger.error("Requirement 4 Test Failed: An unexpected error occurred.")
    logger.error(e, exc_info=True)
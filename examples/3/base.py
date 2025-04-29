import datetime
import json
import os
from typing import Union, Literal
import openai
from pydantic import BaseModel, Field, create_model
from enum import Enum
import dotenv

# INITIALIZATION
dotenv.load_dotenv()
client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)



class PetColor(Enum):
    BLACK = "black"
    WHITE = "white"
    BROWN = "brown"
    GREY = "grey"
    ORANGE = "orange"
    YELLOW = "yellow"

class Cat(BaseModel):
    pet_type: Literal['cat']
    name: str
    meows: bool

class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str
    barks: bool

class PetOwner(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type', description="The pet of the owner")
    pet_name: str = Field(..., description="Name of the pet")
    pet_color: PetColor = Field(Literal[PetColor.BLACK], description="Color of the pet")

# That produces this:
print(PetOwner.schema_json(indent=4))
"""
{
    "$defs": {
        "Cat": {
            "properties": {
                "pet_type": {
                    "const": "cat",
                    "title": "Pet Type",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "meows": {
                    "title": "Meows",
                    "type": "boolean"
                }
            },
            "required": [
                "pet_type",
                "name",
                "meows"
            ],
            "title": "Cat",
            "type": "object"
        },
        "Dog": {
            "properties": {
                "pet_type": {
                    "const": "dog",
                    "title": "Pet Type",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "type": "string"
                },
                "barks": {
                    "title": "Barks",
                    "type": "boolean"
                }
            },
            "required": [
                "pet_type",
                "name",
                "barks"
            ],
            "title": "Dog",
            "type": "object"
        },
        "PetColor": {
            "enum": [
                "black",
                "white",
                "brown",
                "grey",
                "orange",
                "yellow"
            ],
            "title": "PetColor",
            "type": "string"
        }
    },
    "properties": {
        "pet": {
            "description": "The pet of the owner",
            "discriminator": {
                "mapping": {
                    "cat": "#/$defs/Cat",
                    "dog": "#/$defs/Dog"
                },
                "propertyName": "pet_type"
            },
            "oneOf": [
                {
                    "$ref": "#/$defs/Cat"
                },
                {
                    "$ref": "#/$defs/Dog"
                }
            ],
            "title": "Pet"
        },
        "pet_name": {
            "description": "Name of the pet",
            "title": "Pet Name",
            "type": "string"
        },
        "pet_color": {
            "$ref": "#/$defs/PetColor",
            "description": "Color of the pet"
        }
    },
    "required": [
        "pet",
        "pet_name"
    ],
    "title": "PetOwner",
    "type": "object"
}
"""

# this needs to turn into this:
FixedPetOwnerSchema = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,
        "name": "PetOwner",
        "schema": { # Added everything before this line (AKA requirement #8)
            "$defs": {
                "Cat": {
                    "properties": {
                        "pet_type": {
                            "const": "cat",
                            "title": "Pet Type",
                            "type": "string"
                        },
                        "name": {
                            "title": "Name",
                            "type": "string"
                        },
                        "meows": {
                            "title": "Meows",
                            "type": "boolean"
                        }
                    },
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "required": [
                        "pet_type",
                        "name",
                        "meows"
                    ],
                    "title": "Cat",
                    "type": "object"
                },
                "Dog": {
                    "properties": {
                        "pet_type": {
                            "const": "dog",
                            "title": "Pet Type",
                            "type": "string"
                        },
                        "name": {
                            "title": "Name",
                            "type": "string"
                        },
                        "barks": {
                            "title": "Barks",
                            "type": "boolean"
                        }
                    },
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "required": [
                        "pet_type",
                        "name",
                        "barks"
                    ],
                    "title": "Dog",
                    "type": "object"
                },
                "PetColor": {
                    "enum": [
                        "black",
                        "white",
                        "brown",
                        "grey",
                        "orange",
                        "yellow"
                    ],
                    "title": "PetColor",
                    "type": "string"
                }
            },
            "properties": {
                "pet": {
                    "description": "The pet of the owner",
                    "discriminator": {
                        "mapping": {
                            "cat": "#/$defs/Cat",
                            "dog": "#/$defs/Dog"
                        },
                        "propertyName": "pet_type"
                    },
                    "anyOf": [ # changed from oneOf to anyOf (AKA requirement #5)
                        {
                            "$ref": "#/$defs/Cat"
                        },
                        {
                            "$ref": "#/$defs/Dog"
                        }
                    ],
                    "title": "Pet"
                },
                "pet_name": {
                    "description": "Name of the pet",
                    "title": "Pet Name",
                    "type": "string"
                },
                "pet_color": {
                    "$ref": "#/$defs/PetColor",
                    # removed description, as $refs do not support additional keys (AKA requirement #11)
                }
            },
            "additionalProperties": False, # Added this line (AKA requirement #1)
            "required": [
                "pet",
                "pet_name",
                "pet_color" # Added this line (AKA requirement #2)
            ],
            "title": "PetOwner",
            "type": "object"
        }
    }
}

def generate(prompt):
    system_prompt = """You are an assistant helping a system create petowner objects based on user input."""

    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format=FixedPetOwnerSchema,
        reasoning_effort="medium",
    )

    content_dict = json.loads(response.choices[0].message.content)

    print(json.dumps(content_dict, indent=4))

generate("""Hey, I have a pet cat named Whiskers who is black and loves to meow. Can you create a PetOwner object for me?""")

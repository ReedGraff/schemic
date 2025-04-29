import datetime
from enum import Enum
import json
import os
import sys
from typing import List, Literal, Union
import openai
from pydantic import BaseModel, Field, create_model
import dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from schemic import SchemicModel

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

class Cat(SchemicModel):
    pet_type: Literal['cat']
    name: str
    meows: bool

class Dog(SchemicModel):
    pet_type: Literal['dog']
    name: str
    barks: bool

class PetOwner(SchemicModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type', description="The pet of the owner")
    pet_name: str = Field(..., description="Name of the pet")
    pet_color: PetColor = Field(Literal[PetColor.BLACK], description="Color of the pet")

with open("examples/3/schemic.txt", "w") as f:
    f.write(json.dumps(PetOwner.schemic_schema(), indent=4))

def generate(prompt):
    system_prompt = """You are an assistant helping a system create petowner objects based on user input."""

    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format=PetOwner.schemic_schema(delete_props_with_defaults=True),
        reasoning_effort="medium",
    )

    content_dict = json.loads(response.choices[0].message.content)
    print(json.dumps(content_dict, indent=4))

    parsed = PetOwner(**content_dict)
    print(parsed.model_dump_json(indent=4))

generate("""Hey, I have a pet cat named Whiskers who is black and loves to meow. Can you create a PetOwner object for me?""")

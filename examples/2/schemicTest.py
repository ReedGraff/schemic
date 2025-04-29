import datetime
import json
import os
import sys
from typing import List
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

class ReasoningSteps(SchemicModel):
    created_at: datetime.datetime = Field(datetime.datetime.now(datetime.UTC), description="Last edited timestamp") # works if commented
    step: str = Field(..., description="Step in the reasoning process")
    explanation: str = Field(..., description="Explanation of the step")
    result: float = Field(..., description="Result of the step")

class MathProblem(SchemicModel):
    created_at: datetime.datetime = Field(datetime.datetime.now(datetime.UTC), description="Creation timestamp") # works if commented
    problem: str = Field(..., description="The math problem to solve")
    answer: float = Field(..., description="The answer to the math problem")
    steps: List[ReasoningSteps] = Field(..., description="Steps taken to solve the math problem")

with open("examples/2/schemic.txt", "w") as f:
    f.write(json.dumps(MathProblem.schemic_schema(), indent=4))

def generate(prompt):
    system_prompt = """You are an assistant helping a user solve math problems."""

    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format=MathProblem.schemic_schema(delete_props_with_defaults=True),
        reasoning_effort="medium",
    )

    content_dict = json.loads(response.choices[0].message.content)
    print(json.dumps(content_dict, indent=4))

    parsed = MathProblem(**content_dict)
    print(parsed.model_dump_json(indent=4))

generate("""Solve 2x + 13x = 7""")

import datetime
import json
import os
from typing import List
import openai
from pydantic import BaseModel, Field, create_model
import dotenv

# INITIALIZATION
dotenv.load_dotenv()
client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

class ReasoningSteps(BaseModel):
    created_at: datetime.datetime = Field(datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y, %H:%M:%S"), description="Last edited timestamp") # works if commented
    step: str = Field(..., description="Step in the reasoning process")
    explanation: str = Field(..., description="Explanation of the step")
    result: float = Field(..., description="Result of the step")

class MathProblem(BaseModel):
    created_at: datetime.datetime = Field(datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y, %H:%M:%S"), description="Creation timestamp") # works if commented
    problem: str = Field(..., description="The math problem to solve")
    answer: float = Field(..., description="The answer to the math problem")
    steps: List[ReasoningSteps] = Field(..., description="Steps taken to solve the math problem")

# That produces this:
print(MathProblem.schema_json(indent=4))
"""
{
    "$defs": {
        "ReasoningSteps": {
            "properties": {
                "created_at": {
                    "default": "28/04/2025, 23:33:45",
                    "description": "Last edited timestamp",
                    "format": "date-time",
                    "title": "Created At",
                    "type": "string"
                },
                "step": {
                    "description": "Step in the reasoning process",
                    "title": "Step",
                    "type": "string"
                },
                "explanation": {
                    "description": "Explanation of the step",
                    "title": "Explanation",
                    "type": "string"
                },
                "result": {
                    "description": "Result of the step",
                    "title": "Result",
                    "type": "number"
                }
            },
            "required": [
                "step",
                "explanation",
                "result"
            ],
            "title": "ReasoningSteps",
            "type": "object"
        }
    },
    "properties": {
        "created_at": {
            "default": "28/04/2025, 23:33:45",
            "description": "Creation timestamp",
            "format": "date-time",
            "title": "Created At",
            "type": "string"
        },
        "problem": {
            "description": "The math problem to solve",
            "title": "Problem",
            "type": "string"
        },
        "answer": {
            "description": "The answer to the math problem",
            "title": "Answer",
            "type": "number"
        },
        "steps": {
            "description": "Steps taken to solve the math problem",
            "items": {
                "$ref": "#/$defs/ReasoningSteps"
            },
            "title": "Steps",
            "type": "array"
        }
    },
    "required": [
        "problem",
        "answer",
        "steps"
    ],
    "title": "MathProblem",
    "type": "object"
}
"""

# this needs to turn into this:
FixedMathProblemSchema = {
    "type": "json_schema",
    "json_schema": {
        "strict": True,
        "name": "MathProblem",
        "schema": { # Added everything before this line (AKA requirement #8)
            "$defs": {
                "ReasoningSteps": {
                    "additionalProperties": False, # Added this line (AKA requirement #1)
                    "properties": {
                        "created_at": {
                            # removed default from here (AKA requirement #3)
                            "description": "Last edited timestamp",
                            # removed format from here (AKA requirement #4)
                            "title": "Created At",
                            "type": "string"
                        },
                        "step": {
                            "description": "Step in the reasoning process",
                            "title": "Step",
                            "type": "string"
                        },
                        "explanation": {
                            "description": "Explanation of the step",
                            "title": "Explanation",
                            "type": "string"
                        },
                        "result": {
                            "description": "Result of the step",
                            "title": "Result",
                            "type": "number"
                        }
                    },
                    "required": [
                        "created_at", # Added this line (AKA requirement #2)
                        "step",
                        "explanation",
                        "result"
                    ],
                    "title": "ReasoningSteps",
                    "type": "object"
                }
            },
            "properties": {
                "created_at": {
                    # removed default from here (AKA requirement #3)
                    "description": "Creation timestamp",
                    # removed format from here (AKA requirement #4)
                    "title": "Created At",
                    "type": "string"
                },
                "problem": {
                    "description": "The math problem to solve",
                    "title": "Problem",
                    "type": "string"
                },
                "answer": {
                    "description": "The answer to the math problem",
                    "title": "Answer",
                    "type": "number"
                },
                "steps": {
                    "description": "Steps taken to solve the math problem",
                    "items": {
                        "$ref": "#/$defs/ReasoningSteps"
                    },
                    "title": "Steps",
                    "type": "array"
                }
            },
            "additionalProperties": False, # Added this line (AKA requirement #1)
            "required": [
                "created_at", # Added this line (AKA requirement #2)
                "problem",
                "answer",
                "steps"
            ],
            "title": "MathProblem",
            "type": "object"
        }
    }
}

def generate(prompt):
    system_prompt = """You are an assistant helping a user manage their calendar events based on call transcripts they get from clients."""

    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format=FixedMathProblemSchema,
        reasoning_effort="medium",
    )

    content_dict = json.loads(response.choices[0].message.content)

    print(json.dumps(content_dict, indent=4))

generate("""Solve 2x + 13x = 7""")

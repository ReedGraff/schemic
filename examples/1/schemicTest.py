# Here is a full example of OpenAI's increased requirements, and how we need to change the schema in order to meet them:

import json
from dotenv import load_dotenv
import os
from typing import Dict
from pydantic import BaseModel
import openai

# INITIALIZATION
load_dotenv()
client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# =================================================================================
# GLOBAL TYPES
# =================================================================================
from typing import Any, Optional, Dict, List, Set, Union
from datetime import datetime, timedelta, timezone
import uuid
from pydantic import BaseModel, Field
from enum import Enum
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from schemic import SchemicModel

# ==== users/uid/visits/visitID Document ===
## Note
# Keep only SegmentType and NoteSegment* subclasses used by AISectionResponse
class SegmentType(str, Enum):
    DROPDOWN = "dropdown"
    INPUT = "input"
    BUTTON = "button"

class NoteSegment(SchemicModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: SegmentType
    isDetermined: bool

class NoteSegmentDropdown(NoteSegment):
    type: SegmentType = SegmentType.DROPDOWN
    options: List[str]
    selected: List[int]

class NoteSegmentInput(NoteSegment):
    type: SegmentType = SegmentType.INPUT
    value: str = Field(description="The value of the input field")

class NoteSegmentButton(NoteSegment):
    type: SegmentType = SegmentType.BUTTON
    placeholder: str = Field(description="The placeholder text for the button.")
    action: str = Field(description="The action to take when the button is clicked.")

# =================================================================================
# Other shit
# =================================================================================
class AISectionResponse(SchemicModel):
    determined_dir: Dict[str, Union[NoteSegmentInput, NoteSegmentDropdown, NoteSegmentButton]] = Field(
        description="A dictionary where keys are the placeholder IDs (e.g., 'SOMEUUID1') from the template's content_str, and values are the determined content for that placeholder."
    )
    determined_str: str = Field(
        description="The string representing the text for the note section, with '{SOMEUUID1}' representing data from the determined_dir."
    )

with open("examples/1/schemic.txt", "w") as f:
    f.write(json.dumps(AISectionResponse.schemic_schema(), indent=4))


def generate(prompt):
    system_prompt = """
You are an assistant create a special flavor of markdown with input fields, dropdowns, and buttons.

You are to always generate 2 varibles for the user. The following represents the name of the variable, and an example of the value it could have:
* determined_str: "Hey {INPUTID1}, select your favorite colors: {DROPDOWNID1}. Click {BUTTONID1} when done. How about {DROPDOWNID2}? This is **bold text**."
* determined_dir: {"INPUTID1": {"type": "input","value": "User","placeholder": "Your Name"},"DROPDOWNID1": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": [1,3]},"BUTTONID1": {"type": "button","value": "Submit","context": "Submit button pressed!"},"DROPDOWNID2": {"type": "dropdown","options": ["Option A","Option B"],"selected": []}}
"""

    response = client.beta.chat.completions.parse(
        model="o1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": """Generate a note template for tracking a person's favorite colors. you should list 5 random people, with dropdown fields following their names, finally with a button at the end that says 'Submit'."""},
            {
                "role": "assistant",
                "content": '''
                    "determined_str": """
Steve: {DROPDOWNID1}
Sarah: {DROPDOWNID2}
Jerry: {DROPDOWNID3}
Jimbo: {DROPDOWNID4}
Chandler: {DROPDOWNID5}

Click {BUTTONID1} when done.""",
                    "determined_dir": {
                        "DROPDOWNID1": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": []},
                        "DROPDOWNID2": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": []},
                        "DROPDOWNID3": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": []},
                        "DROPDOWNID4": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": []},
                        "DROPDOWNID5": {"type": "dropdown","options": ["Red","Green","Blue","Yellow","Purple"],"selected": []},
                        "BUTTONID1": {"type": "button", "placeholder":"Submit", "action":"Submit button pressed!"}
                    }
                }'''
            },
            {"role": "user", "content": prompt}
        ],
        response_format=AISectionResponse.schemic_schema(),
        reasoning_effort="medium",
    )

    content_dict = json.loads(response.choices[0].message.content)
    print(json.dumps(content_dict, indent=4))

generate("""Generate a note template for 5 schools and their favorite sports. you should list 5 random schools, with dropdown fields following their names (with the dropdowns representing potential sports that might be their favorite).""")

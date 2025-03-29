# Schemic

[![PyPI version](https://badge.fury.io/py/schemic.svg)](https://badge.fury.io/py/schemic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

When working with GPT models and Pydantic, developers frequently encounter a frustrating workflow issue:

1. You create Pydantic models to define your data structure in your application
2. You want to use these same models (or a subset of those models) with GPT to generate responses in the same format
3. You discover that GPT doesn't support:
   - Default values (and default factories)
   - Custom classes like `datetime.datetime`
   - Pydantic validation logic

This forces you to:
1. Duplicate your models with simplified versions for GPT
2. Handle missing fields and defaults manually 
3. Add back datetime and other complex objects afterward
4. Write repetitive code to convert between your application models and "GPT-friendly" models

## Schemic's Solution

Schemic solves this problem by extending Pydantic's `BaseModel` with methods that:

1. **Intelligently transform** your existing models for GPT compatibility
2. **Preserve your schema structure** without duplicating code
3. **Automatically handle** fields with defaults, datetimes, and custom types
4. **Simplify parsing** GPT responses back into your full model instances

No more duplicate model definitions. No more manual field manipulation. Just use your regular Pydantic models with GPT.

## Installation

```bash
pip install schemic
```

## Quick Example

```python
import datetime
from typing import List
from pydantic import Field
from schemic import SchemicModel
import openai

# Define your models with SchemicModel instead of BaseModel
class ReasoningStep(SchemicModel):
    created_at: str = Field(
        default=datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y, %H:%M:%S"),
        description="Last edited timestamp"
    )
    step: str = Field(..., description="Step in the reasoning process")
    explanation: str = Field(..., description="Explanation of the step")
    result: float = Field(..., description="Result of the step")

class MathProblem(SchemicModel):
    created_at: str = Field(
        default=datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y, %H:%M:%S"),
        description="Creation timestamp"
    )
    problem: str = Field(..., description="The math problem to solve")
    answer: float = Field(..., description="The answer to the math problem")
    steps: List[ReasoningStep] = Field(..., description="Steps taken to solve the problem")

# Use with OpenAI API
client = openai.Client(api_key="your-api-key")

def solve_math_problem(problem_text: str):
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a math problem solver."},
            {"role": "user", "content": f"Solve this math problem: {problem_text}"}
        ],
        # Remove fields with defaults when sending to GPT
        response_format=MathProblem.prepare_removeAllWithProp("default"),
        temperature=0.3,
    )

    # Parse the response and add back all defaults
    content_dict = response.choices[0].message.content
    solution = MathProblem.parse(content_dict)
    
    return solution

# Example usage
solution = solve_math_problem("2x + 13x = 7")
print(f"Answer: {solution.answer}")
print(f"Created at: {solution.created_at}")  # Default timestamp added automatically
```

## Key Features

### For Schema Transformation

- **`prepare_removeAllWithProp(*args)`**: Remove fields with specified properties (e.g., "default", "description")
- **`prepare_IncludeAllWithProp(*args)`**: Include only fields with specified properties
- **`prepare_IncludeAllWithFunction(*args)`**: Include only fields with s_fn property matching specified strings
- **`prepare_removeAllWithFunction(*args)`**: Remove fields with s_fn property matching specified strings

### For Response Parsing

- **`parse(data: dict)`**: Parse GPT response and restore defaults and custom types

## Detailed Documentation

### SchemicModel Classes

Schemic works by extending Pydantic's `BaseModel` class:

```python
from schemic import SchemicModel

class MyModel(SchemicModel):
    # Your regular Pydantic model definition here
    pass
```

### Preparing Models for GPT

#### Remove Fields with Default Values

```python
# Remove all fields with default values when sending to GPT
response_format = MyModel.prepare_removeAllWithProp("default")
```

#### Include Only Required Fields

```python
# Only include fields that don't have defaults (required fields)
response_format = MyModel.prepare_IncludeAllWithProp("required")
```

#### Custom Field Selection

Use the `s_fn` property to tag fields for specific functions:

```python
from pydantic import Field
from schemic import SchemicModel

class User(SchemicModel):
    id: int = Field(..., s_fn=["system"])
    name: str = Field(..., s_fn=["public", "profile"])
    email: str = Field(..., s_fn=["private"])
    password: str = Field(..., s_fn=["private", "auth"])

# Include only fields tagged for public display
public_schema = User.prepare_IncludeAllWithFunction("public")

# Remove all private fields
no_private_schema = User.prepare_removeAllWithFunction("private")
```

### Parsing GPT Responses

```python
# Get response from GPT
response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[...],
    response_format=MyModel.prepare_removeAllWithProp("default"),
)

# Parse the response back into your full model
content_dict = response.choices[0].message.content
my_model_instance = MyModel.parse(content_dict)
```

## Advanced Example

Here's a more complex example showing how Schemic can handle nested models:

```python
from typing import List, Optional
from datetime import datetime
from pydantic import Field
from schemic import SchemicModel

class Address(SchemicModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State or province")
    zip_code: str = Field(..., description="Postal code")
    country: str = Field("USA", description="Country name")

class ContactInfo(SchemicModel):
    email: str = Field(..., description="Email address", s_fn=["contact", "private"])
    phone: Optional[str] = Field(None, description="Phone number", s_fn=["contact"])
    address: Optional[Address] = Field(None, description="Physical address")

class User(SchemicModel):
    id: int = Field(..., description="User ID", s_fn=["system"])
    username: str = Field(..., description="Username", s_fn=["public"])
    full_name: str = Field(..., description="Full name", s_fn=["public", "profile"])
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Account creation timestamp"
    )
    contact: ContactInfo = Field(..., description="Contact information")
    roles: List[str] = Field(default_factory=list, description="User roles")

# Create schema for GPT that only includes public fields
public_schema = User.prepare_IncludeAllWithFunction("public")

# Create schema for GPT that excludes private data
no_private_schema = User.prepare_removeAllWithFunction("private")

# Create schema for GPT that excludes default values and system fields
user_input_schema = User.prepare_removeAllWithProp("default")
user_input_schema = User.prepare_removeAllWithFunction("system")
```

## Why Use Schemic?

- **Eliminate Duplicate Models**: Define your data model once and use it for both your application and GPT.
- **Preserve Type Safety**: Maintain Pydantic's validation while still being compatible with GPT.
- **Reduce Boilerplate**: Avoid writing code to convert between your models and simplified versions.
- **Flexible Field Selection**: Easily select which fields to send to GPT based on properties or custom tags.
- **Automatic Default Handling**: No more manually adding default values back to GPT responses.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
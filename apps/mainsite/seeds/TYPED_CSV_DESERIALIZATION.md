# Typed CSV Deserialization Approach

## Problem

CSV readers in Python (including `csv.DictReader`) return all values as strings. When these values need to be used as numeric types (int, float) or booleans, manual type conversion is required. Without proper type enforcement, it's easy to accidentally pass string values where numeric types are expected, leading to runtime errors or unexpected behavior.

## Solution

We enforce typed deserialization of CSV data using **dataclasses with explicit parsing functions**. This approach provides:

1. **Type safety**: Dataclasses with type annotations make the expected types explicit
2. **Clear conversion logic**: A dedicated parser function handles all type conversions
3. **Runtime validation**: Type conversions happen at parse time, failing fast on invalid data
4. **Better IDE support**: IDEs can provide autocomplete and type checking

## Implementation Approaches

### Approach 1: Custom Parser Function (Recommended for CSVs with special characters)

Used in `04_badgeclasses.py` for the `courses.csv` file:

```python
from dataclasses import dataclass

@dataclass
class CourseRow:
    """Typed representation of a course CSV row."""
    # String fields
    CourseID: str
    Name: str
    # Numeric fields - properly typed
    ECTS: float
    Studyload: int
    EQF: int
    # Boolean fields
    Supervised: bool

def parse_course_row(row: dict[str, str]) -> CourseRow:
    """Parse a CSV row dictionary into a typed CourseRow object."""
    return CourseRow(
        CourseID=row['CourseID'],
        Name=row['Name'],
        # Type conversions for numeric fields
        ECTS=float(row['ECTS']) if row['ECTS'] else 0.0,
        Studyload=int(row['Studyload']) if row['Studyload'] else 0,
        EQF=int(row['EQF']) if row['EQF'] else 0,
        # Type conversions for boolean fields
        Supervised=row['Supervised'].lower() == 'yes' if row['Supervised'] else False,
    )

# Usage:
for row in read_seed_csv('courses'):
    course = parse_course_row(row)
    # course.ECTS is now a float, not a string
    # course.Studyload is now an int, not a string
    # course.Supervised is now a bool, not a string
```

**Advantages:**
- Works with CSV columns that have special characters (spaces, hyphens)
- Explicit control over mapping between CSV column names and Python field names
- Custom conversion logic per field
- Clear and straightforward to understand

**Disadvantages:**
- Requires manual mapping of each field
- More boilerplate code

### Approach 2: Generic Typed CSV Reader (For well-named CSVs)

A generic function `read_typed_seed_csv()` is available in `util.py` for CSV files where column names match Python naming conventions:

```python
from dataclasses import dataclass

@dataclass
class SimpleSchema:
    name: str
    count: int
    ratio: float
    active: bool

# Usage:
items = read_typed_seed_csv('items', SimpleSchema)
# Automatic type conversion based on dataclass annotations
```

**Advantages:**
- Less boilerplate - automatic type conversion
- Reusable across different CSV files
- Type annotations drive the conversion logic

**Disadvantages:**
- CSV column names must match Python field names exactly
- Less flexible for custom conversion logic
- Doesn't handle CSV columns with special characters well

## Type Conversion Rules

Both approaches follow these conversion rules:

- **int**: Converts string to integer, empty strings become `0`
- **float**: Converts string to float, empty strings become `0.0`
- **bool**: Converts 'yes'/'no' (case insensitive) to `True`/`False`, empty strings become `False`
- **str**: Keeps as string (no conversion)
- **Optional[T]**: Converts to `T` or `None` if empty string (generic approach only)

## Benefits

1. **Type Safety**: IDEs and type checkers (mypy, pyright) can verify correct usage
2. **Self-Documenting**: The dataclass clearly shows what fields exist and their types
3. **Fail Fast**: Type conversion errors are caught at parse time, not when the value is used
4. **Reduced Errors**: Impossible to accidentally pass a string where an int is expected
5. **Better Testing**: Easy to create typed test fixtures

## Example: Before and After

### Before (Untyped)
```python
for course in read_seed_csv('courses'):
    # course['ECTS'] is a string "5.0"
    # Passing it to a function expecting float may cause issues
    extensions = badge_class_extensions(
        ects=course['ECTS'],  # ⚠️ Type mismatch: str vs float
    )
```

### After (Typed)
```python
for row in read_seed_csv('courses'):
    course = parse_course_row(row)
    # course.ECTS is a float 5.0
    # Type-safe and IDE can verify correctness
    extensions = badge_class_extensions(
        ects=course.ECTS,  # ✓ Correct type: float
    )
```

## Recommendations

1. **For new CSV files**: Design column names to match Python naming conventions (no spaces, no special chars) and use `read_typed_seed_csv()`
2. **For existing CSV files**: Use the custom parser approach (Approach 1) as shown in `04_badgeclasses.py`
3. **Always create a dataclass**: Even if you use the custom parser, define a dataclass to document the expected structure
4. **Add docstrings**: Document the conversion rules and any special handling in the parser function

## Further Improvements

Consider these enhancements for the future:

1. **Validation**: Add `__post_init__` to validate field values (e.g., ECTS must be positive)
2. **Error Handling**: Provide helpful error messages when conversion fails (e.g., "Invalid ECTS value 'abc' in row 5")
3. **Pydantic**: Consider using Pydantic for even more robust validation and type coercion
4. **CSV Schema Files**: Define schemas in separate configuration files for better maintainability

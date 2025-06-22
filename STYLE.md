# Coding Style & Guidelines

## Typing

### Avoid creation and importing foreign types

- Use `if TYPE_CHECKING:` blocks to define or import types to prevent unnecessary runtime
importing and object creation.
- Use strings as type hints to refer to types that aren't available at runtime.
- Builtin types should also be inside strings to avoid creating `types.GenericAlias` objects.

**Good**

```python
if typing.TYPE_CHECKING:
  from functionality_module import SomeType

my_obj: 'SomeType' # foreign type
my_set: 'set[int]' # builtin type
```

**Bad**

```python
from functionality_module import SomeType # forces loading of module

my_obj: SomeType
```

**Bad**

```python
if typing.TYPE_CHECKING:
  from functionality_module import SomeType

my_obj: SomeType # 'SomeType' is not defined
```

**Bad**

```python
if typing.TYPE_CHECKING:
  from functionality_module import SomeType

my_obj: 'SomeType'
my_set: set[int] # creates `types.GenericAlias` instance
```

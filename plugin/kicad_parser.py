"""
Minimal S-expression parser for KiCad files.
Parses KiCad's S-expression format without external dependencies.
"""

from typing import Any, List, Optional, Union

SExpr = Union[str, List["SExpr"]]


def parse_kicad(text: str) -> SExpr:
    """
    Parse S-expression text into nested Python lists.

    Args:
        text: S-expression formatted string

    Returns:
        Nested list structure representing the S-expression

    Example:
        >>> parse_sexpr('(kicad_sch (version 20230101))')
        ['kicad_sch', ['version', '20230101']]
    """
    tokens = _tokenize(text)
    result, _ = _parse_tokens(tokens, 0)
    return result


def _tokenize(text: str) -> List[str]:
    """Tokenize S-expression text into a list of tokens."""
    tokens: List[str] = []
    i = 0
    length = len(text)

    while i < length:
        char = text[i]

        # Skip whitespace
        if char in " \t\n\r":
            i += 1
            continue

        # Opening/closing parentheses
        if char == "(":
            tokens.append("(")
            i += 1
            continue

        if char == ")":
            tokens.append(")")
            i += 1
            continue

        # Quoted string
        if char == '"':
            j = i + 1
            while j < length:
                if text[j] == "\\":
                    j += 2  # Skip escaped character
                elif text[j] == '"':
                    break
                else:
                    j += 1
            # Include quotes in token, will be stripped later
            tokens.append(text[i : j + 1])
            i = j + 1
            continue

        # Unquoted atom (symbol, number, etc.)
        j = i
        while j < length and text[j] not in " \t\n\r()\"":
            j += 1
        tokens.append(text[i:j])
        i = j

    return tokens


def _parse_tokens(tokens: List[str], pos: int) -> tuple[SExpr, int]:
    """Parse tokens starting at position, return (result, new_position)."""
    if pos >= len(tokens):
        return [], pos

    token = tokens[pos]

    if token == "(":
        # Parse a list
        result: List[SExpr] = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ")":
            item, pos = _parse_tokens(tokens, pos)
            result.append(item)
        # Skip closing parenthesis
        if pos < len(tokens):
            pos += 1
        return result, pos

    elif token == ")":
        # Shouldn't happen in well-formed input
        return [], pos + 1

    else:
        # Atom (string or symbol)
        if token.startswith('"') and token.endswith('"'):
            # Remove quotes and handle escapes
            value = token[1:-1]
            value = value.replace('\\"', '"')
            value = value.replace("\\\\", "\\")
            return value, pos + 1
        return token, pos + 1


def find_elements(tree: SExpr, element_name: str) -> List[List[Any]]:
    """
    Find all elements with given name in parsed S-expression tree.

    Args:
        tree: Parsed S-expression (nested lists)
        element_name: Name of element to find (e.g., "sheet", "lib")

    Returns:
        List of matching elements (each element is a list)

    Example:
        >>> tree = parse_sexpr('(root (sheet (at 0 0)) (sheet (at 1 1)))')
        >>> find_elements(tree, 'sheet')
        [['sheet', ['at', '0', '0']], ['sheet', ['at', '1', '1']]]
    """
    results: List[List[Any]] = []
    _find_elements_recursive(tree, element_name, results)
    return results


def _find_elements_recursive(
    node: SExpr, element_name: str, results: List[List[Any]]
) -> None:
    """Recursively search for elements with given name."""
    if not isinstance(node, list):
        return

    # Check if this node matches
    if len(node) > 0 and node[0] == element_name:
        results.append(node)

    # Recurse into children
    for child in node:
        if isinstance(child, list):
            _find_elements_recursive(child, element_name, results)


def get_property(element: List[Any], property_name: str) -> Optional[str]:
    """
    Extract property value from a KiCad element.

    KiCad properties look like: (property "Name" "Value" ...)

    Args:
        element: Parsed element (list)
        property_name: Name of property to find

    Returns:
        Property value string, or None if not found

    Example:
        >>> elem = ['sheet', ['property', 'Sheetfile', 'sub.kicad_sch']]
        >>> get_property(elem, 'Sheetfile')
        'sub.kicad_sch'
    """
    if not isinstance(element, list):
        return None

    for item in element:
        if isinstance(item, list) and len(item) >= 3:
            if item[0] == "property" and item[1] == property_name:
                return str(item[2])

    return None


def get_element_value(element: List[Any], key: str) -> Optional[str]:
    """
    Get value from element by key.

    Handles patterns like: (lib (name "foo")(uri "bar"))
    where you want to get "bar" given key "uri"

    Args:
        element: Parsed element (list)
        key: Key to find (e.g., "uri", "name")

    Returns:
        Value string, or None if not found

    Example:
        >>> elem = ['lib', ['name', 'MyLib'], ['uri', '/path/to/lib']]
        >>> get_element_value(elem, 'uri')
        '/path/to/lib'
    """
    if not isinstance(element, list):
        return None

    for item in element:
        if isinstance(item, list) and len(item) >= 2:
            if item[0] == key:
                return str(item[1])

    return None

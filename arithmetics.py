import operator
import re

# Define supported operators
operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '**': operator.pow,
    '/': operator.truediv,
}


def parse_atom(tokens: list[str]) -> float:
    token = tokens.pop(0)
    if token == '(':
        result = parse_expression(tokens)
        tokens.pop(0)  # remove ')'
        return result
    else:
        return float(token)


def parse_term(tokens: list[str]) -> float:
    result = parse_atom(tokens)
    while tokens and tokens[0] in ('**', '*', '/'):
        op = tokens.pop(0)
        result = operators[op](result, parse_atom(tokens))
    return result


# Tokenize and evaluate the expression
def parse_expression(tokens: list[str]) -> float:
    result = parse_term(tokens)
    while tokens and tokens[0] in ('+', '-'):
        op = tokens.pop(0)
        result = operators[op](result, parse_term(tokens))
    return result


def eval_expression(expression: str, variables: dict = None) -> float:
    # Replace variables with their values in the expression
    if variables is not None:
        for var, value in variables.items():
            expression = expression.replace(var, str(value))

    # Split the expression into tokens
    tokens = re.findall(r'[\d.]+|\+|-|\*\*|\*|/|\(|\)', expression)

    return parse_expression(tokens)


def main():
    # Define the expression and variable values
    expression = "(foo * 3) + 1"
    variables = {"foo": 5}

    # Evaluate the expression
    result = eval_expression(expression, variables)
    print(result)


if __name__ == '__main__':
    main()

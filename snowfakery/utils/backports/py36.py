import ast

orig_literal_eval = ast.literal_eval


def correct_literal_eval(node_or_string):
    if isinstance(node_or_string, str) and node_or_string.count("-") > 1:
        raise SyntaxError("Not a literal")
    else:
        return orig_literal_eval(node_or_string)


ast.literal_eval = correct_literal_eval

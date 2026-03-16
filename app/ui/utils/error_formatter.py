def simplify_execution_error(error: str) -> str:

    if not error:
        return ""

    lines = error.splitlines()

    for line in lines:

        if "SyntaxError" in line:
            return "Syntax error in submitted code."

        if "OperationalError" in line:
            return "SQL syntax error."

        if "NameError" in line:
            return "Name error in submitted code."

    return lines[-1] if lines else error

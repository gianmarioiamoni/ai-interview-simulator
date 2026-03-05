# app/execution/python_executor.py

class PythonExecutor:
    # Executes Python coding questions inside a controlled sandbox.

    def execute(self, code: str):

        local_vars = {}

        try:

            exec(code, {}, local_vars)

            return {
                "success": True,
                "result": local_vars,
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }

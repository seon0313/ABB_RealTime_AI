class Tool:
    def __init__(self):
        self.tool = {
            "type": "function",
            "name": "calculate_sum",
            "description": "두 숫자를 더하는 함수입니다. 예: '4 + 6은 얼마야?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "첫 번째 숫자"},
                    "b": {"type": "number", "description": "두 번째 숫자"}
                },
                "required": ["a", "b"]
            }
        }
        

    def run(self, call_id, arg) -> dict:
        print(arg)
        a=arg['a']+arg['b']
        result_event = {
            "type": "function_call_output",
            "call_id": call_id,
            "output": a
        }
        return result_event
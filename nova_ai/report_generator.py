from .llm import ask_nova
from .prompts import executive_report_prompt

def generate_report(statistics):
    prompt = executive_report_prompt(statistics)

    return ask_nova(prompt)
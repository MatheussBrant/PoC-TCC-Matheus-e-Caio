import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def chamar_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada no arquivo .env")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=prompt
    )

    return response.output_text
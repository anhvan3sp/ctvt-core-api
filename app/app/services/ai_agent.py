from openai import OpenAI
import json
import os

client = OpenAI(api_key="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")



SYSTEM_PROMPT = """
Bạn là AI ERP GAS.
Chỉ trả JSON.
"""

def ask_ai(user_input):
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    return json.loads(response.choices[0].message.content)

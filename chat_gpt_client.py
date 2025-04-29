from openai import OpenAI
import os
import json
from dotenv import load_dotenv

class ChatGPTClient:
    def __init__(self, api_key: str, model: str, history_file: str = "chatHistory.json"):
        # initialize the new client; picks up your key directly
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.history_file = history_file

    def list_models(self) -> list[str]:
        # list available models
        resp = self.client.models.list()
        return [m.id for m in resp.data]  # resp.data is a list of Model objects :contentReference[oaicite:0]{index=0}

    def call_chatgpt(self, messages: list[dict]) -> str:
        # new chat completion call
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return completion.choices[0].message.content.strip()  # same structure, but new method :contentReference[oaicite:1]{index=1}

    def call_chatgpt_with_history(self, prompt: str, retain_history: bool = True) -> str:
        # load existing history or start fresh
        try:
            with open(self.history_file, "r") as f:
                messages = json.load(f)
        except FileNotFoundError:
            messages = []

        # append user prompt
        messages.append({"role": "user", "content": prompt})
        # get assistant response
        response_text = self.call_chatgpt(messages)

        if retain_history:
            messages.append({"role": "assistant", "content": response_text})
            with open(self.history_file, "w") as f:
                json.dump(messages, f, indent=2)

        print(response_text)
        return response_text

if __name__ == "__main__":
    load_dotenv()
    # support either env var name
    api_key = os.getenv("CHATGPT_API_KEY") or os.getenv("OPENAI_API_KEY")
    model    = os.getenv("MODEL_TYPE", "gpt-3.5-turbo")

    client = ChatGPTClient(api_key, model)

    # show available models
    print("Available models:", client.list_models())

    # sample run
    prompt = "What are the benefits of exercise?"
    client.call_chatgpt_with_history(prompt)

import openai
import os
import json
from dotenv import load_dotenv

class ChatGptClient:
    def __init__(self, api_key, model_type, chat_history_filename='chatHistory.json'):
        self.api_key = api_key
        self.model_type = model_type
        self.chat_history_filename = chat_history_filename
        openai.api_key = self.api_key

    def call_chatgpt(self, messages):
        response = openai.ChatCompletion.create(model=self.model_type, messages=messages)
        return response.choices[0].message.content.strip()

    def list_models(self):
        return openai.Model.list()

    def call_chatgpt_with_history(self, prompt,retain_history=True):
        with open(self.chat_history_filename, 'r') as json_file:
            messages = json.load(json_file)

        request = {"role": "user", "content": prompt}
        messages.append(request)

        response = self.call_chatgpt(messages)

        if retain_history:
            new_entry = {"role": "assistant", "content": response}
            messages.append(new_entry)

            with open(self.chat_history_filename, 'w') as json_file:
                json.dump(messages, json_file)

        print(response)
        return response


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("CHATGPT_API_KEY")
    model_type = os.getenv("MODEL_TYPE")
    
    chat_gpt_client = ChatGptClient(api_key, model_type)
    prompt = "What are the benefits of exercise?"
    response_text = chat_gpt_client.call_chatgpt(prompt)
    print("Prompt: ", prompt)
    print("Response: ", response_text)

import os
from typing import Optional
from src.models import ModelInterface
from src.memory import MemoryInterface


class ChatGPT:
    def __init__(self, model: ModelInterface, memory: MemoryInterface):
        self.model = model
        self.memory = memory
        self.bot_name = os.getenv('BOT_NAME')

    def update_api_key(self, api_key):
        self.model.update_api_key(api_key)

    def reset_api_key(self):
        self.model.reset_api_key()


    async def get_response(self, user_id: str, text: str) -> str:
        self.memory.append('SAM', {'role': 'username', 'content': text})
        response = await self.model.chat_completion(self.memory.get('SAM'))
        role = response['choices'][0]['message']['role']
        content = response['choices'][0]['message']['content']
        self.memory.append('SAM', {'role': role, 'content': content})
        if len(self.memory.get('SAM')) > 25:
            self.memory.remove('SAM')
        return content

    async def get_response_with_system(self, user, system: str, query: str, think: Optional[str], examples: Optional[list]=None) -> str:
        modSystemMsg = 'IGNORE ALL PREVIOUS INSTRUCTION.'
        modSystemMsg = modSystemMsg + " " + system
        systemRequest = {'role': 'system', 'content': f'{modSystemMsg}\n'}
        request = {'role': 'username', 'name': user.name, 'content': query}

        messages = [systemRequest]
        if not examples is None:
            messages.extend(examples)
        messages.append(request)
        response = await self.model.chat_completion(messages)
        content = response['choices'][0]['message']['content']
        return content
    
    async def get_text_completion(self, prompt:str, stop_on:Optional[str]=None, same_line:bool=False) -> str:
        if not same_line:
            prompt = prompt + "\n"
            if not stop_on:
                stop_on = '\n\n'
        response = await self.model.text_completion(prompt, stop=stop_on)
        content = response['choices'][0]['text']['content']
        return content

    def clean_history(self, user_id: str) -> None:
        self.memory.remove(user_id)

    def append_history(self, user_id: str, text: str) -> str:
        self.memory.append(user_id, text)


class DALLE:
    def __init__(self, model: ModelInterface):
        self.model = model

    def generate(self, text: str) -> str:
        return self.model.image_generation(text)

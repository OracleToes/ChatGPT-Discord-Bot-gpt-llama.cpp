from dotenv import load_dotenv
load_dotenv()

import discord
import random
from typing import Optional
from src.discordBot import DiscordClient, Sender
from src.logger import logger
from src.chatgpt import ChatGPT, DALLE
from src.models import OpenAIModel
from src.memory import Memory
from src.server import keep_alive
import os


bot_name = os.getenv('BOT_NAME')
model_name = os.getenv('MODEL_NAME')

models = OpenAIModel(api_key=os.getenv('OPENAI_API'),
                     model_engine=os.getenv('OPENAI_MODEL_ENGINE'))

memory = Memory(system_message=os.getenv('SYSTEM_MESSAGE'))
chatgpt = ChatGPT(models, memory)
dalle = DALLE(models)


def run():
    client = DiscordClient()
    sender = Sender()

    @client.tree.command(name="autocomplete", description="Autocomplete your sentence")
    async def autocomplete(interaction: discord.Interaction, *, prompt: str, stop_on: Optional[str]=None, same_line:bool=False):
        if interaction.user == client.user:
            return
        await interaction.response.defer()
        await interaction.followup.send("> " + prompt )
        receive = await chatgpt.get_text_completion(prompt, stop_on, same_line)
        if len(receive) > 2000:
            await interaction.followup.send(receive[:2000])
            await interaction.followup.send(receive[2000:])
        else:
            await interaction.followup.send(receive)


    @client.tree.command(name="reset", description="Reset JANE's memory")
    async def reset(interaction: discord.Interaction):
        user_id = interaction.user.id
        logger.info(f"resetting memory from {user_id}")
        try:
            await interaction.response.defer(ephemeral=True)
            chatgpt.clean_history('SAM')
            await interaction.followup.send(f'> Reset ChatGPT conversation history < - <@{user_id}>')
        except Exception as e:
            logger.error(f"Error resetting memory: {e}")
            await interaction.followup.send('> Oops! Something went wrong. <')

    @client.event
    async def on_message(message):
        # don't react to your own messages
        if message.author == client.user:
            return

        print(f'Channel ID: {message.channel.id}')
        if str(message.channel.id) != '658742005794471953':
            return

        # respond if addressed
        # if not addressed only respond to 10% of the messages
        randomChance = random.random()
        print(f'Random Value: {randomChance}')
        if (bot_name.lower() not in message.content.lower()) and randomChance > 0.15:
            return
        
        print(f'{bot_name} auto-generating a message...')

        # content = message.content  # username: user.name
        channel = message.channel
        # if random.random() < 0.1:

        # Get last 30 messages in the channel
        messages = [message async for message in channel.history(limit=20)]
        message_history = []

        # Just get the last 20 before the current message
        for i, msg in enumerate(messages):
            if msg.id == message.id:
                message_history = messages[i:i+15]
        message_history.reverse() # they come in reversed order

        # Replace author bot_name with 'You' for the prompt
        # Replace bot responses (starting with 🤖) with "Bot" author. This is so we don't confuse "you" with being the bot
        message_history_str = "\n".join(f"{'JANE' if m.content.startswith('🤖') else 'jane' if m.author.name == bot_name else m.author.name}: {m.content}" for m in message_history)
        
        authors = [message.author.name for message in message_history if message.author.name != bot_name]
        authors = list(set(authors)) # get unique set of authors
        author_names = ", ".join(authors)

        prompt = f"""You, {author_names} are users on a discord server, in #the-jar. You are {bot_name}, the female human brain-in-a-jar experiment:
{message_history_str}
jane:"""
        async with channel.typing():
            receive = await chatgpt.get_text_completion(prompt, '\n', True)
            receive = ':no_mouth:' if len(receive) == 0 else receive # response with :no_mouth: if the response failed
        await sender.send_human_message(receive.lower(), channel)
        return


    @client.event
    async def on_reaction_add(reaction, user):
        message = reaction.message
        content = message.content  # username: user.name
        channel = message.channel

        # Max only 1 reply per reaction
        if reaction.count > 1:
            return

        if reaction.emoji == '🧠':
            pending_message = await message.reply(f'🧠 _{bot_name} is thinking..._')
            receive = await chatgpt.get_response(user.id, content)
            await sender.reply_message(message, receive, pending_message)

    # ImageGen not supported
    # @client.tree.command(name="imagine", description="Generate image from text")
    # async def imagine(interaction: discord.Interaction, *, prompt: str):
    #     if interaction.user == client.user:
    #         return
    #     await interaction.response.defer()
    #     image_url = dalle.generate(prompt)
    #     await sender.send_image(interaction, prompt, image_url)

    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    keep_alive()
    run()

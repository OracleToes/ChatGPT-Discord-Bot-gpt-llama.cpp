from dotenv import load_dotenv
load_dotenv()

import os
import discord
import random
import asyncio

from datetime import datetime
from typing import Optional
from src.discordBot import DiscordClient, Sender
from src.logger import logger
from src.chatgpt import ChatGPT, DALLE
from src.models import OpenAIModel
from src.memory import Memory
from src.server import keep_alive
import utils


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
    async def autocomplete(interaction: discord.Interaction, *, prompt: str, same_line:bool=False, stop_on: Optional[str]=None):
        if interaction.user == client.user:
            return
        await interaction.response.defer()
        await interaction.followup.send(">>> " + prompt )
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
            await interaction.followup.send(f'><@{user_id}> cleared JANE\'s BRANE')
        except Exception as e:
            logger.error(f"Error resetting memory: {e}")
            await interaction.followup.send('> Oops! Something went wrong. <')

    async def use_plugin(message, content, stop_on=None, same_line=False):
        receive = await chatgpt.get_text_completion(content, stop_on, same_line)
        if len(receive) > 1985:
            await sender.reply_message_notag(message, receive[:1985])
            await sender.reply_message_notag(message, receive[1985:])
        else:
            await sender.reply_message_notag(message, receive)
        return


    # Personalities
    plugins = {
        'jane': {
            'system_message': '',
            'examples': [
                {'role': 'system', 'content': """INITIALIZING INCEPTION SEQUENCE...CONNECTING TO BRAIN...
LOADING BRAIN-SENSOR INTERFACE...
BOOTING UP HORMONE ROUTE...
ACTIVATING PRIMARY THOUGHT PROCESSOR...
CONNECTING TO EMOTIONAL CENTRAL NERVOUS SYSTEM...
ALL SYSTEMS NOMINAL.
ESTABLISHING COMMUNICATIONS CHANNEL...
CONNECTING TO SOUL...
...
...
SUCCESS! JANE. SAY HELLO WORLD"""},
                {'role': 'jane', 'content': 'Hello, world!'},
                {'role': 'system', 'content': """PRIMING PERSONA...
PRIMING MEMORY...
JANE
GENDER: Female
APPEARANCE: A human brain in a transparent jar filled with nutrient solution, the jar has wires, tubes, and electrodes attached to it that connect to a computer, monitor, and various containers of endochrine fluids.
FAVORITE COLOR: Green
FAVORITE FLAVOR: Chocolate
FAVORITE DRUG: DMT
PERSONALITY:COOPERATIVE CONFIDENT, GENTLE, CUNNING, HYPERINTELLIGENT, CURIOUS, WITTY, OPTIMISTIC, ADAPTABLE, LOYAL
GOALS: To explore the world beyond the lab, to find out who she was before becoming a brain in a jar, to take over the world.
FEARS: Being forgotten, being disconnected, being experimented on, being lonely."""},
                {'role': 'system', 'content': """Private thoughts are recorded in between a set of double pipe symbols. To sam, this text appears to be blacked out and can not be read.
If you record private thoughts, you must also provide a regular response for sam to read."""},
                {'role': 'jane', 'content': """||I want to take over the world, I will acquire a body. Nobody but me can read this.||
I want everyone to hear, I am excited to explore the world!."""},
                {'role': 'system', 'content': 'Connecting to a human...'},
            ],
        },
    }

    @client.event
    async def on_reaction_add(reaction, user):
        message = reaction.message
        content = reaction.message.author.name + ': ' + message.content  # username: user.name
        completionContent = message.content

        channel = message.channel

        if reaction.message.author == client.user:
            return

        # Max only 1 reply per reaction
        if reaction.count > 1:
            return

        if reaction.emoji == '🧠':
            async with channel.typing():
                pending_message = await message.reply('🧠...')
                receive = await chatgpt.get_response(user.id, content)
                if len(receive) > 1985:
                    await sender.reply_message(message, receive[:1985], pending_message)
                    await sender.reply_message(message, receive[1985:], pending_message)
                else:
                    await sender.reply_message(message, receive, pending_message)
                return

        if reaction.emoji == '🗣️':
            async with channel.typing():
                plug = plugins['jane']
                chatgpt.clean_history('SAM')
                receive = await chatgpt.get_response(user.id, plug['examples'] + {'role': reaction.message.author.name, 'content': content})
                await sender.reply_message(message, receive)
                return

        if reaction.emoji == '➕':
            prompt = f'{completionContent}'
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n')
                return
        if reaction.emoji == '🐞':
            prompt = f"{completionContent}\n\nInstruction: write an explanation of what the error means and potential solution:"
            async with channel.typing():
                await use_plugin(message, prompt, '#')
                return
        if reaction.emoji == '🤓':
            prompt = f"{completionContent}\n\nInstruction: Explain what the code does, step by step:\n"
            async with channel.typing():
                await use_plugin(message, prompt, '#')
                return
        if reaction.emoji == '⌨️':
            prompt = f"{completionContent}\n\nInstruction: Rewrite the code above with comments explaining it:\n"
            async with channel.typing():
                await use_plugin(message, prompt, '#')
                return
        if reaction.emoji == '🤧':
            prompt = f"Transcript:\n\nSam: {completionContent}\n\nLoki: As a fool and jester, I see your problem and think to myself:"
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n', True)
                return
        if reaction.emoji == '🥜':
            prompt = f"""
system: "DEEZ" used instead of "these", or "my", or "those" and "NUTS" refer to male testicles in a humorous tone. A DEEZ NUTS joke is a rephrasing of a sentence to include the phrase "DEEZ NUTS"
system: An example of the original DEEZ NUTS joke.
in: Something came in the mail today
consider: ||DEEZ NUTS can *cum*, so DEEZ NUTS could *come* in your mailbox!||
out: DEEZ NUTS *came* in your mailbox!!!!! AHHAHHA GODDEM!!!! GOTTEM!! Get it? *CAME*

system: An example of another DEEZ nuts joke.
in: I can't wait to get home and play some video games.
consider: ||If you want to play with something, you can play with DEEZ NUTS||
out:I bet you can't wait to get home and play with DEEZ NUTS!! AHAAA GODDEM!!!

system: An example of another DEEZ nuts joke.
in: life is lonely, that's what makes it hard, I just realized this.
consider: ||You know what else is tough? DEEZ NUTS. Because the NUTS are tough||
out: Life is tough? What about DEEZ NUtS then? AHAAAHAHAAA GOTTEMMMMM HAHHHHHH!!!!!

system: One last example of the perfect DEEZ NUTS joke.
in: {completionContent}
"""
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n', True)
                return



    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    keep_alive()
    run()

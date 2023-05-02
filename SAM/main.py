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

    async def use_plugin(message, content, stop_on=None, same_line=False):
        receive = await chatgpt.get_text_completion(content, stop_on, same_line)
        if len(receive) > 1985:
            await sender.reply_message_notag(message, receive[:1985])
            await sender.reply_message_notag(message, receive[1985:])
        else:
            await sender.reply_message_notag(message, receive)
        return


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

        if reaction.emoji == '➕':
            prompt = f'{completionContent}'
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n')
                return
        if reaction.emoji == '🐞':
            prompt = f"{completionContent}\n\nInstruction: write an explanation of what the error means and potential solution, when finished print FINISHED:"
            async with channel.typing():
                await use_plugin(message, prompt, 'FINISHED')
                return
        if reaction.emoji == '🤓':
            prompt = f"{completionContent}\n\nInstruction: Explain what the code does to a five year old, when finished, print FINISHED:\n"
            async with channel.typing():
                await use_plugin(message, prompt, 'FINISHED')
                return
        if reaction.emoji == '⌨️':
            prompt = f"{completionContent}\n\nInstruction: Rewrite the code above with comments explaining it, when finished write FINISHED:\n"
            async with channel.typing():
                await use_plugin(message, prompt, 'FINISHED')
                return
        if reaction.emoji == '🤧':
            prompt = f"Transcript titled 'Loki, God of Mischief, tells it like it is'\n\n\n{reaction.message.author.name}: {completionContent}\nLoki: As a fool and a jester, I see your situation and think to myself,"
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n', True)
                return
        if reaction.emoji == '🥜':
            prompt = f"""system: "DEEZ" is used instead of "these", or "my", or "those" and "NUTS" refer to male testicles in a humorous tone. Avoid saying "my DEEZ" or "those DEEZ" instead you would just say "DEEZ"
system: An example of the original DEEZ NUTS joke.
in: Something came in the mail today
out: *DEEZ NUTS* *came* in your mailbox!!!!! AHHAHUEHA GODDEM!!!! GOTTEM!! Get it? *CAME*

in: I can't wait to get home and play some video games.
out:I bet you can't wait to *play* with *DEEZ NUTS*!! HAAAUUEUAAHAuAHH GOTTEM!!!

in: They're everywhere, I can't hide!
out: I can't hide from "DEEZ NUTS*! *They're EVERYWHERE*!! AHAAHAHHUEUHAUAUEUUHGODDEM!!! GOTTTEMMM!!!

in: I don't know, that one is kind of reaching...
out: REACHING FOR DEEZ NUTS!! AHAAHHGODDEM!!! GOTTTEMMM!!!

in: {completionContent}
out:"""
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n', True)
                return

        if reaction.emoji == '😬':
            prompt = f"""instruction: reply with the most cringeworthy reply possible
{reaction.message.author.name}: I don't feel so good.
Twangy: I'm sorry to hear that homie, I hope it gets better for you. 

{reaction.message.author.name}: I like spirituality, magic, aliens, and psychic stuff
Twangy:That's bad homie. I don't do that.

Twangy: sorry to hear about that homie

{reaction.message.author.name}: What did you do today?
Twangy: I whacko my snacko again, I feel really bad.

Twangy: I always coom in my pants.

{reaction.message.author.name}: I got hurt today
Twangy: It always hurts when i coom

{reaction.message.author.name}: I had a bad day today
Twangy: sorry to hear about that homie, I hope it gets better for you.

{reaction.message.author.name}: My hair is brown
Twangy: The only thing brown is the tip of my penis.

Twangy: That's bad, homie

{reaction.message.author.name}: What do you think about vampires and werewolves
Twangy: I hate them, that's bad, homie.

Twangy: okay homie.

instruction: reply with the most cringeworthy reply possible
{reaction.message.author.name}: {completionContent}
Twangy:"""
            async with channel.typing():
                await use_plugin(message, prompt, '\n\n', True)
                return



    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    keep_alive()
    run()

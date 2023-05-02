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

        if reaction.emoji == '👁️':
                await chatgpt.append_history('SAM', content)
        return



    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    keep_alive()
    run()

import os
import discord
import random

from src.logger import logger

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

class DiscordClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=intents)
        self.synced = False
        self.added = False
        self.tree = discord.app_commands.CommandTree(self)
        self.activity = discord.Activity(
            type=discord.ActivityType.watching, name="➕🐞🤓⌨️🤧🥜 reacts")


    async def on_ready(self):
        await self.wait_until_ready()
        logger.info("Syncing")
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        if not self.added:
            self.added = True
        logger.info(f"Synced, {self.user} is running!")


class Sender():
    bot_name = os.getenv('BOT_NAME')
    model_name = os.getenv('MODEL_NAME')

    async def send_message(self, interaction, send, receive, system_message=None):
        try:
            user_id = interaction.user.id
            system_msg = '' if system_message is None else f'> _**SYSTEM**: {system_message}_\n> \n'
            response = f'{receive}\n🧠'
            await interaction.followup.send(system_msg + response)
            logger.info(f"{user_id} sent: {send}, response: {receive}")
        except Exception as e:
            await interaction.followup.send('> **Error: Something went wrong, please try again later!**')
            logger.exception(
                f"Error while sending:{send} in chatgpt model, error: {e}")
            
    async def send_human_message(self, receive, text_channel):
        try:
            await text_channel.send(receive)
        except Exception as e:
            await text_channel.send('> **Error: Something went wrong, please try again later!**')
            logger.exception(
                f"Error while replying to message in chatgpt model, error: {e}")

    async def reply_message(self, message, receive, pending_message=None):
        try:
            response = f'{receive}\n🧠'
            await message.reply(response)
                
            logger.info(f"message replied sent: {receive}")
        except Exception as e:
            await message.reply('> **Error: Something went wrong, please try again later!**')
            logger.exception(
                f"Error while replying to message in chatgpt model, error: {e}")

    async def reply_message_notag(self, message, receive, pending_message=None):
        try:
            response = f'{receive}'
            await message.reply(response)
                
            logger.info(f"message replied sent: {receive}")
        except Exception as e:
            await message.reply('> **Error: Something went wrong, please try again later!**')
            logger.exception(
                f"Error while replying to message in chatgpt model, error: {e}")

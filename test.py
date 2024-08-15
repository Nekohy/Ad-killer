import asyncio
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon import functions, types, events
from opentele.tl import TelegramClient
from opentele.api import API
from telethon.sessions import StringSession


async def main():
    api = API.TelegramDesktop.Generate(system="windows", unique_id="test")
    await asyncio.sleep(10)
    async with TelegramClient(StringSession(string_bot), api) as client:
        @client.on(events.NewMessage(pattern='/report'))
        async def report(event):
            if event.is_reply:
                reply = await event.get_reply_message()
                sender = await reply.get_sender()
                result = await client(functions.users.GetFullUserRequest(
                    id=reply.from_user.id
                ))

asyncio.run(main())

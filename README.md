# @honka_says_bot - an animated sticker generator bot for Telegram
A Python script to run Honka Says Bot.
This simple script will generate text, place it onto a sticker and send them to you via inline.

Its available at https://t.me/honka_says_bot and works in any chat via inline request.

As the Bot API doesn't let you send animated stickers via inline response (yet), we have to use something more powerful, like Telethon. It has the tools we need to create what we need.

# Requirements
This bot uses:
`Telethon==1.16.2`  
`lottie==0.6.5`  
`systemd==0.16.1`

There is a requirements file to help you with that. 
`systemd` package is just for convenient logging when you launch the script as a service.
You will also need to register your custom Telegram Client to use it's credentials with Telethon, please refer to it's documentation.

# Launch
Simply run `bot.py`

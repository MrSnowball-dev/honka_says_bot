#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

import os, json, gzip, hashlib
from systemd import journal

# import API keys
from settings import *

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon import events, utils

from lottie.utils.font import FontStyle
from lottie.objects.text import TextJustify
from lottie import objects, Color

# load templates once script starts
with open('template.json', encoding='utf-8') as temp_json:
    template_sticker = json.load(temp_json)
with open('reverse_template.json', encoding='utf-8') as temp_json:
    reverse_template_sticker = json.load(temp_json)

# define sticker generator:
# file_name - how generated sticker will be named
# text - what text to render on a sticker
# size, margin, top_margin - variables to properly position generated text, these are fixed, but might be customizable later
# direction - which way the sticker will face, defines what sticker template to use for generation
def generateHonka(file_name: str, text: str, size: int = 35, margin: int = 0, top_margin: int = -5, direction: str = 'normal'):
    # define font and template to work with
    font = FontStyle("Comic Sans MS:style=bold", size, justify=TextJustify.Center, emoji_svg='twemoji-svg/')
    t_sticker = template_sticker.copy()
    if direction == 'reverse':
        t_sticker = reverse_template_sticker.copy()
    t_layer = t_sticker["layers"][2]

    # render text
    text_shape = font.render(text)

    # create a layer with the same parameters as the template
    layer = objects.ShapeLayer.load(t_layer)
    layer.name = f"{text} outlines"
    layer.shapes.clear()

    # add text shapes on the layer
    added_text = layer.add_shape(text_shape)
    added_text.transform.position.value.x = margin
    added_text.transform.position.value.y = top_margin
    layer.add_shape(objects.Fill(Color(0, 0, 0)))

    # replace existing layer with the new one
    layer_dict = layer.to_dict()
    t_sticker["layers"][2] = layer_dict

    # save to .tgs
    with gzip.open(os.path.join('renders', file_name+'.tgs'), "wb") as final_tgs:
        final_tgs.write(json.dumps(t_sticker).encode("utf-8"))

    return True;

# init Telethon bot client and start it
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
journal.send('Bot started!')

# create inline request handler
@bot.on(events.InlineQuery)
async def handler(event):
    # define default variables
    builder = event.builder

    direction = 'normal'
    text_to_render = event.text
    # check if user has the dot at the end of a query to reduce load and not generate excessive
    # amounts of unused files
    if not text_to_render.endswith('.'):
        await event.answer(results=[
            builder.document(utils.resolve_bot_file_id('CAADAgADUAADq1fEC2ZINSTHw8cmAg'), type='sticker')
        ], switch_pm='End your query with a dot', switch_pm_param='DOT', cache_time=0, gallery=True)
    else:
        text_to_render = text_to_render[:-1]

        # check if user wants reversed sticker
        if text_to_render.startswith('-'):
            text_to_render = text_to_render[1:]
            direction = 'reverse'

        try:
            # we generate sticker name based on a text someone sent,
            # hashing it for security and convenience
            sticker_name = hashlib.md5(str(text_to_render).encode('utf-8')).hexdigest()

            # check if the text in query is empty and answer
            # with a stub sticker and warning text, if not - generate sticker with this text
        
            if text_to_render == '':
                await event.answer(results=[
                    builder.document(utils.resolve_bot_file_id('CAADAgADUAADq1fEC2ZINSTHw8cmAg'), type='sticker')
                ], switch_pm='Visit @honka_home for updates', switch_pm_param='HONK', cache_time=86400, gallery=True)
            else:
                # we don't want to generate the same sticker over again,
                # so if someone happen to use the same query and TG has no cache for it
                # we just answer with existing stickers
                if os.path.exists(os.path.join('renders', sticker_name+'.tgs')):
                    journal.send('Send existing '+direction+' stickers for '+text_to_render+', hash '+sticker_name)
                    await event.answer(results=[
                        builder.document(os.path.join('renders', sticker_name+'-small.tgs'), type='sticker'),
                        builder.document(os.path.join('renders', sticker_name+'.tgs'), type='sticker'),
                        builder.document(os.path.join('renders', sticker_name+'-large.tgs'), type='sticker')
                    ], switch_pm='Visit @honka_home for updates', switch_pm_param='HONK', cache_time=86400, gallery=True)
                else:
                    # generate and send stickers for a query, in different sizes,
                    # setting cache time to 86400 seconds (a day) 
                    # helps to skip generating similar queries
                    journal.send('Generating '+direction+' stickers for '+text_to_render+', hash '+sticker_name)
                    generateHonka(sticker_name, str(text_to_render), direction=direction)
                    generateHonka(sticker_name+'-small', str(text_to_render), 25, top_margin=-10, direction=direction)
                    generateHonka(sticker_name+'-large', str(text_to_render), 48, top_margin=1, direction=direction)
                    await event.answer(results=[
                        builder.document(os.path.join('renders', sticker_name+'-small.tgs'), type='sticker'),
                        builder.document(os.path.join('renders', sticker_name+'.tgs'), type='sticker'),
                        builder.document(os.path.join('renders', sticker_name+'-large.tgs'), type='sticker')
                    ], switch_pm='Visit @honka_home for updates', switch_pm_param='HONK', cache_time=86400, gallery=True)
        except FloodWaitError as identifier:
            # show an explanation on why no stickers being sent to a user in case of a flood detection
            journal.send('Got flooded, waiting for '+identifier.seconds+' seconds')
            await event.answer([builder.article('ERROR', description='Telegram paused the bot for '+str(identifier.seconds)+' seconds. Please wait.', text='Patiently waiting for '+str(identifier.seconds)+' seconds and then I HONK!!!')], cache_time=identifier.seconds)

        bot.session.close()

# create simple message handler
# set some advertising messages when someone uses PM with the bot
@bot.on(events.NewMessage)
async def messageHandler(event):
    if event.text == '/start HONK':
        await bot.send_message(event.sender_id, 'Go to @honka_home for updates!')
    elif event.text == '/start DOT':
        await bot.send_message(event.sender_id, 'You must end your query with a dot\n\nВаш запрос должен оканчиваться точкой')
    else:
        await bot.send_message(event.sender_id, 'Use this bot inline in any chat!\nJust type your text with a dot at the end:\n@honka_says_bot `text.`\n\nБот работает в любом чате!\nПросто наберите (не забудьте точку в конце):\n@honka_says_bot `ваш_текст.`', parse_mode='md')

bot.run_until_disconnected()
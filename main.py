import asyncio
import logging
import re
import os
from config import config
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from SsstikScraper import scraper
from downloader import downloader  # Importing the downloader module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

# Regex patterns for validating Instagram and TikTok URLs
REG_INSTAGRAM = r'https:\/\/www\.instagram\.com\/(p|reel)\/([A-Za-z0-9-_]+)\/'
REG_TIKTOK = r'https://(vm\.tiktok\.com/\w+|www\.tiktok\.com/@[\w.-]+/(photo|video)/\d+|www\.tiktok\.com/video/\d+|www\.tiktok\.com/@\w+/video/\d+|vm\.tiktok\.com/\d+|www\.tiktok\.com/t/\w+|m\.tiktok\.com/v/\d+|www\.tiktok\.com/[\w.-]+/video/\d+|vt\.tiktok\.com/\w+)'

@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку TikTok или Instagram, чтобы получить медиафайл.")

@dp.message()
async def download_content(message: types.Message):
    url = message.text
    instagram = re.search(REG_INSTAGRAM, url)
    tiktok = re.search(REG_TIKTOK, url)

    try:
        if instagram or tiktok:
            msg = await message.answer('⏳идет скачивание ...')
            content = await downloader(urls=url)

            if not content.get('error'):
                media = content['medias'][0]
                if media['type'] == 'image':
                    await bot.send_photo(chat_id=message.chat.id, photo=media['url'])
                elif media['type'] == 'video':
                    await bot.send_video(chat_id=message.chat.id, video=media['url'])

                # Check if there are multiple media items for TikTok
                if tiktok and 'medias' in content and len(content['medias']) > 1:
                    await bot.send_audio(chat_id=message.chat.id, audio=content['medias'][-1]['url'])
            else:
                # Provide fallback link if content isn't available
                fallback_url = url.replace('www.', 'dd')
                await message.answer(f"Content not available. Here's a fallback link: {fallback_url}")

            await msg.delete()
        else:
            await message.answer("Неверный URL-адрес. Пожалуйста, отправьте действительную ссылку Instagram или TikTok.")
    except Exception as e:
        logger.error(f"Failed to send media: {e}")
        await message.answer("Failed to process the media.")

@dp.message(lambda message: re.match(REG_TIKTOK, message.text))
async def handle_tiktok_link(message: types.Message):

    user_id = message.from_user.id
    user_lock = await get_user_lock(user_id)

    async with user_lock:
        url = message.text  # Extracting URL from the message text
        logger.info(f"Received TikTok link from user {user_id}: {url}")

        # Log the request
        await log_request(user_id, url)

        # Notify user about the start of the download
        start_message = await message.reply('Starting download, please wait...')

        # Send a random sticker
        sticker_message_id = await send_random_sticker(message.chat.id)

    try:
        result = scraper(url)  # Using the URL here
        logger.info(f"Scraper result: {result}")

        if result and 'type' in result:
            async with aiohttp.ClientSession() as session:
                # Handle video download
                if result['type'] == 'video' and 'video' in result:
                    video_file = await download_file(session, result['video'], 'video.mp4')
                    if video_file:
                        with open(video_file, 'rb') as video:
                            await bot.send_video(message.chat.id, video)
                        os.remove(video_file)  # Remove video after sending

                # Handle music download
                if 'music' in result:
                    music_file = await download_file(session, result['music'], 'music.mp3')
                    if music_file:
                        with open(music_file, 'rb') as music:
                            await bot.send_audio(message.chat.id, music)
                        os.remove(music_file)  # Remove music after sending

                # Handle image downloads
                if 'images' in result:
                    for i, img_url in enumerate(result['images']):
                        img_file = await download_file(session, img_url, f'image_{i}.jpg')
                        if img_file:
                            with open(img_file, 'rb') as image:
                                await bot.send_photo(message.chat.id, image)
                            os.remove(img_file)  # Remove image after sending

                # Send description if available
                if 'desc' in result:
                    await message.reply(f"{result['desc']}")

        else:
            await message.reply("Could not determine the content type or keys are missing. Try another link.")

    except Exception as e:
        logger.error(f"Error processing link {url} from user {user_id}: {e}")

    finally:
        try:
            await bot.delete_message(message.chat.id, sticker_message_id)
            await bot.delete_message(message.chat.id, start_message.message_id)
        except Exception as e:
            logger.error(f"Error deleting message or sticker: {e}")

async def main():
    print("Bot is running")
    print("████████╗███████╗████████╗██████╗░██╗██╗░░██╗")
    print("╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██║╚██╗██╔╝")
    print("░░░██║░░░█████╗░░░░░██║░░░██████╔╝██║░╚███╔╝░")
    print("░░░██║░░░██╔══╝░░░░░██║░░░██╔══██╗██║░██╔██╗░")
    print("░░░██║░░░███████╗░░░██║░░░██║░░██║██║██╔╝╚██╗")
    print("░░░╚═╝░░░╚══════╝░░░╚═╝░░░╚═╝░░╚═╝╚═╝╚═╝░░╚═╝")
    print("GitHub repository: https://github.com/TETRIX8/insta.git")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


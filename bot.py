import asyncio
import os
import tempfile
from pathlib import Path

import edge_tts
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message

from pronunciation import MAX_CHARS, prepare_for_tts, split_text

TOKEN = os.getenv("BOT_TOKEN")
VOICE = os.getenv("EDGE_VOICE", "uz-UZ-MadinaNeural")
RATE = os.getenv("EDGE_RATE", "+10%")

async def synthesize(text: str, output: Path) -> None:
    prepared = prepare_for_tts(text)
    if not prepared:
        raise ValueError("Matn bo'sh")
    await edge_tts.Communicate(prepared, VOICE, rate=RATE).save(str(output))

async def send_audio_parts(message: Message, text: str) -> None:
    chunks = split_text(text, MAX_CHARS)
    status = await message.answer(
        f"Tayyorlanmoqda...\nQismlar: {len(chunks)}\n"
        f"Limit: {MAX_CHARS:,} belgi\nVoice: {VOICE}"
    )

    with tempfile.TemporaryDirectory() as td:
        outputs = []
        for index, chunk in enumerate(chunks, 1):
            output = Path(td) / f"part_{index:03d}.mp3"
            await synthesize(chunk, output)
            outputs.append((index, chunk, output))

        for index, chunk, output in outputs:
            await message.answer_audio(
                FSInputFile(output),
                caption=f"{index}-qism / {len(chunks)} | {len(chunk):,} belgi | G2P -> Madina",
            )

    await status.edit_text(
        f"Tayyor: {len(chunks)} ta qism.\n"
        "G2P preprocessing -> uz-UZ-MadinaNeural -> MP3"
    )

async def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN secret topilmadi")

    bot = Bot(TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            "Assalomu alaykum!\n\n"
            "Oddiy matn yoki TXT fayl yuboring.\n"
            f"Matn {MAX_CHARS:,} belgigacha qismlarga bo'linadi, "
            "G2P/preprocessing qilinadi va Madina ovozida MP3 yuboriladi."
        )

    @dp.message(F.document)
    async def document_handler(message: Message, bot: Bot) -> None:
        filename = message.document.file_name or "text.txt"
        if Path(filename).suffix.lower() != ".txt":
            await message.answer("Hozircha faqat TXT fayl qabul qilinadi.")
            return

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / filename
            await bot.download(message.document, destination=path)
            text = path.read_text(encoding="utf-8", errors="ignore")
            await send_audio_parts(message, text)

    @dp.message(F.text)
    async def text_handler(message: Message) -> None:
        text = (message.text or "").strip()
        if text and not text.startswith("/"):
            await send_audio_parts(message, text)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

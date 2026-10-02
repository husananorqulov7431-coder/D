# Uzbek G2P Edge TTS Bot

Independent test project for Uzbek pronunciation preprocessing with Microsoft Edge TTS.

Flow:

TXT/plain text
-> 14,800-character chunking
-> Uzbek G2P-inspired preprocessing
-> Edge TTS: uz-UZ-MadinaNeural
-> MP3

IPA is not sent directly to Edge TTS. The pronunciation rules are converted into readable TTS-friendly text.

Required GitHub Actions secret:

BOT_TOKEN

Optional environment variables:

EDGE_VOICE=uz-UZ-MadinaNeural
EDGE_RATE=+10%

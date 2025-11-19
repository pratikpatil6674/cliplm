from googletrans import Translator

async def translate_text(src_text, dest='en'):
    async with Translator() as translator:
        result = await translator.translate(src_text, dest=dest)
        return result.text

async def main():
    print(await translate_text("こんにちは", dest="en"))

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(translate_text("こんにちは", dest="en"))
    print(result)
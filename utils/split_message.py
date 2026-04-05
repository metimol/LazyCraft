async def split_message(text: str, limit: int = 4000):
    chunks = []
    current_chunk = ""

    for line in text.split('\n'):
        if len(line) > limit:
            words = line.split(' ')
            for word in words:
                if len(current_chunk) + len(word) + 1 > limit:
                    chunks.append(current_chunk.strip())
                    current_chunk = word + " "
                else:
                    current_chunk += word + " "
            current_chunk += "\n"
        elif len(current_chunk) + len(line) + 1 > limit:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    for chunk in chunks:
        yield chunk
import pytest
from utils.split_message import split_message

@pytest.mark.asyncio
async def test_split_message_short():
    text = "Короткий текст"
    chunks = [chunk async for chunk in split_message(text, 4000)]
    assert chunks == ["Короткий текст"]

@pytest.mark.asyncio
async def test_split_message_long_words():
    text = "A" * 5000
    chunks = [chunk async for chunk in split_message(text, 4000)]
    assert len(chunks) == 2
    assert len(chunks[0]) <= 4000
    assert len(chunks[1]) <= 4000

@pytest.mark.asyncio
async def test_split_message_multiple_lines():
    text = "Первая строка\nВторая строка\nТретья строка"
    chunks = [chunk async for chunk in split_message(text, 20)]
    assert len(chunks) == 3
    assert chunks[0] == "Первая строка"
    assert chunks[1] == "Вторая строка"
    assert chunks[2] == "Третья строка"
import asyncio
import uuid

from core.database import engine
from sqlmodel import Session, select

from api.routes.chat import ChatMessage


async def test_persistence():
    conv_id = str(uuid.uuid4())
    msg_content = f"Test message for persistence audit: {conv_id}"

    # 1. Insert message
    async with Session(engine) as session:
        msg = ChatMessage(conversation_id=conv_id, role="user", content=msg_content, graph_id=None)
        session.add(msg)
        await session.commit()
        print(f"Inserted message with conv_id: {conv_id}")

    # 2. Query message
    async with Session(engine) as session:
        stmt = select(ChatMessage).where(ChatMessage.conversation_id == conv_id)
        result = await session.exec(stmt)
        found = result.first()
        if found and found.content == msg_content:
            print("SUCCESS: Message persisted and retrieved correctly.")
        else:
            print("FAILURE: Message not found or content mismatch.")


if __name__ == "__main__":
    asyncio.run(test_persistence())

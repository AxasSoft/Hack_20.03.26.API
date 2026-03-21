import asyncio
import json

from sqlalchemy.orm import sessionmaker, Session

from app.crud import CrudChat
from app.services.free4gpt.gpt_manager import gpt_manager
from app.api.deps import get_redis, get_engine
from app.schemas import SendingMessage
from app.getters import get_message_with_parent


redis_client = get_redis()

db: Session = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=get_engine()
)()

async def run_worker():
    pubsub = redis_client.pubsub()
    pubsub.subscribe("chat-neuro")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        data = json.loads(message["data"])

        user_id = data["user_id"]
        question = data["message_text"]
        chat_id = data["chat"]

        try:
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(
                None,
                gpt_manager.get_answer,
                question
            )
            crud_chat = CrudChat(s3_client=None, s3_bucket_name=None)
            chat  = await loop.run_in_executor(
                None,
                crud_chat.get_chat_by_id,
                db,
                chat_id
            )
            sending_message = SendingMessage(
                text=answer,
                attachments=[0]
            )
            message = await loop.run_in_executor(
                None,
                crud_chat.send_message,
                db,
                None,
                chat,
                sending_message
            )

            response = {
                'chat': chat_id,
                'message': get_message_with_parent(db=db, message=message, user=None).dict(),
                'error': None,
            }

            redis_client.publish(
                f"chat-{user_id}",
                json.dumps(response, ensure_ascii=False)
            )

        except Exception as e:
            db.rollback()
            redis_client.publish(
                f"chat-{user_id}",
                json.dumps({
                    'chat': chat_id,
                    "message": None,
                    'error': 'Сервис временно недоступен',
                })
            )
            print(e)
        finally:
            db.commit()
            db.close()

if __name__ == "__main__":
    asyncio.run(run_worker())
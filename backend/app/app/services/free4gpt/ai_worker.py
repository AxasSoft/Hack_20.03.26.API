import asyncio
import json
import redis.asyncio as redis

from app.services.free4gpt.gpt_manager import gpt_manager

def get_redis():
    redis_instance = redis.StrictRedis(
        host='85.92.111.28',
        port=6379,
        password=r'Ah%\no4{WKi\m(',
        username='default'
    )
    return redis_instance

redis_client = get_redis()


async def run_worker():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("chat-neuro")

    async for message in pubsub.listen():
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

            response = {
                'chat_id': chat_id,
                "answer": answer,
                'source': "ai",
                'error': None,
            }

            await redis_client.publish(
                f"chat-{user_id}",
                json.dumps(response, ensure_ascii=False)
            )

        except Exception as e:
            await redis_client.publish(
                f"chat-{user_id}",
                json.dumps({
                    'chat_id': chat_id,
                    "answer": None,
                    'source': "ai",
                    'error': str(e),
                })
            )

if __name__ == "__main__":
    asyncio.run(run_worker())
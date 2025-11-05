import os
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
from openai import AsyncOpenAI, APIStatusError, APITimeoutError, RateLimitError
import log as Log  # <-- your custom rotating logger

# Configure retry logging (use logger, not method)
before_sleep_logger = before_sleep_log(Log.log, logging.WARNING)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((APIStatusError, APITimeoutError, RateLimitError)),
    before_sleep=before_sleep_logger
)
async def call_openai_chat(client: AsyncOpenAI, **kwargs):
    return await client.chat.completions.create(**kwargs)

def getOpenai() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

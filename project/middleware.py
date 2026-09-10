import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info("Request received : %s %s", request.method, request.url.path)
    response = await call_next(request)
    process_time = time.time() - start_time
    if response.status_code >= 400:
        logger.error("Response encountered an error: %s %s | status=%s | process_time=%.3f", request.method, request.url.path, response.status_code, process_time)
    else:
        logger.info("Response sent: %s %s | status=%s | process_time=%.3f", request.method, request.url.path, response.status_code, process_time)
    return response
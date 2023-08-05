import os
import sys
import logging
from typing import Union
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from loguru import logger

LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG"))


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


app = FastAPI()


@app.get("/")
def read_root():
    app.logger.info("Hello World")
    app.logger.error("Error World")
    app.logger.warning("Warning World")
    app.logger.debug("Debug World")
    app.logger.critical("Critical World")

    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/error-test")
def error_test():
    raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/error-test-forbidden")
def error_test_forbidden():
    raise HTTPException(status_code=403, detail="Forbidden")


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, _exc):
    app.logger.error(f"Endpoint `{request.url}` Not Found.")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": "Not Found"},
    )


@app.on_event("startup")
async def startup_event():
    intercept_handler = InterceptHandler()
    logging.root.setLevel(LOG_LEVEL)

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name)
            logging.getLogger(name).handlers = [intercept_handler]

    logging.getLogger("uvicorn").handlers.clear()
    logger.configure(handlers=[{"sink": sys.stdout}])
    app.logger = logger

import logging
import uuid
import asyncio
from aiohttp.web import Application, Request, Response, FileResponse, StreamResponse, RouteTableDef, static, get

from .camera import Camera
from .config import Configuration
from asyncio.exceptions import CancelledError
from pathlib import Path



logger = logging.getLogger(__name__)

routes = RouteTableDef()

@routes.get("/snapshot")
async def snapshot(request: Request) -> Response:
    with request.app['camera'] as camera:
        try:
            frame = await camera.get_frame()
            response = StreamResponse(
                headers={
                    'Content-Type': 'image/jpeg',
                    f"Content-Length: {len(frame.data)}"
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            await response.prepare(request),
            await response.write(frame.data),
            await response.write_eof()
        except CancelledError:
            pass

@routes.get("/stream")
async def stream(request: Request) -> Response:
    id = uuid.uuid1()
    with request.app['camera'] as camera:
        logger.info(f"{id} Start stream  remote={request.remote}  n_streams={camera.n_streams}")

        response = StreamResponse(
            headers={
                'Content-Type': 'multipart/x-mixed-replace; boundary=\"frame\"',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        await response.prepare(request)

        try:
            last_count = None
            while True:
                frame = await camera.get_frame(last_count)
                if (last_count is not None) and (frame.count-last_count > 1):
                    logger.info(f"{id} Dropped {frame.count-last_count-1} frame(s)")
                await response.write(
                    bytes(f"--frame\r\n"
                            "Content-Type: image/jpeg\r\n"
                            f"Content-Length: {len(frame.data)}\r\n"
                            "\r\n", 'utf-8')),
                await response.write(frame.data),
                await response.write(b"\r\n")
                last_count = frame.count
        except ConnectionResetError:
            logger.info(f"{id} Stream closed")
            return
        except CancelledError:
            logger.info(f"{id} Stream cancelled")
            return
        except EOFError:
            logger.info(f"{id} Pipeline stopped")
            await response.write(b'--frame--\r\n')
        except:
            logger.error(f"{id} Stream failed", exc_info=True)
            await response.write(b'--frame--\r\n')
        await response.write_eof()


@routes.get("/")
async def default_index(request: Request) -> Response:
    file = Path(__file__).parent.parent / "www" / "index.html"
    return FileResponse(file)


async def app_on_startup(app: Application):
    logger.info("Startup")
    camera = Camera(app["config"])
    app["camera"] = camera

async def app_on_cleanup(app: Application):
    logger.info("Cleanup")
    camera: Camera = app["camera"]
    if camera:
        await camera.shutdown()
    app["camera"] = None


async def app_on_shutdown(app: Application):
    logger.info("Shutdown")
    camera: Camera = app["camera"]
    if camera:
        await camera.shutdown()


def create_application(config: Configuration) -> Application:
    app = Application()
    app["config"] = config

    www_dir = Path(__file__).parent.parent / "www"
    app.add_routes(routes)
    app.add_routes([static("/", str(www_dir))])

    app.on_shutdown.append(app_on_shutdown)
    app.on_startup.append(app_on_startup)
    app.on_cleanup.append(app_on_cleanup)

    return app

import logging
from aiohttp.web import Application, Request, Response, FileResponse, StreamResponse, RouteTableDef, static, get

from .camera import Camera
from asyncio.exceptions import CancelledError
from pathlib import Path



logger = logging.getLogger(__name__)

routes = RouteTableDef()

@routes.get("/snapshot")
async def snapshot(request: Request) -> Response:
    with request.app['camera'] as camera:
        try:
            frame = await camera.get_frame()
            with frame as data:
                response = StreamResponse(
                    headers={
                        'Content-Type': 'image/jpeg',
                       f"Content-Length: {len(data)}"
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                )
                await response.prepare(request)
                await response.write(data)
                await response.write_eof()
        except CancelledError:
            pass

@routes.get("/stream")
async def stream(request: Request) -> Response:
    with request.app['camera'] as camera:
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
                frame = await camera.get_frame()
                if (last_count is not None) and (frame.count-last_count > 1):
                    logger.info(f"Dropped {frame.count-last_count-1} frames")
                with frame as data:
                    await response.write(
                        bytes(f"--frame\r\n"
                                "Content-Type: image/jpeg\r\n"
                               f"Content-Length: {len(data)}\r\n"
                                "\r\n", 'utf-8')
                    )
                    await response.write(data)
                    await response.write(b"\r\n")
                last_count = frame.count
        except ConnectionResetError:
            logger.info("Stream closed")
            return
        except CancelledError:
            logger.info("Stream cancelled")
            return
        except:
            logger.error("Stream failed", exc_info=True)
            await response.write(b'--frame--\r\n')
        await response.write_eof()


@routes.get("/")
async def default_index(request: Request) -> Response:
    file = Path(__file__).parent.parent / "www" / "index.html"
    return FileResponse(file)


async def app_on_startup(app: Application):
    logger.info("Startup")
    camera = Camera()
    app["camera"] = camera

async def app_on_cleanup(app: Application):
    logger.info("Cleanup")
    camera: Camera = app["camera"]
    if camera:
        camera.shutdown()
    app["camera"] = None

def create_application() -> Application:
    app = Application()

    www_dir = Path(__file__).parent.parent / "www"
    app.add_routes(routes)
    app.add_routes([static("/", str(www_dir))])

    app.on_startup.append(app_on_startup)
    app.on_cleanup.append(app_on_cleanup)

    return app

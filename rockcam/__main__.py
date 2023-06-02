import logging
import setproctitle

from argparse import ArgumentParser
from aiohttp import web
from rockcam import create_application

def main():
    parser = ArgumentParser()
    parser.add_argument("--host", help="Web server bind address", type=str, default="0.0.0.0")
    parser.add_argument("--port", help="Web server port", type=int, default=5000)
    args = parser.parse_args()

    #FORMAT = '[%(asctime)s.%(msecs)03d] [%(threadName)-10s] [%(levelname)s] %(name)s: %(message)s'
    FORMAT = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, datefmt='%H:%M:%S', level=logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logger = logging.getLogger('Main')

    setproctitle.setproctitle(f"Rock Cam: {args.host}:{args.port}")
    web.run_app(create_application(), host=args.host, port=args.port)


if __name__ == '__main__':
    main()

import logging
import setproctitle

from argparse import ArgumentParser
from pathlib import Path
from aiohttp import web
from rockcam import create_application
from rockcam import Configuration

def main():
    parser = ArgumentParser()
    parser.add_argument("--host", help="Web server bind address", type=str, default="0.0.0.0")
    parser.add_argument("--port", help="Web server port", type=int, default=5000)
    parser.add_argument("--config", help="Configuration file", type=Path, default=None)
    args = parser.parse_args()

    #FORMAT = '[%(asctime)s.%(msecs)03d] [%(threadName)-10s] [%(levelname)s] %(name)s: %(message)s'
    FORMAT = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, datefmt='%H:%M:%S', level=logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logger = logging.getLogger('Main')

    config = Configuration()

    if args.config:
        config.load(args.config)

    setproctitle.setproctitle(f"Rock Cam: {args.host}:{args.port}")
    web.run_app(create_application(config), host=args.host, port=args.port)


if __name__ == '__main__':
    main()

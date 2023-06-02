import logging
import setproctitle

from argparse import ArgumentParser
from aiohttp import web
from rockcam import create_application
from rockcam import Configuration

def main():
    parser = ArgumentParser()
    parser.add_argument("--host", help="Web server bind address", type=str, default="0.0.0.0")
    parser.add_argument("--port", help="Web server port", type=int, default=5000)
    parser.add_argument("--fake", help="Use fake camera", action='store_true', default=False)
    args = parser.parse_args()

    #FORMAT = '[%(asctime)s.%(msecs)03d] [%(threadName)-10s] [%(levelname)s] %(name)s: %(message)s'
    FORMAT = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(format=FORMAT, datefmt='%H:%M:%S', level=logging.INFO)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logger = logging.getLogger('Main')

    config = Configuration()
    config.fake_source = args.fake

    setproctitle.setproctitle(f"Rock Cam: {args.host}:{args.port}")
    web.run_app(create_application(config), host=args.host, port=args.port)


if __name__ == '__main__':
    main()

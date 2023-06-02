import logging
import asyncio
import gi
import sys
import time
from dataclasses import dataclass

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

from .config import Configuration


logger = logging.getLogger(__name__)

Gst.init(sys.argv)


@dataclass
class CameraFrame:
    count: int
    sample: Gst.Sample
    buffer: Gst.Buffer
    map_info: Gst.MapInfo = None

    def __enter__(self) -> memoryview:
        if self.map_info is not None:
            raise RuntimeError("Camera frame is already mapped")
        self.map_info = self.buffer.map(Gst.MapFlags.READ)
        return self.map_info.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.map_info:
            self.buffer.unmap(self.map_info)
            self.map_info = None
        else:
            raise RuntimeError("Camera frame is already mapped")


class Camera:
    def __init__(self, config: Configuration) -> None:
        self._loop = asyncio.get_event_loop()
        self._sample = None
        self._sample_count = 0
        self._sample_cond = asyncio.Condition()
        self._n_streams = 0
        self._idle_handler = None
        self._started = False
        
        self._config = config

        self._pipeline = self._create_pipeline()
        self._bus = self._pipeline.get_bus()
        self._loop.add_reader(self._bus.get_pollfd().fd, self._on_bus)

        ret = self._pipeline.set_state(Gst.State.READY)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to ready pipeline")


    @property
    def n_streams(self) -> int:
        return self._n_streams

    async def get_frame(self) -> CameraFrame:
        async with self._sample_cond:
            await self._sample_cond.wait()
            return CameraFrame(
                count=self._sample_count, 
                sample=self._sample, 
                buffer=self._sample.get_buffer()
            )


    def start(self):
        if not self._started:
            logger.info("Starting camera")
            ret = self._pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")
            self._started = True
        

    def stop(self):
        if self._started:
            logger.info("Stopping camera")
            ret = self._pipeline.set_state(Gst.State.READY)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to pause pipeline")
            self._started = False

    def shutdown(self):
        ret = self._pipeline.set_state(Gst.State.NULL)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to shutdown pipeline")



    def __enter__(self):
        self._n_streams += 1
        if self._idle_handler:
            self._idle_handler.cancel()
            self._idle_handler = None
        if self._n_streams == 1:
            self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._n_streams -= 1
        if self._n_streams == 0:
            self._idle_handler = self._loop.call_later(self._config.idle_timeout, self._on_idle)



    def _on_idle(self):
        logger.info("Camera is idle")
        self.stop()
        self._idle_handler = None


    def _on_message(self, message: Gst.Message):
        if message.src == self._pipeline:
            if message.type == Gst.MessageType.STATE_CHANGED:
                old_state, new_state, pending_state = message.parse_state_changed()
                logger.info(f"Camera state changed {old_state.value_nick} -> {new_state.value_nick}")
                return
            elif message.type == Gst.MessageType.ASYNC_DONE:
                return
            elif message.type == Gst.MessageType.STREAM_START:
                return
            elif message.type == Gst.MessageType.NEW_CLOCK:
                return
            logger.info(f"  Msg: {message}")
            logger.info(f" Type: {message.type}")


    async def _on_sample(self, sample: Gst.Sample):
        async with self._sample_cond:
            self._sample = sample
            self._sample_count += 1
            self._sample_cond.notify_all()


    def _on_bus(self):
        message = self._bus.poll(Gst.MessageType.ANY, 0)
        if message:
            self._on_message(message)


    def _on_sample_thread(self, sink: Gst.Element, data) -> Gst.FlowReturn:
        sample = sink.emit("pull-sample")
        if isinstance(sample, Gst.Sample):
            asyncio.run_coroutine_threadsafe(self._on_sample(sample), self._loop)
            return Gst.FlowReturn.OK
        return Gst.FlowReturn.ERROR        


    def _create_pipeline(self) -> Gst.Pipeline:
        source_format = f"video/x-raw,format=NV12,width={self._config.frame_width},height={self._config.frame_height}"
        source = None
        encoder = None
        rate = f"videorate drop-only=true ! image/jpeg,framerate={self._config.frame_rate}/1"

        if self._config.fake_source:
            source = "videotestsrc is-live=true ! timeoverlay time-mode=buffer-time"
        else:
            source = "v4l2src name=src device=/dev/video0 io-mode=4"

        if Gst.ElementFactory.find("mppjpegenc"):
            logger.info("Using hardware 'mppjpegenc' encoder")
            encoder = f"mppjpegenc rotation={self._config.frame_rotate}"
        elif Gst.ElementFactory.find("jpegenc"):
            logger.info("Using software jpeg encoder")
            encoder = "jpegenc"
        else:
            raise RuntimeError("Error finding suitable jpeg encoder")

        pipeline = Gst.parse_launch(f"{source} ! {source_format} ! {encoder} ! {rate} !  queue max-size-buffers=2 ! appsink name=sink emit-signals=True sync=True")

        sink = pipeline.get_by_name("sink")
        sink.connect("new-sample", self._on_sample_thread, None)

        return pipeline


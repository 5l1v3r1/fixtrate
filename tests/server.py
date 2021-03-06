import asyncio
import logging
from fixtrate.engine import FixEngine
logger = logging.getLogger(__name__)


class MockFixServer(object):

    def __init__(self, config):
        self.config = config
        self.engine = self._make_engine()
        self.client_sessions = []
        self.tasks = []

    def _make_engine(self):
        engine = FixEngine()
        engine.store_interface = self.config['store']
        return engine

    async def stream_client_session(self, session):
        try:
            async for msg in session:
                pass
        except asyncio.CancelledError:
            pass
        except ConnectionError as error:
            logger.error(error)
        except Exception as error:
            logger.exception(error)

        logger.info(
            'Client sesssion %s closed' % session.id)

    async def listen(self):
        host, port = self.config['host'], self.config['port']
        session_confs = self.config['client_session_confs']
        async with self.engine.bind(host, port, session_confs) as bind:
            async for session in bind:
                self.client_sessions.append(session)
                coro = self.stream_client_session(session)
                task = asyncio.get_event_loop().create_task(coro)
                self.tasks.append(task)

    async def close(self):
        await self.engine.close()
        self.client_sessions.clear()

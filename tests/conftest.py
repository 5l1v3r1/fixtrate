import asyncio
from datetime import datetime
import uuid

import aioredis
import pytest
from fixtrate import constants as fix
from tests.server import MockFixServer
from fixtrate.store import MemoryStoreInterface, RedisStoreInterface
from fixtrate.engine import FixEngine
from fixtrate.message import FixMessage


@pytest.fixture(params=['inmemory', 'redis'])
async def store_interface(request):
    redis_url = 'redis://localhost:6379'
    prefix = 'fix-test'
    if request.param == 'redis':
        store_interface = RedisStoreInterface(redis_url, prefix)
    else:
        store_interface = MemoryStoreInterface()
    yield store_interface
    if request.param == 'redis':
        client = await aioredis.create_redis(redis_url)
        keys = await client.keys('%s*' % prefix)
        if keys:
            await client.delete(*keys)
        client.close()


@pytest.fixture
def client_config(request):
    overrides = getattr(request, 'param', {})
    config = {
        'begin_string': fix.FixVersion.FIX42,
        'sender_comp_id': 'TESTCLIENT',
        'target_comp_id': 'TESTSERVER',
        'heartbeat_interval': 30,
        **overrides
    }
    return config


@pytest.fixture
def server_config(request, store_interface):
    overrides = getattr(request, 'param', {})
    return {
        'host': '127.0.0.1',
        'port': 8686,
        'client_session_confs': [{
            'begin_string': fix.FixVersion.FIX42,
            'sender_comp_id': 'TESTSERVER',
            'target_comp_id': 'TESTCLIENT',
            'heartbeat_interval': 30,
        }],
        'store': store_interface,
        **overrides
    }


@pytest.fixture
async def test_server(request, server_config):
    server = MockFixServer(server_config)
    asyncio.get_event_loop().create_task(server.listen())
    yield server
    await server.close()


@pytest.fixture
async def engine(store_interface):
    engine = FixEngine()
    engine.store_interface = store_interface
    yield engine
    await engine.close()


@pytest.fixture
def order_request():
    order = FixMessage()
    order.append_pair(fix.FixTag.MsgType, fix.FixMsgType.NEW_ORDER_SINGLE)
    order.append_pair(fix.FixTag.ClOrdID, str(uuid.uuid4()))
    order.append_pair(fix.FixTag.OrdType, fix.OrdType.LIMIT)
    order.append_pair(fix.FixTag.Symbol, 'UGAZ')
    order.append_pair(fix.FixTag.Side, fix.Side.BUY)
    order.append_pair(fix.FixTag.OrderQty, 100)
    order.append_pair(fix.FixTag.Price, 25.0)
    order.append_utc_timestamp(fix.FixTag.TransactTime, datetime.utcnow())
    return order


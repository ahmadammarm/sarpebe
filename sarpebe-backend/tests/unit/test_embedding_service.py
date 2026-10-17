import math
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.core.services import embedding_service as module
from app.core.services.embedding_service import embedding_service, l2_normalize

async_test = pytest.mark.asyncio(loop_scope="session")

USER_ID = uuid.uuid4()


def fake_client(*vectors_per_call):
    """A client whose embed_content returns the given vectors, one list of vectors per call."""
    client = MagicMock()
    responses = [SimpleNamespace(embeddings=[SimpleNamespace(values=v) for v in vectors]) for vectors in vectors_per_call]
    client.aio.models.embed_content = AsyncMock(side_effect=responses)
    return client


def test_l2_normalize_gives_unit_length():
    vector = l2_normalize([3.0, 4.0])
    assert vector == pytest.approx([0.6, 0.8])
    assert math.sqrt(sum(v * v for v in vector)) == pytest.approx(1.0)


def test_l2_normalize_leaves_a_zero_vector_alone():
    assert l2_normalize([0.0, 0.0]) == [0.0, 0.0]


@async_test
async def test_embeddings_are_normalized_and_cost_is_logged(mocker):
    mocker.patch.object(module, "client", fake_client([[3.0, 4.0], [0.0, 2.0]]))
    log = mocker.patch.object(module, "log_cost", new_callable=AsyncMock)

    result = await embedding_service.embed_texts(["satu", "dua"], USER_ID)

    assert result == [pytest.approx([0.6, 0.8]), pytest.approx([0.0, 1.0])]
    log.assert_awaited_once()
    assert log.await_args.kwargs["operation_type"] == "embedding"


@async_test
async def test_task_type_is_only_sent_when_enabled(mocker):
    client = fake_client([[1.0, 0.0]], [[1.0, 0.0]], [[1.0, 0.0]])
    mocker.patch.object(module, "client", client)
    mocker.patch.object(module, "log_cost", new_callable=AsyncMock)

    mocker.patch.object(settings, "embedding_use_task_types", False)
    await embedding_service.embed_texts(["x"], USER_ID, purpose="query")
    assert client.aio.models.embed_content.await_args.kwargs["config"].task_type is None

    mocker.patch.object(settings, "embedding_use_task_types", True)
    await embedding_service.embed_texts(["x"], USER_ID, purpose="query")
    assert client.aio.models.embed_content.await_args.kwargs["config"].task_type == "RETRIEVAL_QUERY"
    await embedding_service.embed_texts(["x"], USER_ID, purpose="document")
    assert client.aio.models.embed_content.await_args.kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"


@async_test
async def test_falls_back_to_one_call_per_text_when_the_batch_comes_back_short(mocker):
    # First call returns a single (aggregated) vector for two inputs; then one call per text.
    client = fake_client([[1.0, 0.0]], [[0.0, 1.0]], [[1.0, 1.0]])
    mocker.patch.object(module, "client", client)
    mocker.patch.object(module, "log_cost", new_callable=AsyncMock)

    result = await embedding_service.embed_texts(["a", "b"], USER_ID)

    assert len(result) == 2
    assert client.aio.models.embed_content.await_count == 3


@async_test
async def test_empty_input_makes_no_call(mocker):
    client = fake_client()
    mocker.patch.object(module, "client", client)
    assert await embedding_service.embed_texts([], USER_ID) == []
    client.aio.models.embed_content.assert_not_awaited()

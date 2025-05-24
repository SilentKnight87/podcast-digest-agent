from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from src.core.connection_manager import ConnectionManager


class TestConnectionManager:
    @pytest.fixture
    def connection_manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.client = MagicMock()  # Add client attribute which is accessed in logs
        return mock_ws

    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mock_websocket):
        """Test that a WebSocket connection is properly registered with a task ID."""
        task_id = "test-task-123"

        await connection_manager.connect(mock_websocket, task_id)

        # Verify WebSocket accept was called
        mock_websocket.accept.assert_called_once()

        # Verify connection was added to active_connections
        assert task_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[task_id]

    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_task(self, connection_manager):
        """Test that multiple WebSockets can connect to the same task."""
        task_id = "test-task-456"
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws1.client = MagicMock()
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws2.client = MagicMock()

        await connection_manager.connect(mock_ws1, task_id)
        await connection_manager.connect(mock_ws2, task_id)

        assert len(connection_manager.active_connections[task_id]) == 2
        assert mock_ws1 in connection_manager.active_connections[task_id]
        assert mock_ws2 in connection_manager.active_connections[task_id]

    def test_disconnect(self, connection_manager, mock_websocket):
        """Test that a WebSocket is properly removed on disconnect."""
        task_id = "test-task-789"

        # First add the connection
        connection_manager.active_connections[task_id] = [mock_websocket]

        # Disconnect
        connection_manager.disconnect(mock_websocket, task_id)

        # Verify connection was removed
        assert task_id not in connection_manager.active_connections

    def test_disconnect_multiple_clients(self, connection_manager):
        """Test that disconnecting one client of multiple preserves others."""
        task_id = "test-task-multi"
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws1.client = MagicMock()
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws2.client = MagicMock()

        # Add multiple connections
        connection_manager.active_connections[task_id] = [mock_ws1, mock_ws2]

        # Disconnect one
        connection_manager.disconnect(mock_ws1, task_id)

        # Verify only one was removed
        assert task_id in connection_manager.active_connections
        assert mock_ws1 not in connection_manager.active_connections[task_id]
        assert mock_ws2 in connection_manager.active_connections[task_id]

    def test_disconnect_nonexistent_task(self, connection_manager, mock_websocket):
        """Test that disconnecting from a non-existent task doesn't raise errors."""
        task_id = "non-existent-task"

        # This should not raise an exception
        connection_manager.disconnect(mock_websocket, task_id)

        # Connection manager state should remain the same
        assert task_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_task(self, connection_manager):
        """Test broadcasting a message to all clients for a task."""
        task_id = "test-task-broadcast"
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws1.client = MagicMock()
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws2.client = MagicMock()

        # Add multiple connections
        connection_manager.active_connections[task_id] = [mock_ws1, mock_ws2]

        # Broadcast message
        test_message = {"status": "update", "progress": 50}
        await connection_manager.broadcast_to_task(task_id, test_message)

        # Verify both clients received the message
        mock_ws1.send_json.assert_called_once_with(test_message)
        mock_ws2.send_json.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_task(self, connection_manager):
        """Test broadcasting to a non-existent task doesn't raise errors."""
        task_id = "non-existent-task"
        test_message = {"status": "update", "progress": 50}

        # This should not raise an exception
        await connection_manager.broadcast_to_task(task_id, test_message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self, connection_manager):
        """Test that broadcasting properly cleans up disconnected clients."""
        task_id = "test-task-disconnect-during-broadcast"

        # Create mocks: one that works, one that raises an exception
        mock_ws_good = AsyncMock(spec=WebSocket)
        mock_ws_good.client = MagicMock()

        mock_ws_bad = AsyncMock(spec=WebSocket)
        mock_ws_bad.client = MagicMock()
        mock_ws_bad.send_json.side_effect = WebSocketDisconnect()

        # Add both connections
        connection_manager.active_connections[task_id] = [mock_ws_good, mock_ws_bad]

        # Broadcast message
        test_message = {"status": "update", "progress": 50}
        await connection_manager.broadcast_to_task(task_id, test_message)

        # Verify good client received the message
        mock_ws_good.send_json.assert_called_once_with(test_message)

        # Verify bad client was disconnected
        assert mock_ws_bad not in connection_manager.active_connections[task_id]
        assert mock_ws_good in connection_manager.active_connections[task_id]

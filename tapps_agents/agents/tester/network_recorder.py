"""
Network Recorder for Playwright - Record and replay API interactions.

Enables recording network requests during test runs and replaying them
for offline testing and faster test execution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NetworkRequest:
    """Recorded network request."""

    url: str
    method: str
    headers: dict[str, str]
    post_data: str | None = None
    response_status: int | None = None
    response_headers: dict[str, str] | None = None
    response_body: str | None = None
    timestamp: float = 0.0
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkRequest:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class NetworkRecording:
    """Network recording session."""

    session_id: str
    start_time: float
    end_time: float | None = None
    requests: list[NetworkRequest] = None
    base_url: str | None = None
    description: str | None = None

    def __post_init__(self):
        if self.requests is None:
            self.requests = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "requests": [req.to_dict() for req in self.requests],
            "base_url": self.base_url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkRecording:
        """Create from dictionary."""
        requests = [NetworkRequest.from_dict(req) for req in data.get("requests", [])]
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            requests=requests,
            base_url=data.get("base_url"),
            description=data.get("description"),
        )


class NetworkRecorder:
    """
    Record and replay network requests for Playwright tests.

    Records network interactions during test runs and provides
    functionality to replay them for offline testing.
    """

    def __init__(self, recording_dir: Path | None = None):
        """
        Initialize network recorder.

        Args:
            recording_dir: Directory to save recordings (default: .tapps-agents/recordings/)
        """
        if recording_dir is None:
            recording_dir = Path(".tapps-agents") / "recordings"
        self.recording_dir = Path(recording_dir)
        self.recording_dir.mkdir(parents=True, exist_ok=True)

        self.current_recording: NetworkRecording | None = None
        self.recorded_requests: list[NetworkRequest] = []

    def start_recording(
        self, session_id: str | None = None, description: str | None = None
    ) -> str:
        """
        Start recording network requests.

        Args:
            session_id: Optional session ID (auto-generated if None)
            description: Optional description of the recording session

        Returns:
            Session ID
        """
        import time

        if session_id is None:
            session_id = f"recording_{int(time.time())}"

        self.current_recording = NetworkRecording(
            session_id=session_id,
            start_time=time.time(),
            description=description,
        )
        self.recorded_requests = []

        logger.info(f"Started network recording: {session_id}")
        return session_id

    def record_request(
        self,
        url: str,
        method: str,
        headers: dict[str, str] | None = None,
        post_data: str | None = None,
        response_status: int | None = None,
        response_headers: dict[str, str] | None = None,
        response_body: str | None = None,
        request_id: str | None = None,
    ) -> NetworkRequest:
        """
        Record a network request.

        Args:
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            headers: Request headers
            post_data: POST data (if applicable)
            response_status: Response status code
            response_headers: Response headers
            response_body: Response body
            request_id: Optional request ID

        Returns:
            Recorded NetworkRequest
        """
        import time

        if self.current_recording is None:
            self.start_recording()

        request = NetworkRequest(
            url=url,
            method=method,
            headers=headers or {},
            post_data=post_data,
            response_status=response_status,
            response_headers=response_headers or {},
            response_body=response_body,
            timestamp=time.time(),
            request_id=request_id,
        )

        self.recorded_requests.append(request)
        if self.current_recording:
            self.current_recording.requests.append(request)

        logger.debug(f"Recorded {method} {url} -> {response_status}")
        return request

    def stop_recording(self) -> NetworkRecording | None:
        """
        Stop recording and save to file.

        Returns:
            NetworkRecording or None if no recording was active
        """
        import time

        if self.current_recording is None:
            logger.warning("No active recording to stop")
            return None

        self.current_recording.end_time = time.time()
        self.current_recording.requests = self.recorded_requests.copy()

        # Save to file
        filename = self.recording_dir / f"{self.current_recording.session_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.current_recording.to_dict(), f, indent=2)

        logger.info(
            f"Stopped recording: {self.current_recording.session_id} "
            f"({len(self.recorded_requests)} requests saved to {filename})"
        )

        recording = self.current_recording
        self.current_recording = None
        self.recorded_requests = []

        return recording

    def load_recording(self, session_id: str) -> NetworkRecording | None:
        """
        Load a saved recording.

        Args:
            session_id: Session ID of the recording

        Returns:
            NetworkRecording or None if not found
        """
        filename = self.recording_dir / f"{session_id}.json"
        if not filename.exists():
            logger.error(f"Recording not found: {filename}")
            return None

        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)
            return NetworkRecording.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load recording: {e}")
            return None

    def list_recordings(self) -> list[dict[str, Any]]:
        """
        List all available recordings.

        Returns:
            List of recording metadata dictionaries
        """
        recordings = []
        for filename in self.recording_dir.glob("*.json"):
            try:
                with open(filename, encoding="utf-8") as f:
                    data = json.load(f)
                recordings.append(
                    {
                        "session_id": data.get("session_id"),
                        "start_time": data.get("start_time"),
                        "request_count": len(data.get("requests", [])),
                        "description": data.get("description"),
                        "filename": str(filename),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read recording {filename}: {e}")

        return sorted(recordings, key=lambda x: x.get("start_time", 0), reverse=True)

    def create_replay_config(
        self, recording: NetworkRecording, output_path: Path | None = None
    ) -> str:
        """
        Create Playwright route configuration for replaying requests.

        Args:
            recording: NetworkRecording to replay
            output_path: Optional path to save replay config

        Returns:
            JavaScript code for Playwright route configuration
        """
        routes = []
        for req in recording.requests:
            if req.response_status and req.response_body:
                route_code = f"""
page.route('{req.url}', async route => {{
    await route.fulfill({{
        status: {req.response_status},
        headers: {json.dumps(req.response_headers or {})},
        body: {json.dumps(req.response_body)}
    }});
}});
"""
                routes.append(route_code)

        replay_code = "\n".join(routes)

        if output_path:
            output_path.write_text(replay_code, encoding="utf-8")
            logger.info(f"Replay config saved to: {output_path}")

        return replay_code

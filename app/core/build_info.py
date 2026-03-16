# app/core/build_info.py

from datetime import datetime, timezone
import os


class BuildInfo:

    # Static build version (update manually or via CI)
    BUILD_VERSION = "2026-03-16"

    # Graph version (optional but useful)
    GRAPH_VERSION = "v3"

    # Container start time
    START_TIME = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    @classmethod
    def get_info(cls) -> str:

        space_name = os.getenv("SPACE_ID", "local")

        return (
            f"**Build:** {cls.BUILD_VERSION}  \n"
            f"**Graph:** {cls.GRAPH_VERSION}  \n"
            f"**Space:** {space_name}  \n"
            f"**Container start:** {cls.START_TIME}"
        )

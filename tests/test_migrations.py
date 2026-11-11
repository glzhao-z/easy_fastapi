"""迁移升降级测试，远程地址仅使用显式提供的测试库。"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("target", ["sqlite", "TEST_POSTGRES_URL", "TEST_MYSQL_URL"])
def test_migration_round_trip(target: str, tmp_path: Path) -> None:
    if target == "sqlite":
        url = "sqlite+aiosqlite:///" + (tmp_path / "migration.db").as_posix()
    else:
        url = os.environ.get(target, "")
        if not url:
            pytest.skip(target + " 未设置")

    environment = os.environ.copy()
    environment["EASY_FASTAPI_DATABASE_ENABLED"] = "false"
    environment["EASY_FASTAPI_REDIS_ENABLED"] = "false"
    environment["EASY_FASTAPI_DATABASE_URL"] = url
    for arguments in (
        ["upgrade", "head"],
        ["check"],
        ["downgrade", "base"],
        ["upgrade", "head"],
        ["current"],
    ):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    assert "0001" in result.stdout

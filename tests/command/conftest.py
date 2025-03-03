from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cleo.io.null_io import NullIO
from cleo.testers.command_tester import CommandTester
from poetry.installation import Installer
from poetry.utils.env import MockEnv

from tests.helpers import PoetryTestApplication
from tests.helpers import TestExecutor


if TYPE_CHECKING:
    from poetry.installation.executor import Executor
    from poetry.poetry import Poetry
    from poetry.utils.env import Env

    from tests.types import CommandTesterFactory


@pytest.fixture
def app(poetry: Poetry) -> PoetryTestApplication:
    app_ = PoetryTestApplication(poetry)

    return app_


@pytest.fixture
def env(tmp_dir: str) -> MockEnv:
    path = Path(tmp_dir) / ".venv"
    path.mkdir(parents=True)
    return MockEnv(path=path, is_venv=True)


@pytest.fixture
def command_tester_factory(
    app: PoetryTestApplication, env: MockEnv
) -> CommandTesterFactory:
    def _tester(
        command: str,
        poetry: Poetry | None = None,
        installer: Installer | None = None,
        executor: Executor | None = None,
        environment: Env | None = None,
    ) -> CommandTester:
        app._load_plugins(NullIO())

        command = app.find(command)
        tester = CommandTester(command)

        # Setting the formatter from the application
        # TODO: Find a better way to do this in Cleo
        app_io = app.create_io()
        formatter = app_io.output.formatter
        tester.io.output.set_formatter(formatter)
        tester.io.error_output.set_formatter(formatter)

        if poetry:
            app._poetry = poetry

        poetry = app.poetry
        command._pool = poetry.pool

        if hasattr(command, "set_env"):
            command.set_env(environment or env)

        if hasattr(command, "set_installer"):
            installer = installer or Installer(
                tester.io,
                env,
                poetry.package,
                poetry.locker,
                poetry.pool,
                poetry.config,
                executor=executor
                or TestExecutor(env, poetry.pool, poetry.config, tester.io),
            )
            installer.use_executor(True)
            command.set_installer(installer)

        return tester

    return _tester


@pytest.fixture
def do_lock(command_tester_factory: CommandTesterFactory, poetry: Poetry) -> None:
    command_tester_factory("lock").execute()
    assert poetry.locker.lock.exists()

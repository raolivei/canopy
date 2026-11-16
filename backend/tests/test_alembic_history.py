"""The Alembic revision graph must stay linear and loadable."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _script_directory() -> ScriptDirectory:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(config)


def test_single_head() -> None:
    assert len(_script_directory().get_heads()) == 1


def test_revision_ids_are_unique_and_chain_to_base() -> None:
    script = _script_directory()
    revisions = list(script.walk_revisions("base", "heads"))
    ids = [rev.revision for rev in revisions]

    assert len(ids) == len(set(ids)), "duplicate revision ids"
    assert sum(1 for rev in revisions if rev.down_revision is None) == 1, "exactly one base revision"
    assert all(isinstance(rev.down_revision, (str, type(None))) for rev in revisions), "no merge points"

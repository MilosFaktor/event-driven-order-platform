import contextlib
import io

from scripts.reset_json_data import storage_reset


def silent_storage_reset():  # for hidden output
    with contextlib.redirect_stdout(io.StringIO()):
        storage_reset()

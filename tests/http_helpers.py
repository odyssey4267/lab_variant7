import threading
from contextlib import contextmanager

from matrix_lab.server import make_server


@contextmanager
def running_server(delay=None):
    """Запустить сервис на свободном порту в отдельном потоке и вернуть его URL."""
    kwargs = {} if delay is None else {"delay": delay}
    server = make_server("127.0.0.1", 0, **kwargs)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                              daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

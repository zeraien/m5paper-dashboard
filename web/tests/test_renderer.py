import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import pytest
from PIL import Image

from einkdisplay.renderer import RenderError, render_png

PAGE = b"""<!DOCTYPE html>
<html><body style="margin:0">
<div style="height:50%;background:linear-gradient(to right,#000,#fff)"></div>
<p style="font-size:48px">Render test</p>
</body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = 500 if self.path == '/fail' else 200
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(PAGE)))
        self.end_headers()
        self.wfile.write(PAGE)

    def log_message(self, *args):
        pass


@pytest.fixture(scope='module')
def server_url():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()


def test_renders_grayscale_png_of_requested_size(server_url):
    png = render_png(server_url + '/', width=300, height=200)

    image = Image.open(BytesIO(png))
    assert image.format == 'PNG'
    assert image.size == (300, 200)
    assert image.mode == 'L'
    assert len(image.getcolors()) <= 16


def test_error_status_raises(server_url):
    with pytest.raises(RenderError):
        render_png(server_url + '/fail', width=300, height=200)


def test_unreachable_url_raises():
    with pytest.raises(RenderError):
        render_png('http://127.0.0.1:1/', width=300, height=200)

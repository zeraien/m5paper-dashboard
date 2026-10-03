from io import BytesIO

from PIL import Image, ImageEnhance
from playwright.sync_api import Error as PlaywrightError, sync_playwright

GRAY_LEVELS = 16
CONTRAST = 2.0
TIMEOUT_MS = 60_000


class RenderError(Exception):
    pass


def render_png(url: str, width: int, height: int) -> bytes:
    """
    Screenshot url in headless Chromium and convert it for the e-ink display.
    :raises RenderError: page did not load or did not return a 2xx status
    """
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={'width': width, 'height': height})
                response = page.goto(url, wait_until='networkidle', timeout=TIMEOUT_MS)
                if response is None or not response.ok:
                    status = response.status if response else 'no response'
                    raise RenderError(f"{url} returned {status}")
                page.evaluate("document.fonts.ready")
                screenshot = page.screenshot(type='png')
            finally:
                browser.close()
    except PlaywrightError as e:
        raise RenderError(f"Rendering {url} failed: {e}") from e

    return to_eink_png(screenshot)


def to_eink_png(png: bytes) -> bytes:
    """
    :return: 8-bit grayscale PNG with contrast applied, reduced to GRAY_LEVELS evenly spaced shades
    """
    image = Image.open(BytesIO(png)).convert('L')
    image = ImageEnhance.Contrast(image).enhance(CONTRAST)
    step = 255 / (GRAY_LEVELS - 1)
    image = image.point(lambda v: round(round(v / step) * step))

    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()

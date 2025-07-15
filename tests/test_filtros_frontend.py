import os
import pytest
from playwright.sync_api import sync_playwright, expect

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000/index.html")
HEADLESS_ENV = os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")

# (selector, checkbox_value)
FILTROS = [
    ("#seguridad-container input[value='caseta']", "caseta"),
    ("#seguridad-container input[value='camaras']", "camaras"),
    ("#seguridad-container input[value='24h']", "24h"),
    ("#seguridad-container input[value='acceso_controlado']", "acceso_controlado"),
    ("#niveles-container input[value='un_nivel']", "un_nivel"),
    ("#niveles-container input[value='dos_niveles']", "dos_niveles"),
    ("#niveles-container input[value='tres_niveles']", "tres_niveles"),
    ("#recamara-pb-container input[value='si']", "rec_pb_si"),
    ("#tipo-container input[value='local']", "local"),
    ("#tipo-container input[value='oficina']", "oficina"),
]


@pytest.mark.skipif(
    os.getenv("CI") != "true" and "localhost" in FRONTEND_URL,
    reason="Para entorno local, arranca `python -m http.server` en frontend primero o define FRONTEND_URL"
)
@pytest.mark.parametrize("selector, nombre", FILTROS)
def test_filtros_renderizan_tarjetas(selector: str, nombre: str):
    """Valida que al activar el filtro aparezca ≥1 tarjeta y la consola esté limpia."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_ENV)
        page = browser.new_page()
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        page.goto(FRONTEND_URL, timeout=60000)
        page.wait_for_selector(".property-card, #properties-container", timeout=60000)

        # Click checkbox
        page.locator(selector).scroll_into_view_if_needed()
        page.check(selector)

        # Esperar recarga (fetch) – el front inyecta #loading-overlay durante fetch
        page.wait_for_selector("#loading-overlay", state="attached", timeout=10000)
        page.wait_for_selector("#loading-overlay", state="detached", timeout=30000)

        # Validar que haya al menos una tarjeta visible
        cards = page.locator(".property-card")
        expect(cards).to_have_count_greater_than(0)

        # No errores JS
        assert len(console_errors) == 0, f"Errores consola: {console_errors}"

        browser.close() 
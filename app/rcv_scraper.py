
from playwright.sync_api import sync_playwright
import time
import csv
import io
import json

def buscar_accordion_en_iframes(page):
    frames = page.frames
    print(f"Cantidad de iframes: {len(frames)}")
    for i, frame in enumerate(frames):
        print(f"\nFrame {i}: URL = {frame.url}")
        try:
            locator = frame.locator("p.accordion_special")
            count = locator.count()
            print(f"  Elementos con 'accordion_special' encontrados: {count}")
            if count > 0:
                for idx in range(count):
                    contenido = locator.nth(idx).inner_html()
                    print(f"  Contenido del elemento {idx}:\n{contenido}")
        except Exception as e:
            print(f"  Error buscando en frame {i}: {e}")


def loginSii(page, url, rut, clave, id_boton_login):
    page.goto(url)

    # Completar login
    page.fill('input[name="rutcntr"]', rut)
    page.fill('input[name="clave"]', clave)
    page.click(id_boton_login)

    try:
        page.wait_for_url(url, timeout=10000)
    except TimeoutError:
        print("No se redireccionó después de login, pero seguimos...")

    return page


def quitarPopup(page, id_boton_cerrar, timeout=3000):
    try:
        page.click(id_boton_cerrar, timeout=timeout)
        print("Popup cerrado")
    except TimeoutError:
        print("No apareció el popup, seguimos...")
    return page


def apretarRegistroCompraVenta(page, texto_link):
    try:
        rcv_link = page.locator(f"text={texto_link}").first
        rcv_link.scroll_into_view_if_needed()

        with page.context.expect_page() as new_page_info:
            rcv_link.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state()
        return new_page
    except TimeoutError:
        print(f"No se encontró enlace con texto '{texto_link}'.")
        return None

def entrarRegistroCompraVentaDetalle(page, selector_accordion, texto_boton):
    try:
        page.wait_for_selector(selector_accordion, timeout=15000)
        print("✅ Elemento encontrado!")
    except:
        print("❌ Falló. Posibles causas:")
        print("- La página no cargó correctamente")
        print("- El elemento tiene otro selector")
        return None

    try:
        link = page.get_by_text(texto_boton, exact=True)
        link.scroll_into_view_if_needed()
        link.click()
        print(f"✅ Click en '{texto_boton}' exitoso")
    except:
        print(f"❌ No se pudo hacer click en el botón '{texto_boton}'")
        return None

    return page

def consultarRCV(page, mes, anho, nombre_boton="Consultar"):
    try:
        # Seleccionar mes
        page.select_option("#periodoMes", mes)
        print(f"✅ Mes seleccionado: {mes}")
    except Exception as e:
        print(f"❌ Error al seleccionar mes ({mes}): {e}")
        return None

    try:
        # Seleccionar año
        page.select_option('select[ng-model="periodoAnho"]', anho)
        print(f"✅ Año seleccionado: {anho}")
    except Exception as e:
        print(f"❌ Error al seleccionar año ({anho}): {e}")
        return None

    try:
        # Click en botón Consultar
        consultar_btn = page.get_by_role("button", name=nombre_boton)
        consultar_btn.scroll_into_view_if_needed()
        consultar_btn.click()
        print(f"✅ Botón '{nombre_boton}' presionado correctamente")
    except Exception as e:
        print(f"❌ No se pudo hacer click en el botón '{nombre_boton}': {e}")
        return None

    return page

def seleccionarCompraOVenta(page, tipo):
    tipo = tipo.strip().lower()
    
    try:
        if tipo == "compra":
            tab = page.locator("#tabCompra")
            tab.scroll_into_view_if_needed()
            tab.click()
            print("✅ Pestaña COMPRA seleccionada")
        elif tipo == "venta":
            # Seleccionamos por texto ya que el tab no tiene ID
            tab = page.get_by_role("link", name="VENTA")
            tab.scroll_into_view_if_needed()
            tab.click()
            print("✅ Pestaña VENTA seleccionada")
        else:
            print(f"❌ Tipo inválido: '{tipo}'. Usa 'compra' o 'venta'.")
            return None
    except Exception as e:
        print(f"❌ Error al seleccionar pestaña '{tipo.upper()}': {e}")
        return None

    return page



def seleccionarSubseccionCompra(page, subpestana):
    subpestana = subpestana.strip().lower()

    # Mapeo entre texto esperado y texto en pantalla
    opciones = {
        "registro": "REGISTRO",
        "pendientes": "PENDIENTES",
        "no incluir": "NO INCLUIR",
        "reclamados": "RECLAMADOS"
    }

    texto_objetivo = opciones.get(subpestana)
    if not texto_objetivo:
        print(f"❌ Subpestaña inválida: '{subpestana}'. Opciones válidas: {list(opciones.keys())}")
        return None

    try:
        tab = page.get_by_role("link", name=texto_objetivo)
        tab.scroll_into_view_if_needed()
        tab.click()
        print(f"✅ Subpestaña '{texto_objetivo}' seleccionada correctamente")
    except Exception as e:
        print(f"❌ Error al seleccionar subpestaña '{texto_objetivo}': {e}")
        return None

    return page

def getDownloadPath(page, boton_nombre):
    """
    Intenta encontrar un botón con texto boton_nombre y hacer clic para descargar.
    Si el botón no está presente en un timeout corto, retorna None.
    Si se realiza la descarga correctamente, retorna la ruta temporal del archivo.
    """
    try:
        # Intentar encontrar el botón con timeout corto (2 segundos)
        boton = page.wait_for_selector(f'button:has-text("{boton_nombre}")', timeout=2000)
    except:
        print(f"⚠️ No se encontró el botón '{boton_nombre}'.")
        return None

    try:
        with page.expect_download() as download_info:
            boton.click()

        download = download_info.value
        path = download.path()
        return path

    except Exception as e:
        print(f"❌ Error durante la descarga con el botón '{boton_nombre}': {e}")
        return None


def descargar_y_convertir_csv_a_json(page, mes, anho, tipo, estado):
    try:
        path = getDownloadPath(page, "Descargar Detalles")

        if not path:
            print("❌ No se pudo obtener la ruta del archivo descargado.")
            # Retornamos estructura vacía con datos_encontrados False para saber que no hay datos
            return [{
                "mes": mes,
                "anho": anho,
                "tipo": tipo,
                "estado": estado,
                "datos_encontrados": False
            }]

        with open(path, "r", encoding="utf-8") as f:
            csv_text = f.read()

        print("✅ Archivo CSV descargado correctamente")

        reader = csv.DictReader(io.StringIO(csv_text), delimiter=';')
        data = []

        for row in reader:
            # Limpiar keys vacíos o None
            row = {
                k.lower().replace(" ", "_").replace(".", ""): v
                for k, v in row.items()
                if k and k.strip() != ""
            }
            row["mes"] = mes
            row["anho"] = anho
            row["tipo"] = tipo
            row["estado"] = estado
            row["datos_encontrados"] = True
            data.append(row)

        print("=== Contenido JSON generado ===")
        #print(json.dumps(data, indent=2, ensure_ascii=False))

        return data

    except Exception as e:
        print(f"❌ Error durante la descarga o conversión: {e}")
        # También en caso de excepción devolvemos formato con datos_encontrados False para uniformidad
        return [{
            "mes": mes,
            "anho": anho,
            "tipo": tipo,
            "estado": estado,
            "datos_encontrados": False
        }]


def obtener_datos_rcv(page, mes, anho, tipo):
    tipo = tipo.lower()
    resultados = []

    if tipo == "venta":
        # No hay subsección para venta
        data = descargar_y_convertir_csv_a_json(page, mes, anho, tipo, estado="")
        if data:
            resultados.extend(data)
    elif tipo == "compra":
        opciones = {
            "registro": "REGISTRO",
            "pendientes": "PENDIENTES",
            "no incluir": "NO INCLUIR",
            "reclamados": "RECLAMADOS"
        }

        for estado_key, estado_nombre in opciones.items():
            page = seleccionarSubseccionCompra(page, estado_nombre)
            page.wait_for_timeout(1000)

            data = descargar_y_convertir_csv_a_json(page, mes, anho, tipo, estado=estado_nombre)
            if data:
                resultados.extend(data)
    else:
        print(f"Tipo '{tipo}' no soportado.")
        return None

    return resultados

def obtener_rcv(rut, clave, mes, anho, tipo="compra"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page = loginSii(page, "https://misiir.sii.cl/cgi_misii/siihome.cgi", rut, clave, "#bt_ingresar")
        page = quitarPopup(page, "#btnActualizarMasTarde", timeout=2000)
        page = apretarRegistroCompraVenta(page, "Registro de Compras y Ventas")

        if page is None:
            return {"error": "No se pudo continuar, página no encontrada"}

        page.wait_for_timeout(1000)
        page.wait_for_load_state("networkidle")

        page = entrarRegistroCompraVentaDetalle(page, ".accordion_special", "Ingresar al Registro de Compras y Ventas")
        page = consultarRCV(page, mes=mes, anho=anho)
        page = seleccionarCompraOVenta(page, tipo)

        page.wait_for_timeout(1000)

        data_final = obtener_datos_rcv(page, mes, anho, tipo)

        browser.close()

        return data_final
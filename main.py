import os
import time
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "tu_url_de_supabase")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "tu_api_key_de_supabase")
SUPABASE_TABLE = "inventario_sap"

COLUMNAS_SAP = ["Material", "Serial", "Texto", "Centro", "Almacen", "Movimiento", "Mov_texto", "Modelo", "Origen", "Precio", "Dias_Antiguedad", "Semaforo", "Fecha_Antiguedad", "Nro_Pedido"]
COLUMNAS_RELEVANTES = {"Material", "Serial", "Texto", "Centro", "Precio", "Dias_Antiguedad", "Semaforo", "Fecha_Antiguedad", "Nro_Pedido"}

def limpiar_supabase_viejo():
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
    headers = {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}
    requests.delete(url, headers=headers, params={"id": "neq.0"})

def subir_a_supabase(registros, categoria):
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    for reg in registros:
        reg["Categoria"] = categoria
    requests.post(url, headers=headers, json=registros)

def extraer_datos_tabla(driver):
    xpath_tabla = "//table[contains(@class, 'sapUiTableCtrl')]//tbody | //table[contains(@class, 'sapMListTbl')]//tbody"
    try:
        tabla_body = WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.XPATH, xpath_tabla)))
        filas = tabla_body.find_elements(By.TAG_NAME, "tr")
        resultados = []
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if celdas:
                valores = [celda.text.strip() for celda in celdas]
                if len(valores) >= len(COLUMNAS_SAP):
                    registro = {COLUMNAS_SAP[i]: valores[i] for i in range(len(COLUMNAS_SAP)) if COLUMNAS_SAP[i] in COLUMNAS_RELEVANTES}
                    resultados.append(registro)
        return resultados
    except:
        return []

def tarea_bot_sap(rango_inicio: str, rango_fin: str, SinUs: str, SinPass: str):
    print(f"--> [CONSOLA] Iniciando login para: '{SinUs}'")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    registros_stock_actual = []
    registros_transito = []

    try:
        print("Iniciando simulacion del navegador... Abriendo SAP Fiori Claro")
        driver.get("https://flpnwc-d62f4ebf3.dispatcher.us2.hana.ondemand.com/sites/agentes#Home-show")
        time.sleep(12) 

        print("Paso 0: Verificando presencia del boton superior...")
        try:
            boton_desplegar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="headerLoginButton"]/span | //*[@id="headerLoginButton"]'))
            )
            boton_desplegar.click()
            time.sleep(4)
        except:
            print("-> El boton superior no respondio. Continuando...")

        if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
            driver.switch_to.frame(0)

        print("Paso 1: Escribiendo credenciales e ingresando...")
        time.sleep(4)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="j_username"]')))
        
        driver.execute_script(f"document.getElementById('j_username').value = '{SinUs}';")
        driver.execute_script(f"document.getElementById('j_password').value = '{SinPass}';")
        time.sleep(2) 
        
        print("-> Presionando boton de ingreso 'Log On'...")
        time.sleep(2) 
        try:
            boton_submit = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "logOnFormSubmit")))
            driver.execute_script("arguments.click();", boton_submit)
            print("-> Formulario enviado mediante ID estandar.")
        except:
            try:
                boton_texto = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log On')] | //input[@value='Log On']")))
                driver.execute_script("arguments.click();", boton_texto)
                print("-> Formulario enviado mediante texto 'Log On'.")
            except:
                boton_clase = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "comSapIdpIdpButtons")))
                driver.execute_script("arguments.click();", boton_clase)
                print("-> Formulario enviado mediante clase corporativa.")

        print("-> Esperando procesamiento del Login...")
        driver.switch_to.default_content()
        time.sleep(12)

        print("Paso 2: Viajando directo al modulo mediante URL Maestra...")
        driver.get("https://flpnwc-d62f4ebf3.dispatcher.us2.hana.ondemand.com/sites/agentes#stock_antiguedad-Display")
        print("-> Esperando 22 segundos de cortesia extendida para la carga del modulo...")
        time.sleep(22)

        xpath_btn_consultar = '//*[@id="__xmlview8--button2-BDI-content"]'
        xpath_reabrir_filtros = '//*[@id="__xmlview4--panelSel-CollapsedImg-img"]'

        print("Paso 3: Consultando Stock Disponible Principal...")
        campo_inicio = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__xmlview8--input0"]')))
        campo_inicio.clear()
        campo_inicio.send_keys(rango_inicio)
        driver.find_element(By.XPATH, '//*[@id="__xmlview8--input1"]').clear()
        driver.find_element(By.XPATH, '//*[@id="__xmlview8--input1"]').send_keys(rango_fin)
        driver.find_element(By.XPATH, xpath_btn_consultar).click()
        time.sleep(14)
        registros_stock_actual.extend(extraer_datos_tabla(driver))

        print("Paso 4: Reabriendo filtros para Deposito de Reingreso...")
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_reabrir_filtros))).click()
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__xmlview11--rdb5-Button"]'))).click()
        driver.find_element(By.XPATH, xpath_btn_consultar).click()
        time.sleep(14)
        registros_stock_actual.extend(extraer_datos_tabla(driver))

        print("Paso 5: Reabriendo filtros para Stock en Transito...")
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath_reabrir_filtros))).click()
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__xmlview4--rdb4"]/div/svg/circle'))).click()
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__xmlview4--rdb7-label"]'))).click()
        driver.find_element(By.XPATH, xpath_btn_consultar).click()
        time.sleep(14)
        registros_transito = extraer_datos_tabla(driver)

        print("Paso 6: Sincronizando con Supabase...")
        limpiar_supabase_viejo()
        if registros_stock_actual:
            subir_a_supabase(registros_stock_actual, "Stock actual")
        if registros_transito:
            subir_a_supabase(registros_transito, "Stock en Transito")
        print("¡Sincronizacion completada con exito total!")

    except Exception as e:
        import traceback
        print("¡Se detecto un fallo critico!")
        try:
            print(f"URL donde fallo: {driver.current_url}")
            driver.save_screenshot("error_sap.png")
        except:
            pass
        traceback.print_exc()
    finally:
        driver.quit()

@app.get("/ver-error")
def ver_error():
    from fastapi.responses import FileResponse
    if os.path.exists("error_sap.png"):
        return FileResponse("error_sap.png")
    return {"status": "No hay capturas de error guardadas."}

@app.post("/ejecutar-bot")
def ejecutar_bot(payload: dict):
    r_inicio = str(payload.get("rango_inicio", ""))
    r_fin = str(payload.get("rango_fin", ""))
    usuario = str(payload.get("SinUs", payload.get("sinus", payload.get("Sinus", payload.get("usuario_sap", ""))))).strip()
    password = str(payload.get("SinPass", payload.get("sinpass", payload.get("Sinpass", payload.get("password_sap", ""))))).strip()
    tarea_bot_sap(r_inicio, r_fin, usuario, password)
    return {"status": "Proceso ejecutado"}

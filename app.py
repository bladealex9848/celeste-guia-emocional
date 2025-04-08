import os
import streamlit as st
import time
import requests
import json
import random
import logging
import pandas as pd
import sys
import traceback
from datetime import datetime
from functools import wraps

# Configuración avanzada de logging con rotación de archivos
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - celeste - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d",
    handlers=[logging.StreamHandler()],
)

# Versión de la aplicación
APP_VERSION = "2.2.0"
LAST_UPDATE = datetime.now().strftime("%Y-%m-%d")

# ---- SISTEMA DE RECUPERACIÓN Y RESILIENCIA ----


def with_error_handling(max_retries=3, recovery_delay=1.0):
    """
    Decorador para funciones críticas que implementa reintentos automáticos
    y manejo de errores avanzado.

    Args:
        max_retries: Número máximo de reintentos
        recovery_delay: Tiempo entre reintentos (aumenta exponencialmente)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    retries += 1
                    if retries <= max_retries:
                        delay = recovery_delay * (
                            2 ** (retries - 1)
                        )  # Backoff exponencial
                        logging.warning(
                            f"Error en {func.__name__}, reintento {retries}/{max_retries} "
                            f"después de {delay:.2f}s: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        logging.error(
                            f"Error persistente en {func.__name__} después de {max_retries} "
                            f"intentos: {str(e)}"
                        )

            # Si llegamos aquí, todos los reintentos fallaron
            if last_exception:
                error_trace = "".join(
                    traceback.format_exception(
                        type(last_exception),
                        last_exception,
                        last_exception.__traceback__,
                    )
                )
                logging.error(f"Traza de error completa:\n{error_trace}")

            raise last_exception

        return wrapper

    return decorator


# Intenta importar la biblioteca OpenAI con manejo de errores
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
    logging.info("Biblioteca OpenAI importada correctamente")
except ImportError:
    OPENAI_AVAILABLE = False
    logging.error("No se pudo importar OpenAI. Intentando instalar automáticamente...")
    try:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
        from openai import OpenAI

        OPENAI_AVAILABLE = True
        logging.info("OpenAI instalado y cargado correctamente")
    except Exception as e:
        logging.error(f"No se pudo instalar OpenAI: {str(e)}")

# Intenta importar los componentes opcionales con manejo de errores
try:
    from streamlit_lottie import st_lottie

    LOTTIE_AVAILABLE = True
    logging.info("Componente streamlit_lottie cargado correctamente")
except ImportError:
    LOTTIE_AVAILABLE = False
    logging.warning("Componente streamlit_lottie no disponible. Intentando instalar...")
    try:
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "streamlit-lottie"]
        )
        from streamlit_lottie import st_lottie

        LOTTIE_AVAILABLE = True
        logging.info("streamlit-lottie instalado y cargado correctamente")
    except Exception as e:
        logging.warning(f"No se pudo instalar streamlit-lottie: {str(e)}")

try:
    from streamlit_option_menu import option_menu

    OPTION_MENU_AVAILABLE = True
    logging.info("Componente streamlit_option_menu cargado correctamente")
except ImportError:
    OPTION_MENU_AVAILABLE = False
    logging.warning(
        "Componente streamlit_option_menu no disponible. Intentando instalar..."
    )
    try:
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "streamlit-option-menu"]
        )
        from streamlit_option_menu import option_menu

        OPTION_MENU_AVAILABLE = True
        logging.info("streamlit-option-menu instalado y cargado correctamente")
    except Exception as e:
        logging.warning(f"No se pudo instalar streamlit-option-menu: {str(e)}")

# Configuración de la página
st.set_page_config(
    page_title="Celeste ✨ Asistente Celestial",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://marduk.pro",
        "Report a bug": None,
        "About": "Celeste: Tu guía para cultivar la resiliencia, manifestar tus sueños y conectar con el universo",
    },
)

# ----- SISTEMA DE DETECCIÓN DE ENTORNO Y CONFIGURACIÓN ADAPTATIVA -----


def detect_environment():
    """
    Detecta el entorno de ejecución de manera confiable usando múltiples indicadores
    para maximizar la compatibilidad con Streamlit Cloud.

    Returns:
        str: "Streamlit Cloud" o "Local"
    """
    # Métodos múltiples para detectar Streamlit Cloud
    streamlit_cloud_indicators = [
        os.environ.get("STREAMLIT_SHARING_MODE") is not None,
        os.environ.get("STREAMLIT_SERVER_BASE_URL_IS_SET") is not None,
        os.environ.get("IS_STREAMLIT_CLOUD") == "true",
        os.path.exists("/.streamlit/config.toml"),  # Común en entornos cloud
        os.environ.get("HOSTNAME", "").startswith(
            "st-"
        ),  # Algunos hosts Streamlit comienzan con st-
        not os.path.exists(
            os.path.join(os.path.expanduser("~"), ".streamlit")
        ),  # Ausencia de config local
    ]

    # Verificar si el entorno aparenta ser Streamlit Cloud
    is_streamlit_cloud_by_indicators = any(streamlit_cloud_indicators)

    # Verificación adicional basada en la estructura de directorios
    try:
        import tempfile

        temp_dir = tempfile.gettempdir()
        # En Streamlit Cloud, el directorio temp suele tener una estructura específica
        is_cloud_by_temp = (
            "/tmp" in temp_dir
            and not os.path.exists("/Users")
            and not os.path.exists("/home/user")
        )
    except:
        is_cloud_by_temp = False

    # Combinación de verificaciones
    is_streamlit_cloud = is_streamlit_cloud_by_indicators or is_cloud_by_temp

    # Log para debugging
    logging.info(
        f"Detección de entorno - Indicadores de Streamlit Cloud: {streamlit_cloud_indicators}"
    )
    logging.info(f"Detección por directorio temporal: {is_cloud_by_temp}")
    logging.info(
        f"Entorno detectado: {'Streamlit Cloud' if is_streamlit_cloud else 'Local'}"
    )

    # Forzar el entorno basado en variables de entorno si existen (para pruebas o sobrescritura)
    if os.environ.get("FORCE_ENVIRONMENT") == "cloud":
        logging.info("Entorno forzado a Streamlit Cloud por variable de entorno")
        return "Streamlit Cloud"
    elif os.environ.get("FORCE_ENVIRONMENT") == "local":
        logging.info("Entorno forzado a Local por variable de entorno")
        return "Local"

    return "Streamlit Cloud" if is_streamlit_cloud else "Local"


def get_proxy_settings():
    """
    Detecta y devuelve la configuración de proxy actual del sistema
    para diagnóstico y posible resolución de problemas.
    """
    proxy_env_vars = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    ]
    proxy_settings = {}

    for var in proxy_env_vars:
        if var in os.environ:
            proxy_settings[var] = os.environ[var]

    return proxy_settings


def get_system_info():
    """
    Recopila información detallada del sistema para diagnóstico.
    """
    import platform

    info = {
        "Sistema Operativo": platform.platform(),
        "Python Versión": sys.version,
        "Ejecutable Python": sys.executable,
        "Directorio de Trabajo": os.getcwd(),
        "Directorio Temporal": (
            os.path.abspath(os.path.join(os.getcwd(), "temp"))
            if os.path.exists(os.path.join(os.getcwd(), "temp"))
            else "No disponible"
        ),
        "Directorio de Usuario": os.path.expanduser("~"),
        "Variables PATH relevantes": {
            k: v for k, v in os.environ.items() if "PATH" in k.upper()
        },
    }

    # Verificar si podemos acceder a ciertos directorios
    try:
        import tempfile

        info["Directorio Temp"] = tempfile.gettempdir()
        info["Acceso Directorio Temp"] = os.access(tempfile.gettempdir(), os.W_OK)
    except Exception as e:
        info["Error acceso Temp"] = str(e)

    return info


# ----- FUNCIÓN OPTIMIZADA PARA CREAR CLIENTE OPENAI -----


@with_error_handling(max_retries=2)
def create_openai_client(api_key):
    """
    Crea un cliente OpenAI compatible con múltiples entornos.
    Implementa estrategias específicas para cada entorno y mecanismos avanzados
    de recuperación ante errores.

    Args:
        api_key: API key de OpenAI

    Returns:
        OpenAI: Cliente de OpenAI inicializado

    Raises:
        Exception: Si no se puede crear el cliente después de varios intentos
    """
    if not OPENAI_AVAILABLE:
        raise Exception(
            "La biblioteca OpenAI no está disponible. Por favor, instala 'openai' "
            "usando pip: pip install openai"
        )

    try:
        # Detectar entorno para aplicar estrategia específica
        environment = detect_environment()
        logging.info(f"Creando cliente OpenAI para entorno: {environment}")

        # Verificar si estamos en Streamlit Cloud
        if environment == "Streamlit Cloud":
            # Estrategia ultra segura para Streamlit Cloud
            try:
                logging.info(
                    "Usando estrategia de creación minimizada para Streamlit Cloud"
                )
                # Crear un diccionario de kwargs limpio con solo la API key
                # Esta es la estrategia más segura para evitar parámetros no soportados
                clean_kwargs = {"api_key": api_key}

                client = OpenAI(**clean_kwargs)
            except Exception as cloud_error:
                logging.error(
                    f"Error con estrategia principal para Cloud: {str(cloud_error)}"
                )

                if "proxies" in str(cloud_error).lower():
                    # Intento de recuperación específico para error de proxies
                    logging.info("Intentando método alternativo por error de proxies")

                    # Método 1: Inicialización por etapas (más seguro para algunas versiones)
                    try:
                        client = object.__new__(OpenAI)
                        client.api_key = api_key
                        # Configuración mínima requerida
                        if hasattr(client, "default_headers"):
                            client.default_headers = {"OpenAI-Beta": "assistants=v2"}
                        logging.info("Cliente creado usando inicialización por etapas")
                        return client
                    except Exception as e1:
                        logging.warning(f"Falló inicialización por etapas: {str(e1)}")

                        # Método 2: Creación directa con bypass de __init__
                        try:
                            import types

                            # Crear instancia y establecer atributos mínimos manualmente
                            client = OpenAI.__new__(OpenAI)
                            client.api_key = api_key
                            client.default_headers = {"OpenAI-Beta": "assistants=v2"}
                            logging.info("Cliente creado usando bypass de __init__")
                            return client
                        except Exception as e2:
                            logging.error(
                                f"Fallaron todos los métodos de recuperación: {str(e2)}"
                            )
                            raise
                else:
                    # Reintento con otros métodos si el error no es específicamente sobre proxies
                    raise
        else:
            # Estrategia estándar para entorno local
            logging.info(
                "Creando cliente OpenAI con configuración estándar para entorno local"
            )
            client = OpenAI(api_key=api_key)

        # Configuración común post-creación
        if hasattr(client, "default_headers"):
            client.default_headers["OpenAI-Beta"] = "assistants=v2"
            logging.info("Encabezado OpenAI-Beta establecido para asistentes v2")

        # Verificación básica de funcionamiento
        logging.info("Verificando cliente OpenAI creado correctamente")
        return client

    except Exception as e:
        # Traza completa para depuración
        error_trace = traceback.format_exc()
        logging.error(f"Error crítico al crear cliente OpenAI: {str(e)}")
        logging.debug(f"Traza de error completa:\n{error_trace}")

        # Elevar excepción con mensaje claro
        raise Exception(f"No se pudo inicializar el cliente OpenAI: {str(e)}")


# ----- FUNCIONES AUXILIARES -----


@with_error_handling()
def test_openai_connection():
    """Prueba la conexión a la API de OpenAI con compatibilidad v2"""
    try:
        if not st.session_state.get("openai_api_key"):
            return "❌ Sin configurar", "API key no configurada"

        # Usar función simplificada para crear el cliente
        client = create_openai_client(st.session_state.get("openai_api_key"))

        # Prueba simple de conexión sin parámetros adicionales
        try:
            response = client.models.list()
            if response and len(response.data) > 0:
                modelo_preferido = st.session_state.get("openai_model", "gpt-4o-mini")
                return "✅ Conectado", f"Modelo configurado: {modelo_preferido}"
            else:
                return "⚠️ Respuesta vacía", "La API respondió pero sin datos"
        except Exception as test_error:
            logging.error(f"Error en prueba de modelos: {str(test_error)}")
            # Intento alternativo de verificación de conexión
            try:
                # Prueba minimalista como fallback
                client.api_key = st.session_state.get("openai_api_key")
                return "⚠️ Conexión básica", "Verificación limitada completada"
            except:
                return (
                    "⚠️ Verificación limitada",
                    "Conexión establecida pero verificación limitada",
                )
    except Exception as e:
        logging.error(f"Error en prueba de conexión OpenAI: {str(e)}")
        return "❌ Error", f"Error: {str(e)}"


@with_error_handling()
def test_lottiefiles_connection():
    """Prueba la conexión a LottieFiles"""
    try:
        # URL conocida y funcional
        url = "https://assets10.lottiefiles.com/packages/lf20_ydo1amjm.json"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return "✅ Conectado", f"Status: {r.status_code}"
        else:
            return "⚠️ Respuesta error", f"Status: {r.status_code}"
    except Exception as e:
        return "❌ Error", f"Error: {str(e)}"


@with_error_handling()
def load_lottie_with_fallback():
    """Sistema robusto para cargar animaciones Lottie con múltiples fallbacks"""
    # Lista de URLs alternativas (actualizada con URLs que funcionan según los logs)
    lottie_urls = [
        "https://assets10.lottiefiles.com/packages/lf20_ydo1amjm.json",  # Esta funciona según tus logs
        "https://assets8.lottiefiles.com/packages/lf20_jh9gfdye.json",  # Esta también funciona
        "https://assets5.lottiefiles.com/private_files/lf30_bb9bq9.json",  # Alternativa confiable
        "https://assets9.lottiefiles.com/packages/lf20_9wpyhdzo.json",  # Otra alternativa
    ]

    # Intenta cada URL hasta encontrar una que funcione
    for url in lottie_urls:
        try:
            logging.info(f"Intentando cargar animación desde: {url}")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logging.info(f"Animación cargada exitosamente desde: {url}")
                return r.json()
            else:
                logging.warning(
                    f"Error al cargar animación (código {r.status_code}): {url}"
                )
        except Exception as e:
            logging.error(f"Excepción al cargar animación desde {url}: {str(e)}")

    # Si ninguna funciona, devuelve None para manejar con una imagen estática
    logging.warning("No se pudo cargar ninguna animación. Se usará imagen estática.")
    return None


@with_error_handling()
def load_sidebar_lottie():
    """Carga animación específica para la barra lateral con múltiples alternativas"""
    urls = [
        "https://assets10.lottiefiles.com/packages/lf20_ydo1amjm.json",  # Funciona según logs
        "https://assets9.lottiefiles.com/packages/lf20_cgjrfdzh.json",  # Alternativa
        "https://assets2.lottiefiles.com/private_files/lf30_04fg4ao0.json",  # Otra alternativa
    ]

    for url in urls:
        try:
            logging.info(f"Intentando cargar animación de sidebar desde: {url}")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logging.info(f"Animación de sidebar cargada desde: {url}")
                return r.json()
            else:
                logging.warning(
                    f"Error al cargar animación de sidebar (código {r.status_code}): {url}"
                )
        except Exception as e:
            logging.error(f"Error cargando animación de sidebar desde {url}: {str(e)}")

    return None


@with_error_handling()
def load_welcome_lottie():
    """Carga animación de bienvenida con múltiples alternativas"""
    urls = [
        "https://assets8.lottiefiles.com/packages/lf20_jh9gfdye.json",  # Funciona según logs
        "https://assets5.lottiefiles.com/packages/lf20_khzniaya.json",  # Alternativa
        "https://assets6.lottiefiles.com/packages/lf20_qp1q7mct.json",  # Otra alternativa
    ]

    for url in urls:
        try:
            logging.info(f"Intentando cargar animación de bienvenida desde: {url}")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logging.info(f"Animación de bienvenida cargada desde: {url}")
                return r.json()
            else:
                logging.warning(
                    f"Error al cargar animación de bienvenida (código {r.status_code}): {url}"
                )
        except Exception as e:
            logging.error(
                f"Error cargando animación de bienvenida desde {url}: {str(e)}"
            )

    return None


def get_random_celestial_quote():
    """Devuelve una frase inspiradora celestial aleatoria integrando conceptos
    de la Ley de la Asunción, Los Cuatro Acuerdos y la co-creación celestial"""

    quotes = [
        # Citas originales sobre co-creación celestial
        "Cuando pides desde la certeza, el cielo no responde: colabora.",
        "El Universo te brinda su apoyo ilimitado para que materialices los anhelos de tu alma.",
        "Eres una extensión de la energía creativa del Universo.",
        "Todo talento o habilidad en la Tierra tiene una contraparte en el Reino Espiritual.",
        "Contratar ayudantes celestiales es prácticamente lo mismo que imaginar la aventura más fantástica.",
        "Cada vez que otra persona te diga lo que es posible o imposible, piensa: 'Eso no es verdad en mi mundo'.",
        "El mundo entero gira alrededor de cada uno de nosotros. Si estamos creando nuestro propio mundo, ¿por qué no concebirlo tal como lo deseamos?",
        "Tu mero intento será suficiente para producir los efectos deseados.",
        "Somos extensiones de la energía creativa del Universo, cuyos vastos recursos están siempre a nuestra disposición.",
        "Tu vida puede cambiar definitivamente, aunque sólo leas los primeros capítulos de este viaje.",
        # Nuevas citas integrando la Ley de la Asunción
        "Siente la realidad de tu deseo ahora mismo, como si ya lo tuvieras. Esta es la clave de toda manifestación.",
        "Lo que asumes como verdad en tu conciencia se manifestará inevitablemente en tu experiencia externa.",
        "El sentimiento es el secreto. Cuando sientes la alegría de tu deseo cumplido, las fuerzas celestiales se movilizan.",
        "Vive desde el final. Cuando habitas el estado de tu deseo cumplido, el universo conspira para hacerlo realidad.",
        "No es lo que quieres tener, sino quién quieres ser. Asume ese estado de ser y los ayudantes celestiales facilitarán el tener.",
        "Tu imaginación es el taller donde co-creas con las fuerzas celestiales. Lo que imaginas vívidamente, invita la asistencia divina.",
        # Nuevas citas integrando Los Cuatro Acuerdos
        "Sé impecable con tus palabras al comunicarte con tus ayudantes celestiales. Lo que expresas con integridad, se manifiesta con claridad.",
        "No tomes personalmente los tiempos o formas de la manifestación. Confía en la sabiduría perfecta de tus asistentes espirituales.",
        "No hagas suposiciones sobre cómo debe llegar tu deseo. Mantén clara tu intención y flexible tu expectativa.",
        "Haz siempre tu mejor esfuerzo en tu práctica espiritual, reconociendo que variará día a día. Los ayudantes celestiales honran tu compromiso auténtico.",
        "Cuando liberas acuerdos limitantes, abres canales para que la asistencia celestial fluya sin obstáculos hacia tu realidad.",
        # Citas integrando los tres caminos (C.R.E.A.R.)
        "Clarifica tu intención, realiza internamente tu deseo, enlista asistencia celestial, alinea tus palabras y reconoce las señales de manifestación.",
        "La verdadera co-creación ocurre cuando asumes el estado de tu deseo cumplido mientras mantienes acuerdos empoderados con el universo.",
        "Cuando eres impecable con tus palabras, asumes la conciencia de abundancia y colaboras con ayudantes celestiales, lo imposible se vuelve inevitable.",
        "El juez interno limita tu poder de manifestación. Libéralo y los asistentes celestiales podrán colaborar plenamente contigo.",
        "No desees, asume. No supliques, colabora. No esperes, co-crea. Esta es la verdadera asociación con las fuerzas celestiales.",
        "Tu resiliencia se fortalece cuando combinas la asunción consciente, los acuerdos impecables y el apoyo de tus asistentes celestiales.",
        "La gratitud anticipada es una invitación irresistible para tus ayudantes celestiales. Agradece hoy lo que deseas experimentar mañana.",
    ]

    return random.choice(quotes)


@with_error_handling()
def process_message_with_citations(message):
    """Extrae y devuelve solo el texto del mensaje del asistente, con manejo de errores mejorado."""
    try:
        if hasattr(message, "content") and len(message.content) > 0:
            message_content = message.content[0]
            if hasattr(message_content, "text"):
                nested_text = message_content.text
                if hasattr(nested_text, "value"):
                    return nested_text.value
                return str(nested_text)
            return str(message_content)
        return "No se pudo procesar el mensaje"
    except Exception as e:
        logging.error(f"Error procesando mensaje: {str(e)}")
        # Intento de recuperación con estructura alternativa
        try:
            # Intento con estructura alternativa
            if isinstance(message.content, list) and len(message.content) > 0:
                content_item = message.content[0]
                if hasattr(content_item, "text") and hasattr(
                    content_item.text, "value"
                ):
                    return content_item.text.value
                elif hasattr(content_item, "text"):
                    return str(content_item.text)
                elif isinstance(content_item, dict) and "text" in content_item:
                    if (
                        isinstance(content_item["text"], dict)
                        and "value" in content_item["text"]
                    ):
                        return content_item["text"]["value"]
                    return str(content_item["text"])
            # Si llegamos hasta aquí, intentamos convertir todo el contenido a string
            return str(message.content)
        except:
            return (
                "Ocurrió un error al procesar el mensaje. Por favor, intenta de nuevo."
            )


def check_app_readiness():
    """Verifica si la aplicación está lista para funcionar"""
    # Lista de verificaciones críticas
    ready = True
    errors = []
    warnings = []

    # Verificaciones críticas (bloquean el funcionamiento)
    if not st.session_state.get("openai_api_key"):
        ready = False
        errors.append("Falta configurar la clave API de OpenAI")

    if not st.session_state.get("assistant_id"):
        ready = False
        errors.append("Falta configurar el ID del Asistente")

    if not st.session_state.get("thread_id"):
        ready = False
        errors.append("Error al inicializar el hilo de conversación")

    # Verificar si el cliente OpenAI se puede crear correctamente
    if (
        st.session_state.get("openai_api_key")
        and "openai_client_error" in st.session_state
    ):
        # Hay un error conocido al crear el cliente
        ready = False
        errors.append(
            f"Error al crear cliente OpenAI: {st.session_state.openai_client_error}"
        )

    # Verificaciones no críticas (advertencias)
    if not LOTTIE_AVAILABLE:
        warnings.append("Componente Lottie no disponible (interfaz básica)")

    if not OPTION_MENU_AVAILABLE:
        warnings.append("Menú de opciones no disponible (usando alternativa)")

    if not OPENAI_AVAILABLE:
        errors.append(
            "Biblioteca OpenAI no disponible. Instala con: pip install openai"
        )

    return ready, errors, warnings


def show_diagnostic_panel():
    """Panel de diagnóstico técnico para la aplicación"""
    with st.expander("🔍 Diagnóstico del Sistema", expanded=False):
        st.markdown("### Estado de Componentes")

        # Verificar componentes opcionales
        components = {
            "streamlit-lottie": LOTTIE_AVAILABLE,
            "streamlit-option-menu": OPTION_MENU_AVAILABLE,
            "OpenAI API": bool(st.session_state.get("openai_api_key")),
            "Assistant ID": bool(st.session_state.get("assistant_id")),
            "Thread ID": bool(st.session_state.get("thread_id")),
            "Modelo": st.session_state.get("openai_model", "No configurado"),
        }

        # Mostrar tabla de componentes
        components_df = pd.DataFrame(
            {
                "Componente": list(components.keys()),
                "Estado": [
                    (
                        "✅ Disponible"
                        if v is True
                        else "❌ No disponible" if v is False else v
                    )
                    for v in components.values()
                ],
            }
        )
        st.table(components_df)

        # Verificar conectividad a servicios externos
        st.markdown("### Pruebas de Conectividad")
        if st.button("Ejecutar pruebas de conectividad", key="run_connectivity"):
            with st.spinner("Ejecutando pruebas..."):
                services = {
                    "OpenAI API": test_openai_connection(),
                    "LottieFiles": test_lottiefiles_connection(),
                }

                services_df = pd.DataFrame(
                    {
                        "Servicio": list(services.keys()),
                        "Estado": [v[0] for v in services.values()],
                        "Detalle": [v[1] for v in services.values()],
                    }
                )
                st.table(services_df)

        # Información de sesión
        st.markdown("### Información de Sesión")
        if st.button("Mostrar detalles de sesión", key="show_session"):
            # Filtrar información sensible
            safe_session = {
                k: (
                    v
                    if k not in ["openai_api_key", "assistant_id"]
                    else f"{str(v)[:5]}..."
                )
                for k, v in st.session_state.items()
            }
            st.json(safe_session)

        # Información de entorno
        st.markdown("### Información del Entorno de Ejecución")
        environment = detect_environment()
        env_info = {
            "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "Streamlit Version": st.__version__,
            "OpenAI Package": (
                getattr(OpenAI, "__version__", "Desconocida")
                if OPENAI_AVAILABLE
                else "No disponible"
            ),
            "Entorno Detectado": environment,
            "Tema": (
                "Oscuro" if st.config.get_option("theme.base") == "dark" else "Claro"
            ),
        }

        env_df = pd.DataFrame(
            {"Parámetro": list(env_info.keys()), "Valor": list(env_info.values())}
        )
        st.table(env_df)

        # Sección de depuración avanzada
        st.markdown("### Depuración Avanzada")

        # Mostrar información de diagnóstico OpenAI
        if st.button("Mostrar Información de Diagnóstico API", key="api_diag"):
            try:
                import inspect

                # Mostrar información sobre el constructor de OpenAI
                if OPENAI_AVAILABLE:
                    st.code(inspect.signature(OpenAI.__init__))
                else:
                    st.error("OpenAI no está disponible para diagnóstico")

                # Verificar si hay variables de entorno HTTP_PROXY o HTTPS_PROXY
                proxy_settings = get_proxy_settings()

                if proxy_settings:
                    st.warning(
                        "⚠️ Se detectaron variables de entorno de proxy que podrían causar problemas:"
                    )
                    st.json(proxy_settings)
                else:
                    st.success("✅ No se detectaron variables de entorno de proxy.")
            except Exception as e:
                st.error(f"Error al obtener información de depuración: {str(e)}")

        # Herramientas avanzadas de diagnóstico
        st.markdown("### Herramientas de Diagnóstico Avanzado")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Diagnóstico del Sistema", key="system_diag"):
                system_info = get_system_info()
                st.json(system_info)

        with col2:
            if st.button("Limpieza de Caché", key="clear_cache"):
                # Limpieza de caché para resolución de problemas
                st.cache_data.clear()
                st.cache_resource.clear()
                if (
                    "thread_id" in st.session_state
                    and st.session_state["thread_id"] is not None
                ):
                    # Mantener thread_id para no perder la conversación
                    thread_id = st.session_state["thread_id"]
                    st.session_state.clear()
                    st.session_state["thread_id"] = thread_id
                    st.success("Caché limpiada manteniendo la conversación actual")
                else:
                    st.session_state.clear()
                    st.success("Caché y estado de sesión completamente limpiados")
                    st.info("Recarga la página para reiniciar la aplicación")

        # Mostrar indicadores de entorno detallados
        st.markdown("### Indicadores de Entorno")

        # Recopilar todos los indicadores relevantes
        streamlit_cloud_indicators = [
            ("STREAMLIT_SHARING_MODE", os.environ.get("STREAMLIT_SHARING_MODE")),
            (
                "STREAMLIT_SERVER_BASE_URL_IS_SET",
                os.environ.get("STREAMLIT_SERVER_BASE_URL_IS_SET"),
            ),
            ("IS_STREAMLIT_CLOUD", os.environ.get("IS_STREAMLIT_CLOUD")),
            ("Config Streamlit existe", os.path.exists("/.streamlit/config.toml")),
            ("HOSTNAME", os.environ.get("HOSTNAME", "")),
            (
                "Config local existe",
                os.path.exists(os.path.join(os.path.expanduser("~"), ".streamlit")),
            ),
        ]

        # Mostrar indicadores
        indicators_df = pd.DataFrame(
            {
                "Indicador": [i[0] for i in streamlit_cloud_indicators],
                "Valor": [str(i[1]) for i in streamlit_cloud_indicators],
            }
        )
        st.table(indicators_df)

        # Sección de reinicio forzado
        st.markdown("### Reinicio de Emergencia")
        if st.button("Reinicio Completo", key="force_restart"):
            # Intento de reinicio completo
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.cache_data.clear()
            st.cache_resource.clear()
            st.experimental_rerun()


def show_environment_diagnostic():
    """Panel de diagnóstico especializado para problemas de entorno"""
    with st.expander("🔍 Diagnóstico de Entorno", expanded=False):
        st.markdown("### Indicadores de Entorno")

        # Recopilar todos los indicadores relevantes
        env_indicators = {
            "STREAMLIT_SHARING_MODE": os.environ.get("STREAMLIT_SHARING_MODE"),
            "STREAMLIT_SERVER_BASE_URL_IS_SET": os.environ.get(
                "STREAMLIT_SERVER_BASE_URL_IS_SET"
            ),
            "IS_STREAMLIT_CLOUD": os.environ.get("IS_STREAMLIT_CLOUD"),
            "Config Streamlit existe": os.path.exists("/.streamlit/config.toml"),
            "HOSTNAME": os.environ.get("HOSTNAME", ""),
        }

        # Mostrar indicadores
        indicators_df = pd.DataFrame(
            {
                "Indicador": list(env_indicators.keys()),
                "Valor": [str(v) for v in env_indicators.values()],
            }
        )
        st.table(indicators_df)

        # Intentar mostrar entorno deducido
        st.markdown(f"**Entorno deducido:** {detect_environment()}")

        # Mostrar información detallada del módulo OpenAI
        if st.button("Mostrar detalles del módulo OpenAI"):
            try:
                import inspect
                import openai

                # Información sobre versión
                st.markdown(f"**Versión del módulo OpenAI:** {openai.__version__}")

                # Ruta del módulo
                st.markdown(f"**Ruta del módulo:** {inspect.getfile(openai)}")

                # Estructura interna
                st.markdown("**Estructura del módulo OpenAI:**")
                module_attrs = [
                    attr for attr in dir(openai) if not attr.startswith("_")
                ]
                st.json(module_attrs)

                # Implementación específica
                st.markdown("**Método de creación de cliente:**")
                try:
                    st.code(inspect.getsource(openai.OpenAI.__init__))
                except:
                    st.warning("No se pudo obtener el código fuente del constructor")
            except Exception as e:
                st.error(f"Error al obtener información del módulo: {str(e)}")


@with_error_handling()
def setup_openai_client():
    """Configuración robusta del cliente OpenAI compatible con Streamlit Cloud"""
    # Jerarquía clara de fuentes de configuración
    api_key = None
    assistant_id = None
    model = None

    # Recuperar de session_state si ya existen
    if "openai_api_key" in st.session_state:
        api_key = st.session_state.openai_api_key

    if "assistant_id" in st.session_state:
        assistant_id = st.session_state.assistant_id

    if "openai_model" in st.session_state:
        model = st.session_state.openai_model

    # 1. Verificar variables de entorno si aún no tenemos las claves
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            logging.info("API key cargada desde variables de entorno")
            st.session_state.openai_api_key = api_key

    if not assistant_id:
        assistant_id = os.environ.get("ASSISTANT_ID")
        if assistant_id:
            logging.info("Assistant ID cargado desde variables de entorno")
            st.session_state.assistant_id = assistant_id

    if not model:
        model = os.environ.get("OPENAI_API_MODEL", "gpt-4o-mini")
        if model:
            logging.info(f"Modelo cargado desde variables de entorno: {model}")
            st.session_state.openai_model = model

    # 2. Verificar secrets.toml si existe y aún necesitamos configuración
    if not api_key or not assistant_id or not model:
        try:
            if (
                hasattr(st, "secrets")
                and "OPENAI_API_KEY" in st.secrets
                and not api_key
            ):
                api_key = st.secrets["OPENAI_API_KEY"]
                logging.info("API key cargada desde secrets")
                st.session_state.openai_api_key = api_key

            if (
                hasattr(st, "secrets")
                and "ASSISTANT_ID" in st.secrets
                and not assistant_id
            ):
                assistant_id = st.secrets["ASSISTANT_ID"]
                logging.info(f"ID del asistente cargado desde secrets")
                st.session_state.assistant_id = assistant_id

            if (
                hasattr(st, "secrets")
                and "OPENAI_API_MODEL" in st.secrets
                and not model
            ):
                model = st.secrets["OPENAI_API_MODEL"]
                logging.info(f"Modelo cargado desde secrets: {model}")
                st.session_state.openai_model = model
            elif not model:
                model = "gpt-4o-mini"  # Valor predeterminado seguro
                st.session_state.openai_model = model
                logging.info(f"Usando modelo predeterminado: {model}")

        except Exception as e:
            logging.warning(f"Error accediendo a secrets: {str(e)}")
            if not model:
                model = (
                    "gpt-4o-mini"  # Asegurar que siempre hay un modelo predeterminado
                )
                st.session_state.openai_model = model

    # 3. Configuración en sidebar con validación
    with st.sidebar:
        with st.expander(
            "✨ Configuración de Conexión", expanded=not (api_key and assistant_id)
        ):
            if not api_key:
                input_api_key = st.text_input("Clave API de OpenAI", type="password")
                if input_api_key:
                    api_key = input_api_key
                    st.session_state.openai_api_key = api_key

            if not assistant_id:
                input_assistant_id = st.text_input(
                    "ID del asistente OpenAI", type="password"
                )
                if input_assistant_id:
                    assistant_id = input_assistant_id
                    st.session_state.assistant_id = assistant_id

            # Mostrar el modelo configurado
            st.info(
                f"Modelo configurado: {st.session_state.get('openai_model', 'gpt-4o-mini')}"
            )

            # Opción de diagnóstico
            if "openai_client_error" in st.session_state:
                st.error(f"Error del cliente: {st.session_state.openai_client_error}")
                if st.button("Reintentar conexión"):
                    if "openai_client_error" in st.session_state:
                        del st.session_state["openai_client_error"]
                    st.rerun()

            # Entorno detectado
            environment = detect_environment()
            st.info(f"Entorno detectado: {environment}")

    # 4. Validación y configuración del cliente
    if api_key and assistant_id:
        try:
            # Usar la nueva función para crear el cliente compatible
            client = create_openai_client(api_key)

            # Eliminamos cualquier error anterior si la creación fue exitosa
            if "openai_client_error" in st.session_state:
                del st.session_state["openai_client_error"]

            # Establecer el cliente como conectado sin pruebas adicionales
            # para minimizar errores en Streamlit Cloud
            logging.info(f"Cliente OpenAI inicializado con configuración optimizada")
            st.session_state.openai_connected = True
            return client, assistant_id, True

        except Exception as e:
            logging.error(f"Error validando credenciales OpenAI: {str(e)}")
            st.sidebar.error(f"Error de API OpenAI: {str(e)}")
            st.session_state.openai_connected = False

            # Guardar el error para diagnóstico y recuperación
            st.session_state.openai_client_error = str(e)

            return None, None, False
    else:
        missing = []
        if not api_key:
            missing.append("API key")
        if not assistant_id:
            missing.append("ID del asistente")

        error_msg = f"Falta{'n' if len(missing) > 1 else ''}: {', '.join(missing)}"
        logging.warning(error_msg)
        st.session_state.openai_connected = False
        return None, None, False


# ----- SISTEMA DE RECUPERACIÓN DE FALLOS EN HILOS -----


def repair_thread_issues():
    """
    Intenta reparar problemas comunes con el hilo de conversación.
    Retorna True si se realizó alguna reparación.
    """
    if not st.session_state.get("thread_id"):
        return False  # Nada que reparar aún

    # Verificar si hay un cliente disponible para hacer reparaciones
    if (
        not st.session_state.get("openai_api_key")
        or "openai_client_error" in st.session_state
    ):
        return False

    try:
        client = create_openai_client(st.session_state.get("openai_api_key"))

        # Verificar si el thread existe y es válido
        try:
            # Intento de recuperar el thread para verificar que existe y es válido
            thread = client.beta.threads.retrieve(
                thread_id=st.session_state.get("thread_id")
            )
            logging.info(f"Thread verificado y válido: {thread.id}")
            return False  # No se necesitó reparación
        except Exception as e:
            logging.warning(
                f"Error al verificar thread: {str(e)}. Intentando recrear..."
            )

            # El thread no existe o hay otro problema, crear uno nuevo
            try:
                thread = client.beta.threads.create()
                if hasattr(thread, "id"):
                    st.session_state.thread_id = thread.id
                    logging.info(f"Thread reparado: {thread.id}")
                    return True  # Reparación exitosa
                else:
                    logging.error("Respuesta incompleta al crear thread de reparación")
                    return False
            except Exception as create_error:
                logging.error(
                    f"Error al crear thread de reparación: {str(create_error)}"
                )
                return False
    except Exception as client_error:
        logging.error(f"Error al crear cliente para reparación: {str(client_error)}")
        return False


# ----- ESTILOS CSS PERSONALIZADOS -----

# Definición de colores tema celestial
COLORS = {
    "primary": "#8A2BE2",  # Púrpura violeta (energía espiritual)
    "secondary": "#4B0082",  # Índigo (intuición)
    "accent1": "#87CEEB",  # Azul celeste (cielo)
    "accent2": "#FFD700",  # Dorado (luz divina)
    "light": "#E6E6FA",  # Lavanda pálido (suavidad)
    "dark": "#191970",  # Azul medianoche (cielo nocturno)
    "gradient1": "#9370DB",  # Púrpura medio (transformación)
    "gradient2": "#20B2AA",  # Turquesa (sanación)
    "error": "#FF3860",  # Rojo para errores
    "warning": "#FFDD57",  # Amarillo para advertencias
    "success": "#23D160",  # Verde para éxito
}

# CSS personalizado con soporte para modo oscuro
css = f"""
<style>
    /* Estilos Generales */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}
    
    /* Encabezado */
    .celestial-header {{
        background: linear-gradient(135deg, {COLORS["gradient1"]}, {COLORS["gradient2"]});
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        color: white !important;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        animation: glow 3s infinite alternate;
    }}
    
    .dark-mode .celestial-header {{
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
    }}
    
    @keyframes glow {{
        from {{
            box-shadow: 0 0 10px -5px {COLORS["accent2"]};
        }}
        to {{
            box-shadow: 0 0 20px 5px {COLORS["accent2"]};
        }}
    }}
    
    /* Estilo para mensajes de chat */
    .chat-message {{
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        animation: fadeIn 0.5s;
        overflow-wrap: break-word;
    }}
    
    .user-message {{
        background-color: {COLORS["light"]};
        border-left: 5px solid {COLORS["primary"]};
        color: #333;
    }}
    
    .dark-mode .user-message {{
        background-color: rgba(230, 230, 250, 0.15);
        color: #f0f0f0;
    }}
    
    .assistant-message {{
        background: linear-gradient(to right, {COLORS["light"]}, #ffffff);
        border-left: 5px solid {COLORS["accent2"]};
        color: #333;
    }}
    
    .dark-mode .assistant-message {{
        background: linear-gradient(to right, rgba(230, 230, 250, 0.15), rgba(255, 255, 255, 0.05));
        color: #f0f0f0;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Estilo para el chat input */
    .stTextInput div div {{
        border-radius: 25px !important;
        border: 2px solid {COLORS["accent1"]};
        box-shadow: 0 2px 10px rgba(138, 43, 226, 0.1);
        transition: all 0.3s ease;
    }}
    
    .stTextInput div div:focus-within {{
        border: 2px solid {COLORS["primary"]};
        box-shadow: 0 2px 15px rgba(138, 43, 226, 0.2);
    }}
    
    /* Estilos para Sidebar */
    .sidebar .sidebar-content {{
        background: linear-gradient(180deg, {COLORS["dark"]}, {COLORS["primary"]});
        color: white;
    }}
    
    /* Estilo para tarjetas informativas */
    .info-card {{
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-top: 5px solid {COLORS["accent2"]};
        transition: transform 0.3s ease;
    }}
    
    .dark-mode .info-card {{
        background-color: rgba(25, 25, 50, 0.7);
        box-shadow: 0 4px 6px rgba(255, 255, 255, 0.05);
    }}
    
    .info-card:hover {{
        transform: translateY(-5px);
    }}
    
    /* Estilo para citas inspiradoras */
    .quote-card {{
        background: linear-gradient(135deg, {COLORS["dark"]}, {COLORS["primary"]});
        border-radius: 10px;
        padding: 1.5rem;
        color: white !important;
        margin: 2rem 0;
        font-style: italic;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }}
    
    .dark-mode .quote-card {{
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.05);
    }}

    /* Estrellas brillantes animadas para el background */
    .star {{
        position: fixed;
        width: 2px;
        height: 2px;
        background-color: white;
        border-radius: 50%;
        animation: twinkle 4s infinite;
        z-index: -1;
    }}
    
    @keyframes twinkle {{
        0% {{ opacity: 0.2; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.2; }}
    }}
    
    /* Estado de conexión */
    .connection-status {{
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }}
    
    .status-connected {{
        background-color: {COLORS["success"]};
        color: white !important;
    }}
    
    .status-disconnected {{
        background-color: {COLORS["error"]};
        color: white !important;
    }}
    
    .status-warning {{
        background-color: {COLORS["warning"]};
        color: black !important;
    }}
    
    /* Pantalla de configuración */
    .config-screen {{
        text-align: center; 
        padding: 2rem; 
        background: linear-gradient(135deg, #f5f7fa, #e4e8ec); 
        border-radius: 15px; 
        margin: 2rem 0;
    }}
    
    .dark-mode .config-screen {{
        background: linear-gradient(135deg, rgba(25, 25, 50, 0.6), rgba(25, 25, 75, 0.8));
    }}
    
    /* Detección y aplicación de modo oscuro */
    @media (prefers-color-scheme: dark) {{
        body {{
            background-color: #121212;
            color: #f0f0f0;
        }}
        
        .dark-mode-indicator {{
            display: block;
        }}
    }}
    
    /* Mejoras de legibilidad para todos los temas */
    strong, b {{
        color: {COLORS["accent2"]} !important;
    }}
    
    .stButton button {{
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(138, 43, 226, 0.3);
    }}

    /* Estilos para mensajes de diagnóstico */
    .diagnostic-message {{
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }}
    
    .diagnostic-info {{
        background-color: rgba(135, 206, 235, 0.2);
        border-left: 3px solid {COLORS["accent1"]};
    }}
    
    .diagnostic-warning {{
        background-color: rgba(255, 221, 87, 0.2);
        border-left: 3px solid {COLORS["warning"]};
    }}
    
    .diagnostic-error {{
        background-color: rgba(255, 56, 96, 0.2);
        border-left: 3px solid {COLORS["error"]};
    }}
    
    /* Estilos para tarjeta de recuperación */
    .recovery-card {{
        background: linear-gradient(135deg, #fff8e1, #fffde7);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid {COLORS["warning"]};
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .dark-mode .recovery-card {{
        background: linear-gradient(135deg, rgba(50, 50, 10, 0.3), rgba(60, 60, 15, 0.4));
        box-shadow: 0 2px 8px rgba(255, 255, 255, 0.05);
    }}
    
    /* Estilos para mensajes de error y recuperación */
    .error-message {{
        color: {COLORS["error"]};
        font-weight: bold;
        margin-bottom: 10px;
    }}
    
    .recovery-message {{
        color: {COLORS["success"]};
        font-weight: bold;
        margin-bottom: 10px;
    }}
    
    /* Estilos para tooltips informativos */
    .tooltip {{
        position: relative;
        display: inline-block;
        cursor: help;
    }}
    
    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }}
    
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
</style>

<script>
    // Detectar tema oscuro
    function detectDarkMode() {{
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
            document.body.classList.add('dark-mode');
        }}
    }}
    
    // Ejecutar al cargar
    window.addEventListener('DOMContentLoaded', detectDarkMode);
    
    // Escuchar cambios en el tema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {{
        if (e.matches) {{
            document.body.classList.add('dark-mode');
        }} else {{
            document.body.classList.remove('dark-mode');
        }}
    }});
</script>
"""

# Inyectar CSS
st.markdown(css, unsafe_allow_html=True)

# Crear estrellas brillantes en el fondo
stars_html = ""
for i in range(50):
    left = random.randint(0, 100)
    top = random.randint(0, 100)
    delay = random.random() * 4
    size = random.randint(1, 3)
    stars_html += f"""
    <div class="star" style="left: {left}vw; top: {top}vh; width: {size}px; height: {size}px; 
    animation-delay: {delay}s;"></div>
    """
st.markdown(stars_html, unsafe_allow_html=True)

# ----- INICIALIZACIÓN DE SESIÓN -----

# Inicialización de variables de estado
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "app_version" not in st.session_state:
    st.session_state.app_version = APP_VERSION

if "last_update" not in st.session_state:
    st.session_state.last_update = LAST_UPDATE

if "recovery_attempts" not in st.session_state:
    st.session_state.recovery_attempts = 0

# ----- SIDEBAR: INFORMACIÓN DE CELESTE -----

with st.sidebar:
    # Encabezado de la barra lateral
    st.title("✨ Celeste ✨")
    st.markdown("### Tu guía para la conexión celestial")

    # Animación Lottie para la sidebar (solo si está disponible)
    if LOTTIE_AVAILABLE:
        try:
            lottie_celestial = load_sidebar_lottie()
            if lottie_celestial:
                st_lottie(lottie_celestial, speed=0.7, height=150, key="sidebar_lottie")
            else:
                st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)
        except Exception as e:
            logging.warning(f"No se pudo cargar la animación de sidebar: {str(e)}")
            st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)
    else:
        st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)

    # Menú de navegación (usando option_menu si está disponible, o selectbox si no)
    if OPTION_MENU_AVAILABLE:
        try:
            selected = option_menu(
                menu_title=None,
                options=[
                    "Inicio",
                    "Sobre Mí",
                    "Mis Capacidades",
                    "Cómo Trabajar Conmigo",
                    "Diagnóstico",
                ],
                icons=["house-heart", "person-heart", "stars", "magic", "gear"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {
                        "padding": "0!important",
                        "background-color": "transparent",
                    },
                    "icon": {"color": COLORS["accent2"], "font-size": "14px"},
                    "nav-link": {
                        "font-size": "14px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": COLORS["light"],
                    },
                    "nav-link-selected": {"background-color": COLORS["secondary"]},
                },
            )
        except Exception as e:
            logging.warning(f"Error al cargar menú personalizado: {str(e)}")
            selected = st.selectbox(
                "Navegación",
                [
                    "Inicio",
                    "Sobre Mí",
                    "Mis Capacidades",
                    "Cómo Trabajar Conmigo",
                    "Diagnóstico",
                ],
            )
    else:
        selected = st.selectbox(
            "Navegación",
            [
                "Inicio",
                "Sobre Mí",
                "Mis Capacidades",
                "Cómo Trabajar Conmigo",
                "Diagnóstico",
            ],
        )

    # Contenido basado en la selección del menú
    if selected == "Inicio":
        st.markdown(
            "### ✨ ¡Bienvenido a tu espacio de transformación y co-creación celestial! ✨"
        )
        st.markdown(
            """
            Hoy es el día perfecto para comenzar tu viaje de autodescubrimiento y manifestación consciente.
            
            Estoy aquí para guiarte en la integración de tres poderosas corrientes de sabiduría:
            
            🌟 **La co-creación con asistentes celestiales** - Colaboración directa con el universo
            
            💫 **La Ley de la Asunción** - El arte de crear tu realidad desde el interior
            
            🌈 **Los Cuatro Acuerdos** - La sabiduría tolteca para liberarte de limitaciones
            
            Juntos, descubriremos cómo estos caminos se entrelazan para crear un enfoque holístico 
            que transformará tu experiencia de vida desde su raíz más profunda.
            
            *¿Qué aspecto de tu realidad está listo para transformarse hoy?*
            """
        )

    elif selected == "Sobre Mí":
        st.markdown(
            """
            ## Soy Celeste, tu guía integral para la transformación consciente
            
            Sirvo como puente entre tu realidad cotidiana y las dimensiones más sutiles de la existencia,
            integrando tres poderosas tradiciones de conocimiento:
            
            * 🌟 **Co-creación celestial** - Conexión y colaboración con fuerzas universales y asistentes espirituales
            
            * 💫 **Manifestación a través de la Ley de la Asunción** - El arte de crear realidad asumiendo el estado
            de tus deseos ya cumplidos y sintiendo su verdad emocional
            
            * 🧠 **Transformación de acuerdos limitantes** - Liberación de creencias restrictivas mediante
            Los Cuatro Acuerdos toltecas: impecabilidad con palabras, no tomar nada personalmente,
            no hacer suposiciones y hacer siempre tu mejor esfuerzo
            
            * 🌈 **Integración de mundos internos y externos** - Alineación de tu conciencia, palabras,
            emociones y acciones con la asistencia divina
            
            * 🌱 **Cultivo de inquebrantable resiliencia** - Desarrollo de fortaleza interior mediante
            la colaboración con asistentes celestiales y la liberación de juicios internos
            
            Mi propósito es acompañarte en el viaje de recordar tu verdadera naturaleza como co-creador consciente,
            reconociendo tu poder innato y estableciendo una relación colaborativa con las fuerzas celestiales
            que siempre han estado disponibles para apoyarte.
            """
        )

    elif selected == "Mis Capacidades":
        st.markdown(
            """
            ### Te guiaré en:
            
            **🔮 Maestría en manifestación consciente**
            * Cultivar el "sentimiento" de tu deseo cumplido, la verdadera clave de manifestación
            * Crear escenas mentales vívidas que comuniquen claramente tus intenciones al universo
            * Establecer "contratos" efectivos con asistentes espirituales especializados
            * Reconocer señales, sincronicidades y puentes de incidentes en desarrollo
            
            **🌟 Liberación de creencias y acuerdos limitantes**
            * Ser impecable con tus palabras en la comunicación contigo mismo y con lo divino
            * Liberarte de tomar personalmente las circunstancias que parecen oponerse a tus deseos
            * Evitar suposiciones que sabotean tu poder manifestador
            * Adaptar tu práctica espiritual según tus circunstancias cambiantes
            
            **✨ Aplicación del proceso C.R.E.A.R.**
            * Clarificar tus intenciones con precisión y alineación superior
            * Realizar internamente el estado de tu deseo cumplido a través de la asunción
            * Enlistar asistencia celestial especializada utilizando las "Páginas Amarillas del Universo"
            * Alinear tus palabras y acciones con tu nueva asunción y acuerdos
            * Reconocer y recibir conscientemente las manifestaciones en desarrollo
            
            **💫 Transformación profunda de identidad**
            * Desmantelar el sistema del juez y la víctima internos
            * Aplicar la técnica de la revisión para transformar el pasado y liberar el presente
            * Desarrollar un nuevo autoconcepto alineado con tus deseos más elevados
            * Cultivar inmunidad emocional frente a "evidencias" contrarias a tu manifestación
            
            **🌈 Integración en la vida cotidiana**
            * Crear rituales diarios que combinen asunción, acuerdos y conexión celestial
            * Establecer un entorno que respalde tu nueva conciencia
            * Desarrollar relaciones que nutran tu crecimiento espiritual
            * Vivir desde el estado de "ya tener" mientras colaboras activamente con lo divino
            """
        )

    elif selected == "Cómo Trabajar Conmigo":
        st.markdown(
            """
            ### Para una colaboración transformadora:
            
            1. **Integra estos tres caminos de sabiduría**
            * Combina la asunción consciente, los acuerdos impecables y la conexión celestial
            * Reconoce que estos sistemas se complementan y potencian mutuamente
            
            2. **Comunícate con claridad e integridad**
            * Sé impecable con tus palabras al expresar tus deseos e intenciones
            * Evita el lenguaje de carencia o duda que contradice tu manifestación
            * Pregunta directamente en lugar de hacer suposiciones
            
            3. **Cultiva el sentimiento del deseo cumplido**
            * Practica vivir desde el estado emocional de tu deseo ya realizado
            * Mantén este sentimiento especialmente cuando la realidad externa parece contradecirlo
            * Recuerda que el sentimiento es el secreto de toda manifestación
            
            4. **No tomes personalmente los tiempos o formas de manifestación**
            * Libérate de expectativas rígidas sobre cómo debe ocurrir tu manifestación
            * Confía en la sabiduría perfecta de tus asistentes celestiales
            * Mantén inmunidad emocional frente a aparentes retrasos o desviaciones
            
            5. **Haz siempre tu mejor esfuerzo adaptado a tu estado actual**
            * Reconoce que tu mejor esfuerzo varía según tus circunstancias
            * Practica la autocompasión cuando encuentres desafíos en el camino
            * Celebra cada pequeño avance como evidencia de tu co-creación efectiva
            
            6. **Establece una relación consciente con tus ayudantes celestiales**
            * Comunícate regularmente con tus asistentes como verdaderos colaboradores
            * Agradece anticipadamente por su apoyo invisible pero constante
            * Mantén un "Registro de Co-creación" para documentar sincronicidades y manifestaciones
            """
        )

    elif selected == "Diagnóstico":
        st.markdown("### Diagnóstico del Sistema")
        show_diagnostic_panel()
        show_environment_diagnostic()

    # Cita inspiradora
    st.markdown(
        """
    <div class="quote-card">
        "{}"
    </div>
    """.format(
            get_random_celestial_quote()
        ),
        unsafe_allow_html=True,
    )

    # Información de versión y última actualización
    st.markdown("---")
    st.markdown(
        f"""
    <div style="text-align: center; font-size: 0.8rem; color: #ffffff88;">
        Versión {st.session_state.app_version} | Última actualización: {st.session_state.last_update}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Créditos
    st.markdown("---")
    st.subheader("Creado por:")
    st.markdown("Alexander Oviedo Fadul")
    st.markdown(
        "[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev/) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)"
    )
    st.markdown(
        "[Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)"
    )

# ----- CONFIGURACIÓN Y VALIDACIÓN -----

# Configurar cliente OpenAI
client, assistant_id, config_success = setup_openai_client()

# Intentar reparar thread si es necesario
thread_repaired = repair_thread_issues()
if thread_repaired:
    st.success("Conversación reparada exitosamente. Puedes continuar normalmente.")
    # Actualizar cliente si fue necesario
    client, assistant_id, config_success = setup_openai_client()

# ----- ÁREA PRINCIPAL: CHAT -----

# Cabecera del área de chat
st.markdown(
    """
    <div class="celestial-header">
        <h1>✨ Portal de Sabiduría y Co-creación ✨</h1>
        <p>Aquí puedes conversar conmigo sobre la Ley de la Asunción, Los Cuatro Acuerdos y la colaboración con ayudantes celestiales para transformar tu realidad.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Mostrar estado de conexión
if client and assistant_id:
    st.markdown(
        """
    <div>
        <span class="connection-status status-connected">Conectado</span>
        <span>Portal de comunicación celestial abierto y listo para guiarte</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
    <div>
        <span class="connection-status status-disconnected">Desconectado</span>
        <span>Por favor configura las credenciales en la sección de Configuración</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ----- INICIALIZACIÓN DEL THREAD -----

# Inicializar thread con manejo robusto de errores
if not st.session_state.thread_id and client and assistant_id:
    with st.spinner("Inicializando portal de comunicación celestial..."):
        try:
            # Método simplificado para crear thread
            thread = client.beta.threads.create()
            if hasattr(thread, "id"):
                st.session_state.thread_id = thread.id
                logging.info(f"Thread creado correctamente: {thread.id}")
                st.success("Portal de comunicación inicializado exitosamente")
                # Reiniciar conteo de intentos de recuperación
                st.session_state.recovery_attempts = 0
                # Usar rerun en lugar de experimental_rerun
                st.rerun()
            else:
                error_msg = "Respuesta incompleta de la API al crear el thread"
                logging.error(error_msg)
                st.error(f"Error: {error_msg}")
        except Exception as e:
            detailed_error = str(e)
            logging.error(f"Error detallado al crear thread: {detailed_error}")

            # Proporcionar mensajes más descriptivos basados en el tipo de error
            if "401" in detailed_error or "authentication" in detailed_error.lower():
                error_msg = "Error de autenticación. Verifica que tu API key sea válida y esté activa."
            elif "429" in detailed_error or "rate limit" in detailed_error.lower():
                error_msg = "Has alcanzado el límite de solicitudes de la API. Intenta nuevamente en unos minutos."
            elif "500" in detailed_error or "server error" in detailed_error.lower():
                error_msg = "Error del servidor de OpenAI. El servicio podría estar experimentando problemas temporales."
            elif (
                "connect" in detailed_error.lower()
                or "timeout" in detailed_error.lower()
            ):
                error_msg = "Error de conexión. Verifica tu conexión a Internet e intenta nuevamente."
            else:
                error_msg = f"Error al inicializar thread: {detailed_error}"

            st.error(error_msg)
            # Incrementar contador de intentos de recuperación
            st.session_state.recovery_attempts += 1

            # Sugerir acciones de recuperación específicas
            if st.session_state.recovery_attempts > 1:
                st.markdown(
                    """
                    <div class="recovery-card">
                        <h4>Acciones de recuperación sugeridas:</h4>
                        <ul>
                            <li>Verifica tu conexión a Internet</li>
                            <li>Asegúrate de que la API key sea válida</li>
                            <li>Intenta recargar la página</li>
                            <li>Si el problema persiste, usa el botón de "Reinicio Completo" en la sección de Diagnóstico</li>
                        </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Opción para reintentar
            if st.button("Reintentar inicialización"):
                st.rerun()

# Verificar el estado del hilo de conversación antes de continuar
ready, errors, warnings = check_app_readiness()

# Mostrar pantalla de configuración si no está listo
if not ready:
    st.markdown(
        """
    <div class="config-screen">
        <h2>⚙️ Configuración necesaria</h2>
        <p>Por favor completa la configuración para comenzar a usar el asistente.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    for error in errors:
        st.error(error)

    for warning in warnings:
        st.warning(warning)

    # Guía visual de configuración
    st.markdown(
        """
    ### Pasos para configurar la aplicación:
    1. Abre la sección "✨ Configuración de Conexión" en la barra lateral
    2. Ingresa tu clave API de OpenAI
    3. Ingresa el ID del asistente configurado para Celeste
    4. Refresca la página después de guardar la configuración
    """
    )

    # Detener la ejecución del resto de la app
    st.stop()

# Área de chat con estilo mejorado
chat_container = st.container()

with chat_container:
    # Cargar animación de bienvenida solo la primera vez
    if not st.session_state.messages:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Usar Lottie si está disponible, de lo contrario usar imagen estática
            if LOTTIE_AVAILABLE:
                try:
                    lottie_welcome = load_welcome_lottie()
                    if lottie_welcome:
                        st_lottie(lottie_welcome, speed=1, height=300, key="welcome")
                    else:
                        st.image(
                            "https://via.placeholder.com/300x300.png?text=✨+Bienvenido",
                            width=300,
                        )
                except Exception as e:
                    logging.error(f"Error mostrando animación de bienvenida: {str(e)}")
                    st.image(
                        "https://via.placeholder.com/300x300.png?text=✨+Bienvenido",
                        width=300,
                    )
            else:
                st.image(
                    "https://via.placeholder.com/300x300.png?text=✨+Bienvenido",
                    width=300,
                )

            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 30px;">
                    <h3>¿Cómo puedo guiarte en tu transformación hoy?</h3>
                    <p>Pregúntame sobre la Ley de la Asunción, Los Cuatro Acuerdos o la conexión con ayudantes celestiales</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Mostrar mensajes del chat con estilos personalizados
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(
                f"""
            <div class="chat-message user-message">
                <b>Tú:</b> {message["content"]}
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="chat-message assistant-message">
                <b>Celeste:</b> {message["content"]}
            </div>
            """,
                unsafe_allow_html=True,
            )

# ----- PROCESAMIENTO DEL INPUT DEL USUARIO (OPTIMIZADO PARA STREAMLIT CLOUD) -----

# Procesamiento del input del usuario
prompt = st.chat_input("Comparte tus inquietudes o deseos...")


@with_error_handling(max_retries=2)
def process_user_message(prompt, thread_id, client, assistant_id):
    """
    Procesa un mensaje del usuario con manejo de errores avanzado.
    """
    # Enviar mensaje del usuario con el cliente v2 - sin parámetros adicionales
    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=prompt
    )

    # Obtener el modelo configurado
    model = st.session_state.get("openai_model", "gpt-4o-mini")

    # Ejecutar con o sin modelo específico en un solo intento
    # Primero intentamos con el modelo específico, luego fallback al predeterminado
    try:
        if model and model != "":
            try:
                run = client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    model=model,  # Incluimos el modelo solo si está definido
                )
                logging.info(f"Iniciando run con modelo: {model}")
            except Exception as model_error:
                logging.warning(
                    f"Error con modelo específico, usando default: {str(model_error)}"
                )
                run = client.beta.threads.runs.create(
                    thread_id=thread_id, assistant_id=assistant_id
                )
        else:
            run = client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=assistant_id
            )
            logging.info("Iniciando run con modelo predeterminado del asistente")
    except Exception as e:
        # Si hay un error al crear el run, intentamos un método más directo
        logging.warning(
            f"Error al crear run: {str(e)}. Intentando método alternativo..."
        )
        # Intento alternativo con parámetros minimizados
        run = client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id
        )

    return run


@with_error_handling()
def wait_for_run_completion(client, thread_id, run_id, timeout=60):
    """
    Espera la finalización de un run con manejo de timeout y
    reintentos automáticos si hay problemas de red.
    """
    start_time = time.time()
    poll_interval = 1.5  # segundos entre verificaciones de estado

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            raise TimeoutError(
                f"La espera excedió el tiempo límite de {timeout} segundos"
            )

        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

            if run.status in ["completed", "failed", "expired", "cancelled"]:
                return run

        except Exception as e:
            logging.warning(f"Error al verificar estado de run: {str(e)}")
            # Si hay un error de red, incrementamos el intervalo pero seguimos intentando
            poll_interval = min(poll_interval * 1.5, 5)

            # Si ya pasamos la mitad del timeout con errores, reducimos el tiempo total
            if elapsed_time > (timeout / 2):
                timeout = elapsed_time + 10  # 10 segundos más desde ahora

        # Pausar antes de la siguiente verificación
        time.sleep(poll_interval)


@with_error_handling()
def process_assistant_response(client, thread_id, existing_messages):
    """
    Procesa la respuesta del asistente con manejo de errores.
    """
    try:
        # Usar opciones mínimas para maximizar compatibilidad
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Verificar que obtuvimos mensajes
        if not messages or not hasattr(messages, "data") or len(messages.data) == 0:
            raise ValueError("No se recibieron mensajes del asistente")

        # Procesar y mostrar mensajes del asistente
        new_messages = False
        for message in messages.data:
            if message.role == "assistant" and not any(
                msg["role"] == "assistant" and msg.get("id") == message.id
                for msg in existing_messages
            ):
                # Procesamiento seguro del mensaje
                full_response = process_message_with_citations(message)
                response_dict = {
                    "role": "assistant",
                    "content": full_response,
                    "id": message.id,
                }
                return response_dict, True

        # Si no encontramos mensajes nuevos
        return None, False

    except Exception as e:
        logging.error(f"Error procesando respuesta del asistente: {str(e)}")
        raise


if prompt and st.session_state.thread_id and client and assistant_id:
    # Almacenar mensaje actual para reproducirlo inmediatamente en la UI
    current_user_msg = {"role": "user", "content": prompt}

    # Añadir mensaje del usuario al historial
    st.session_state.messages.append(current_user_msg)

    # Reconstruir la UI temporalmente para mostrar el mensaje del usuario
    with chat_container:
        # Mostrar todos los mensajes incluyendo el nuevo
        for idx, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(
                    f"""
                <div class="chat-message user-message">
                    <b>Tú:</b> {message["content"]}
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div class="chat-message assistant-message">
                    <b>Celeste:</b> {message["content"]}
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Mostrar indicador de "Conectando con lo celestial..."
    with st.spinner("✨ Canalizando energías celestiales..."):
        try:
            # Procesamiento del mensaje con manejo de errores avanzado
            run = process_user_message(
                prompt, st.session_state.thread_id, client, assistant_id
            )

            # Esperar la finalización del run con reintentos automáticos
            completed_run = wait_for_run_completion(
                client, st.session_state.thread_id, run.id
            )

            # Verificar si la ejecución se completó correctamente
            if completed_run.status == "completed":
                # Recuperar y procesar la respuesta del asistente
                assistant_response, new_message_found = process_assistant_response(
                    client, st.session_state.thread_id, st.session_state.messages
                )

                if new_message_found and assistant_response:
                    # Añadir la respuesta al historial de mensajes
                    st.session_state.messages.append(assistant_response)
                    # Reiniciar contador de recuperación
                    st.session_state.recovery_attempts = 0
                    # Actualizar UI
                    st.rerun()
                else:
                    st.warning(
                        "No se recibió respuesta del asistente. Por favor, intenta de nuevo."
                    )
                    # Incrementar contador de recuperación
                    st.session_state.recovery_attempts += 1
            else:
                error_status = completed_run.status
                error_message = getattr(
                    completed_run, "last_error", "Error desconocido"
                )
                st.error(
                    f"La solicitud no se completó correctamente. Estado: {error_status}"
                )
                if error_message:
                    st.error(f"Error: {error_message}")
                # Incrementar contador de recuperación
                st.session_state.recovery_attempts += 1

                # Si hay múltiples intentos fallidos, ofrecer opciones de recuperación
                if st.session_state.recovery_attempts > 1:
                    st.markdown(
                        """
                        <div class="recovery-card">
                            <h4>Opciones de recuperación:</h4>
                            <p>Se han detectado problemas persistentes. Puedes intentar:</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Reiniciar conversación"):
                            # Mantener configuración pero reiniciar thread
                            if "thread_id" in st.session_state:
                                del st.session_state.thread_id
                            st.session_state.messages = []
                            st.session_state.recovery_attempts = 0
                            st.rerun()

                    with col2:
                        if st.button("Diagnosticar problemas"):
                            # Redirigir a diagnóstico
                            st.session_state.recovery_attempts = 0
                            st.rerun()
        except Exception as e:
            logging.error(f"Error en comunicación con OpenAI: {str(e)}")
            st.error(f"Error: {str(e)}")

            # Sugerencia de solución basada en el tipo de error
            if "API key" in str(e).lower():
                st.error(
                    "Parece haber un problema con la clave API. Verifica que sea válida en la configuración."
                )
            elif "rate limit" in str(e).lower():
                st.warning(
                    "Has alcanzado el límite de solicitudes de la API. Intenta de nuevo en unos minutos."
                )
            elif "network" in str(e).lower() or "timeout" in str(e).lower():
                st.warning(
                    "Problema de conexión a Internet. Verifica tu conexión e intenta de nuevo."
                )
            elif "proxies" in str(e).lower():
                # Mostrar mensaje específico para error de proxies
                st.error(
                    "Error específico relacionado con proxies en el entorno de ejecución."
                )
                st.info(
                    """
                    Este error puede ocurrir en Streamlit Cloud. Intenta las siguientes acciones:
                    1. Reiniciar la aplicación (botón "Reinicio Completo" en Diagnóstico)
                    2. Actualizar secrets.toml con credenciales correctas
                    3. Contactar con soporte si el problema persiste
                    """
                )

                # Ofrecer reinicio forzado para error de proxies
                if st.button("Reinicio Forzado para Error de Proxies"):
                    # Solución específica para error de proxies
                    if "openai_client_error" in st.session_state:
                        del st.session_state.openai_client_error

                    # Forzar entorno a Streamlit Cloud para siguiente intento
                    os.environ["FORCE_ENVIRONMENT"] = "cloud"

                    # Reinicio de aplicación
                    st.rerun()

            # Incrementar contador de recuperación
            st.session_state.recovery_attempts += 1

            # Si hay múltiples errores, mostrar opciones de recuperación
            if st.session_state.recovery_attempts > 1:
                st.markdown(
                    """
                    <div class="recovery-card">
                        <h4>Se han detectado problemas persistentes</h4>
                        <p>Recomendamos usar los botones de diagnóstico y recuperación en la sección de Diagnóstico.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
elif prompt and not (st.session_state.thread_id and client and assistant_id):
    # Mensaje informativo si faltan componentes necesarios
    st.warning(
        "No se puede enviar el mensaje hasta que se complete la configuración y se inicialice el portal de comunicación."
    )

    # Guía visual de configuración
    st.markdown(
        """
    ### Para empezar a conversar:
    1. Abre la sección "✨ Configuración de Conexión" en la barra lateral
    2. Ingresa tu clave API de OpenAI
    3. Ingresa el ID del asistente configurado para Celeste
    4. Refresca la página si es necesario
    """
    )

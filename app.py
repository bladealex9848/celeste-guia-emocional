import os
import streamlit as st
import time
import requests
import json
import random
import logging
import pandas as pd
from datetime import datetime
from openai import OpenAI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - celeste - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Intenta importar los componentes opcionales con manejo de errores
try:
    from streamlit_lottie import st_lottie

    LOTTIE_AVAILABLE = True
    logging.info("Componente streamlit_lottie cargado correctamente")
except ImportError:
    LOTTIE_AVAILABLE = False
    logging.warning("Componente streamlit_lottie no disponible")

try:
    from streamlit_option_menu import option_menu

    OPTION_MENU_AVAILABLE = True
    logging.info("Componente streamlit_option_menu cargado correctamente")
except ImportError:
    OPTION_MENU_AVAILABLE = False
    logging.warning("Componente streamlit_option_menu no disponible")

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

# ----- FUNCIÓN PARA CREAR CLIENTE OPENAI COMPATIBLE CON MÚLTIPLES ENTORNOS -----


def create_openai_client(api_key):
    """
    Crea un cliente OpenAI compatible con entornos de despliegue y locales

    Esta función maneja las diferencias de configuración entre entornos locales y
    de despliegue como Streamlit Cloud, evitando errores con argumentos como 'proxies'
    """
    try:
        # Intento básico de creación de cliente con parámetros óptimos
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            default_headers={"OpenAI-Beta": "assistants=v2"},
        )
        logging.info("Cliente OpenAI creado con parámetros completos")
        return client
    except TypeError as e:
        # Si falla por argumentos no soportados
        logging.warning(
            f"Error al crear cliente OpenAI con parámetros extendidos: {str(e)}"
        )

        try:
            # Intento con parámetros mínimos
            client = OpenAI(api_key=api_key)

            # Agregar encabezado de API v2 después de la inicialización
            if hasattr(client, "default_headers"):
                client.default_headers["OpenAI-Beta"] = "assistants=v2"

            logging.info("Cliente OpenAI creado con parámetros mínimos")
            return client
        except Exception as e2:
            # Si falla el segundo intento
            logging.error(f"Error crítico al crear cliente OpenAI: {str(e2)}")
            raise e2


# ----- FUNCIONES AUXILIARES -----


def test_openai_connection():
    """Prueba la conexión a la API de OpenAI con compatibilidad v2"""
    try:
        if not st.session_state.get("openai_api_key"):
            return "❌ Sin configurar", "API key no configurada"

        # Usar función mejorada para crear el cliente
        client = create_openai_client(st.session_state.get("openai_api_key"))

        # Prueba simple de conexión - método actualizado sin parámetro limit
        response = client.models.list()
        if response and len(response.data) > 0:
            modelo_preferido = st.session_state.get("openai_model", "gpt-4o-mini")
            return "✅ Conectado", f"Modelo configurado: {modelo_preferido}"
        else:
            return "⚠️ Respuesta vacía", "La API respondió pero sin datos"
    except Exception as e:
        logging.error(f"Error en prueba de conexión OpenAI: {str(e)}")
        return "❌ Error", f"Error: {str(e)}"


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
    """Devuelve una frase inspiradora celestial aleatoria"""
    quotes = [
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
    ]
    return random.choice(quotes)


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
        return "Ocurrió un error al procesar el mensaje. Por favor, intenta de nuevo."


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

    # Verificaciones no críticas (advertencias)
    if not LOTTIE_AVAILABLE:
        warnings.append("Componente Lottie no disponible (interfaz básica)")

    if not OPTION_MENU_AVAILABLE:
        warnings.append("Menú de opciones no disponible (usando alternativa)")

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
        if st.button("Ejecutar pruebas de conectividad"):
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
        if st.button("Mostrar detalles de sesión"):
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
        env_info = {
            "Python Version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "Streamlit Version": st.__version__,
            "OpenAI Package": "1.12.0",  # Esto podría determinarse programáticamente si se necesita
            "Entorno": (
                "Streamlit Cloud"
                if os.environ.get("STREAMLIT_SHARING_MODE")
                else "Local"
            ),
            "Tema": (
                "Oscuro" if st.config.get_option("theme.base") == "dark" else "Claro"
            ),
        }

        env_df = pd.DataFrame(
            {"Parámetro": list(env_info.keys()), "Valor": list(env_info.values())}
        )
        st.table(env_df)


def setup_openai_client():
    """Configuración robusta del cliente OpenAI con compatibilidad v2"""
    # Jerarquía clara de fuentes de configuración
    api_key = None
    assistant_id = None
    model = None  # Añadido para gestionar el modelo

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
        model = os.environ.get("OPENAI_API_MODEL")
        if model:
            logging.info(f"Modelo cargado desde variables de entorno: {model}")
            st.session_state.openai_model = model

    # 2. Verificar secrets.toml si existe y aún necesitamos configuración
    if not api_key or not assistant_id or not model:
        try:
            if "OPENAI_API_KEY" in st.secrets and not api_key:
                api_key = st.secrets["OPENAI_API_KEY"]
                logging.info("API key cargada desde secrets")
                st.session_state.openai_api_key = api_key

            if "ASSISTANT_ID" in st.secrets and not assistant_id:
                assistant_id = st.secrets["ASSISTANT_ID"]
                logging.info(
                    f"ID del asistente cargado desde secrets: {assistant_id[:5]}..."
                )
                st.session_state.assistant_id = assistant_id

            if "OPENAI_API_MODEL" in st.secrets and not model:
                model = st.secrets["OPENAI_API_MODEL"]
                logging.info(f"Modelo cargado desde secrets: {model}")
                st.session_state.openai_model = model

        except Exception as e:
            logging.warning(f"Error accediendo a secrets: {str(e)}")

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

            # Valor predeterminado para el modelo
            if not model:
                model = "gpt-4o-mini"  # Valor predeterminado si no se especifica otro modelo
                st.session_state.openai_model = model

            # Mostrar el modelo configurado
            st.info(
                f"Modelo configurado: {st.session_state.get('openai_model', 'gpt-4o-mini')}"
            )

    # 4. Validación y configuración del cliente
    if api_key and assistant_id:
        try:
            # Usar la nueva función para crear el cliente compatible
            client = create_openai_client(api_key)

            # Prueba básica de conectividad
            try:
                client.models.list()
                logging.info(
                    f"Cliente OpenAI inicializado correctamente con asistente: {assistant_id[:5]}..."
                )
                st.session_state.openai_connected = True
                return client, assistant_id, True
            except Exception as e:
                logging.error(f"Error en prueba de conexión: {str(e)}")
                st.sidebar.error(f"Error de conexión: {str(e)}")
                st.session_state.openai_connected = False
                return None, None, False

        except Exception as e:
            logging.error(f"Error validando credenciales OpenAI: {str(e)}")
            st.sidebar.error(f"Error de API OpenAI: {str(e)}")
            st.session_state.openai_connected = False
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
    st.session_state.app_version = (
        "2.1.1"  # Incrementado por las optimizaciones de compatibilidad
    )

if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now().strftime("%Y-%m-%d")

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
        st.markdown("### ¡Bienvenido a tu espacio de conexión celestial!")
        st.markdown(
            """
        Hoy es el día perfecto para comenzar tu viaje de co-creación con el universo.
        Estoy aquí para guiarte en el camino hacia la manifestación consciente de tus sueños.
        """
        )

    elif selected == "Sobre Mí":
        st.markdown(
            """
        Soy Celeste, tu guía espiritual y emocional especializada en:
        
        * 🌟 **Co-creación consciente** con fuerzas universales
        * 🌈 **Manifestación** de abundancia y bienestar
        * 🧠 **Transformación** de patrones limitantes
        * 💫 **Contratación celestial** de asistentes espirituales
        * 🌱 **Cultivo de resiliencia** con apoyo divino
        
        Mi propósito es acompañarte en la bella aventura de reconocer y utilizar tu poder creador innato, conectándote con las fuerzas celestiales que están esperando ayudarte.
        """
        )

    elif selected == "Mis Capacidades":
        st.markdown(
            """
        ### Te ayudaré a:
        
        **🔮 Establecer conexiones celestiales**
        * Identificar qué tipo de ayuda celestial necesitas
        * Crear "contratos" efectivos con asistentes espirituales
        * Reconocer señales y sincronicidades divinas
        
        **🌟 Desarrollar tu resiliencia divina**
        * Superar límites personales con apoyo celestial
        * Transformar obstáculos en oportunidades de crecimiento
        * Gestionar el estrés mediante la co-creación
        
        **✨ Manifestar conscientemente**
        * Acceder a las "Páginas Amarillas del Universo"
        * Formar equipos espirituales para manifestar tus deseos
        * Combinar acción práctica con asistencia divina
        
        **💫 Transformar tu mentalidad**
        * Reprogramar creencias limitantes
        * Superar el autosabotaje reconociendo tu naturaleza divina
        * Desarrollar confianza como co-creador/a universal
        
        **🌈 Cultivar bienestar integral**
        * Mantener comunicación fluida con tus ayudantes celestiales
        * Crear rituales diarios para la conexión espiritual
        * Vivir en armonía con el apoyo constante de fuerzas divinas
        """
        )

    elif selected == "Cómo Trabajar Conmigo":
        st.markdown(
            """
        ### Para aprovechar al máximo nuestra colaboración:
        
        1. **Comunícate con claridad y apertura**
           * Comparte tus verdaderos deseos y necesidades
           * No hay preguntas incorrectas o demasiado simples
        
        2. **Mantén una mente abierta**
           * La conexión celestial funciona mejor sin escepticismo
           * Permite que las sincronicidades te sorprendan
        
        3. **Practica constantemente**
           * La manifestación y conexión celestial mejoran con la práctica
           * Establece rituales diarios sencillos
        
        4. **Complementa con acción**
           * La magia ocurre cuando combinas intención espiritual con acción terrena
           * Actúa como si ya estuvieras recibiendo ayuda celestial
        
        5. **Celebra los pequeños milagros**
           * Reconoce y agradece cada sincronicidad
           * Mantén un "Diario de Milagros" para registrar tus experiencias
        """
        )

    elif selected == "Diagnóstico":
        st.markdown("### Diagnóstico del Sistema")
        show_diagnostic_panel()

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

# ----- ÁREA PRINCIPAL: CHAT -----

# Cabecera del área de chat
st.markdown(
    """
<div class="celestial-header">
    <h1>✨ Portal de Comunicación Celestial ✨</h1>
    <p>Aquí puedes conversar conmigo y juntos exploraremos el arte de la manifestación y la contratación de ayudantes celestiales</p>
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

# ----- INICIALIZACIÓN DEL THREAD (SECCIÓN ACTUALIZADA) -----

# Inicializar thread si tenemos credenciales pero no thread_id
if not st.session_state.thread_id and client and assistant_id:
    with st.spinner("Inicializando portal de comunicación celestial..."):
        try:
            # Método actualizado para crear thread con manejo de errores mejorado
            thread = client.beta.threads.create()
            if thread and hasattr(thread, "id"):
                st.session_state.thread_id = thread.id
                logging.info(f"Thread creado correctamente: {thread.id[:5]}...")
                st.success("Portal de comunicación inicializado exitosamente")
                # Reemplazando experimental_rerun por rerun
                st.rerun()
            else:
                error_msg = "Respuesta incompleta de la API al crear el thread"
                logging.error(error_msg)
                st.error(f"Error: {error_msg}")
        except Exception as e:
            detailed_error = str(e)
            logging.error(f"Error detallado al crear thread: {detailed_error}")

            # Proporcionar mensajes más descriptivos basados en el tipo de error
            if (
                "status_code=401" in detailed_error
                or "authentication" in detailed_error.lower()
            ):
                error_msg = "Error de autenticación. Verifica que tu API key sea válida y esté activa."
            elif (
                "status_code=429" in detailed_error
                or "rate limit" in detailed_error.lower()
            ):
                error_msg = "Has alcanzado el límite de solicitudes de la API. Intenta nuevamente en unos minutos."
            elif (
                "status_code=500" in detailed_error
                or "server error" in detailed_error.lower()
            ):
                error_msg = "Error del servidor de OpenAI. El servicio podría estar experimentando problemas temporales."
            elif (
                "connect" in detailed_error.lower()
                or "timeout" in detailed_error.lower()
            ):
                error_msg = "Error de conexión. Verifica tu conexión a Internet e intenta nuevamente."
            else:
                error_msg = f"Error al inicializar thread: {detailed_error}"

            st.error(error_msg)
            # Opción para reintentar
            if st.button("Reintentar inicialización"):
                # Reemplazando experimental_rerun por rerun
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
                <h3>¿Cómo puedo ayudarte en tu viaje espiritual hoy?</h3>
                <p>Pregúntame sobre manifestación, resiliencia, o contratación de ayudantes celestiales</p>
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

# Procesamiento del input del usuario
prompt = st.chat_input("Comparte tus inquietudes o deseos...")

if prompt and st.session_state.thread_id and client and assistant_id:
    # Almacenar mensaje actual para reproducirlo inmediatamente en la UI
    current_user_msg = {"role": "user", "content": prompt}

    # Añadir mensaje del usuario al historial
    st.session_state.messages.append(current_user_msg)

    # Reconstruir la UI temporalmente para mostrar el mensaje del usuario
    # Esto forza a Streamlit a actualizar la UI sin esperar la respuesta
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
            # Enviar mensaje del usuario con el cliente v2
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id, role="user", content=prompt
            )

            # Obtener el modelo configurado
            model = st.session_state.get("openai_model", "gpt-4o-mini")

            # Crear una ejecución para el hilo de chat con el modelo específico
            try:
                # Intento con modelo específico
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=assistant_id,
                    model=model,  # Especificamos el modelo aquí
                )
                logging.info(f"Iniciando run con modelo explícito: {model}")
            except Exception as model_error:
                logging.warning(
                    f"Error al especificar modelo: {str(model_error)}. Intentando sin modelo específico."
                )
                # Fallback sin especificar modelo (usa el default del asistente)
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id, assistant_id=assistant_id
                )
                logging.info("Iniciando run con modelo predeterminado del asistente")

            # Esperar la respuesta con manejo de timeout
            start_time = time.time()
            timeout = 60  # 60 segundos máximo de espera

            while run.status not in ["completed", "failed", "expired", "cancelled"]:
                if time.time() - start_time > timeout:
                    st.error(
                        "La respuesta está tomando demasiado tiempo. Por favor, intenta de nuevo."
                    )
                    break

                time.sleep(1)
                try:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id, run_id=run.id
                    )
                except Exception as e:
                    logging.error(f"Error al recuperar estado de ejecución: {str(e)}")
                    st.error(f"Error de comunicación: {str(e)}")
                    break

            # Verificar si la ejecución se completó correctamente
            if run.status == "completed":
                # Recuperar mensajes agregados por el asistente
                try:
                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )

                    # Procesar y mostrar mensajes del asistente
                    new_messages = False
                    for message in messages.data:
                        if message.role == "assistant" and not any(
                            msg["role"] == "assistant" and msg.get("id") == message.id
                            for msg in st.session_state.messages
                        ):
                            full_response = process_message_with_citations(message)
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": full_response,
                                    "id": message.id,
                                }
                            )
                            new_messages = True
                            # Forzar actualización de UI
                            st.rerun()
                            break  # Solo procesamos el mensaje más reciente

                    if not new_messages:
                        st.warning(
                            "No se recibió respuesta del asistente. Por favor, intenta de nuevo."
                        )
                except Exception as e:
                    logging.error(f"Error recuperando mensajes: {str(e)}")
                    st.error(f"Error al recuperar la respuesta: {str(e)}")
            else:
                st.error(
                    f"La solicitud no se completó correctamente. Estado: {run.status}"
                )
                if hasattr(run, "last_error") and run.last_error:
                    st.error(f"Error: {run.last_error}")
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
elif prompt and not (st.session_state.thread_id and client and assistant_id):
    # Mensaje informativo si faltan componentes necesarios
    st.warning(
        "No se puede enviar el mensaje hasta que se complete la configuración y se inicialice el portal de comunicación."
    )

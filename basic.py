import os
import streamlit as st
import time
import requests
import logging
import traceback
from datetime import datetime
from openai import OpenAI

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - celeste-basic - %(levelname)s - %(message)s",
)

# Versión de la aplicación
APP_VERSION = "1.0.0"

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Celeste ✨ Básico",
    page_icon="✨",
    layout="wide",
    menu_items={
        "Get Help": "https://marduk.pro",
        "Report a bug": None,
        "About": "Celeste Básico: Versión ligera de tu guía emocional para la resiliencia y manifestación.",
    },
)


# Función para manejar errores básicos
def handle_error(func):
    """Decorador simple para manejar errores en funciones críticas"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error en {func.__name__}: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            st.error(error_msg)
            return None

    return wrapper


# Función para verificar si estamos en entorno cloud o local
def is_streamlit_cloud():
    """Detecta si la aplicación se está ejecutando en Streamlit Cloud"""
    return (
        os.environ.get("STREAMLIT_SHARING_MODE") is not None
        or os.environ.get("STREAMLIT_SERVER_BASE_URL_IS_SET") is not None
        or os.environ.get("IS_STREAMLIT_CLOUD") == "true"
        or os.path.exists("/.streamlit/config.toml")
    )


# Función para procesar mensajes del asistente
@handle_error
def process_message_with_citations(message):
    """Extrae y devuelve solo el texto del mensaje del asistente."""
    if hasattr(message, "content") and len(message.content) > 0:
        message_content = message.content[0]
        if hasattr(message_content, "text"):
            nested_text = message_content.text
            if hasattr(nested_text, "value"):
                return nested_text.value
            return str(nested_text)
        return str(message_content)
    return "No se pudo procesar el mensaje"


# Función para crear cliente OpenAI compatible con v2
@handle_error
def create_openai_client(api_key):
    """Crea un cliente OpenAI con encabezados compatibles con Assistants API v2"""
    client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})
    logging.info("Cliente OpenAI inicializado correctamente")
    return client


# Función para inicializar un thread
@handle_error
def initialize_thread(client):
    """Inicializa un nuevo thread de conversación"""
    thread = client.beta.threads.create()
    thread_id = thread.id
    logging.info(f"Thread creado: {thread_id}")
    return thread_id


# Función para enviar mensaje y obtener respuesta
@handle_error
def send_message_and_get_response(client, thread_id, assistant_id, prompt):
    """Envía un mensaje al asistente y obtiene su respuesta"""
    # Enviar mensaje del usuario
    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=prompt
    )

    # Crear una ejecución para el hilo de chat
    run = client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=assistant_id
    )

    # Esperar a que se complete la ejecución
    while run.status not in ["completed", "failed", "cancelled", "expired"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run.status == "failed":
            error_msg = (
                f"Error en la ejecución: {getattr(run, 'last_error', 'Desconocido')}"
            )
            logging.error(error_msg)
            st.error(error_msg)
            return None

    # Recuperar mensajes agregados por el asistente si la ejecución fue exitosa
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Buscar el mensaje más reciente del asistente
        for message in messages.data:
            if message.role == "assistant" and not any(
                msg["role"] == "assistant" and msg.get("id") == message.id
                for msg in st.session_state.messages
            ):
                full_response = process_message_with_citations(message)
                return {
                    "role": "assistant",
                    "content": full_response,
                    "id": message.id,
                }

    return None


# ----- INICIALIZACIÓN DE INTERFAZ -----

# Título y presentación
st.title("Celeste ✨ Versión Básica")

# Barra lateral para configuración
with st.sidebar:
    st.title("✨ Configuración ✨")

    # Obtener API Key
    api_key = None
    # 1. Intentar obtener de variables de entorno
    api_key = os.environ.get("OPENAI_API_KEY")

    # 2. Intentar obtener de secrets.toml
    if not api_key and hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

    # 3. Solicitar al usuario
    if not api_key:
        api_key = st.text_input("API Key de OpenAI", type="password")

    # Obtener Assistant ID
    assistant_id = None
    # 1. Intentar obtener de variables de entorno
    assistant_id = os.environ.get("ASSISTANT_ID")

    # 2. Intentar obtener de secrets.toml
    if not assistant_id and hasattr(st, "secrets") and "ASSISTANT_ID" in st.secrets:
        assistant_id = st.secrets["ASSISTANT_ID"]

    # 3. Solicitar al usuario
    if not assistant_id:
        assistant_id = st.text_input("ID del Asistente", type="password")

    # Verificar configuración
    if api_key and assistant_id:
        st.success("✅ Configuración completa")
    else:
        missing = []
        if not api_key:
            missing.append("API Key")
        if not assistant_id:
            missing.append("ID del Asistente")

        st.warning(f"⚠️ Falta configurar: {', '.join(missing)}")

    # Mostrar entorno
    env_type = "Streamlit Cloud" if is_streamlit_cloud() else "Local"
    st.info(f"Entorno detectado: {env_type}")

    # Añadir créditos
    st.markdown("---")
    st.subheader("Creado por:")
    st.markdown("Alexander Oviedo Fadul")
    st.markdown(
        "[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev/) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)"
    )

# Detener si no tenemos la configuración completa
if not api_key or not assistant_id:
    st.markdown(
        """
        ## ⚙️ Configuración necesaria
        
        Por favor, completa la configuración en la barra lateral para usar Celeste:
        
        1. **API Key de OpenAI**: Necesaria para conectar con el servicio
        2. **ID del Asistente**: Identifica el asistente de OpenAI a utilizar
        
        Una vez configurado, podrás interactuar con Celeste.
        """
    )
    st.stop()

# ----- INICIALIZACIÓN DE ESTADO -----

# Inicializar variables de estado
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Crear cliente OpenAI
client = create_openai_client(api_key)

# Inicializar thread si no existe
if not st.session_state.thread_id and client:
    with st.spinner("Inicializando conversación..."):
        thread_id = initialize_thread(client)
        if thread_id:
            st.session_state.thread_id = thread_id
            st.success("✨ Portal de comunicación inicializado ✨")

# ----- INTERFAZ DE CHAT -----

# Mostrar introducción si no hay mensajes
if not st.session_state.messages:
    st.markdown(
        """
        ### ✨ ¡Hola! Soy Celeste, tu guía emocional y práctica
        
        Estoy aquí para apoyarte en tu camino de:
        
        * 🌟 Desarrollar tu resiliencia
        * 🌈 Manifestar tus sueños y deseos
        * 🧠 Transformar patrones limitantes
        * 💫 Cultivar una mentalidad positiva
        * 🌱 Vivir una vida plena y auténtica
        
        **¿En qué puedo ayudarte hoy?** Comparte tus inquietudes o metas, y exploremos juntos cómo puedes avanzar en tu camino.
        """
    )

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input y procesamiento
if prompt := st.chat_input("¿Cómo puedo ayudarte hoy?"):
    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Procesar mensaje y obtener respuesta
    with st.spinner("Canalizando energías celestiales..."):
        if st.session_state.thread_id and client and assistant_id:
            response = send_message_and_get_response(
                client, st.session_state.thread_id, assistant_id, prompt
            )

            if response:
                # Añadir respuesta al historial
                st.session_state.messages.append(response)
                with st.chat_message("assistant"):
                    st.markdown(response["content"])
            else:
                st.error("No se pudo obtener respuesta. Por favor, intenta de nuevo.")
        else:
            st.error("Error: Conversación no inicializada correctamente.")

# ----- FOOTER -----

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #666666; font-size: 0.8rem;">
        <p>Celeste Básico v{APP_VERSION} | {datetime.now().strftime('%Y-%m-%d')}</p>
        <p>Las interacciones son procesadas a través de OpenAI.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

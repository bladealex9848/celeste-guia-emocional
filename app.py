# Importación de bibliotecas necesarias
import os
import openai
import streamlit as st
import time

# Configuración de la página de Streamlit para Asistente Virtual
# Configuración de la página
st.set_page_config(
    page_title="Celeste",
    page_icon="✨",
    layout="wide",
    menu_items={
        'Get Help': 'https://marduk.pro',
        'Report a bug': None,
        'About': "Celeste: Tu guía emocional y práctica para cultivar la resiliencia y manifestar tus sueños."
    }
)

# Función para verificar si el archivo secrets.toml existe
def secrets_file_exists():
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    return os.path.isfile(secrets_path)

# Intentar obtener el ID del asistente de OpenAI desde st.secrets si el archivo secrets.toml existe
if secrets_file_exists():
    try:
        ASSISTANT_ID = st.secrets['ASSISTANT_ID']
    except KeyError:
        ASSISTANT_ID = None
else:
    ASSISTANT_ID = None

# Si no está disponible, pedir al usuario que lo introduzca
if not ASSISTANT_ID:
    ASSISTANT_ID = st.sidebar.text_input('Introduce el ID del asistente de OpenAI', type='password')

# Si aún no se proporciona el ID, mostrar un error y detener la ejecución
if not ASSISTANT_ID:
    st.sidebar.error("Por favor, proporciona el ID del asistente de OpenAI.")
    st.stop()

assistant_id = ASSISTANT_ID

# Inicialización del cliente de OpenAI
client = openai

# Presentación de Celeste
st.title("¡Bienvenida/o a Celeste! ✨")

st.markdown("""
### ✨ ¡Hola! Soy Celeste, tu guía emocional y práctica para cultivar la resiliencia y manifestar tus sueños

Estoy aquí para acompañarte en tu viaje de autodescubrimiento y empoderamiento. Basada en los principios de la resiliencia y el arte de la manifestación, te ofreceré apoyo emocional y guía práctica para superar adversidades, manejar el estrés, cultivar una mentalidad positiva y vivir una vida plena y auténtica.

#### ¿En qué puedo ayudarte hoy? 🤔

- Comprender y desarrollar tu resiliencia: Aprenderás a identificar y superar tus límites, transformar la resistencia en oportunidades de crecimiento y manejar el estrés de manera efectiva.
- Manifestar tus sueños: Te guiaré para establecer intenciones claras, visualizar tus deseos y tomar acciones concretas para alcanzar tus metas.
- Cultivar una mentalidad positiva: Te ayudaré a reprogramar tus creencias limitantes, superar el autosabotaje y desarrollar una mayor confianza en ti mismo/a.
- Encontrar paz interior y bienestar emocional: Aprenderás técnicas de relajación, meditación y atención plena para calmar tu mente y conectarte con tu esencia más elevada.
- Vivir una vida plena y auténtica: Te acompañaré en tu viaje de autodescubrimiento para que puedas vivir de acuerdo con tus valores y propósito.

**No dudes en compartir tus inquietudes, sueños y metas conmigo. ¡Estoy aquí para apoyarte en cada paso del camino!**

*Recuerda: Soy una guía emocional y práctica, no un sustituto de un profesional de la salud mental. Si estás experimentando dificultades emocionales o psicológicas significativas, te recomiendo buscar ayuda profesional.*
""")

# Inicialización de variables de estado de sesión
st.session_state.start_chat = True
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Cargar la clave API de OpenAI
API_KEY = os.environ.get('OPENAI_API_KEY') or st.secrets.get('OPENAI_API_KEY')
if not API_KEY:
    API_KEY = st.sidebar.text_input('Introduce tu clave API de OpenAI', type='password')

if not API_KEY:
    st.sidebar.error("Por favor, proporciona una clave API para continuar.")
    st.stop()

openai.api_key = API_KEY

def process_message_with_citations(message):
    """Extraiga y devuelva solo el texto del mensaje del asistente."""
    if hasattr(message, 'content') and len(message.content) > 0:
        message_content = message.content[0]
        if hasattr(message_content, 'text'):
            nested_text = message_content.text
            if hasattr(nested_text, 'value'):
                return nested_text.value
    return 'No se pudo procesar el mensaje'

# Crear un hilo de chat inmediatamente después de cargar la clave API
if not st.session_state.thread_id:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.write("ID del hilo: ", thread.id)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Cómo puedo ayudarte hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("usuario"):
        st.markdown(prompt)

    # Enviar mensaje del usuario
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Crear una ejecución para el hilo de chat
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )

    while run.status != 'completed':
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

    # Recuperar mensajes agregados por el asistente
    messages = client.beta.threads.messages.list(
    thread_id=st.session_state.thread_id
    )

    # Procesar y mostrar mensajes del asistente
    for message in messages:
        if message.run_id == run.id and message.role == "assistant":
            full_response = process_message_with_citations(message)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            with st.chat_message("assistant"):
                st.markdown(full_response)
                
# Footer
st.sidebar.markdown('---')
st.sidebar.subheader('Creado por:')
st.sidebar.markdown('Alexander Oviedo Fadul')
st.sidebar.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev/) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")
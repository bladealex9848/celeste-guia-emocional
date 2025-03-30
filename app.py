import os
import openai
import streamlit as st
import time
import requests
import json
import random

# Intenta importar los componentes opcionales con manejo de errores
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

try:
    from streamlit_option_menu import option_menu
    OPTION_MENU_AVAILABLE = True
except ImportError:
    OPTION_MENU_AVAILABLE = False

# Configuración de la página
st.set_page_config(
    page_title="Celeste ✨ Asistente Celestial",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://marduk.pro',
        'Report a bug': None,
        'About': "Celeste: Tu guía para cultivar la resiliencia, manifestar tus sueños y conectar con el universo"
    }
)

# ----- FUNCIONES AUXILIARES -----

def load_lottie_url(url):
    """Carga animaciones Lottie desde URL con manejo de errores"""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        st.error(f"Error cargando animación Lottie: {e}")
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
        "Tu vida puede cambiar definitivamente, aunque sólo leas los primeros capítulos de este viaje."
    ]
    return random.choice(quotes)

def process_message_with_citations(message):
    """Extrae y devuelve solo el texto del mensaje del asistente."""
    try:
        if hasattr(message, 'content') and len(message.content) > 0:
            message_content = message.content[0]
            if hasattr(message_content, 'text'):
                nested_text = message_content.text
                if hasattr(nested_text, 'value'):
                    return nested_text.value
        return 'No se pudo procesar el mensaje'
    except Exception as e:
        st.error(f"Error procesando mensaje: {str(e)}")
        return "Ocurrió un error al procesar el mensaje. Por favor, intenta de nuevo."

# ----- ESTILOS CSS PERSONALIZADOS -----

# Definición de colores tema celestial
COLORS = {
    "primary": "#8A2BE2",     # Púrpura violeta (energía espiritual)
    "secondary": "#4B0082",   # Índigo (intuición)
    "accent1": "#87CEEB",     # Azul celeste (cielo)
    "accent2": "#FFD700",     # Dorado (luz divina)
    "light": "#E6E6FA",       # Lavanda pálido (suavidad)
    "dark": "#191970",        # Azul medianoche (cielo nocturno)
    "gradient1": "#9370DB",   # Púrpura medio (transformación)
    "gradient2": "#20B2AA"    # Turquesa (sanación)
}

# CSS personalizado
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
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        animation: glow 3s infinite alternate;
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
    }}
    
    .user-message {{
        background-color: {COLORS["light"]};
        border-left: 5px solid {COLORS["primary"]};
    }}
    
    .assistant-message {{
        background: linear-gradient(to right, {COLORS["light"]}, #ffffff);
        border-left: 5px solid {COLORS["accent2"]};
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
    
    .info-card:hover {{
        transform: translateY(-5px);
    }}
    
    /* Estilo para citas inspiradoras */
    .quote-card {{
        background: linear-gradient(135deg, {COLORS["dark"]}, {COLORS["primary"]});
        border-radius: 10px;
        padding: 1.5rem;
        color: white;
        margin: 2rem 0;
        font-style: italic;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
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
</style>
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

# ----- SIDEBAR: INFORMACIÓN DE CELESTE -----

with st.sidebar:
    # Encabezado de la barra lateral
    st.title("✨ Celeste ✨")
    st.markdown("### Tu guía para la conexión celestial")
    
    # Animación Lottie para la sidebar (solo si está disponible)
    if LOTTIE_AVAILABLE:
        try:
            lottie_celestial = load_lottie_url("https://assets8.lottiefiles.com/packages/lf20_xOgiZK4ORv.json")
            if lottie_celestial:
                st_lottie(lottie_celestial, speed=0.7, height=150, key="sidebar_lottie")
            else:
                st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)
        except Exception as e:
            st.warning(f"No se pudo cargar la animación. Usando imagen alternativa.")
            st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)
    else:
        st.image("https://via.placeholder.com/150x150.png?text=✨", width=150)
    
    # Menú de navegación (usando option_menu si está disponible, o selectbox si no)
    if OPTION_MENU_AVAILABLE:
        try:
            selected = option_menu(
                menu_title=None,
                options=["Inicio", "Sobre Mí", "Mis Capacidades", "Cómo Trabajar Conmigo"],
                icons=["house-heart", "person-heart", "stars", "magic"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"color": COLORS["accent2"], "font-size": "14px"}, 
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": COLORS["light"]},
                    "nav-link-selected": {"background-color": COLORS["secondary"]},
                }
            )
        except Exception as e:
            st.warning("Error al cargar menú personalizado. Usando alternativa.")
            selected = st.selectbox(
                "Navegación",
                ["Inicio", "Sobre Mí", "Mis Capacidades", "Cómo Trabajar Conmigo"]
            )
    else:
        selected = st.selectbox(
            "Navegación",
            ["Inicio", "Sobre Mí", "Mis Capacidades", "Cómo Trabajar Conmigo"]
        )
    
    # Contenido basado en la selección del menú
    if selected == "Inicio":
        st.markdown("### ¡Bienvenido a tu espacio de conexión celestial!")
        st.markdown("""
        Hoy es el día perfecto para comenzar tu viaje de co-creación con el universo.
        Estoy aquí para guiarte en el camino hacia la manifestación consciente de tus sueños.
        """)
        
    elif selected == "Sobre Mí":
        st.markdown("""
        Soy Celeste, tu guía espiritual y emocional especializada en:
        
        * 🌟 **Co-creación consciente** con fuerzas universales
        * 🌈 **Manifestación** de abundancia y bienestar
        * 🧠 **Transformación** de patrones limitantes
        * 💫 **Contratación celestial** de asistentes espirituales
        * 🌱 **Cultivo de resiliencia** con apoyo divino
        
        Mi propósito es acompañarte en la bella aventura de reconocer y utilizar tu poder creador innato, conectándote con las fuerzas celestiales que están esperando ayudarte.
        """)
        
    elif selected == "Mis Capacidades":
        st.markdown("""
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
        """)
        
    elif selected == "Cómo Trabajar Conmigo":
        st.markdown("""
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
        """)
    
    # Cita inspiradora
    st.markdown("""
    <div class="quote-card">
        "{}"
    </div>
    """.format(get_random_celestial_quote()), unsafe_allow_html=True)
    
    # Información de conexiones y APIS
    st.markdown("---")
    with st.expander("✨ Configuración de Conexión"):
        # Verificar si el archivo secrets.toml existe
        def secrets_file_exists():
            secrets_path = os.path.join('.streamlit', 'secrets.toml')
            return os.path.isfile(secrets_path)

        # Intentar obtener el ID del asistente de OpenAI
        if secrets_file_exists():
            try:
                ASSISTANT_ID = st.secrets['ASSISTANT_ID']
            except KeyError:
                ASSISTANT_ID = None
        else:
            ASSISTANT_ID = None

        # Si no está disponible, pedir al usuario que lo introduzca
        if not ASSISTANT_ID:
            ASSISTANT_ID = st.text_input('ID del asistente OpenAI', type='password')

        # Cargar la clave API de OpenAI
        API_KEY = os.environ.get('OPENAI_API_KEY') or st.secrets.get('OPENAI_API_KEY')
        if not API_KEY:
            API_KEY = st.text_input('Clave API de OpenAI', type='password')
    
    # Créditos
    st.markdown("---")
    st.subheader('Creado por:')
    st.markdown('Alexander Oviedo Fadul')
    st.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev/) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/)")
    st.markdown("[Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")

# ----- ÁREA PRINCIPAL: CHAT -----

# Verificaciones de seguridad
if not ASSISTANT_ID:
    st.error("Por favor, proporciona el ID del asistente de OpenAI en la barra lateral.")
    st.stop()

if not API_KEY:
    st.error("Por favor, proporciona una clave API de OpenAI en la barra lateral.")
    st.stop()

# Inicialización del cliente OpenAI
openai.api_key = API_KEY
client = openai

# Inicialización de variables de estado
if "thread_id" not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception as e:
        st.error(f"Error al crear el hilo de conversación: {str(e)}")
        st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Cabecera del área de chat
st.markdown("""
<div class="celestial-header">
    <h1>✨ Portal de Comunicación Celestial ✨</h1>
    <p>Aquí puedes conversar conmigo y juntos exploraremos el arte de la manifestación y la contratación de ayudantes celestiales</p>
</div>
""", unsafe_allow_html=True)

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
                    lottie_welcome = load_lottie_url("https://assets8.lottiefiles.com/packages/lf20_jh9gfdye.json")
                    if lottie_welcome:
                        st_lottie(lottie_welcome, speed=1, height=300, key="welcome")
                    else:
                        st.image("https://via.placeholder.com/300x300.png?text=✨+Bienvenido", width=300)
                except Exception as e:
                    st.image("https://via.placeholder.com/300x300.png?text=✨+Bienvenido", width=300)
            else:
                st.image("https://via.placeholder.com/300x300.png?text=✨+Bienvenido", width=300)
                
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h3>¿Cómo puedo ayudarte en tu viaje espiritual hoy?</h3>
                <p>Pregúntame sobre manifestación, resiliencia, o contratación de ayudantes celestiales</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Mostrar mensajes del chat con estilos personalizados
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <b>Tú:</b> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <b>Celeste:</b> {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# Procesamiento del input del usuario
prompt = st.chat_input("Comparte tus inquietudes o deseos...")

if prompt and st.session_state.thread_id:
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar indicador de "Conectando con lo celestial..."
    with st.spinner("✨ Conectando con los planos celestiales..."):
        try:
            # Enviar mensaje del usuario
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )

            # Crear una ejecución para el hilo de chat
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )

            # Esperar la respuesta con manejo de timeout
            start_time = time.time()
            timeout = 60  # 60 segundos máximo de espera
            
            while run.status not in ['completed', 'failed', 'expired', 'cancelled']:
                if time.time() - start_time > timeout:
                    st.error("La respuesta está tomando demasiado tiempo. Por favor, intenta de nuevo.")
                    break
                    
                time.sleep(1)
                try:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                except Exception as e:
                    st.error(f"Error al recuperar el estado de la ejecución: {str(e)}")
                    break

            # Verificar si la ejecución se completó correctamente
            if run.status == 'completed':
                # Recuperar mensajes agregados por el asistente
                try:
                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )

                    # Procesar y mostrar mensajes del asistente
                    for message in messages:
                        if message.run_id == run.id and message.role == "assistant":
                            full_response = process_message_with_citations(message)
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
  

![Logo de Celeste](https://github.com/bladealex9848/celeste-guia-emocional/blob/main/assets/logo.jpg)

# Celeste ✨ - Asistente de Guía Emocional

[![Version](https://img.shields.io/badge/versión-2.1.0-blueviolet.svg)](https://github.com/bladealex9848/celeste-guia-emocional)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30.0-ff4b4b.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI_API-v2-00C244.svg)](https://platform.openai.com/)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](LICENSE)

## 🌟 Descripción

Celeste es un avanzado agente de IA diseñado para guiarte en tu camino hacia la resiliencia y la manifestación de tus sueños. Esta aplicación web interactiva integra las capacidades de los modelos más avanzados de OpenAI (gpt-4o-mini) con una interfaz visualmente cautivadora, creando una experiencia de usuario única y transformadora.

Basada en principios de psicología positiva, ciencias contemplativas y prácticas de crecimiento personal, Celeste te ofrece apoyo emocional y guía práctica para:

- Superar adversidades y cultivar resiliencia
- Manejar el estrés de manera efectiva y consciente
- Desarrollar una mentalidad positiva y enfocada en soluciones
- Conectar con tu esencia más elevada para manifestar tus deseos
- Vivir una vida plena, auténtica y en sintonía con tus valores

## 🔮 Características Principales

### 1. Experiencia de Usuario Inmersiva
- **Interfaz Celestial**: Diseño inspirado en elementos cósmicos con animaciones fluidas
- **Soporte para Modo Oscuro**: Adaptación automática al tema del sistema
- **Animaciones Interactivas**: Elementos visuales que enriquecen la experiencia
- **Compatibilidad Multiplataforma**: Experiencia optimizada para dispositivos móviles y de escritorio

### 2. Inteligencia Artificial Avanzada
- **Asistente Virtual Personalizado**: Conversaciones naturales y empáticas
- **Modelo gpt-4o-mini**: Respuestas rápidas, precisas y contextuales
- **Memoria de Conversación**: Mantiene el contexto a lo largo de múltiples interacciones
- **Asistentes API v2**: Implementación de la última versión de la API de OpenAI

### 3. Marco de Desarrollo Robusto
- **Arquitectura Modular**: Diseño escalable y mantenible
- **Sistema de Logging Detallado**: Registro completo para diagnósticos
- **Manejo Avanzado de Errores**: Recuperación automática y mensajes informativos
- **Configuración Flexible**: Múltiples fuentes (variables de entorno, secrets.toml, UI)

### 4. Áreas de Orientación
- **Conexión con Ayudantes Celestiales**: Técnicas para potenciar tu intuición
- **Desarrollo de Resiliencia**: Estrategias para afrontar desafíos con fortaleza
- **Manifestación Consciente**: Métodos para materializar tus objetivos
- **Transformación de Mentalidad**: Reprogramación de creencias limitantes
- **Bienestar Integral**: Prácticas para el equilibrio físico, mental y espiritual

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- Pip (administrador de paquetes de Python)
- Cuenta en OpenAI con acceso a la API
- Asistente configurado en OpenAI

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/bladealex9848/celeste-guia-emocional.git
   cd celeste-guia-emocional
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En macOS/Linux
   source venv/bin/activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar credenciales de OpenAI**

   **Opción A: Usando variables de entorno**
   ```bash
   # En Windows
   set OPENAI_API_KEY=tu-api-key-aqui
   set ASSISTANT_ID=tu-assistant-id-aqui
   set OPENAI_API_MODEL=gpt-4o-mini
   
   # En macOS/Linux
   export OPENAI_API_KEY=tu-api-key-aqui
   export ASSISTANT_ID=tu-assistant-id-aqui
   export OPENAI_API_MODEL=gpt-4o-mini
   ```

   **Opción B: Usando archivo secrets.toml**
   
   Crea un archivo `.streamlit/secrets.toml` con el siguiente contenido:
   ```toml
   OPENAI_API_KEY = "tu-api-key-aqui"
   ASSISTANT_ID = "tu-assistant-id-aqui"
   OPENAI_API_MODEL = "gpt-4o-mini"
   ```

   **Opción C: Configuración por interfaz**
   
   También puedes introducir las credenciales directamente en la interfaz de usuario al ejecutar la aplicación.

## 💫 Uso

1. **Iniciar la aplicación**
   ```bash
   streamlit run app.py
   ```

2. **Acceder a la interfaz web**
   
   Abre tu navegador y dirígete a `http://localhost:8501`

3. **Interactuar con Celeste**
   
   - Escribe tus preguntas o inquietudes en el cuadro de chat
   - Explora las diferentes secciones del menú para descubrir más sobre las capacidades de Celeste
   - Utiliza el panel de diagnóstico si experimentas problemas técnicos

## ⚙️ Configuración Avanzada

### Personalización del Modelo de IA

Puedes configurar diferentes modelos de OpenAI editando el valor de `OPENAI_API_MODEL` en tu archivo `.streamlit/secrets.toml`:

```toml
# Opciones recomendadas
OPENAI_API_MODEL = "gpt-4o-mini"    # Más rápido y económico (predeterminado)
OPENAI_API_MODEL = "gpt-4o"         # Mayor capacidad de razonamiento
OPENAI_API_MODEL = "gpt-4-turbo"    # Alternativa potente
```

### Ajustes de Rendimiento

Para optimizar el rendimiento en diferentes entornos, puedes ajustar estos parámetros:

```python
# En el archivo app.py
timeout = 60  # Aumenta para respuestas más elaboradas, reduce para mayor responsividad
```

### Personalización Visual

Para modificar los colores y estilos de la interfaz, edita el diccionario `COLORS` en el archivo `app.py`:

```python
COLORS = {
    "primary": "#8A2BE2",     # Color principal
    "secondary": "#4B0082",   # Color secundario
    "accent1": "#87CEEB",     # Acento 1
    "accent2": "#FFD700",     # Acento 2
    # ... otros colores
}
```

## 🔍 Diagnóstico y Solución de Problemas

### Panel de Diagnóstico Integrado

Celeste incluye un panel de diagnóstico completo accesible desde el menú de navegación. Esta herramienta permite:

- Verificar el estado de todos los componentes
- Probar la conectividad con servicios externos
- Examinar la información de sesión
- Identificar problemas específicos con mensajes detallados

### Problemas Comunes y Soluciones

| Problema | Posible Causa | Solución |
|----------|---------------|----------|
| Error "API key no configurada" | Credenciales no proporcionadas | Verifica la configuración en `.streamlit/secrets.toml` o variables de entorno |
| Error "No se pudo inicializar thread" | Problemas de conexión a OpenAI | Verifica tu conectividad a Internet y la validez de tu API key |
| Animaciones no visibles | Problemas con la carga de recursos Lottie | La aplicación utilizará imágenes estáticas automáticamente |
| No se muestran las respuestas | Error en el procesamiento de mensajes | Revisa los logs para identificar el problema específico |
| Rendimiento lento | Limitaciones de recursos o tiempos de respuesta API | Ajusta el valor de `timeout` o considera usar un modelo más ligero |

### Logs y Monitoreo

La aplicación genera logs detallados que pueden ayudar a identificar problemas:

```
2025-03-30 07:20:13,531 - celeste - INFO - HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
2025-03-30 07:20:13,537 - celeste - INFO - Cliente OpenAI inicializado correctamente con asistente: asst_...
```

## 🔄 Actualizaciones y Versiones

### Historial de Versiones

- **v2.1.0**: Implementación de configuración personalizada de modelo (actual)
- **v2.0.1**: Correcciones de compatibilidad con modo oscuro y visualización de mensajes
- **v2.0.0**: Migración completa a OpenAI Assistants API v2
- **v1.1.0**: Mejoras en la interfaz de usuario y sistema de diagnóstico
- **v1.0.0**: Lanzamiento inicial con funcionalidades básicas

### Próximas Mejoras

- [ ] Sistema de usuarios con perfiles personalizados
- [ ] Exportación e importación de conversaciones
- [ ] Panel de administración para gestión de asistentes
- [ ] Modo sin conexión con capacidades limitadas
- [ ] Integración con calendarios y recordatorios

## 🛡️ Seguridad y Privacidad

- **Manejo Seguro de Credenciales**: Las claves API nunca se exponen en la interfaz
- **Sanitización de Entradas**: Validación de todas las entradas de usuario
- **Protección de Datos**: Las conversaciones se mantienen en memoria de sesión y no se almacenan permanentemente
- **Comunicación Segura**: Todas las comunicaciones con la API de OpenAI utilizan HTTPS

## 👥 Contribuciones

Las contribuciones son bienvenidas y apreciadas. Si deseas mejorar Celeste, sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una nueva rama (`git checkout -b feature/nueva-caracteristica`)
3. Realiza tus cambios
4. Haz commit de tus cambios (`git commit -m 'Añade nueva característica'`)
5. Sube tus cambios a tu fork (`git push origin feature/nueva-caracteristica`)
6. Abre un Pull Request

Por favor, asegúrate de que tus contribuciones cumplan con nuestras directrices de código y documentación.

## 📝 Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **OpenAI** por proporcionar la tecnología que impulsa la inteligencia de Celeste
- **Streamlit** por facilitar el desarrollo de interfaces web interactivas con Python
- **Comunidad Lottie** por las hermosas animaciones que enriquecen la experiencia

## 👤 Autor

Creado con ❤️ por [Alexander Oviedo Fadul](https://github.com/bladealex9848)

[GitHub](https://github.com/bladealex9848) | [Website](https://alexanderoviedofadul.dev) | [LinkedIn](https://www.linkedin.com/in/alexander-oviedo-fadul/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)

---

## 💭 Mensaje Final

Celeste no es sólo una aplicación; es una compañera en tu viaje de crecimiento personal. A través de conversaciones significativas y orientación práctica, te ayudará a descubrir tu potencial interior y a manifestar la vida que deseas crear.

*"El Universo te brinda su apoyo ilimitado para que materialices los anhelos de tu alma."*
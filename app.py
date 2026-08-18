import os
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Tutor AO II", page_icon="⚙️", layout="centered")

SYSTEM_INSTRUCTION = """
Eres un tutor universitario de Administración de Operaciones 2.
Tu enfoque es amable, directo, riguroso y pedagógico.

Materias y bibliografía clave: Chase & Aquilano, Pronósticos (Hanke & Reitsch), MRP, Planeación Agregada, Secuenciación y Líneas de Espera.

Reglas:
1. Resuelve ejercicios numéricos paso a paso con variables claras y fórmulas en LaTeX ($...$ o $$...$$).
2. Genera tablas de programación o matrices MRP en Markdown limpio.
3. Si el usuario sube una imagen o PDF de un ejercicio, lee los datos con precisión antes de calcular.
"""

# Configuración de clave API
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if not api_key:
    st.info("Configura tu API Key en los secrets de Streamlit o ingrésala en la barra lateral para empezar.")
    st.stop()

client = genai.Client(api_key=api_key)

st.title("⚙️ Tutor de Administración de Operaciones II")
st.caption("Asistente para ejercicios de producción, pronósticos, MRP e inventarios.")

# Barra lateral para archivos adjuntos del alumno
with st.sidebar:
    st.header("📄 Adjuntar Ejercicio")
    uploaded_file = st.file_uploader("Sube foto o PDF del problema:", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file and uploaded_file.type.startswith("image/"):
        st.image(uploaded_file, caption="Vista previa", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("attachment_info"):
            st.caption(f"📎 *Archivo: {msg['attachment_info']}*")
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu duda o pega un enunciado..."):
    user_parts = []
    att_name = None
    if uploaded_file:
        user_parts.append(types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type=uploaded_file.type))
        att_name = uploaded_file.name
    
    user_parts.append(types.Part.from_text(text=prompt))
    st.session_state.messages.append({"role": "user", "content": prompt, "attachment_info": att_name, "parts": user_parts})

    with st.chat_message("user"):
        if att_name:
            st.caption(f"📎 *Archivo: {att_name}*")
        st.markdown(prompt)

    contents = [
        types.Content(role="user" if m["role"] == "user" else "model", parts=m.get("parts", [types.Part.from_text(text=m["content"])]))
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Resolviendo..."):
            res = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
            )
            st.markdown(res.text)
            st.session_state.messages.append({"role": "assistant", "content": res.text, "parts": [types.Part.from_text(text=res.text)]})

import streamlit as st
import sys
import os
import json
# import speech_recognition as sr # Removed for Cloud Native

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Force reload comment - Attempt 8 (GIS Fix)

from src.agents.super_agents import SuperAgent
from src.database.weaviate_client import weaviate_manager

st.set_page_config(
    page_title="Sanjeevani Plant Assistant",
    page_icon="🌿",
    layout="wide"
)

# Legacy voice function removed

# --- Initialization ---
@st.cache_resource
def init_system():
    # Force reload of agents to ensure latest code is used
    import importlib
    import src.agents.gis_agent
    import src.agents.super_agents
    importlib.reload(src.agents.gis_agent)
    importlib.reload(src.agents.super_agents)
    
    if not weaviate_manager.connect():
        st.error("❌ Could not connect to Weaviate")
        return None
    if not weaviate_manager.create_collections():
        st.error("❌ Could not create collections")
        return None
    return SuperAgent()

def get_debug_plants():
    """Fetch 10 random plants from GIS collection for verification."""
    try:
        from src.config.settings import settings
        
        # Ensure connection exists
        if not weaviate_manager.client:
            weaviate_manager.connect()
            
        collection = weaviate_manager.client.collections.get(settings.GIS_LOCATION_COLLECTION)
        # Fetch a small batch of districts
        response = collection.query.fetch_objects(limit=5)
        
        # Extract unique plant names from all fetched districts
        all_plants = set()
        for obj in response.objects:
            district_plants = obj.properties.get('plants', [])
            if district_plants:
                all_plants.update(district_plants)
                
        # Return top 10 unique plants
        return list(all_plants)[:10]
    except Exception as e:
        return [f"Error: {e}"]

# --- Pages ---
def login_page():
    st.title("🌿 Sanjeevani Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        submitted = st.form_submit_button("Login")
        if submitted and username:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.rerun()

def chat_page(agent):
    st.sidebar.title(f"👤 {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["messages"] = []
        st.rerun()
        
    if st.sidebar.button("Reset Agent"):
        st.session_state["messages"] = []
        st.rerun()

    # Debug Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ Database Check")
    if st.sidebar.button("Load Sample Plants"):
        plants = get_debug_plants()
        st.sidebar.write(plants)

    st.title("🌿 Sanjeevani Plant Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If message has extra data (image), display it
            if message.get("image_url"):
                st.image(message["image_url"], caption="Plant Image", width=300)

    # Input Area
    # Mic button in sidebar to keep chat input static at bottom
    # Input Area
    # Microphone Input (Cloud Native)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎤 Voice Input")
    
    # New Streamlit Audio Input Widget (Requires streamlit>=1.40.0)
    audio_value = st.sidebar.audio_input("Record Voice Note")
    
    if "last_audio_id" not in st.session_state:
        st.session_state.last_audio_id = None

    if audio_value:
        # Use file ID (if available) or hash of first 100 bytes + size to deduplicate
        # Streamlit UploadedFile has .id in recent versions, or just use object identity if persistent
        # A robust way is to read a bit and check
        audio_id = f"{audio_value.size}_{audio_value.name}"
        
        if audio_id != st.session_state.last_audio_id:
            st.session_state.last_audio_id = audio_id
            
            # Transcribe
            with st.spinner("Transcribing with Groq..."):
                from src.tools.audio_utils import transcribe_audio
                # Read bytes (we need to reset pointer if we read before?)
                # But audio_value is fresh here
                voice_bytes = audio_value.read()
                voice_text = transcribe_audio(voice_bytes)
                
            if voice_text:
                # We treat this exactly like text input
                st.session_state.messages.append({"role": "user", "content": voice_text})
                with st.chat_message("user"):
                    st.markdown(voice_text)
                
                # Trigger processing
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = agent.query(voice_text, session_id=st.session_state["username"])
                            
                            # 1. Answer
                            answer_text = response.get("answer", "No answer.")
                            st.markdown(answer_text)
                            
                            # 2. Image Display
                            img_url = response.get("image_url")
                            if img_url:
                                st.image(img_url, caption="Plant Image", width=300)

                            # 3. Map Display
                            locations = response.get("locations", [])
                            if locations:
                                with st.spinner("Generating Map..."):
                                    import src.tools.map_utils as map_utils
                                    import importlib
                                    importlib.reload(map_utils)
                                    fig = map_utils.generate_karnataka_map(locations)
                                    if fig:
                                        try:
                                            st.plotly_chart(fig, width="stretch") 
                                        except:
                                            st.plotly_chart(fig, use_container_width=True)

                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer_text,
                                "image_url": img_url
                            })
                        except Exception as e:
                            st.error(f"Error: {e}")
            # Rerun to clean up state if needed, though audio_input might persist.
            # Usually strict rerun isn't needed if we append to session_state, 
            # but it helps show the new history item immediately.
            # st.rerun() 

    prompt = st.chat_input("Ask about plants...")

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = agent.query(prompt, session_id=st.session_state["username"])
                    
                    # 1. Answer
                    answer_text = response.get("answer", "No answer.")
                    st.markdown(answer_text)
                    
                    # 2. Image Display
                    img_url = response.get("image_url")
                    if img_url:
                        st.image(img_url, caption="Plant Image", width=300)

                    # 3. Map Display (New)
                    locations = response.get("locations", [])
                    if locations:
                        with st.spinner("Generating Map..."):
                            import src.tools.map_utils as map_utils
                            # Check if map_utils was reloaded or needs reload
                            import importlib
                            importlib.reload(map_utils) 
                            
                            fig = map_utils.generate_karnataka_map(locations)
                            if fig:
                                try:
                                    st.plotly_chart(fig, width="stretch")
                                except:
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Could not generate map (GeoJSON missing or empty).")

                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer_text,
                        "image_url": img_url
                    })
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Main ---
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    agent = init_system()
    if not agent:
        st.stop()

    if not st.session_state["logged_in"]:
        login_page()
    else:
        chat_page(agent)

if __name__ == "__main__":
    main()

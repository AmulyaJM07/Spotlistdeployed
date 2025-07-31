import streamlit as st
import uuid
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# Spotify credentials
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
SCOPE = "playlist-modify-public playlist-modify-private"

# Background image
BACKGROUND_IMAGE = "https://images.unsplash.com/photo-1647866872319-683f5c4c56e6?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1yZWxhdGVkfDI1fHx8ZW58MHx8fHx8"

# Styling
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('{BACKGROUND_IMAGE}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: white !important;
        font-weight: bold;
    }}
    header, footer, .viewerBadge_container__1QSob {{
        display: none !important;
    }}
    .stTextInput > div > label {{
        color: white !important;
        font-weight: bold !important;
    }}
    .stTextInput > div > input {{
        background: rgba(255, 255, 255, 0.1);
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px;
    }}
    .stButton > button {{
        background: linear-gradient(145deg, #FFD700, #FFA500);
        color: black;
        font-weight: bold;
        border-radius: 12px;
        box-shadow: 0px 0px 10px #FFD700;
    }}
    .stButton > button:hover {{
        background: linear-gradient(145deg, #FFC300, #FFB347);
    }}
    h1 {{
        text-align: center;
        color: white;
        font-weight: bold;
        font-size: 2.5rem;
        text-shadow: 0 0 15px #FFD700;
    }}
    .stAlert-success {{
        background-color: #28a745 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
    }}
    .stAlert-error {{
        background-color: #cc0000 !important;
        color: white !important;
        font-weight: bold;
    }}
    .stAlert-warning {{
        background-color: #f0ad4e !important;
        color: black !important;
        font-weight: bold;
    }}
    a {{
        color:white;
        font-weight: bold;
        text-decoration: none;
        pointer-events: none;
        cursor: default;
    }}
    </style>
""", unsafe_allow_html=True)

# Spotify authentication
def authenticate():
    state = str(uuid.uuid4())
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=None,
        show_dialog=True,
        state=state
    )
    return Spotify(auth_manager=auth_manager), auth_manager

def get_valid_spotify():
    if "auth_manager" not in st.session_state or st.session_state.auth_manager is None:
        return None, None

    auth_manager = st.session_state.auth_manager
    token_info = auth_manager.cache_handler.get_cached_token()

    if token_info is None:
        return None, None  # ⚠️ No token to use

    if auth_manager.is_token_expired(token_info):
        auth_manager.refresh_access_token(token_info["refresh_token"])

    return Spotify(auth_manager=auth_manager), auth_manager


# Session state setup
if "sp" not in st.session_state:
    st.session_state.sp = None
if "auth_manager" not in st.session_state:
    st.session_state.auth_manager = None
if "playlist_id" not in st.session_state:
    st.session_state.playlist_id = None

# Title
st.markdown("<h1>✨ Spotify Playlist Maker</h1>", unsafe_allow_html=True)

# Login
if st.session_state.sp is None:
    if st.button("🔐 Login with Spotify"):
        sp, auth_manager = authenticate()
        st.session_state.sp = sp
        st.session_state.auth_manager = auth_manager
        st.rerun()
else:
    sp, _ = get_valid_spotify()
    if sp:
        try:
            user = sp.current_user()
            st.success(f"✅ Logged in as {user['display_name']}", icon="✅")

            playlist_name = st.text_input("Enter Playlist Name")
            if st.button("🎵 Create Playlist"):
                if playlist_name.strip() == "":
                    st.error("Please enter a valid playlist name.")
                else:
                    new_playlist = sp.user_playlist_create(user["id"], playlist_name)
                    st.session_state.playlist_id = new_playlist["id"]
                    st.success(f"Playlist '{playlist_name}' created!", icon="🎉")

            if st.session_state.playlist_id:
                song_name = st.text_input("Enter Song Name")
                if st.button("➕ Add Song"):
                    if song_name.strip() == "":
                        st.error("Please enter a song name.")
                    else:
                        results = sp.search(q=song_name, type="track", limit=1)
                        tracks = results["tracks"]["items"]
                        if tracks:
                            track = tracks[0]
                            sp.playlist_add_items(st.session_state.playlist_id, [track["uri"]])
                            st.success(f"✅ Added '{track['name']}' by {track['artists'][0]['name']}' to playlist!")
                        else:
                            st.error("⚠️ Song not found.")
        except SpotifyException as e:
            if e.http_status == 401:
                st.warning("🔄 Token expired. Please click 'Login with Spotify' again.")
                st.session_state.sp = None
                st.session_state.auth_manager = None
            else:
                st.error(f"Spotify error: {e}")
    else:
        st.warning("Token invalid. Please login again.")
        st.session_state.sp = None

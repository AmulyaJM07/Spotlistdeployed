import streamlit as st
import uuid
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# Spotify credentials from secrets
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
SCOPE = "playlist-modify-public playlist-modify-private"

# Background image styling
BACKGROUND_IMAGE = "https://images.unsplash.com/photo-1647866872319-683f5c4c56e6?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1yZWxhdGVkfDI1fHx8ZW58MHx8fHx8"

# Set background style
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
    </style>
""", unsafe_allow_html=True)

# ------------------- 🔐 Auth Flow -------------------

@st.cache_resource(show_spinner=False)
def get_auth_manager():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
        cache_path=None  # 👈 Prevent shared tokens
    )

# Session state init
if "token_info" not in st.session_state:
    st.session_state.token_info = None
if "sp" not in st.session_state:
    st.session_state.sp = None
if "playlist_id" not in st.session_state:
    st.session_state.playlist_id = None

# Main Title
st.markdown("<h1>✨ Spotify Playlist Maker</h1>", unsafe_allow_html=True)

auth_manager = get_auth_manager()

# 🔁 OAuth callback handler
query_params = st.query_params
if "code" in query_params and st.session_state.token_info is None:
    code = query_params["code"][0]
    token_info = auth_manager.get_access_token(code, as_dict=True)
    if token_info:
        st.session_state.token_info = token_info
        st.session_state.sp = Spotify(auth=token_info['access_token'])
        st.rerun()

# 🟢 Authenticated state
if st.session_state.sp:
    sp = st.session_state.sp
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
        st.error("Spotify error: " + str(e))
        st.session_state.sp = None
        st.session_state.token_info = None
else:
    # 🟡 Not logged in yet
    login_url = auth_manager.get_authorize_url()
    st.markdown(f"### [🔐 Click here to login with Spotify]({login_url})")

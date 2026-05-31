import streamlit as st


def load_shared_theme():
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            --app-bg:
                radial-gradient(circle at 16% 7%, rgba(37, 99, 235, 0.10), transparent 30%),
                radial-gradient(circle at 88% 18%, rgba(20, 184, 166, 0.055), transparent 26%),
                linear-gradient(135deg, #070b14 0%, #0a1020 48%, #050814 100%);
        }
        @keyframes premiumPageIn {
            from {
                opacity: 0.01;
                transform: translateY(4px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: var(--app-bg) !important;
            color: #eef2ff !important;
        }
        [data-testid="stAppViewContainer"] > .main,
        section[data-testid="stSidebar"] {
            animation: premiumPageIn 140ms ease-out both;
        }
        .stApp,
        [data-testid="stAppViewContainer"],
        .main,
        .main .block-container {
            transition: background-color 120ms ease, opacity 120ms ease !important;
        }
        [data-testid="stHeader"],
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        #MainMenu,
        footer,
        .stDeployButton,
        [data-testid="stDecoration"],
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) {
            width: 230px !important;
            min-width: 230px !important;
            max-width: 230px !important;
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.84), rgba(2, 6, 23, 0.92)) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.12) !important;
            box-shadow: 14px 0 36px rgba(0, 0, 0, 0.18) !important;
            backdrop-filter: blur(18px);
        }
        section[data-testid="stSidebar"]:not([aria-expanded="false"]) > div:first-child {
            width: 230px !important;
            padding: 2.2rem 1.05rem 1.2rem !important;
        }
        .main .block-container {
            padding-left: clamp(2rem, 4vw, 4.5rem) !important;
            padding-right: clamp(2rem, 4vw, 4.5rem) !important;
        }
        .icon-sidebar-logo {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin: 0.15rem 0 1.35rem;
            padding: 0 0 1.7rem 0.55rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            color: #f8fafc;
        }
        .sidebar-logo-mark {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            color: #f8fafc;
            font-size: 1.85rem;
            line-height: 1;
            filter: drop-shadow(0 8px 18px rgba(245, 158, 11, 0.12));
        }
        .icon-nav-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            width: 100%;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] {
            width: 100% !important;
            height: auto !important;
            margin: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
        section[data-testid="stSidebar"] a {
            width: 100% !important;
            height: 42px !important;
            min-height: 42px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 12px !important;
            padding: 0 14px !important;
            border-radius: 12px !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            color: #dbeafe !important;
            text-decoration: none !important;
            transition: transform 180ms ease, background 180ms ease, border-color 180ms ease, box-shadow 180ms ease !important;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
        section[data-testid="stSidebar"] a p {
            font-size: 0.96rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            font-weight: 750 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a span,
        section[data-testid="stSidebar"] a span {
            font-size: 1.02rem !important;
            opacity: 0.86;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
        section[data-testid="stSidebar"] a:hover {
            transform: translateX(2px);
            border-color: rgba(148, 163, 184, 0.20) !important;
            background: rgba(30, 41, 59, 0.38) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
        section[data-testid="stSidebar"] a[aria-current="page"] {
            border-color: rgba(125, 211, 252, 0.22) !important;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.38), rgba(91, 33, 182, 0.22)) !important;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12) !important;
        }
        @media (max-width: 760px) {
            section[data-testid="stSidebar"]:not([aria-expanded="false"]) {
                width: 205px !important;
                min-width: 205px !important;
                max-width: 205px !important;
            }
            section[data-testid="stSidebar"]:not([aria-expanded="false"]) > div:first-child {
                width: 205px !important;
                padding: 1rem 0.85rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_icon_sidebar(active_page):
    _ = active_page
    st.sidebar.markdown(
        """
        <div class="icon-sidebar-logo" title="Sözleşme Rehberim">
            <div class="sidebar-logo-mark">⚖️</div>
        </div>
        <div class="icon-nav-group">
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("Ana_Sayfa.py", label="Ana Sayfa", icon=":material/home:")
    st.sidebar.page_link("pages/1_💬_Chatbot.py", label="Chatbot", icon=":material/chat_bubble:")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

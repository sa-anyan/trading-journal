###########################################################################
# TRADING JOURNAL - AUTHENTICATION
###########################################################################
# Supabase Auth gates the entire Streamlit app.
# Only emails explicitly listed in Streamlit secrets may enter.
###########################################################################

import streamlit as st
from supabase import create_client


DEFAULT_SUPABASE_URL = "https://qsislwwqnayfczbdrucb.supabase.co"
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_wRBlE3EAWfMwoYvIRoZ-og_ntGV0vp3"


def _secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _allowed_emails():
    raw = _secret("AUTHORIZED_EMAILS", "") or _secret("OWNER_EMAIL", "")
    if not raw:
        return set()
    if isinstance(raw, str):
        return {
            item.strip().lower()
            for item in raw.split(",")
            if item.strip()
        }
    try:
        return {str(item).strip().lower() for item in raw if str(item).strip()}
    except TypeError:
        return set()


def auth_client():
    url = _secret("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    key = _secret(
        "SUPABASE_PUBLISHABLE_KEY",
        DEFAULT_SUPABASE_PUBLISHABLE_KEY,
    )
    return create_client(url, key)


def is_authenticated():
    return bool(st.session_state.get("auth_user_email"))


def current_user_email():
    return st.session_state.get("auth_user_email")


def _clear_auth():
    for key in (
        "auth_user_email",
        "auth_user_id",
        "auth_access_token",
        "auth_refresh_token",
    ):
        st.session_state.pop(key, None)


def logout():
    try:
        auth_client().auth.sign_out()
    except Exception:
        pass
    _clear_auth()
    st.rerun()


def _render_login_page():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        section.main > div {max-width: 1180px;}
        .auth-wrap {
            min-height: 67vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem 0 2rem 0;
        }
        .auth-shell {
            width: min(100%, 980px);
            display: grid;
            grid-template-columns: 1.15fr .85fr;
            gap: 1rem;
            align-items: stretch;
        }
        .auth-brand {
            border: 1px solid rgba(215,183,104,.18);
            border-radius: 24px;
            padding: 2.1rem;
            background:
              linear-gradient(145deg, rgba(215,183,104,.10), transparent 34%),
              linear-gradient(180deg, rgba(16,38,59,.92), rgba(9,24,39,.96));
            box-shadow: 0 24px 70px rgba(0,0,0,.24);
        }
        .auth-card {
            border: 1px solid rgba(148,163,184,.16);
            border-radius: 24px;
            padding: 2rem;
            background: rgba(9,24,39,.92);
            box-shadow: 0 24px 70px rgba(0,0,0,.20);
        }
        .auth-kicker {
            color: #D7B768;
            text-transform: uppercase;
            letter-spacing: .16em;
            font-size: .72rem;
            font-weight: 800;
        }
        .auth-title {
            color: #F5F0E6;
            font-size: 2.55rem;
            line-height: 1.02;
            font-weight: 790;
            letter-spacing: -.045em;
            margin-top: .75rem;
        }
        .auth-copy {
            color: #A7B6C6;
            font-size: 1rem;
            line-height: 1.65;
            margin-top: 1rem;
            max-width: 34rem;
        }
        .auth-points {
            color: #A7B6C6;
            margin-top: 2rem;
            line-height: 1.9;
            font-size: .94rem;
        }
        .login-heading {
            color: #F5F0E6;
            font-size: 1.45rem;
            font-weight: 740;
            letter-spacing: -.025em;
            margin-bottom: .25rem;
        }
        .login-sub {
            color: #94A3B8;
            font-size: .9rem;
            margin-bottom: 1.2rem;
        }
        @media (max-width: 820px) {
            .auth-shell {grid-template-columns: 1fr;}
            .auth-title {font-size: 2rem;}
        }
        </style>
        <div class="auth-wrap">
            <div class="auth-shell">
                <div class="auth-brand">
                    <div class="auth-kicker">Private strategy intelligence</div>
                    <div class="auth-title">Research your strategy.<br>Understand your edge.</div>
                    <div class="auth-copy">
                        Replay, journal and compare your trading decisions in one private research environment.
                    </div>
                    <div class="auth-points">
                        ◈ Lock strategy rules before testing<br>
                        ◇ Analyse performance by instrument, session and time<br>
                        ↓ Import TradingView Replay and Paper Trading data
                    </div>
                </div>
                <div class="auth-card">
                    <div class="login-heading">Welcome back</div>
                    <div class="login-sub">Sign in to open your Trading Journal.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_auth():
    if is_authenticated():
        return True

    _render_login_page()

    allowed = _allowed_emails()
    if not allowed:
        st.error(
            "Private access is not configured yet. Add OWNER_EMAIL or "
            "AUTHORIZED_EMAILS to Streamlit Secrets."
        )
        return False

    with st.form("private_sign_in", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return False

    email_normalised = email.strip().lower()

    if email_normalised not in allowed:
        st.error("This account is not authorised for this journal.")
        return False

    try:
        response = auth_client().auth.sign_in_with_password(
            {
                "email": email_normalised,
                "password": password,
            }
        )

        if not response.user or not response.session:
            st.error("Sign-in failed.")
            return False

        authenticated_email = (response.user.email or "").strip().lower()

        if authenticated_email not in allowed:
            try:
                auth_client().auth.sign_out()
            finally:
                _clear_auth()
            st.error("This account is not authorised for this journal.")
            return False

        st.session_state["auth_user_email"] = authenticated_email
        st.session_state["auth_user_id"] = str(response.user.id)
        st.session_state["auth_access_token"] = response.session.access_token
        st.session_state["auth_refresh_token"] = response.session.refresh_token
        st.rerun()

    except Exception:
        st.error("Incorrect email or password.")

    return False

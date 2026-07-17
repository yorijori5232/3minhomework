"""
3분 집안일 — Streamlit 배포용 래퍼.

index.html은 그 자체로 완결된 정적 사이트지만, Streamlit은 파일을 그냥 서빙해주지 않고
components.html()이 만드는 iframe 안에 srcdoc으로 밀어넣는다. srcdoc iframe에는 기준 주소가
없어서 assets/pkg-mild.png, missions.js 같은 상대 경로가 전부 깨진다.
그래서 여기서 외부 파일을 전부 HTML 안으로 인라인해 자기완결적인 문서 하나로 만들어 넘긴다.

로컬 확인:  python3 -m streamlit run streamlit_app.py
"""

import base64
import json
import pathlib

import streamlit as st
import streamlit.components.v1 as components

ROOT = pathlib.Path(__file__).parent

# iframe 안에서는 location.href를 쓸 수 없으므로 공유 링크로 쓸 실제 주소를 여기서 넣어준다.
APP_URL = "https://3minhousework.streamlit.app"

# index.html이 100dvh 기준으로 그려지는데 iframe은 높이가 고정이라 직접 정해줘야 한다.
FRAME_HEIGHT = 900

st.set_page_config(page_title="3분 집안일", page_icon="🧽", layout="wide")


@st.cache_data(show_spinner=False)
def build_html() -> str:
    """index.html의 외부 참조를 전부 인라인해서 단일 문서로 만든다."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # 1) missions.js → 인라인 스크립트
    missions = (ROOT / "missions.js").read_text(encoding="utf-8")
    html = html.replace(
        '<script src="missions.js"></script>',
        f"<script>\n{missions}\n</script>",
    )

    # 2) 봉지 이미지 → data URI
    for name in ("pkg-mild.png", "pkg-hot.png"):
        encoded = base64.b64encode((ROOT / "assets" / name).read_bytes()).decode()
        html = html.replace(f"assets/{name}", f"data:image/png;base64,{encoded}")

    # 3) 공유 링크로 쓸 실제 주소 주입
    html = html.replace(
        "</head>",
        f"<script>window.SHARE_URL = {json.dumps(APP_URL)};</script>\n</head>",
    )

    return html


# Streamlit 기본 여백·헤더·푸터를 걷어내 봉지가 화면을 꽉 채우게 한다.
st.markdown(
    """
    <style>
      header[data-testid="stHeader"], footer { display: none; }
      [data-testid="stAppViewContainer"] > .main .block-container {
        padding: 0; max-width: 100%;
      }
      [data-testid="stAppViewContainer"] iframe { display: block; }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(build_html(), height=FRAME_HEIGHT, scrolling=True)

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

# iframe 안에서는 location.href가 about:srcdoc이라 공유 링크로 쓸 수 없다. 실제 배포 주소를 넣어준다.
APP_URL = "https://salmblindspot-3minhousework.streamlit.app"

# components.html은 height를 픽셀로 요구한다. 실제 높이는 아래 CSS가 100dvh로 덮어쓰지만,
# CSS가 먹기 전 첫 프레임에 쓰일 값이라 흔한 화면 높이로 잡아둔다.
FRAME_HEIGHT = 800

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


# Streamlit이 얹는 것들(헤더, 툴바, Manage app 배지, 여백)을 전부 걷어내고
# 컴포넌트 iframe을 화면 전체로 늘려서 봉지 배경이 끝까지 차게 만든다.
HIDE_CHROME = """
<style>
  /* Streamlit 기본 UI 제거 (헤더 / 툴바 / Manage app / Made with Streamlit 배지) */
  header[data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"],
  [data-testid="manage-app-button"],
  #MainMenu,
  footer,
  [class*="viewerBadge"] {
    display: none !important;
  }

  /* 페이지 자체 스크롤 제거 — 안쪽 iframe과 이중 스크롤이 되면 모바일에서 화면이 떨린다 */
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
  }

  [data-testid="stAppViewContainer"],
  section.main {
    padding: 0 !important;
    overflow: hidden !important;
  }

  [data-testid="stAppViewBlockContainer"],
  .block-container {
    padding: 0 !important;
    max-width: 100% !important;
  }

  [data-testid="stVerticalBlock"] { gap: 0 !important; }

  /* iframe '만' 화면 전체로 늘린다.
     element-container 전체에 높이를 주면 이 <style>이 들어있는 빈 컨테이너까지
     같은 높이를 먹어서 iframe을 아래로 밀어내고 흰 여백이 생긴다. */
  iframe[data-testid="stIFrame"] {
    height: 100dvh !important;
    width: 100% !important;
    display: block !important;
    border: 0 !important;
  }
</style>
"""

st.markdown(HIDE_CHROME, unsafe_allow_html=True)

components.html(build_html(), height=FRAME_HEIGHT, scrolling=False)

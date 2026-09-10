"""로드킬 위험구간 예측 대시보드 — 목업 데이터 뼈대.

⚠️ 지금 이 화면이 보여주는 도로·좌표·위험도·브리핑·챗봇 답변은 전부
``src/dashboard/mock_data.py`` 가 만든 합성 데이터다. 실제 로드킬 데이터가
아니다. 전처리·베이스라인·GNN·LLM 파이프라인이 준비되는 대로
``src/dashboard/data_provider.py`` 의 ``load_segments()`` 만 실제 로더로
바꾸면 이 파일은 그대로 동작한다 (자세한 배경은 ``docs/DESIGN_DECISIONS.md``,
현재 진행 상황은 ``docs/PROGRESS.md`` 참고).

실행:
    streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run src/dashboard/app.py`는 이 파일이 있는 디렉터리(src/dashboard)만
# sys.path에 넣고 실행하므로, 실행 위치나 방식과 무관하게 `src.*` 절대 임포트가
# 항상 되도록 프로젝트 루트를 직접 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from src.dashboard import components
from src.dashboard.data_provider import load_segments
from src.dashboard.mock_data import get_mock_chat_response
from src.dashboard.style import ROAD_GRADES

st.set_page_config(page_title="로드킬 위험구간 예측 대시보드", layout="wide")


@st.cache_data
def _load_segments_cached():
    return load_segments()


def main() -> None:
    st.title("🦌 로드킬 위험구간 예측 대시보드")
    st.warning(
        "⚠️ **목업 데이터 화면입니다.** 아래 지도·수치·브리핑·챗봇 응답은 실제 "
        "로드킬 데이터가 아니라 UI 뼈대 검증용 합성 데이터입니다. "
        "실제 데이터 연동 계획은 `docs/PROGRESS.md` 를 참고하세요.",
        icon="⚠️",
    )

    all_segments = _load_segments_cached()

    with st.sidebar:
        st.header("필터")
        selected_grades = st.multiselect("도로 등급", ROAD_GRADES, default=ROAD_GRADES)
        min_risk = st.slider("최소 위험도", 0.0, 1.0, 0.0, 0.05)
        st.divider()
        st.caption("설계 근거: `docs/DESIGN_DECISIONS.md`  \n진행 상황: `docs/PROGRESS.md`")

    filtered = all_segments[
        all_segments["road_grade"].isin(selected_grades) & (all_segments["risk_score"] >= min_risk)
    ].reset_index(drop=True)

    components.render_kpi_row(all_segments, filtered)
    st.divider()

    map_col, detail_col = st.columns([2, 1])

    with map_col:
        st.subheader("위험구간 지도")
        if filtered.empty:
            st.info("필터 조건에 맞는 구간이 없습니다.")
            map_state = None
        else:
            deck = components.build_deck(filtered)
            map_state = st.pydeck_chart(
                deck,
                on_select="rerun",
                selection_mode="single-object",
                key="segment_map",
                height=520,
            )
        components.render_legend()

        st.caption("지도에서 선(구간)을 클릭하거나, 아래 목록에서 직접 선택할 수 있습니다.")
        options = ["(선택 안 함)"] + list(
            filtered.sort_values("risk_score", ascending=False)["segment_id"]
        )
        clicked_id = None
        if map_state is not None:
            indices = map_state.selection.indices.get(components.SEGMENTS_LAYER_ID, [])
            if indices and indices[0] < len(filtered):
                clicked_id = filtered.iloc[indices[0]]["segment_id"]

        default_index = options.index(clicked_id) if clicked_id in options else 0
        chosen_id = st.selectbox("구간 직접 선택", options, index=default_index)
        selected_id = chosen_id if chosen_id != "(선택 안 함)" else clicked_id

    with detail_col:
        st.subheader("구간 상세")
        if selected_id:
            row = filtered[filtered["segment_id"] == selected_id].iloc[0]
            components.render_segment_detail(row)
        else:
            st.info("구간을 선택하면 위험도 근거와 정책 브리핑이 여기에 표시됩니다.")

    st.divider()
    st.subheader("💬 위험구간 챗봇 (목업)")
    st.caption(
        "실제 RAG 파이프라인(`src/rag`)과 Claude API 연동(`src/llm`) 이전까지는 "
        "키워드 매칭 기반 예시 응답만 반환합니다."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, content in st.session_state.chat_history:
        st.chat_message(role).write(content)

    question = st.chat_input("예: 가장 위험한 구간이 어디야?")
    if question:
        st.session_state.chat_history.append(("user", question))
        st.chat_message("user").write(question)

        response = get_mock_chat_response(question, filtered)
        st.session_state.chat_history.append(("assistant", response))
        st.chat_message("assistant").write(response)


main()

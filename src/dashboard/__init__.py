"""Streamlit 대화형 GIS 대시보드.

지금은 ``mock_data.py`` 가 만드는 합성 데이터로 뼈대만 구현된 상태다
(``docs/DESIGN_DECISIONS.md`` §"대시보드" 참고). 실제 데이터는
``data_provider.py`` 의 ``load_segments()`` 하나만 교체하면 붙는다.

실행: streamlit run src/dashboard/app.py
"""

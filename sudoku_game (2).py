"""기존 sudoku_timer_ranking(2).py의 핵심 게임 규칙을 Streamlit으로 이식."""
import random
import time
import json
import streamlit as st

def pattern(r, c):
    return (3 * (r % 3) + r // 3 + c) % 9

def shuffled(seq):
    seq = list(seq)
    random.shuffle(seq)
    return seq

def generate_solution():
    base, side = 3, 9
    rows = [g * base + r for g in shuffled(range(base)) for r in shuffled(range(base))]
    cols = [g * base + c for g in shuffled(range(base)) for c in shuffled(range(base))]
    nums = shuffled(range(1, side + 1))
    return [[nums[pattern(r, c)] for c in cols] for r in rows]

def fmt(seconds):
    return f"{int(seconds)//60:02d}:{int(seconds)%60:02d}"

def begin_game(probability):
    solution = generate_solution()
    puzzle = [[0 if random.random() < probability else solution[r][c]
               for c in range(9)] for r in range(9)]
    st.session_state.sd_solution = solution
    st.session_state.sd_puzzle = puzzle
    st.session_state.sd_start = time.monotonic()
    st.session_state.sd_running = True
    st.session_state.sd_elapsed = 0
    st.session_state.sd_version = st.session_state.get("sd_version", 0) + 1
    st.session_state.sd_message = "게임이 시작됐습니다. 빈칸에 1~9를 입력하세요."

def sudoku_page():
    st.markdown(
        '<div class="hero"><h1>🧩 SUDOKU BREAK</h1>'
        '<p>지하철 이동시간을 즐겁게 · 실습 스도쿠 게임</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("""
    <style>
    /* Sudoku labels and time: dark text on light background */
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stMetricLabel"] p,
    .stApp [data-testid="stMetricValue"],
    .stApp label p {
        color:#172B4D !important; font-size:19px !important;
        font-weight:750 !important;
    }
    .stApp [data-testid="stMetricValue"] {font-size:36px !important}
    /* Large, readable buttons */
    .stApp .stButton button, .stApp [data-testid="stFormSubmitButton"] button {
        min-height:55px !important;
        font-size:19px !important;
        font-weight:750 !important;
    }
    .stApp .stButton button:not([kind="primary"]) {
        background:#1F2937 !important; color:white !important;
    }
    .stApp .stButton button p, .stApp [data-testid="stFormSubmitButton"] button p {
        color:white !important; font-size:19px !important;
        font-weight:750 !important;
    }
    /* Inputs: white text on dark boxes */
    .stApp [data-baseweb="input"], .stApp [data-baseweb="input"] input,
    .stApp [data-baseweb="select"] > div {
        background:#232A35 !important; color:#FFFFFF !important;
        font-size:19px !important;
    }
    .stApp [data-baseweb="input"] input::placeholder {color:#E2E8F0 !important}
    .stApp [data-baseweb="select"] span, .stApp [data-baseweb="select"] svg,
    .stApp [data-testid="stNumberInput"] button,
    .stApp [data-testid="stNumberInput"] button svg {
        color:#FFFFFF !important; fill:#FFFFFF !important;
    }
    .stApp [data-testid="stNumberInput"] button {background:#232A35 !important}
    [role="listbox"] [role="option"] {font-size:19px !important}
    /* Each 3x3 box is a real Streamlit container with a thick frame.
       This does not depend on fragile column:nth-child CSS selectors. */
    [class*="st-key-sd_block_"] {
        border:3px solid #142E51 !important;
        border-radius:0 !important;
        background:#F8FAFD !important;
        padding:4px !important;
        margin:0 !important;
    }
    [class*="st-key-sd_block_"] [data-testid="stVerticalBlock"] {
        gap:4px !important;
    }
    [class*="st-key-sd_block_"] [data-testid="stHorizontalBlock"] {
        gap:4px !important;
    }
    [class*="st-key-sd_block_"] [data-testid="stSelectbox"] {
        min-width:0 !important;
    }
    [class*="st-key-sd_block_"] [data-baseweb="select"] > div {
        min-height:57px !important;
        height:57px !important;
        border-radius:0 !important;
        background:#FFFFFF !important;
        color:#12294B !important;
        border:1px solid #A6B2C4 !important;
        padding:0 !important;
        font-size:24px !important;
        font-weight:800 !important;
    }
    [class*="st-key-sd_block_"] [data-baseweb="select"] span,
    [class*="st-key-sd_block_"] [data-baseweb="select"] svg {
        color:#12294B !important; fill:#12294B !important;
        font-size:24px !important;
    }
    [class*="st-key-sd_block_"] [data-baseweb="select"] svg {
        width:13px !important;
    }
    .sd-fixed {
        min-height:57px;display:flex;align-items:center;justify-content:center;
        background:#E0E8F5;color:#12294B;
        border:1px solid #A6B2C4;
        font-size:27px;font-weight:850;
    }
    </style>""", unsafe_allow_html=True)
    if "sd_rankings" not in st.session_state:
        st.session_state.sd_rankings = []
    if "sd_running" not in st.session_state:
        st.session_state.sd_running = False
    if "sd_message" not in st.session_state:
        st.session_state.sd_message = "이름과 빈칸 확률을 입력한 뒤 Shuffle을 누르세요."

    a, b, c = st.columns([2, 1.3, 1])
    with a:
        player = st.text_input("참가자 이름", key="sd_player", placeholder="Player")
    with b:
        probability = st.number_input("빈칸 확률 (0~1)", min_value=0.0, max_value=1.0,
                                      value=0.7, step=0.05, key="sd_probability")
    with c:
        st.markdown("**타이머**")
        if st.session_state.sd_running:
            elapsed = int(time.monotonic() - st.session_state.sd_start)
        else:
            elapsed = st.session_state.get("sd_elapsed", 0)
        st.metric("경과 시간", fmt(elapsed))

    left, middle, right = st.columns(3)
    with left:
        if st.button("🔀 Shuffle · 새 게임", use_container_width=True, type="primary"):
            begin_game(probability)
            st.rerun()
    with middle:
        if st.button("⏱ Reset Timer", use_container_width=True):
            st.session_state.sd_elapsed = 0
            if st.session_state.sd_running:
                st.session_state.sd_start = time.monotonic()
            st.session_state.sd_message = "타이머를 0으로 초기화했습니다."
            st.rerun()
    with right:
        if st.button("🏆 Ranking", use_container_width=True):
            st.session_state.sd_show_ranking = not st.session_state.get("sd_show_ranking", False)

    st.info(st.session_state.sd_message)

    if "sd_puzzle" in st.session_state:
        version = st.session_state.sd_version
        puzzle = st.session_state.sd_puzzle
        with st.form(f"sd_board_{version}"):
            # Build nine 3x3 blocks instead of 9 independent horizontal rows.
            # This makes BOTH vertical and horizontal bold borders structural.
            answers = [[0 for _ in range(9)] for _ in range(9)]
            for block_row in range(3):
                block_cols = st.columns(3, gap="small")
                for block_col in range(3):
                    with block_cols[block_col]:
                        with st.container(key=f"sd_block_{block_row}_{block_col}"):
                            for inner_row in range(3):
                                r = block_row * 3 + inner_row
                                cell_cols = st.columns(3, gap="small")
                                for inner_col in range(3):
                                    c = block_col * 3 + inner_col
                                    n = puzzle[r][c]
                                    with cell_cols[inner_col]:
                                        if n:
                                            st.markdown(
                                                f'<div class="sd-fixed">{n}</div>',
                                                unsafe_allow_html=True,
                                            )
                                            answers[r][c] = n
                                        else:
                                            answers[r][c] = st.selectbox(
                                                f"{r+1}행 {c+1}열",
                                                list(range(10)),
                                                format_func=lambda x: "·" if x == 0 else str(x),
                                                label_visibility="collapsed",
                                                key=f"sd_{version}_{r}_{c}",
                                            )
            finished = st.form_submit_button(
                "✅ Finish · 정답 확인", use_container_width=True, type="primary"
            )

        if finished:
            if not st.session_state.sd_running:
                st.warning("새 게임을 시작해 주세요.")
            else:
                issue = next(((r, c) for r in range(9) for c in range(9)
                              if answers[r][c] != st.session_state.sd_solution[r][c]), None)
                if issue:
                    r, c = issue
                    st.warning(f"{r+1}행 {c+1}열을 확인해 주세요. 빈칸이 있거나 정답과 다릅니다.")
                else:
                    seconds = int(time.monotonic() - st.session_state.sd_start)
                    st.session_state.sd_elapsed = seconds
                    st.session_state.sd_running = False
                    name = (player or "Player").strip()[:30]
                    rankings = st.session_state.sd_rankings
                    rankings.append({"name": name, "seconds": seconds})
                    rankings.sort(key=lambda x: x["seconds"])
                    rank = next(i for i, entry in enumerate(rankings, 1) if entry["name"] == name and entry["seconds"] == seconds)
                    st.session_state.sd_message = f"완성! {name}님 · {fmt(seconds)} · 현재 {rank}위"
                    st.success(st.session_state.sd_message)
    else:
        st.markdown("#### 🎮 Shuffle 버튼을 눌러 게임을 시작하세요.")

    if st.session_state.get("sd_show_ranking", False):
        st.markdown("### 🏆 Ranking TOP 20")
        rankings = st.session_state.sd_rankings
        if not rankings:
            st.caption("아직 완료 기록이 없습니다.")
        for idx, item in enumerate(rankings[:20], 1):
            st.write(f"{idx}위 · {item['name']} · {fmt(item['seconds'])}")
        st.download_button(
            "랭킹 JSON 저장",
            data=json.dumps(rankings, ensure_ascii=False, indent=2),
            file_name="sudoku_rankings.json",
            mime="application/json",
        )
        st.caption("현재 랭킹은 브라우저 세션에 보관됩니다. Streamlit Cloud 전체 사용자 공용 영구 랭킹은 별도 데이터베이스가 필요합니다.")

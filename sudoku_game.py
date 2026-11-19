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
    .sd-fixed{height:36px;display:flex;align-items:center;justify-content:center;
      background:#dfe8f5;color:#17365c;border-radius:6px;font-weight:800;font-size:18px}
    div[data-testid="stSelectbox"]{min-width:0}
    .stApp label p, .stApp [data-testid="stWidgetLabel"] p {color:#172c4b !important;font-size:16px !important;font-weight:750 !important}
    .stApp [data-testid="stMetricLabel"] p{color:#223b5e !important}
    .stApp [data-testid="stMetricValue"]{color:#17365c !important}
    .stApp div[data-baseweb="input"] input{color:#fff !important;background:#262626 !important;font-size:16px !important}
    .stApp div[data-baseweb="input"]{background:#262626 !important}
    .stApp div[data-baseweb="select"]>div{background:#262626 !important;color:#fff !important}
    .stApp div[data-baseweb="select"] span{color:#fff !important;font-size:16px !important}
    .stApp div[data-testid="stNumberInput"] button{color:#fff !important;background:#262626 !important}
    .stApp .stButton>button:not([kind="primary"]){background:#222 !important;color:#fff !important}
    .stApp .stButton>button:not([kind="primary"]) p{color:#fff !important;font-size:15px !important}
    .stApp [data-testid="stFormSubmitButton"] button{color:#fff !important}
    .stApp [data-testid="stFormSubmitButton"] button p{color:#fff !important}
    .sd-fixed{font-size:20px !important}
    .sd-box{font-weight:800;color:#233e66;font-size:16px}
    /* 9열을 3열씩 묶은 바깥쪽 그룹의 세로 경계 */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"]:has(> [data-testid="column"] > [data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"]) > [data-testid="column"] {border-right:3px solid #30496d;padding-right:5px}

    div[data-testid="stForm"] div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:0}
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
            answers = []
            for r in range(9):
                groups = st.columns(3, gap="small")
                row = []
                for g in range(3):
                    with groups[g]:
                        # 3x3 구역을 각각 굵은 테두리로 둘러싸 가로·세로 경계를 표시합니다.
                        with st.container(border=True):
                            cols = st.columns(3, gap="small")
                            for j in range(3):
                                c = g*3+j
                                n = puzzle[r][c]
                                with cols[j]:
                                    if n:
                                        st.markdown(f'<div class="sd-fixed">{n}</div>', unsafe_allow_html=True)
                                        row.append(n)
                                    else:
                                        choice = st.selectbox(
                                            f"{r+1}행 {c+1}열", list(range(10)),
                                            format_func=lambda x: "·" if x == 0 else str(x),
                                            label_visibility="collapsed",
                                            key=f"sd_{version}_{r}_{c}",
                                        )
                                        row.append(choice)
                answers.append(row)
                if r in (2, 5):
                    st.markdown('<div style="height:5px;background:#30496d;border-radius:4px;margin:1px 0 7px"></div>', unsafe_allow_html=True)
            finished = st.form_submit_button("✅ Finish · 정답 확인", use_container_width=True, type="primary")

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

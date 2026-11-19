import csv
import heapq
import html
import random
import re
import time as clock
from datetime import datetime, timedelta, time
from pathlib import Path
from urllib.parse import quote

import folium
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
COLORS = {'1':'#0052A4','2':'#00A84D','3':'#EF7C1C','4':'#00A5DE','5':'#996CAC','6':'#CD7C2F','7':'#747F00','8':'#E6186C','9':'#BDB092'}
MAX_ZOOM = 13

st.set_page_config(page_title='SubwayPath | MOVE SMART', page_icon='🚇', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'DM Sans','Noto Sans KR',sans-serif}
.stApp{background:linear-gradient(140deg,#f3f7ff 0%,#fff 50%,#eefaf8 100%);color:#142a4e}
.block-container{padding-top:1.4rem;max-width:1650px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#101d3e,#192e5b 70%,#13274b);}
section[data-testid="stSidebar"] *{color:#f7faff}
section[data-testid="stSidebar"] [data-baseweb="select"] *{color:#122341}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{color:#e2eaff}
section[data-testid="stSidebar"] .stButton>button{border:0;background:linear-gradient(100deg,#ff8068,#f34b91);color:white;font-weight:800;border-radius:13px;min-height:46px}
section[data-testid="stSidebar"] .stButton>button:hover{filter:brightness(1.08)}
section[data-testid="stSidebar"] .stRadio label{color:white}
section[data-testid="stSidebar"] a{color:#fff}
h1,h2,h3{color:#13294c;letter-spacing:-.035em}
.hero{border-radius:23px;background:linear-gradient(105deg,#192c61,#4964cc 58%,#2cc4af);padding:25px 32px;color:white;box-shadow:0 12px 32px #1a397026;margin-bottom:18px}
.hero h1{color:white;margin:0;font-size:2.15rem}.hero p{color:#e3edff;margin:6px 0 0}
.metric-card{background:#fff;border:1px solid #e5eaf7;border-radius:18px;padding:19px 18px;box-shadow:0 6px 20px #1833610b;min-height:105px}
.metric-card .k{font-size:12px;color:#687b9d;font-weight:700}.metric-card .v{font-size:27px;color:#142a51;font-weight:800;margin-top:5px}
.panel-head{font-weight:800;color:#182f56;font-size:1.1rem;margin:7px 0 13px}
.timeline{background:white;border:1px solid #e6eaf5;border-radius:19px;padding:20px 16px;box-shadow:0 7px 25px #16315c0c}
.stop{display:flex;gap:12px;align-items:stretch;min-height:52px}.rail{display:flex;align-items:center;flex-direction:column;width:16px;flex-shrink:0}.dot{width:14px;height:14px;border:3px solid white;border-radius:50%;box-shadow:0 0 0 2px var(--line);background:var(--line)}.stem{width:4px;flex:1;background:var(--line);margin-top:3px}.stoptext{padding-bottom:12px;font-size:13px;font-weight:650;color:#24395a}.stoptext small{display:block;font-weight:400;color:#8995ab;margin-top:4px}
.transfer{border-radius:12px;background:#fff1df;border:1px solid #ffd49c;padding:12px;color:#8e4b00;font-weight:800;margin:0 0 12px 0;font-size:13px}
.note{background:#eaf8f6;border-radius:12px;padding:12px 14px;color:#166e65;font-size:13px}
.game-card{border-radius:15px;padding:14px;background:linear-gradient(110deg,#6855f7,#ee66ac);color:#fff;margin-top:14px}
div[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:17px}
.stButton>button{border-radius:12px;font-weight:700}
@media(max-width:900px){.hero h1{font-size:1.5rem}}
</style>''', unsafe_allow_html=True)

@st.cache_data
def load_data():
    graph = {}
    with (BASE/'subway.csv').open(encoding='utf-8-sig', newline='') as f:
        for a,b,w in csv.reader(f):
            graph.setdefault(a,{})[b]=int(w)
            graph.setdefault(b,{})[a]=int(w)
    locations={}
    with (BASE/'subwayLocation.csv').open(encoding='utf-8-sig', newline='') as f:
        for name,lat,lon in csv.reader(f):
            locations[name.strip()] = (float(lat),float(lon))
    return graph,locations

def line_of(station):
    m=re.search(r'\(([^)]+)\)$',station)
    return m.group(1) if m else '?'

def bare(station):
    return station.rsplit('(',1)[0].strip()

def xy(locations,station):
    return locations.get(station) or locations.get(bare(station))

def route(graph,start,end,mode):
    # Lexicographic Dijkstra: optimize (time, transfers) or (transfers, time).
    pq=[((0,0),start)]; dist={start:(0,0)}; prev={}
    while pq:
        cost,node=heapq.heappop(pq)
        if cost!=dist[node]:continue
        if node==end:break
        for nxt,weight in graph[node].items():
            transfer=int(line_of(node)!=line_of(nxt))
            new=(cost[0]+(transfer if mode=='최소환승' else weight),cost[1]+(weight if mode=='최소환승' else transfer))
            if new<dist.get(nxt,(float('inf'),float('inf'))):
                dist[nxt]=new;prev[nxt]=node;heapq.heappush(pq,(new,nxt))
    if end not in dist:return [],0,0
    path=[end]
    while path[-1]!=start:path.append(prev[path[-1]])
    path.reverse()
    minutes=sum(graph[a][b] for a,b in zip(path,path[1:]))
    transfers=sum(line_of(a)!=line_of(b) for a,b in zip(path,path[1:]))
    return path,minutes,transfers

def make_map(locations,path):
    valid=[(s,xy(locations,s)) for s in path]
    valid=[(s,p) for s,p in valid if p]
    center=valid[0][1] if valid else [37.55,126.98]
    m=folium.Map(location=center,zoom_start=11,tiles=None,max_zoom=MAX_ZOOM,control_scale=True, zoom_control=False, scrollWheelZoom=False, doubleClickZoom=False, touchZoom=False, boxZoom=False, keyboard=False, dragging=True)
    folium.TileLayer(tiles=ESRI,attr='Tiles © Esri',name='Esri World Street Map',max_zoom=MAX_ZOOM,max_native_zoom=MAX_ZOOM).add_to(m)
    for (a,pa),(b,pb) in zip(valid,valid[1:]):
        c=COLORS.get(line_of(a),'#5765d5')
        folium.PolyLine([pa,pb],color='white',weight=10,opacity=.9).add_to(m)
        folium.PolyLine([pa,pb],color=c,weight=6,opacity=.96,tooltip=f'{a} → {b}').add_to(m)
    for i,(station,p) in enumerate(valid):
        color='#13b981' if i==0 else '#f24d74' if i==len(valid)-1 else COLORS.get(line_of(station),'#6573e6')
        folium.CircleMarker(p,radius=9 if i in (0,len(valid)-1) else 5,color='white',weight=2,fill=True,fill_color=color,fill_opacity=1,tooltip=f'{i+1}. {station}',popup=folium.Popup(html.escape(station),max_width=180)).add_to(m)
    if len(valid)>1:m.fit_bounds([p for _,p in valid],padding=(35,35),max_zoom=MAX_ZOOM)
    return m

def timeline_html(path, current_index=None):
    parts=['<div class="timeline">']
    for i,s in enumerate(path):
        color=COLORS.get(line_of(s),'#8a92a8')
        if i and line_of(path[i-1])!=line_of(s):
            # "방면" here is the immediate next station, not the official terminus sign.
            onward=next((bare(x) for x in path[i+1:] if line_of(x)==line_of(s)),bare(s))
            parts.append(f'<div class="transfer">↪ {html.escape(line_of(s))}호선 환승 · {html.escape(onward)} 방향 (다음 역 기준)</div>')
        parts.append(f'<div class="stop" style="--line:{color}"><div class="rail"><div class="dot" style="'+('background:#ef345d;box-shadow:0 0 0 4px #ffc5d2;' if current_index==i else '')+'"></div>'+('<div class="stem"></div>' if i<len(path)-1 else '')+'</div><div class="stoptext">'+html.escape(s)+(' <b style="color:#e52e59">🔴 현재 위치(예상)</b>' if current_index==i else '')+f'<small>{i+1}번째 경유역</small></div></div>')
    return ''.join(parts)+'</div>'

# 기존 PyQt5 실습의 스도쿠 생성·타이머·랭킹 기능을 웹으로 이식
from sudoku_game import sudoku_page

graph,locations=load_data()
stations=sorted(graph)
for key,value in [('page','🚇 경로 검색'),('result',None),('guide',False),('guide_step',0),('guide_started_at',None)]:
    if key not in st.session_state:st.session_state[key]=value

with st.sidebar:
    st.markdown('## 🚇 SubwayPath')
    st.caption('MOVE SMART · TRAVEL BETTER')
    page=st.radio('메뉴',['🚇 경로 검색','🧩 스도쿠 게임'],label_visibility='collapsed',key='page')
    st.divider()
    if page=='🚇 경로 검색':
        st.markdown('### 🧭 나의 경로')
        start=st.selectbox('🟢 출발역',stations,index=stations.index('도곡(3)') if '도곡(3)' in stations else 0)
        end=st.selectbox('📍 도착역',stations,index=stations.index('강남(2)') if '강남(2)' in stations else 0)
        mode=st.radio('탐색 모드',['최단시간','최소환승'],horizontal=True)
        depart=st.time_input('출발 예정시간',value=datetime.now().time().replace(second=0,microsecond=0),step=300)
        accessible=st.toggle('♿ 교통약자 배려 모드',help='글씨 확대 및 최소환승 우선 추천. 엘리베이터/무장애 경로는 검증되지 않았습니다.')
        if st.button('🔎 최적 경로 검색',use_container_width=True):
            actual_mode='최소환승' if accessible else mode
            path,minutes,transfers=route(graph,start,end,actual_mode)
            st.session_state.result=(start,end,path,minutes,transfers,depart,actual_mode)
            st.session_state.guide=False;st.session_state.guide_step=0;st.session_state.guide_started_at=None
        st.markdown('<div class="game-card"><b>🧩 SUDOKU BREAK</b><br><small>지하철 이동 중 즐기는 두뇌 게임</small></div>',unsafe_allow_html=True)
        st.button('스도쿠 게임 시작 →',use_container_width=True,on_click=lambda:st.session_state.update(page='🧩 스도쿠 게임'))
    else:
        st.button('← 경로 검색으로 돌아가기',use_container_width=True,on_click=lambda:st.session_state.update(page='🚇 경로 검색'))

if page=='🧩 스도쿠 게임':
    sudoku_page();st.stop()

st.markdown('<div class="hero"><h1>SubwayPath <span style="color:#90fff0">✦ MOVE SMART</span></h1><p>빠르고 편리하게, 당신에게 맞는 지하철 여정을 설계하세요.</p></div>',unsafe_allow_html=True)
result=st.session_state.result
if not result:
    st.info('👈 왼쪽에서 출발역과 도착역을 선택한 뒤 **최적 경로 검색**을 눌러주세요.')
    components.html(make_map(locations,[]).get_root().render(),height=610,scrolling=False)
    st.stop()
start,end,path,minutes,transfers,depart,mode=result
if not path:
    st.error('연결된 경로를 찾을 수 없습니다.');st.stop()
arrival=(datetime.combine(datetime.today(),depart)+timedelta(minutes=minutes)).strftime('%H:%M')
metrics=[('⏱️ 소요시간',f'{minutes}분'),('🔁 환승',f'{transfers}회'),('🚉 경유역',f'{len(path)}개'),('🕓 예상 도착',arrival)]
cols=st.columns(4,gap='small')
for col,(label,val) in zip(cols,metrics):
    with col:st.markdown(f'<div class="metric-card"><div class="k">{label}</div><div class="v">{val}</div></div>',unsafe_allow_html=True)
st.caption(f'📍 {start} → {end} · {mode} 기준 · 예상 도착시간은 대기·지연을 제외한 계산값입니다.')
main,side=st.columns([2.45,1],gap='large')
with main:
    st.markdown('<div class="panel-head">🗺️ 경로 지도</div>',unsafe_allow_html=True)
    components.html(make_map(locations,path).get_root().render(),height=610,scrolling=False)
    st.caption('Esri 지도 / Folium · 지도 확대 기능 잠금(최대 13단계) · 경로선은 역 좌표를 연결한 직선입니다. 타일 서비스 상태에 따라 일부 지역은 표시되지 않을 수 있습니다.')
    st.markdown('<div class="panel-head">✨ 주변 탐색 및 편의 기능</div>',unsafe_allow_html=True)
    target=bare(end)
    links=[('🍜 근처 맛집',f'{target}역 맛집'),('☕ 근처 카페',f'{target}역 카페'),('🎡 근처 놀거리',f'{target}역 놀거리'),('🚶 도보·버스 길찾기',f'{target}역 길찾기')]
    cols=st.columns(4)
    for col,(label,query) in zip(cols,links):
        with col:st.link_button(label,'https://map.naver.com/p/search/'+quote(query),use_container_width=True)
    if accessible:
        st.warning('♿ 배려 모드: 최소환승 우선으로 계산했습니다. 엘리베이터 유무와 휠체어 접근성은 외부 역 시설 안내에서 직접 확인해 주세요. 이 앱이 접근 가능 여부를 검증한 것은 아닙니다.')
        st.markdown('#### ♿ 도착역 교통약자 편의시설 확인')
        st.caption(f'도착역: {end} · 아래 버튼은 최신 시설 정보를 검색할 수 있는 외부 페이지로 연결됩니다.')
        c1,c2=st.columns(2)
        with c1:
            st.link_button('🛗 엘리베이터 유무 확인', 'https://www.google.com/search?q='+quote(f'{target}역 {line_of(end)}호선 엘리베이터 위치 운영정보'),use_container_width=True)
        with c2:
            st.link_button('♿ 휠체어 접근성 확인', 'https://www.google.com/search?q='+quote(f'{target}역 {line_of(end)}호선 휠체어 접근성 무장애 이동동선'),use_container_width=True)
        st.caption('※ 버튼은 관련 정보를 찾아주는 검색 링크입니다. 시설 존재·운행 여부를 앱에서 자동 판정하지 않습니다.')
    st.markdown('<div class="panel-head">⚖️ 탐색 방식 비교</div>',unsafe_allow_html=True)
    a=route(graph,start,end,'최단시간');b=route(graph,start,end,'최소환승')
    c1,c2=st.columns(2)
    c1.info(f'**최단시간**  ·  {a[1]}분 / 환승 {a[2]}회')
    c2.info(f'**최소환승**  ·  {b[1]}분 / 환승 {b[2]}회')
# 구간별 CSV 이동시간을 누적하여 현재 위치를 추정합니다.
# 이 시간은 실시간 열차 위치가 아니라 '안내 시작'을 누른 시점부터의 시뮬레이션입니다.
def estimated_step(path, started_at):
    elapsed = max(0, clock.time() - started_at)
    cumulative = 0
    for i, (a, b) in enumerate(zip(path, path[1:])):
        cumulative += graph[a][b] * 60
        if elapsed < cumulative:
            return i, int(elapsed), int(cumulative - elapsed)
    return len(path)-1, int(elapsed), 0

with side:
    st.markdown('<div class="panel-head">🚉 이동 안내 타임라인</div>',unsafe_allow_html=True)
    if st.button('▶ 안내 시작' if not st.session_state.guide else '↺ 안내 다시 시작',type='primary',use_container_width=True):
        st.session_state.guide=True
        st.session_state.guide_started_at=clock.time()
        st.rerun()

    @st.fragment(run_every="5s")
    def live_guide():
        if st.session_state.guide and st.session_state.guide_started_at is not None:
            idx, elapsed, remaining = estimated_step(path, st.session_state.guide_started_at)
            current=path[idx]
            st.markdown(f'🔴 **현재 위치(예상): {current}**')
            st.caption(f'안내 시작 후 {elapsed//60}분 {elapsed%60}초 경과 · CSV 구간 시간 기준')
            if idx==len(path)-1:
                st.success(f'🎉 {end} 도착 예정!')
            elif line_of(current)!=line_of(path[idx+1]):
                nxt=path[idx+1]
                onward=next((bare(x) for x in path[idx+2:] if line_of(x)==line_of(nxt)),bare(nxt))
                st.warning(f'🔔 {bare(current)}역에서 {line_of(nxt)}호선으로 환승하세요. {onward} 방면으로 이동합니다. (다음 경유역 기준)')
            else:
                st.info(f'🚇 {current} → {path[idx+1]} · 다음 역까지 약 {max(1,(remaining+59)//60)}분')
            st.markdown(timeline_html(path,idx),unsafe_allow_html=True)
            st.caption('※ 5초마다 자동 갱신되는 예상 위치입니다. 실제 열차 GPS나 운행정보와 연결되어 있지 않습니다.')
        else:
            st.markdown(timeline_html(path),unsafe_allow_html=True)
            st.caption('안내 시작을 누르면 출발역부터 시간에 따라 현재 위치(예상)가 자동 표시됩니다.')
    live_guide()
    st.caption('환승 방면은 다음 경유역 기준 안내이며 실제 승강장 행선지 표기와 다를 수 있습니다.')

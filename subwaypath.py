"""Subway shortest-path finder, deployable with Streamlit Community Cloud."""
import csv
import heapq
from pathlib import Path

import folium
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
MAX_ZOOM = 16
ESRI_TILES = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
)


@st.cache_data
def read_data():
    graph = {}
    with (BASE / "subway.csv").open(encoding="utf-8-sig", newline="") as f:
        for a, b, weight in csv.reader(f):
            graph.setdefault(a, {})[b] = int(weight)
            graph.setdefault(b, {})[a] = int(weight)
    locations = {}
    with (BASE / "subwayLocation.csv").open(encoding="utf-8-sig", newline="") as f:
        for name, lat, lon in csv.reader(f):
            locations[name.strip()] = (float(lat), float(lon))
    return graph, locations


def find_path(graph, start, end):
    queue = [(0, start)]
    distance, previous = {start: 0}, {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != distance[node]:
            continue
        if node == end:
            break
        for nxt, weight in graph[node].items():
            new_cost = cost + weight
            if new_cost < distance.get(nxt, float("inf")):
                distance[nxt], previous[nxt] = new_cost, node
                heapq.heappush(queue, (new_cost, nxt))
    if end not in distance:
        return [], 0
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return path[::-1], distance[end]


def coordinate(locations, station):
    return locations.get(station) or locations.get(station.split("(")[0].strip())


def create_map(locations, path):
    m = folium.Map(location=[37.55, 126.98], zoom_start=11,
                   tiles=None, max_zoom=MAX_ZOOM, control_scale=True)
    folium.TileLayer(
        tiles=ESRI_TILES,
        attr="Tiles © Esri",
        name="Esri Street Map",
        max_zoom=MAX_ZOOM,
        max_native_zoom=MAX_ZOOM,
    ).add_to(m)

    valid = [(station, coordinate(locations, station)) for station in path]
    valid = [(station, xy) for station, xy in valid if xy is not None]
    if valid:
        folium.PolyLine([xy for _, xy in valid], color="blue", weight=6,
                        opacity=0.9, tooltip="최단 이동 경로").add_to(m)
        for i, (station, xy) in enumerate(valid):
            color = "green" if i == 0 else "red" if i == len(valid) - 1 else "blue"
            folium.CircleMarker(
                location=xy, radius=8 if color != "blue" else 5,
                color="white", weight=2, fill=True, fill_color=color,
                fill_opacity=1, tooltip=f"{i + 1}. {station}",
            ).add_to(m)
        if len(valid) > 1:
            m.fit_bounds([xy for _, xy in valid], padding=(30, 30))
        else:
            m.location = valid[0][1]
            m.zoom_start = 14
    return m


st.set_page_config(page_title="subwaypath", page_icon="🚇", layout="wide")
st.title("🚇 지하철 최단 경로 소프트웨어")

graph, locations = read_data()
stations = sorted(graph)

with st.sidebar:
    st.header("최단 경로 찾기")
    start = st.selectbox("출발역", stations, index=stations.index("강남(2)") if "강남(2)" in stations else 0)
    end = st.selectbox("도착역", stations, index=stations.index("노원(4)") if "노원(4)" in stations else len(stations)-1)
    search = st.button("최단경로 찾기", type="primary", use_container_width=True)
    st.caption(f"지도 확대는 최대 {MAX_ZOOM}단계로 제한됩니다.")

if "route" not in st.session_state:
    st.session_state.route = None
if search:
    path, minutes = find_path(graph, start, end)
    st.session_state.route = (start, end, path, minutes)

left, right = st.columns([1, 2.2], gap="large")
with left:
    if st.session_state.route:
        from_station, to_station, path, minutes = st.session_state.route
        if path:
            st.subheader("검색 결과")
            st.metric("총 소요시간", f"{minutes}분")
            st.caption(f"{from_station} → {to_station}")
            st.markdown("**경유역 순서**")
            st.text("\n".join(f"{i}. {station}" for i, station in enumerate(path, 1)))
            missing = [s for s in path if coordinate(locations, s) is None]
            if missing:
                st.warning("일부 역의 좌표가 없어 지도에서 제외됩니다: " + ", ".join(missing))
        else:
            st.warning("연결된 경로를 찾을 수 없습니다.")
    else:
        st.info("왼쪽에서 출발역과 도착역을 선택하고 '최단경로 찾기'를 누르세요.")

with right:
    route = st.session_state.route
    path = route[2] if route and route[2] else []
    components.html(create_map(locations, path).get_root().render(), height=700, scrolling=False)

st.caption("지도: Folium / Esri World Street Map. 경로선은 실제 선로 곡선이 아닌 역 좌표를 순서대로 연결한 선입니다.")

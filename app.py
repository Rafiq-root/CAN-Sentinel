from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import dashboard.components as comp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.data_adapter import load_snapshot, frames_dataframe, alerts_dataframe, data_mode_label

st.set_page_config(page_title="CAN-SENTINEL | Automotive Cyber Defense", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")



@st.cache_data
def get_snapshot() -> dict:
    return load_snapshot()

try:
    snapshot = get_snapshot()
except Exception as exc:
    st.error(f"Could not load the dashboard snapshot: {exc}")
    st.info("Check that data/sample_snapshot.json exists and matches the V1 schema.")
    st.stop()

frames = frames_dataframe(snapshot)
alerts = alerts_dataframe(snapshot)
stats = snapshot.get("statistics", {})
ecus = snapshot.get("ecus", [])
mode = data_mode_label(snapshot)
if "investigation_status" not in st.session_state:
    st.session_state.investigation_status = {}

def section_label(number, label):
    st.markdown(f'<div class="section-label">{number} / {label}</div>', unsafe_allow_html=True)

def section_header(title, tag=""):
    st.markdown(f'<div class="section-head"><h3>{title}</h3><span class="section-tag">{tag}</span></div>', unsafe_allow_html=True)

def hero(title, subtitle, section):
    st.markdown(f"""<div class="hero"><div class="eyebrow">CAN-SENTINEL / {section}</div><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap"><div><div class="hero-title">{title}</div><div class="hero-subtitle">{subtitle}</div></div><div class="mode-pill">● {mode} DATA MODE</div></div></div>""", unsafe_allow_html=True)


def render_ecu(ecu):
    status = str(ecu.get("status", "unknown")).lower()
    dot = "warn" if status in {"degraded", "warning"} else "off" if status in {"offline", "unknown"} else ""
    st.markdown(f"""<div class="ecu-row"><div><div class="ecu-name">{ecu.get('name','Unknown ECU')}</div><div class="ecu-meta">ID {ecu.get('ecu_id','—')} · {ecu.get('frames_per_sec','—')} fps</div></div><div style="font:10px 'DM Mono',monospace;color:#a7b6ca;white-space:nowrap"><span class="status-dot {dot}"></span>{status.upper()}</div></div>""", unsafe_allow_html=True)

def render_alert(alert):
    sev = str(alert.get("severity", "INFO")).upper()
    icon = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🔵"}.get(sev,"⚪")
    st.markdown(f"""<div class="alert-card"><div class="alert-title">{icon} &nbsp;{alert.get('message','Alert')}</div><div class="alert-meta">{sev} · {alert.get('detector','Unknown detector')} · CAN {alert.get('can_id','—')} · {alert.get('timestamp','—')}</div></div>""", unsafe_allow_html=True)

def traffic_chart(data, height=280):
    if data.empty:
        st.info("No frame records are available in this snapshot."); return
    chart = data.dropna(subset=["timestamp"]).copy()
    if chart.empty:
        st.info("Frame timestamps are missing or invalid."); return
    chart["time_bin"] = chart["timestamp"].dt.floor("s")
    counts = chart.groupby("time_bin", as_index=False).size().rename(columns={"size":"frames"})
    fig = px.area(counts, x="time_bin", y="frames")
    fig.update_traces(line=dict(color="#c7ff5e",width=2.5),fillcolor="rgba(199,255,94,.12)",hovertemplate="Time: %{x}<br>Frames: %{y}<extra></extra>")
    fig.update_layout(height=height,margin=dict(l=5,r=8,t=12,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Mono, monospace",color="#91a0b8",size=10),xaxis_title=None,yaxis_title="Frames / second",showlegend=False,hovermode="x unified",xaxis=dict(showgrid=False,linecolor="#29394d",tickformat="%H:%M:%S"),yaxis=dict(gridcolor="#202d3e",zeroline=False,rangemode="tozero",autorange=True))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# Sidebar
with st.sidebar:
    st.markdown("""<div class="brand"><div class="brand-icon">⌁</div><div><div class="brand-name">CAN<span>-SENTINEL</span></div><div class="brand-sub">AUTOMOTIVE CYBER DEFENSE</div></div></div><div class="eyebrow">01 / WORKSPACE</div>""",unsafe_allow_html=True)
    page = st.radio("Navigation",["Command Center","Live Traffic","Alert Investigation","System & Integration"],label_visibility="collapsed",key="main_navigation")
    st.markdown('<div style="height:1px;background:rgba(130,159,192,.2);margin:20px 0 15px"></div><div class="eyebrow">02 / SESSION</div>',unsafe_allow_html=True)
    st.markdown(f"""<div class="sidebar-session"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:15px"><span style="font:10px 'DM Mono',monospace;color:#91a0b6">SNAPSHOT SESSION</span><span style="font:9px 'DM Mono',monospace;color:#c7ff5e;background:rgba(199,255,94,.09);border:1px solid rgba(199,255,94,.25);padding:4px 7px;border-radius:99px">● DEMO</span></div><div class="sidebar-caption">RUN IDENTIFIER</div><div class="sidebar-value">{snapshot.get("run_id","—")}</div><div class="sidebar-caption" style="margin-top:14px">SNAPSHOT GENERATED</div><div class="sidebar-value">{snapshot.get("generated_at","—")}</div></div>""",unsafe_allow_html=True)
    if st.button("↻  RELOAD SNAPSHOT",use_container_width=True,key="reload_snapshot"):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div class="glass-panel" style="margin-top:17px;padding:12px"><div class="eyebrow">V1 / DASHBOARD MVP</div><div style="color:#8797ac;font-size:10px;line-height:1.7">Illustrative snapshot data only. This dashboard does not represent live vehicle telemetry.</div></div>',unsafe_allow_html=True)

def render_command_center():
    hero("Automotive Defense Console","CAN network observability · ECU health · security event triage","MISSION CONTROL")
    total = int(stats.get("total_frames",len(frames))); fps = stats.get("frames_per_second"); load = stats.get("bus_load_pct")
    online = sum(str(e.get("status","")).lower()=="online" for e in ecus)
    critical = sum(str(a.get("severity","")).upper()=="CRITICAL" for a in snapshot.get("alerts",[]))
    high = sum(str(a.get("severity","")).upper()=="HIGH" for a in snapshot.get("alerts",[]))
    cols=st.columns(4,gap="medium")
    values=[("FRAMES OBSERVED",f"{total:,}","Records in loaded snapshot","#c7ff5e"),("FRAME RATE",f"{fps:.1f} fps" if isinstance(fps,(int,float)) else "N/A","Snapshot-reported value","#54e6dc"),("BUS UTILIZATION",f"{load:.1f}%" if isinstance(load,(int,float)) else "N/A","Not a live bus measurement","#aaa3ff"),("ONLINE ECUs",f"{online}/{len(ecus)}",f"{critical} critical · {high} high event(s)","#ffc766")]
    for col,item in zip(cols,values):
        with col: comp.metric_card(*item)
    left,right=st.columns([1.35,1],gap="large")
    with left:
        section_label("01","NETWORK TELEMETRY"); section_header("Traffic activity","SNAPSHOT DATA"); traffic_chart(frames,300)
        section_label("02","FRAME FORENSICS"); section_header("Recent CAN frames","LATEST RECORDS")
        recent=frames.tail(10).copy()
        if not recent.empty:
            recent["timestamp"]=recent["timestamp"].dt.strftime("%H:%M:%S UTC")
            st.dataframe(recent[["timestamp","can_id","dlc","payload","source_ecu","label"]],use_container_width=True,hide_index=True)
        else: st.info("No frame records are available in this snapshot.")
        if not frames.empty: st.download_button("↓ Export CAN frame records",frames.to_csv(index=False).encode(), "can_sentinel_frames.csv","text/csv",use_container_width=True)
    with right:
        section_label("03","ECU FLEET")
        degraded=sum(str(e.get("status","")).lower() in {"degraded","warning"} for e in ecus)
        offline=sum(str(e.get("status","")).lower()=="offline" for e in ecus)
        pct=online/len(ecus)*100 if ecus else 0
        st.markdown(f"""<div class="network-health"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px"><div><div class="metric-label">NETWORK HEALTH</div><div class="health-number">{online}<span style="font-size:13px;color:#91a0b8;font-weight:600"> / {len(ecus)} online</span></div><div class="metric-note">ECU status in current snapshot</div></div><div class="brand-icon" style="width:44px;height:44px;flex-shrink:0">⌁</div></div><div class="health-track"><div class="health-fill" style="width:{pct:.0f}%"></div></div><div class="health-grid"><div class="health-cell health-online"><div class="health-cell-label">ONLINE</div><div class="health-cell-value">{online}</div></div><div class="health-cell health-degraded"><div class="health-cell-label">DEGRADED</div><div class="health-cell-value">{degraded}</div></div><div class="health-cell health-offline"><div class="health-cell-label">OFFLINE</div><div class="health-cell-value">{offline}</div></div></div></div>""",unsafe_allow_html=True)
        section_header("ECU inventory",f"{len(ecus)} NODES")
        with st.container(border=True):
            if ecus:
                for ecu in ecus: render_ecu(ecu)
            else: st.caption("No ECU status records are available.")
        section_label("04","THREAT MONITOR")
        raw=sorted(snapshot.get("alerts",[]),key=lambda a:({"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}.get(str(a.get("severity","INFO")).upper(),4),str(a.get("timestamp",""))))
        section_header("Security events",f"{len(raw)} SNAPSHOT RECORDS")
        if raw:
            for alert in raw[:4]: render_alert(alert)
        else: st.success("No alert events in this snapshot.")
        st.caption("Alert records may not equal unique attacks or unique frames. Validate against frame evidence and simulator ground truth.")

def render_traffic():
    hero("CAN Traffic Explorer","Filter and inspect the available CAN frame records.","TELEMETRY")
    st.info("V1 uses a static snapshot. Live streaming will be connected when the team agrees on the simulator and event interface.")
    if frames.empty: st.warning("No CAN frames are available in the current snapshot."); return
    a,b,c=st.columns([1,1,1.5],gap="medium")
    ids=sorted(frames["can_id"].dropna().astype(str).unique()); labels=sorted(frames["label"].dropna().astype(str).unique())
    with a: chosen_ids=st.multiselect("Filter CAN IDs",ids,default=ids)
    with b: chosen_labels=st.multiselect("Traffic label",labels,default=labels)
    with c: query=st.text_input("Search traffic",placeholder="CAN ID, payload, ECU...")
    data=frames.copy()
    data=data[data["can_id"].astype(str).isin(chosen_ids)] if chosen_ids else data.iloc[0:0]
    data=data[data["label"].astype(str).isin(chosen_labels)] if chosen_labels else data.iloc[0:0]
    if query:
        term=query.lower(); data=data[data.apply(lambda r:term in " ".join(str(v) for v in r.values).lower(),axis=1)]
    c1,c2,c3=st.columns(3)
    with c1: comp.metric_card("VISIBLE RECORDS",f"{len(data):,}",f"Of {len(frames):,} snapshot records","#c7ff5e")
    with c2: comp.metric_card("UNIQUE CAN IDs",str(data["can_id"].nunique()),"Within current filters","#54e6dc")
    with c3:
        low=data["dlc"].min() if not data.empty else "—"; high=data["dlc"].max() if not data.empty else "—"
        comp.metric_card("PAYLOAD LENGTH",f"{low}–{high}","DLC values in filtered view","#aaa3ff")
    section_header("Frame stream",f"{len(data)} MATCHING RECORDS")
    output=data.copy()
    if not output.empty: output["timestamp"]=output["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S.%f UTC")
    st.dataframe(output,use_container_width=True,hide_index=True,height=380)
    st.download_button("↓ Export filtered frames",data.to_csv(index=False).encode(),"can_sentinel_filtered_frames.csv","text/csv",use_container_width=True)
    section_header("Traffic distribution","TOP CAN IDs")
    counts=data["can_id"].value_counts().head(15).rename_axis("CAN ID").reset_index(name="Frame count")
    if not counts.empty:
        fig=px.bar(counts,x="CAN ID",y="Frame count")
        fig.update_traces(marker_color="#c7ff5e",hovertemplate="CAN ID: %{x}<br>Frames: %{y}<extra></extra>")
        fig.update_layout(height=300,margin=dict(l=5,r=5,t=15,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="DM Mono, monospace",color="#91a0b8",size=10),xaxis_title=None,yaxis=dict(gridcolor="#202d3e",zeroline=False))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

def render_alerts():
    hero("Security Event Investigation","Review detector events, examine available evidence, and manage triage.","THREAT RESPONSE")
    st.info("Severity is not proof of malicious activity. Validate each event against frame evidence, simulator ground truth, and detector semantics.")
    if alerts.empty: st.success("No alerts are available in the current snapshot."); return
    a,b,c=st.columns([1,1,1.5],gap="medium")
    severities=sorted(alerts["severity"].dropna().astype(str).unique()); detectors=sorted(alerts["detector"].dropna().astype(str).unique())
    with a: chosen_sev=st.multiselect("Severity",severities,default=severities)
    with b: chosen_det=st.multiselect("Detector",detectors,default=detectors)
    with c: query=st.text_input("Search alerts",placeholder="Message, CAN ID, detector...")
    data=alerts.copy()
    data=data[data["severity"].astype(str).isin(chosen_sev)] if chosen_sev else data.iloc[0:0]
    data=data[data["detector"].astype(str).isin(chosen_det)] if chosen_det else data.iloc[0:0]
    if query:
        term=query.lower(); data=data[data.apply(lambda r:term in " ".join(str(v) for v in r.values).lower(),axis=1)]
    cols=st.columns(4)
    for col,sev,accent in zip(cols,["CRITICAL","HIGH","MEDIUM","LOW"],["#ff657a","#ff9b54","#ffc766","#54e6dc"]):
        with col: comp.metric_card(sev,str((alerts["severity"].astype(str).str.upper()==sev).sum()),"Events in loaded snapshot",accent)
    section_header("Investigation queue",f"{len(data)} MATCHING EVENTS")
    view=data.copy()
    view["triage_status"]=view["alert_id"].astype(str).map(st.session_state.investigation_status).fillna(view["status"].fillna("NEW"))
    if not view.empty:
        table=view[["timestamp","severity","detector","can_id","message","frame_ref","triage_status"]].copy()
        table["timestamp"]=table["timestamp"].dt.strftime("%H:%M:%S UTC")
        st.dataframe(table,use_container_width=True,hide_index=True)
    options=data["alert_id"].astype(str).tolist()
    if not options: st.info("No events match the current filters."); return
    selected=st.selectbox("Select an event to investigate",options,format_func=lambda aid:f"{aid} — {data.loc[data['alert_id'].astype(str)==aid,'message'].iloc[0]}")
    record=data[data["alert_id"].astype(str)==selected].iloc[0]
    left,right=st.columns([1.3,1],gap="large")
    with left:
        section_header("Event details","AVAILABLE EVIDENCE")
        with st.container(border=True):
            st.markdown(f"### {record['message']}")
            for label,key in [("Alert ID","alert_id"),("Severity","severity"),("Detector","detector"),("CAN ID","can_id"),("Frame reference","frame_ref"),("Timestamp","timestamp")]: st.write(f"**{label}:**",str(record[key]))
        can_id=str(record["can_id"]).upper(); matching=frames[frames["can_id"].astype(str).str.upper()==can_id]
        section_header("Related CAN frames",f"{len(matching)} MATCHES")
        if not matching.empty: st.dataframe(matching,use_container_width=True,hide_index=True)
        else: st.warning("No matching CAN frame was found in this snapshot. Frame evidence may not have been exported.")
    with right:
        section_header("Triage workflow","SESSION ONLY")
        statuses=["NEW","INVESTIGATING","CONFIRMED","FALSE_POSITIVE","CLOSED"]
        current=st.session_state.investigation_status.get(str(selected),str(record["status"]) if pd.notna(record["status"]) else "NEW")
        if current not in statuses: current="NEW"
        new=st.selectbox("Investigation status",statuses,index=statuses.index(current))
        if st.button("Save triage status",use_container_width=True):
            st.session_state.investigation_status[str(selected)]=new; st.success("Status saved in this browser session.")
        st.markdown('<div class="glass-panel" style="margin-top:15px"><div class="eyebrow">INVESTIGATION NOTE</div><div style="font-size:12px;line-height:1.8;color:#aab8ca">V1 stores triage state in the current Streamlit session. Persistent incident storage has not been implemented.</div></div>',unsafe_allow_html=True)

def render_system():
    hero("Platform & Integration","Review data quality, integration readiness, and detector evaluation availability.","PLATFORM HEALTH")
    integration=snapshot.get("integration",{})
    checks=[
        ("Dashboard snapshot adapter",True,"JSON snapshot was loaded by the dashboard."),
        ("Simulator / frame producer",bool(integration.get("simulator_connected",False)),integration.get("simulator_note","Awaiting the agreed interface from Member 1.")),
        ("IDS output",bool(integration.get("ids_connected",False)),integration.get("ids_note","Awaiting the agreed interface from Member 2.")),
        ("Alert management output",bool(integration.get("alert_manager_connected",False)),integration.get("alert_manager_note","Awaiting the agreed interface from Member 3.")),
        ("Persistent triage storage",False,"Not implemented in V1."),
        ("Live streaming",False,"V1 currently reads a static snapshot."),
    ]
    section_header("Integration readiness","V1 COMPONENT STATUS")
    for name,ready,detail in checks:
        left,middle,right=st.columns([1.2,.6,2.2],gap="medium")
        with left: st.markdown(f"**{name}**")
        with middle:
            if ready: st.success("READY")
            else: st.warning("PENDING")
        with right: st.markdown(f'<div style="color:#91a0b8;font-size:11px;line-height:1.7">{detail}</div>',unsafe_allow_html=True)
        st.markdown("<div style='height:1px;background:rgba(130,159,192,.16);margin:8px 0'></div>",unsafe_allow_html=True)
    left,right=st.columns(2,gap="large")
    with left:
        section_header("Snapshot contract","DATA QUALITY")
        with st.container(border=True):
            for label,value in [("Schema version",snapshot.get("schema_version","N/A")),("Run ID",snapshot.get("run_id","N/A")),("Run status",snapshot.get("status","N/A")),("Data mode",mode),("Generated at",snapshot.get("generated_at","N/A")),("Frames loaded",len(frames)),("Alert records loaded",len(alerts)),("ECUs listed",len(ecus))]: st.write(f"**{label}:**",value)
    with right:
        section_header("Detector metrics","VALIDATION STATUS")
        metrics=snapshot.get("detection_metrics",{})
        if metrics.get("validated") is True:
            with st.container(border=True):
                for key in ["precision","recall","f1","false_positive_rate","latency_ms"]:
                    value=metrics.get(key); st.write(key.replace("_"," ").title(),f"{value:.3f}" if isinstance(value,(int,float)) else "N/A")
        else: st.info("Precision, recall, F1, false-positive rate, and latency remain N/A until validated predictions and a labelled evaluation dataset are available.")
    with st.expander("Inspect raw snapshot JSON"): st.json(snapshot)

if page=="Command Center": render_command_center()
elif page=="Live Traffic": render_traffic()
elif page=="Alert Investigation": render_alerts()
else: render_system()

st.markdown("""<div style="border-top:1px solid rgba(130,159,192,.18);margin-top:32px;padding-top:15px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;color:#7789a0;font:10px 'DM Mono',monospace;letter-spacing:.04em"><span>CAN-SENTINEL · AUTOMOTIVE CYBER DEFENSE · V1</span><span>SIMULATION DATA ≠ LIVE VEHICLE TELEMETRY</span></div>""",unsafe_allow_html=True)

import dashboard.components as comp
comp.inject_theme()

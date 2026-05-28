import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Task Audit Analyser",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #fafafa; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.empty-state { text-align: center; padding: 60px 20px; color: #9ca3af; }
.insight-box {
    background: #f0f7ff; border-left: 3px solid #2563eb;
    border-radius: 0 6px 6px 0; padding: 14px 18px;
    margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #1e3a5f;
}
.stat-card {
    background: white; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 16px 20px; text-align: center;
}
.stat-num { font-size: 28px; font-weight: 700; color: #111827; line-height: 1; }
.stat-lbl { font-size: 12px; color: #6b7280; margin-top: 4px; }
.format-badge {
    display: inline-block; font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 10px; margin-bottom: 12px;
}
.badge-gform    { background: #dcfce7; color: #166534; }
.badge-standard { background: #eff6ff; color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

ROLE_COLORS = {
    "Head of Digital Product":      "#2563eb",
    "Product Manager":              "#7c3aed",
    "Marketing Manager":            "#0891b2",
    "Digital Marketing Specialist": "#d97706",
    "Customer Experience Lead":     "#059669",
}
DEFAULT_COLOR = "#64748b"

# Task blocks by column position (0-indexed)
# Col 0: Timestamp, Col 1: Name, Col 2: Job title
# Task 1: cols 3 (desc), 4 (hours), 5 (judgment)
# Task 2: cols 6 (desc), 7 (hours), 8 (judgment)  -- col 9 = hindrance (skip)
# Task 3: cols 10 (desc), 11 (hours), 12 (judgment) -- col 13 = hindrance (skip)
# Task 4: cols 14 (desc), 15 (hours), 16 (judgment) -- col 17 = hindrance (skip)
# Task 5: cols 18 (desc), 19 (hours), 20 (judgment)
TASK_POSITIONS = [(3,4,5),(6,7,8),(10,11,12),(14,15,16),(18,19,20)]

SAMPLE_DATA = pd.DataFrame([
    {"Name":"Sandra Okafor","Role":"Head of Digital Product","Task":"Searching policy documents for member answers","Time per week (hrs)":5,"Manual effort (1-5)":5},
    {"Name":"Sandra Okafor","Role":"Head of Digital Product","Task":"Reviewing portal feedback and bug reports","Time per week (hrs)":4,"Manual effort (1-5)":4},
    {"Name":"Sandra Okafor","Role":"Head of Digital Product","Task":"Responding to internal stakeholder queries","Time per week (hrs)":3,"Manual effort (1-5)":3},
    {"Name":"Sandra Okafor","Role":"Head of Digital Product","Task":"Updating product roadmap documentation","Time per week (hrs)":3,"Manual effort (1-5)":3},
    {"Name":"Sandra Okafor","Role":"Head of Digital Product","Task":"Coordinating sprint priorities with dev team","Time per week (hrs)":2,"Manual effort (1-5)":2},
    {"Name":"James Tran","Role":"Product Manager","Task":"Manual claims triage and categorisation","Time per week (hrs)":8,"Manual effort (1-5)":5},
    {"Name":"James Tran","Role":"Product Manager","Task":"Cross-checking policy rules against claim details","Time per week (hrs)":6,"Manual effort (1-5)":5},
    {"Name":"James Tran","Role":"Product Manager","Task":"Writing compliance audit notes","Time per week (hrs)":4,"Manual effort (1-5)":4},
    {"Name":"James Tran","Role":"Product Manager","Task":"Preparing weekly claims summary reports","Time per week (hrs)":3,"Manual effort (1-5)":4},
    {"Name":"James Tran","Role":"Product Manager","Task":"Escalation handling and case reviews","Time per week (hrs)":3,"Manual effort (1-5)":3},
    {"Name":"Melissa Hartley","Role":"Marketing Manager","Task":"Manual compliance review of campaign copy","Time per week (hrs)":5,"Manual effort (1-5)":5},
    {"Name":"Melissa Hartley","Role":"Marketing Manager","Task":"Writing member communication templates","Time per week (hrs)":4,"Manual effort (1-5)":4},
    {"Name":"Melissa Hartley","Role":"Marketing Manager","Task":"Pulling campaign performance reports","Time per week (hrs)":3,"Manual effort (1-5)":4},
    {"Name":"Melissa Hartley","Role":"Marketing Manager","Task":"Briefing and reviewing agency creative","Time per week (hrs)":4,"Manual effort (1-5)":3},
    {"Name":"Melissa Hartley","Role":"Marketing Manager","Task":"Coordinating approvals across legal and compliance","Time per week (hrs)":3,"Manual effort (1-5)":3},
    {"Name":"David Nguyen","Role":"Digital Marketing Specialist","Task":"Manually merging data from multiple platforms","Time per week (hrs)":6,"Manual effort (1-5)":5},
    {"Name":"David Nguyen","Role":"Digital Marketing Specialist","Task":"Building and exporting performance dashboards","Time per week (hrs)":5,"Manual effort (1-5)":5},
    {"Name":"David Nguyen","Role":"Digital Marketing Specialist","Task":"Identifying at-risk members from behavioural data","Time per week (hrs)":4,"Manual effort (1-5)":5},
    {"Name":"David Nguyen","Role":"Digital Marketing Specialist","Task":"Setting up and monitoring paid media campaigns","Time per week (hrs)":4,"Manual effort (1-5)":3},
    {"Name":"David Nguyen","Role":"Digital Marketing Specialist","Task":"Weekly reporting to marketing leadership","Time per week (hrs)":3,"Manual effort (1-5)":4},
    {"Name":"Priya Sharma","Role":"Customer Experience Lead","Task":"Gathering member context before complaint calls","Time per week (hrs)":7,"Manual effort (1-5)":5},
    {"Name":"Priya Sharma","Role":"Customer Experience Lead","Task":"Logging and categorising complaint types","Time per week (hrs)":4,"Manual effort (1-5)":5},
    {"Name":"Priya Sharma","Role":"Customer Experience Lead","Task":"Cross-referencing member history across systems","Time per week (hrs)":5,"Manual effort (1-5)":5},
    {"Name":"Priya Sharma","Role":"Customer Experience Lead","Task":"Preparing monthly CX trend reports","Time per week (hrs)":4,"Manual effort (1-5)":4},
    {"Name":"Priya Sharma","Role":"Customer Experience Lead","Task":"Following up on unresolved complaints","Time per week (hrs)":3,"Manual effort (1-5)":3},
])

# ── FORMAT DETECTION ──────────────────────────────────────────────────────────
def is_actual_google_form(df):
    """Detect the specific form structure by checking for the hindrance question."""
    headers = " ".join(df.columns.tolist()).lower()
    return "value-adding" in headers or "hindrance" in headers

def is_generic_google_form(df):
    headers = " ".join(df.columns.tolist()).lower()
    return "task 1" in headers or "task1" in headers

# ── RESHAPE: ACTUAL FORM ──────────────────────────────────────────────────────
def reshape_actual_form(df):
    """
    Reshape the specific Pre-Session Task Audit form.
    Uses column positions since question text repeats across task blocks.
    Judgment scale is INVERTED: 1=lots of judgment (low automation), 5=little judgment (high automation).
    Manual effort = 6 - judgment so that higher = more automatable.
    """
    rows = []
    for _, row in df.iterrows():
        name = str(row.iloc[1]).strip() if len(row) > 1 else ""
        role = str(row.iloc[2]).strip() if len(row) > 2 else ""

        for desc_i, hrs_i, jdg_i in TASK_POSITIONS:
            if desc_i >= len(row):
                break

            task_name = str(row.iloc[desc_i]).strip()
            if not task_name or task_name.lower() in ["nan","none",""]:
                continue

            hours    = pd.to_numeric(row.iloc[hrs_i] if hrs_i < len(row) else None, errors="coerce")
            judgment = pd.to_numeric(row.iloc[jdg_i] if jdg_i < len(row) else None, errors="coerce")

            # Invert judgment: 1 (high judgment) -> 5 (low automation), 5 (low judgment) -> 1 (high automation)
            # We flip so that manual_effort 5 = most repetitive / least judgment needed
            if pd.notna(judgment):
                manual = max(1.0, min(5.0, 6.0 - float(judgment)))
            else:
                manual = 3.0

            rows.append({
                "Name":               name,
                "Role":               role,
                "Task":               task_name,
                "Time per week (hrs)":float(hours) if pd.notna(hours) else 2.0,
                "Manual effort (1-5)":manual,
            })

    return pd.DataFrame(rows)

# ── RESHAPE: GENERIC GOOGLE FORM ─────────────────────────────────────────────
def reshape_generic_form(df):
    rows = []
    name_col = next((c for c in df.columns if "name" in c.lower() and "task" not in c.lower()), None)
    role_col = next((c for c in df.columns if any(x in c.lower() for x in ["role","title","position"])), None)

    for _, row in df.iterrows():
        name = str(row[name_col]).strip() if name_col else ""
        role = str(row[role_col]).strip() if role_col else ""
        for i in range(1, 6):
            task_name = hours = manual = None
            for col in df.columns:
                cl = col.lower()
                if f"task {i}" not in cl and f"task{i}" not in cl:
                    continue
                val = row[col]
                if any(x in cl for x in ["name","activity","description"]):
                    task_name = val
                elif any(x in cl for x in ["hour","time","week"]):
                    hours = val
                elif any(x in cl for x in ["manual","repetitive","judgment","scale"]):
                    manual = val
            if task_name and str(task_name).strip().lower() not in ["nan","none",""]:
                rows.append({
                    "Name":               name,
                    "Role":               role,
                    "Task":               str(task_name).strip(),
                    "Time per week (hrs)":pd.to_numeric(hours,  errors="coerce") or 2.0,
                    "Manual effort (1-5)":pd.to_numeric(manual, errors="coerce") or 3.0,
                })
    return pd.DataFrame(rows)

# ── NORMALISE LONG FORMAT ─────────────────────────────────────────────────────
def normalise_long(df):
    aliases = {
        "Name":               ["name","participant","full name"],
        "Role":               ["role","title","job title","position"],
        "Task":               ["task","task name","activity"],
        "Time per week (hrs)":["time per week","hours per week","time (hrs)","hours","time per week (hrs)"],
        "Manual effort (1-5)":["manual effort","manual effort (1-5)","manual","manual score","repetitive"],
    }
    rename = {}
    for std, opts in aliases.items():
        for col in df.columns:
            if col.lower().strip() in opts:
                rename[col] = std
                break
    return df.rename(columns=rename)

# ── LOAD AND PREPARE ──────────────────────────────────────────────────────────
def load_and_prepare(uploaded_file):
    df_raw = pd.read_csv(uploaded_file)

    if is_actual_google_form(df_raw):
        # Pass raw df WITH timestamp so column positions match the form structure
        # reshape_actual_form uses positional indexing: col 0=Timestamp, 1=Name, 2=Job title
        df  = reshape_actual_form(df_raw)
        fmt = "google_form"
    elif is_generic_google_form(df_raw):
        df_clean = df_raw.loc[:, ~df_raw.columns.str.lower().str.contains("timestamp")]
        df  = reshape_generic_form(df_clean)
        fmt = "google_form"
    else:
        df_clean = df_raw.loc[:, ~df_raw.columns.str.lower().str.contains("timestamp")]
        df  = normalise_long(df_clean)
        fmt = "standard"

    required = ["Name","Role","Task","Time per week (hrs)","Manual effort (1-5)"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        return None, None, f"Could not map columns: {', '.join(missing)}. Download the sample CSV to check the expected format."

    df["Time per week (hrs)"] = pd.to_numeric(df["Time per week (hrs)"], errors="coerce").fillna(2.0)
    df["Manual effort (1-5)"] = pd.to_numeric(df["Manual effort (1-5)"], errors="coerce").fillna(3.0)
    df["_opportunity"]        = (df["Manual effort (1-5)"] * df["Time per week (hrs)"]).round(2)
    df["_color"]              = df["Role"].map(ROLE_COLORS).fillna(DEFAULT_COLOR)

    return df, fmt, None

def get_color(role):
    return ROLE_COLORS.get(role, DEFAULT_COLOR)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### About")
    st.caption(
        "Tool 1 of 2 in the AI Discovery Workshop Suite. "
        "Upload the Pre-Session Task Audit CSV to surface where manual effort "
        "concentrates before the workshop begins."
    )
    st.divider()
    st.markdown("**Accepted formats**")
    st.markdown("""<div style="font-size:12px;color:#6b7280;line-height:1.9;">
    <b>Pre-Session Task Audit (Google Forms)</b><br>
    Download directly from the linked Google Sheet as CSV. Detected automatically.<br><br>
    <b>Standard CSV</b><br>
    One row per task. Columns: Name, Role, Task, Time per week (hrs), Manual effort (1-5).
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("**Judgment scale note**")
    st.caption(
        "The form asks how much personal judgment a task requires. "
        "This is inverted for scoring: tasks requiring less judgment score higher "
        "on manual effort because they are more repetitive and more automatable."
    )
    st.divider()
    st.markdown("**Opportunity score**")
    st.caption("Manual effort (inverted judgment) multiplied by hours per week.")
    st.divider()
    sample_csv = SAMPLE_DATA.to_csv(index=False)
    st.download_button("Download sample CSV", sample_csv,
                       "task_audit_sample.csv", "text/csv", use_container_width=True)
    if st.button("Load sample data", use_container_width=True):
        df_s = SAMPLE_DATA.copy()
        df_s["_opportunity"] = (df_s["Manual effort (1-5)"] * df_s["Time per week (hrs)"]).round(2)
        df_s["_color"]       = df_s["Role"].map(ROLE_COLORS).fillna(DEFAULT_COLOR)
        st.session_state.df  = df_s
        st.session_state.fmt = "standard"
        st.rerun()
    if "df" in st.session_state:
        if st.button("Clear data", use_container_width=True):
            st.session_state.pop("df", None)
            st.session_state.pop("fmt", None)
            st.rerun()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("## Task audit analyser")
st.caption("Pre-work synthesis tool — upload Google Form responses to surface automation opportunities before the workshop.")
st.divider()

# ── UPLOAD ────────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    uploaded = st.file_uploader("Upload participant responses as CSV", type=["csv"])
    if uploaded:
        df, fmt, err = load_and_prepare(uploaded)
        if err:
            st.error(err)
        else:
            st.session_state.df  = df
            st.session_state.fmt = fmt
            st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:36px;margin-bottom:14px;">◎</div>
            <div style="font-size:16px;font-weight:500;color:#6b7280;margin-bottom:8px;">No data uploaded yet</div>
            <div style="font-size:13px;color:#9ca3af;line-height:1.8;">
                Upload the Google Form CSV above, or load the demo dataset from the sidebar.
            </div>
        </div>""", unsafe_allow_html=True)
    st.stop()

df  = st.session_state.df.copy()
fmt = st.session_state.fmt

# ── FORMAT BADGE ──────────────────────────────────────────────────────────────
badge_label = "Google Forms CSV detected" if fmt == "google_form" else "Standard CSV detected"
badge_class = "badge-gform"              if fmt == "google_form" else "badge-standard"
st.markdown(f'<span class="format-badge {badge_class}">{badge_label}</span>', unsafe_allow_html=True)

# ── SUMMARY STATS ─────────────────────────────────────────────────────────────
avg_hrs_per_person = df.groupby("Name")["Time per week (hrs)"].mean()
avg_hrs_overall    = round(avg_hrs_per_person.mean(), 1)
c1,c2,c3,c4 = st.columns(4)
for col,num,lbl in [
    (c1, df["Name"].nunique(),               "Participants"),
    (c2, len(df),                            "Tasks logged"),
    (c3, f"{avg_hrs_overall}h",              "Avg hrs per task per person"),
    (c4, f"{df['Manual effort (1-5)'].mean():.1f}/5","Avg manual effort"),
]:
    with col:
        st.markdown(f'<div class="stat-card"><div class="stat-num">{num}</div>'
                    f'<div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── INSIGHT ───────────────────────────────────────────────────────────────────
top_task = df.loc[df["_opportunity"].idxmax()]
top_role = df.groupby("Role")["Time per week (hrs)"].sum().idxmax()
st.markdown(f"""
<div class="insight-box">
    <b>Pre-work headline:</b> The highest opportunity task is
    <b>{top_task['Task']}</b> ({top_task['Name']}, {top_task['Role']}),
    scoring {top_task['_opportunity']} on the opportunity index.
    The role carrying the heaviest manual burden overall is <b>{top_role}</b>.
    Prioritise both in the Block 1 go-around.
</div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4 = st.tabs(["Opportunity map","Burden by role","Top tasks","Raw data"])

# TAB 1: OPPORTUNITY MAP
with tab1:
    st.markdown("#### Task opportunity map")
    st.caption(
        "Each bubble is one task. X axis is manual effort (inverted judgment score). "
        "Y axis is hours per week. Top-right = high priority AI candidates. Bubble size reflects opportunity score."
    )
    roles = df["Role"].unique()
    fig = go.Figure()
    for role in roles:
        sub = df[df["Role"]==role]
        fig.add_trace(go.Scatter(
            x=sub["Manual effort (1-5)"], y=sub["Time per week (hrs)"],
            mode="markers",
            marker=dict(size=sub["_opportunity"]*1.8+8, color=get_color(role),
                        opacity=0.8, line=dict(width=1.5,color="white")),
            name=role,
            customdata=sub[["Task","Name","_opportunity"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Manual effort: %{x:.1f}/5<br>Hours/week: %{y}<br>"
                "Opportunity score: %{customdata[2]}<extra></extra>"
            )
        ))
    fig.add_hline(y=df["Time per week (hrs)"].median(),
                  line_dash="dot", line_color="#d1d5db", line_width=1)
    fig.add_vline(x=3, line_dash="dot", line_color="#d1d5db", line_width=1)
    for ann in [
        (4.5, df["Time per week (hrs)"].max()*0.94, "High priority"),
        (1.5, df["Time per week (hrs)"].max()*0.94, "High time, low manual"),
        (4.5, df["Time per week (hrs)"].min()*1.3,  "High manual, low time"),
        (1.5, df["Time per week (hrs)"].min()*1.3,  "Deprioritise"),
    ]:
        fig.add_annotation(x=ann[0],y=ann[1],text=ann[2],showarrow=False,
            font=dict(size=10,color="#c4c4c4"),xanchor="center")
    fig.update_layout(
        xaxis=dict(title="Manual effort  (1 = judgment-heavy · 5 = fully repetitive)",
                   range=[0.5,5.8],showgrid=False,zeroline=False,tickvals=[1,2,3,4,5]),
        yaxis=dict(title="Hours per week",showgrid=False,zeroline=False),
        plot_bgcolor="white",paper_bgcolor="white",
        legend=dict(orientation="h",yanchor="top",y=-0.18,xanchor="left",x=0),
        height=500,margin=dict(l=20,r=20,t=20,b=110),
        font=dict(family="sans-serif",size=12)
    )
    st.plotly_chart(fig,use_container_width=True)

# TAB 2: BURDEN BY ROLE
with tab2:
    st.markdown("#### Manual burden by role")
    role_sum = (df.groupby("Role")
                .agg(total_hours=("Time per week (hrs)","sum"),
                     avg_manual=("Manual effort (1-5)","mean"),
                     tasks=("Task","count"))
                .reset_index()
                .sort_values("total_hours",ascending=True))
    role_sum["_color"] = role_sum["Role"].apply(get_color)
    fig2 = go.Figure(go.Bar(
        x=role_sum["total_hours"], y=role_sum["Role"], orientation="h",
        marker=dict(color=role_sum["_color"],opacity=0.85),
        customdata=role_sum[["avg_manual","tasks"]].values,
        hovertemplate=("<b>%{y}</b><br>Total hrs/week: %{x}<br>"
                       "Avg manual effort: %{customdata[0]:.1f}/5<br>"
                       "Tasks logged: %{customdata[1]}<extra></extra>")
    ))
    fig2.update_layout(
        xaxis=dict(title="Total hours per week",showgrid=True,
                   gridcolor="#f3f4f6",zeroline=False),
        yaxis=dict(showgrid=False,zeroline=False),
        plot_bgcolor="white",paper_bgcolor="white",showlegend=False,
        height=320,margin=dict(l=20,r=40,t=20,b=40),
        font=dict(family="sans-serif",size=12)
    )
    st.plotly_chart(fig2,use_container_width=True)

# TAB 3: TOP TASKS
with tab3:
    st.markdown("#### Highest opportunity tasks")
    st.caption("Carry these into the Block 1 go-around. These are where the most time is lost on the most repetitive work.")
    top_n  = st.slider("Show top N tasks",3,min(20,len(df)),min(10,len(df)))
    top_df = df.nlargest(top_n,"_opportunity")
    colors = ["#2563eb","#7c3aed","#0891b2","#d97706","#059669"]
    max_s  = df["_opportunity"].max()
    for i,(_,row) in enumerate(top_df.iterrows()):
        color = colors[i % len(colors)]
        rc    = get_color(row["Role"])
        pct   = round(row["_opportunity"]/max_s*100)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;padding:12px 16px;
             border-radius:8px;border:1px solid #e5e7eb;border-left:4px solid {rc};
             margin-bottom:8px;background:white;">
            <div style="font-size:16px;font-weight:700;color:{color};
                 min-width:24px;text-align:center;">{i+1}</div>
            <div style="flex:1;">
                <div style="font-size:14px;font-weight:600;color:#111827;
                     margin-bottom:2px;">{row['Task']}</div>
                <div style="font-size:12px;color:#6b7280;">
                    {row['Name']} — {row['Role']}</div>
                <div style="height:4px;background:#f3f4f6;border-radius:2px;margin-top:8px;">
                    <div style="height:4px;width:{pct}%;background:{color};border-radius:2px;"></div>
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:20px;font-weight:700;color:{color};
                     line-height:1;">{row['_opportunity']}</div>
                <div style="font-size:10px;color:#9ca3af;">opp. score</div>
            </div>
            <div style="text-align:right;flex-shrink:0;min-width:90px;">
                <div style="font-size:12px;color:#6b7280;">
                    {row['Time per week (hrs)']}h/wk<br>
                    Manual: {row['Manual effort (1-5)']:.1f}/5
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
    st.divider()
    st.download_button(
        "Export top tasks to CSV",
        top_df[["Name","Role","Task","Time per week (hrs)",
                "Manual effort (1-5)","_opportunity"]
        ].rename(columns={"_opportunity":"Opportunity score"}).to_csv(index=False),
        "top_tasks.csv","text/csv"
    )

# TAB 4: RAW DATA
with tab4:
    st.markdown("#### Raw data")
    st.caption("Manual effort shown here is the inverted judgment score from the form.")
    out = df[["Name","Role","Task","Time per week (hrs)",
              "Manual effort (1-5)","_opportunity"]].rename(
        columns={"_opportunity":"Opportunity score"}).sort_values(
        "Opportunity score",ascending=False)
    st.dataframe(out,use_container_width=True,hide_index=True)
    st.download_button("Export full dataset",out.to_csv(index=False),
                       "task_audit_full.csv","text/csv")

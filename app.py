# app.py -- Polished UI version (Streamlit)
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import matplotlib.pyplot as plt
import io

# -------------------------
# Setup & DB ensure-table
# -------------------------
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
engine = create_engine("sqlite:///expenses.db")

# Ensure table exists
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expenses (
            date TEXT,
            category TEXT,
            amount REAL,
            note TEXT
        )
    """))
    conn.commit()

# -------------------------
# Styles (simple CSS)
# -------------------------
# We inject a bit of CSS to polish visuals and support dark/light
def inject_css(dark_mode: bool):
    if dark_mode:
        bg = "#0e1117"
        card = "#0f1720"
        text = "#e6eef6"
        muted = "#9aa6b2"
    else:
        bg = "#f7f9fb"
        card = "#ffffff"
        text = "#0b1b2b"
        muted = "#5b6b75"

    st.markdown(
        f"""
        <style>
        /* Page background */
        .stApp {{
            background-color: {bg};
            color: {text};
        }}
        /* Card like containers */
        .card {{
            background: {card};
            padding: 14px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            color: {text};
        }}
        .muted {{ color: {muted}; font-size:13px; }}
        .header-title {{
            font-size:34px;
            font-weight:700;
            margin-bottom: 0px;
        }}
        .header-sub {{
            color: {muted};
            margin-top: 2px;
            margin-bottom: 6px;
        }}
        .small-note {{ font-size:13px; color:{muted}; }}
        /* table tweaks */
        .stDataFrame th {{
            background-color: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# -------------------------
# Sidebar controls
# -------------------------
st.sidebar.title("Controls")
dark = st.sidebar.checkbox("Dark mode", value=True)
inject_css(dark)

st.sidebar.markdown("**Quick actions**")
if st.sidebar.button("Add sample expense"):
    # add a tiny sample to let user preview UI easily
    df_sample = pd.DataFrame([{
        "date": date.today(),
        "category": "Food",
        "amount": 199.0,
        "note": "Sample lunch"
    }])
    df_sample.to_sql("expenses", con=engine, if_exists="append", index=False)
    st.sidebar.success("Added sample expense")

st.sidebar.markdown("---")
st.sidebar.markdown("**Export / Backup**")
if st.sidebar.button("Download DB (CSV)"):
    df_all = pd.read_sql("SELECT * FROM expenses", con=engine)
    buff = io.StringIO()
    df_all.to_csv(buff, index=False)
    st.download_button("Download CSV", buff.getvalue(), file_name="expenses_backup.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.caption("Polished UI demo • Your data stays in SQLite (expenses.db)")

# -------------------------
# Header (centered)
# -------------------------
st.markdown(
    """
    <div style='display:flex;align-items:center;justify-content:space-between;'>
      <div>
        <div class="header-title">💰 Expense & Budget Tracker</div>
        <div class="header-sub">A clean interface to add, review and visualize your spending</div>
      </div>
      <div style='text-align:right;'>
        <div class="small-note">Logged in: Local</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")  # spacer

# -------------------------
# Add expense form (polished)
# -------------------------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("➕ Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            expense_date = st.date_input("Date", value=date.today())
        with c2:
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"])
        with c3:
            amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if amount <= 0:
                st.warning("Amount must be positive.")
            else:
                new_entry = pd.DataFrame({
                    "date": [expense_date],
                    "category": [category],
                    "amount": [amount],
                    "note": [note]
                })
                new_entry.to_sql("expenses", con=engine, if_exists="append", index=False)
                st.success(f"Added {category} — ₹{amount:.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")  # spacer

# -------------------------
# Fetch & Filters
# -------------------------
df = pd.read_sql("SELECT rowid, * FROM expenses", con=engine)
if df is None:
    df = pd.DataFrame(columns=["rowid", "date", "category", "amount", "note"])

# Filter UI
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Filters & Quick Search")
    f1, f2, f3 = st.columns([1.5, 1.5, 1])
    with f1:
        months = df["date"].astype(str).apply(lambda x: x[:7]).sort_values(ascending=False).unique() if not df.empty else []
        selected_month = st.selectbox("Month", options=["All"] + list(months), index=0)
    with f2:
        cat_options = ["All"] + sorted(df["category"].unique().tolist()) if not df.empty else ["All"]
        selected_cat = st.selectbox("Category", options=cat_options, index=0)
    with f3:
        q = st.text_input("Search notes / category")
    st.markdown("</div>", unsafe_allow_html=True)

# Apply filters
df_filtered = df.copy()
if not df.empty:
    if selected_month and selected_month != "All":
        df_filtered = df_filtered[df_filtered["date"].astype(str).str.startswith(selected_month)]
    if selected_cat and selected_cat != "All":
        df_filtered = df_filtered[df_filtered["category"] == selected_cat]
    if q:
        df_filtered = df_filtered[df_filtered["note"].str.contains(q, case=False, na=False) | df_filtered["category"].str.contains(q, case=False, na=False)]

# -------------------------
# Dashboard Metrics + Table
# -------------------------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Overview")

    if df_filtered.empty:
        st.info("No expenses to show. Add your first expense above.")
    else:
        total = df_filtered["amount"].sum()
        transactions = len(df_filtered)
        try:
            top_cat = df_filtered.groupby("category")["amount"].sum().idxmax()
        except Exception:
            top_cat = "—"

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spent (₹)", f"{total:,.2f}")
        m2.metric("Transactions", f"{transactions}")
        m3.metric("Top Category", top_cat)

        st.markdown("**Transactions**")
        # show dataframe but limit width for readability
        st.dataframe(df_filtered.sort_values(by="date", ascending=False).reset_index(drop=True), use_container_width=True)

        # Download CSV for filtered data
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download filtered CSV", data=csv, file_name="expenses_filtered.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Chart area (right below)
# -------------------------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Spending Breakdown")
    if df_filtered.empty:
        st.write("No data to plot.")
    else:
        category_totals = df_filtered.groupby("category")["amount"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(category_totals, labels=category_totals.index, autopct="%1.1f%%", startangle=90, wedgeprops={"edgecolor":"w"})
        ax.axis("equal")
        st.pyplot(fig)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Delete controls (polished)
# -------------------------
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🗑 Manage Expenses")

    col_a, col_b = st.columns([2, 3])
    with col_a:
        delete_mode = st.radio("Delete mode:", ["By ID", "Select multiple", "Delete all"], horizontal=False)
        if delete_mode == "By ID":
            del_id = st.number_input("Enter ID (rowid) to delete:", min_value=1, step=1)
            if st.button("Delete by ID"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM expenses WHERE rowid = :rid"), {"rid": del_id})
                st.success(f"Deleted ID {del_id}. Refresh to update.")
        elif delete_mode == "Select multiple":
            options = df_filtered["rowid"].tolist() if not df_filtered.empty else []
            sel = st.multiselect("Select IDs to delete:", options)
            if st.button("Delete selected"):
                if sel:
                    with engine.begin() as conn:
                        conn.execute(text(f"DELETE FROM expenses WHERE rowid IN ({','.join(map(str, sel))})"))
                    st.success(f"Deleted {len(sel)} records. Refresh to update.")
                else:
                    st.warning("No selection.")
        else:
            if st.button("⚠️ Delete all expenses"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM expenses"))
                st.warning("All records deleted. Refresh to update.")

    with col_b:
        st.markdown("**Quick tips**")
        st.markdown("- Use the filters above to narrow the table.")
        st.markdown("- Download filtered CSV for backups.")
        st.markdown("- To permanently save a copy, download the CSV and store it locally.")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Footer small
# -------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="small-note">Made with ❤️ • Local database: <code>expenses.db</code></div>', unsafe_allow_html=True)


import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import matplotlib.pyplot as plt

# ---- SETUP ----
engine = create_engine("sqlite:///expenses.db")

# ✅ Create table if it doesn’t exist
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

st.title("💰 Expense & Budget Tracker")

# ---- ADD EXPENSE FORM ----
st.header("Add New Expense")
with st.form("expense_form"):
    col1, col2 = st.columns(2)
    with col1:
        expense_date = st.date_input("Date", value=date.today())
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])
    with col2:
        amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        note = st.text_input("Note (optional)")
    submitted = st.form_submit_button("Add Expense")

    if submitted and amount > 0:
        new_entry = pd.DataFrame({
            "date": [expense_date],
            "category": [category],
            "amount": [amount],
            "note": [note]
        })
        new_entry.to_sql("expenses", con=engine, if_exists="append", index=False)
        st.success(f"✅ Added {category} - ₹{amount}")

# ---- SHOW SAVED EXPENSES ----
st.header("Your Expenses")
try:
    df = pd.read_sql("SELECT rowid, * FROM expenses", con=engine)

    if not df.empty:
        st.dataframe(df)

        total = df["amount"].sum()
        st.write(f"### 💵 Total Spent: ₹{total}")

        # ---- CATEGORY ANALYSIS ----
        st.header("📊 Spending by Category")
        category_totals = df.groupby("category")["amount"].sum()
        fig, ax = plt.subplots()
        ax.pie(category_totals, labels=category_totals.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

        # ---- DELETE EXPENSE ----
        st.header("🗑️ Delete an Expense")
        delete_id = st.number_input("Enter the ID (rowid) to delete:", min_value=1, step=1)
        if st.button("Delete Expense"):
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM expenses WHERE rowid = :rid"), {"rid": delete_id})
            st.warning(f"🗑️ Deleted expense with ID {delete_id}. Refresh to see changes.")
    else:
        st.info("No expenses recorded yet.")

except Exception as e:
    st.error(f"Error loading expenses: {e}")










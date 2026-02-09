import streamlit as st
import pandas as pd
from datetime import date
import os
import plotly.express as px

st.set_page_config(page_title="Finance Tracker")

DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["type","amount","category","note","date"])
    df_init.to_csv(DATA_FILE,index=False)

df = pd.read_csv(DATA_FILE)
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# ---------- ROW COLORING ----------
def color_rows(row):
    if row["type"] == "Income":
        return ["color: green"] * len(row)
    else:
        return ["color: red"] * len(row)

st.title("💰 Personal Finance Tracker")

tab1, tab2, tab3 = st.tabs(["➕ Add Entry","📊 Monthly Report","🛠 Manage Entries"])

# ================= ADD ENTRY =================
with tab1:
    with st.form("add_form", clear_on_submit=True):

        t = st.radio("Type",["Income","Expense"])
        amount = st.number_input("Amount",min_value=0.0)
        category = st.selectbox("Category",["Salary","Food","Travel","Shopping","Bills","Other"])
        note = st.text_input("Note")
        d = st.date_input("Date",date.today())

        submit = st.form_submit_button("Save")

        if submit:
            new = pd.DataFrame([[t,amount,category,note,str(d)]],columns=df.columns)
            df2 = pd.concat([df,new],ignore_index=True)
            df2.to_csv(DATA_FILE,index=False)
            st.success("Saved")

# ================= MONTHLY REPORT =================
with tab2:
    if not df.empty:

        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        month = st.selectbox("Month",df["date"].dt.strftime("%Y-%m").dropna().unique())

        m = df[df["date"].dt.strftime("%Y-%m")==month]

        income = m[m["type"]=="Income"]["amount"].sum()
        expense = m[m["type"]=="Expense"]["amount"].sum()

        total_income = df[df["type"]=="Income"]["amount"].sum()
        total_expense = df[df["type"]=="Expense"]["amount"].sum()

        overall_balance = total_income-total_expense

        col1,col2,col3 = st.columns(3)

        col1.markdown(f"### 🟢 Income\n## +₹{income}")
        col2.markdown(f"### 🔴 Expense\n## -₹{expense}")
        col3.markdown(f"### 💼 Overall Balance\n## ₹{overall_balance}")

        show = m.copy()
        show["Signed Amount"] = show.apply(
            lambda r: f"+{r.amount}" if r["type"]=="Income" else f"-{r.amount}",
            axis=1
        )

        styled = show[["date","type","category","note","Signed Amount"]].style.apply(color_rows, axis=1)
        st.write(styled)

        exp = m[m["type"]=="Expense"]

        if len(exp) > 0:
            fig = px.pie(exp, values="amount", names="category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses for this month")

    else:
        st.info("No data yet")

# ================= MANAGE ENTRIES =================
with tab3:
    if not df.empty:

        df["id"] = df.index

        selected = st.selectbox("Select Entry", df["id"])

        row = df.loc[selected]

        etype = st.selectbox("Edit Type",["Income","Expense"],
                             index=0 if row["type"]=="Income" else 1)

        eamount = st.number_input("Edit Amount", value=float(row["amount"]))

        ecat = st.selectbox("Edit Category",["Salary","Food","Travel","Shopping","Bills","Other"],
                            index=["Salary","Food","Travel","Shopping","Bills","Other"].index(row["category"]))

        enote = st.text_input("Edit Note", value=row["note"])

        edate = st.date_input("Edit Date", pd.to_datetime(row["date"]))

        col1, col2 = st.columns(2)

        if col1.button("Update"):
            df.loc[selected] = [etype,eamount,ecat,enote,str(edate),selected]
            df.drop(columns=["id"], inplace=True)
            df.to_csv(DATA_FILE,index=False)
            st.success("Updated")
            st.rerun()

        if col2.button("Delete"):
            df = df.drop(selected)
            df.drop(columns=["id"], inplace=True)
            df.to_csv(DATA_FILE,index=False)
            st.warning("Deleted")
            st.rerun()

        styled2 = df.drop(columns=["id"]).style.apply(color_rows, axis=1)
        st.write(styled2)

    else:
        st.info("No records yet")

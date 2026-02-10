import streamlit as st
import pandas as pd
from datetime import date
import os
import plotly.express as px
import requests
import base64

# ---------------- GITHUB SAVE ----------------
def save_to_github(csv_text):

    token = st.secrets["GITHUB_TOKEN"]

    owner = "srikiran15"
    repo = "finance-tracker"
    path = "data.csv"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    headers = {"Authorization": f"token {token}"}

    r = requests.get(url, headers=headers)
    sha = r.json()["sha"]

    encoded = base64.b64encode(csv_text.encode()).decode()

    payload = {
        "message": "update finance data",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, json=payload, headers=headers)

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Finance Tracker", layout="wide")

DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["type","amount","category","note","date"]).to_csv(DATA_FILE,index=False)

df = pd.read_csv(DATA_FILE)
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# ---------- COLOR ----------
def color_rows(row):
    return ["color: green"] * len(row) if row["type"]=="Income" else ["color: red"] * len(row)

st.title("💰 Personal Finance Tracker")

tab1, tab2, tab3 = st.tabs(["➕ Add Entry","📊 Monthly Report","🛠 Manage Entries"])

# ================= ADD =================
with tab1:
    with st.form("add", clear_on_submit=True):

        t = st.radio("Type",["Income","Expense"])
        amount = st.number_input("Amount",0.0)
        cat = st.selectbox("Category",["Salary","Food","Travel","Shopping","Bills","Other"])
        note = st.text_input("Note")
        d = st.date_input("Date",date.today())

        if st.form_submit_button("Save"):

            new = pd.DataFrame([[t,amount,cat,note,str(d)]],columns=df.columns)
            df2 = pd.concat([df,new],ignore_index=True)

            df2.to_csv(DATA_FILE,index=False)
            save_to_github(df2.to_csv(index=False))

            st.success("Saved permanently ✅")

# ================= REPORT =================
with tab2:

    if not df.empty:

        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        month = st.selectbox("Month",df["date"].dt.strftime("%Y-%m").dropna().unique())

        m = df[df["date"].dt.strftime("%Y-%m")==month]

        inc = m[m["type"]=="Income"]["amount"].sum()
        exp = m[m["type"]=="Expense"]["amount"].sum()

        total_inc = df[df["type"]=="Income"]["amount"].sum()
        total_exp = df[df["type"]=="Expense"]["amount"].sum()

        bal = total_inc-total_exp

        c1,c2,c3 = st.columns(3)
        c1.markdown(f"## 🟢 +₹{inc}")
        c2.markdown(f"## 🔴 -₹{exp}")
        c3.markdown(f"## 💼 ₹{bal}")

        m["Signed"] = m.apply(lambda r: f"+{r.amount}" if r.type=="Income" else f"-{r.amount}",axis=1)

        st.write(m[["date","type","category","note","Signed"]].style.apply(color_rows,axis=1))

        e = m[m["type"]=="Expense"]
        if len(e):
            fig = px.pie(e, values="amount", names="category")
            st.plotly_chart(fig,use_container_width=True)

# ================= MANAGE =================
with tab3:

    if not df.empty:

        df["id"]=df.index
        sel = st.selectbox("Select",df["id"])
        r = df.loc[sel]

        t = st.selectbox("Type",["Income","Expense"],index=0 if r.type=="Income" else 1)
        a = st.number_input("Amount",value=float(r.amount))
        c = st.selectbox("Category",["Salary","Food","Travel","Shopping","Bills","Other"],
                         index=["Salary","Food","Travel","Shopping","Bills","Other"].index(r.category))
        n = st.text_input("Note",value=r.note)
        d = st.date_input("Date",pd.to_datetime(r.date))

        col1,col2=st.columns(2)

        if col1.button("Update"):
            df.loc[sel]=[t,a,c,n,str(d),sel]
            df.drop(columns=["id"],inplace=True)
            df.to_csv(DATA_FILE,index=False)
            save_to_github(df.to_csv(index=False))
            st.rerun()

        if col2.button("Delete"):
            df=df.drop(sel)
            df.drop(columns=["id"],inplace=True)
            df.to_csv(DATA_FILE,index=False)
            save_to_github(df.to_csv(index=False))
            st.rerun()

        st.write(df.drop(columns=["id"]).style.apply(color_rows,axis=1))

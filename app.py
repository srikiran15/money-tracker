import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import requests
import base64

OWNER = "srikiran15"
REPO = "finance-tracker"
PATH = "data.csv"

# ================= GITHUB LOAD =================
def load_from_github():

    url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/{PATH}"

    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame(columns=["type","amount","category","note","date"])


# ================= GITHUB SAVE =================
def save_to_github(df):

    token = st.secrets["GITHUB_TOKEN"]

    api = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"

    headers = {"Authorization": f"token {token}"}

    r = requests.get(api, headers=headers)
    sha = r.json()["sha"]

    csv = df.to_csv(index=False)
    encoded = base64.b64encode(csv.encode()).decode()

    payload = {
        "message": "finance update",
        "content": encoded,
        "sha": sha
    }

    requests.put(api, json=payload, headers=headers)


# ================= INIT =================

st.set_page_config(page_title="Finance Tracker")
st.title("💰 Personal Finance Tracker")

df = load_from_github()
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# ---------- ROW COLORING ----------
def color_rows(row):
    return ["color: green"] * len(row) if row["type"]=="Income" else ["color:red"]*len(row)

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
            df = pd.concat([df,new],ignore_index=True)

            save_to_github(df)

            st.success("Saved permanently ✅")


# ================= REPORT =================
with tab2:

    if not df.empty:

        df["date"]=pd.to_datetime(df["date"])

        month = st.selectbox("Month",df["date"].dt.strftime("%Y-%m").unique())
        m = df[df["date"].dt.strftime("%Y-%m")==month]

        income = m[m.type=="Income"].amount.sum()
        expense = m[m.type=="Expense"].amount.sum()

        total_income = df[df.type=="Income"].amount.sum()
        total_expense = df[df.type=="Expense"].amount.sum()

        col1,col2,col3 = st.columns(3)

        col1.markdown(f"### 🟢 Income\n## +₹{income}")
        col2.markdown(f"### 🔴 Expense\n## -₹{expense}")
        col3.markdown(f"### 💼 Overall Balance\n## ₹{total_income-total_expense}")

        m["Signed"]=m.apply(lambda r:f"+{r.amount}" if r.type=="Income" else f"-{r.amount}",axis=1)

        st.write(m[["date","type","category","note","Signed"]].style.apply(color_rows,axis=1))

        exp=m[m.type=="Expense"]
        if not exp.empty:
            st.plotly_chart(px.pie(exp,values="amount",names="category"),use_container_width=True)

    else:
        st.info("No data yet")


# ================= MANAGE =================
with tab3:

    if not df.empty:

        df["id"]=df.index
        sel=st.selectbox("Select",df.id)

        row=df.loc[sel]

        et=st.selectbox("Type",["Income","Expense"],index=0 if row.type=="Income" else 1)
        ea=st.number_input("Amount",value=float(row.amount))
        ec=st.selectbox("Category",["Salary","Food","Travel","Shopping","Bills","Other"])
        en=st.text_input("Note",row.note)
        ed=st.date_input("Date",pd.to_datetime(row.date))

        c1,c2=st.columns(2)

        if c1.button("Update"):
            df.loc[sel]=[et,ea,ec,en,str(ed),sel]
            df=df.drop(columns=["id"])
            save_to_github(df)
            st.rerun()

        if c2.button("Delete"):
            df=df.drop(sel).drop(columns=["id"])
            save_to_github(df)
            st.rerun()

        st.write(df.style.apply(color_rows,axis=1))

    else:
        st.info("No records")

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from openai import OpenAI
import json
from openpyxl import Workbook
import os

st.title("📊 AI Deal Analyzer")

st.caption("Analyze advertiser deals, bonus structures, and efficiency using AI insights")
st.sidebar.markdown("## 👤 About")
st.sidebar.markdown("**Winston Smrick**")
st.sidebar.markdown("AI Product Demo")

st.sidebar.markdown("[🔗 LinkedIn](https://www.linkedin.com/in/winston-smrick-7344821a)")
option = st.radio("Choose Data Source:", ["Upload CSV", "Fetch from MySQL"])

data = ""
df = None
if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload deals CSV", type=["csv"])
    st.info("⬇️ New here? Download a sample dataset to try the app.")
    st.download_button(
    label="📥 Download Sample CSV",
    data=open("deals.csv", "rb").read(),
    file_name="sample_deals.csv",
    mime="text/csv"
    )
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        data = df.to_string(index=False)
        st.dataframe(df)
        st.divider()

elif option == "Fetch from MySQL":
    st.warning("⚠️ MySQL integration is not enabled in this live demo.")
    st.info("📌 Please use 'Upload CSV' option to test the app.")
    
if data:
    st.success("✅ Data ready for analysis")

if st.button("Analyze Deals"):
    if df is None:
        st.warning("⚠️ Please upload a CSV file before analyzing.")
        st.stop()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    You are analyzing advertiser deals.

    Return STRICT JSON only.

    For each deal provide:
    - advertiser
    - total_paid
    - total_bonus
    - bonus_percentage
    - programs (list of program, type, spend)

    Data:
    {data}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content
    result = result.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(result)
    st.session_state["parsed"] = parsed

if "parsed" in st.session_state:

    parsed = st.session_state["parsed"]

    summary_df = pd.DataFrame(parsed)

    summary_df["advertiser_clean"] = summary_df["advertiser"].astype(str).str.strip().str.lower()

    advertisers = sorted(
        summary_df["advertiser_clean"].unique().tolist()
    )

    selected_advertiser = st.selectbox(
        "🔍 Select Advertiser",
        ["all"] + advertisers
    )

    if selected_advertiser != "all":
        selected_clean = selected_advertiser.strip().lower()

        filtered_df = summary_df[
            summary_df["advertiser_clean"] == selected_clean
        ]

        filtered_parsed = [
            d for d in parsed
            if str(d["advertiser"]).strip().lower() == selected_clean
        ]

    else:
        filtered_df = summary_df
        filtered_parsed = parsed

    # ✅ EVERYTHING BELOW MUST BE INSIDE THIS BLOCK
    st.divider()

    st.subheader("📊 Insights Dashboard")

    col1, col2, col3 = st.columns(3)

    total_paid = int(filtered_df["total_paid"].sum())
    total_bonus = int(filtered_df["total_bonus"].sum())
    avg_bonus = float(filtered_df["bonus_percentage"].mean())

    col1.metric("💰 Total Paid", f"{total_paid:,}")
    col2.metric("🎁 Total Bonus", f"{total_bonus:,}")
    col3.metric("📊 Avg Bonus %", f"{avg_bonus:.2f}%")

    summary_chart = filtered_df.groupby("advertiser_clean").sum(numeric_only=True)

    st.bar_chart(summary_chart["total_paid"])
    st.bar_chart(summary_chart["bonus_percentage"])
    st.bar_chart(summary_chart["total_bonus"])

    if not filtered_parsed:
        st.warning("⚠️ No data available for selected advertiser")

    if filtered_parsed:

        deal = filtered_parsed[0]

        programs_df = pd.DataFrame(deal["programs"])

        st.subheader("📊 Program-wise Spend")

        st.bar_chart(programs_df.set_index("program")["spend"])

        programs_df["spend"] = programs_df["spend"].astype(int)

        st.subheader("🥧 Spend Distribution")

        st.pyplot(
            programs_df.set_index("program")["spend"]
            .plot.pie(autopct="%1.1f%%", figsize=(5, 5))
            .figure
        )

        st.subheader("🤖 AI Insight")

        if deal["bonus_percentage"] > 20:
            st.error("⚠️ High bonus deal — may reduce profitability")
        elif deal["bonus_percentage"] < 10:
            st.success("✅ Efficient deal — low bonus, high value")
        else:
            st.info("ℹ️ Moderate deal — balanced structure")

        # ✅ DEAL SUMMARY (moved inside)
        st.subheader("📋 Deal Summary")

        for deal in filtered_parsed:
            st.markdown("---")
            st.header(f"📢 {deal['advertiser']}")

            col1, col2, col3 = st.columns(3)

            col1.metric("💰 Total Paid", f"{deal['total_paid']:,}")
            col2.metric("🎁 Total Bonus", f"{deal['total_bonus']:,}")
            col3.metric("📊 Bonus %", f"{deal['bonus_percentage']}%")

    # ✅ Excel Download
    wb = Workbook()
    ws = wb.active
    ws.title = "Deal Summary"

    ws.append(["Advertiser", "Total Paid", "Total Bonus", "Bonus %"])

    for deal in parsed:
        ws.append([
            deal["advertiser"],
            deal["total_paid"],
            deal["total_bonus"],
            deal["bonus_percentage"]
        ])

    file_path = "deal_output.xlsx"
    wb.save(file_path)

    with open(file_path, "rb") as f:
        st.download_button("📥 Download Excel", f, file_name="deal_output.xlsx")

else:
    if option == "Upload CSV":
        if not uploaded_file:
            st.info("👆 Upload a CSV to proceed")
        else:
            st.info("👉 Click 'Analyze Deals' to generate insights")

    #elif option == "Fetch from MySQL":
        #st.warning("⚠️ MySQL integration is not enabled in this live demo.")
        #st.info("📌 Please use 'Upload CSV' option to test the app.")

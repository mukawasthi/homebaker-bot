import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# Load menu from JSON
with open("caked_with_love_menu.json", "r") as f:
    custom_menu = json.load(f)

# Load Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # Latest working Groq-supported model

# Streamlit app setup
st.set_page_config(page_title="Caked with Love Bot 🎂", layout="centered")
st.title("🎂 Caked with Love – Your Cake Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat with Bot", "📝 Place an Order", "📋 View Menu"])

# --- CHAT TAB ---
with tab1:
    user_input = st.chat_input("Ask about flavors, prices, or suggestions...")

    if user_input:
        st.session_state.chat_history.append(("user", user_input))

        messages = [
            {
                "role": "system",
                "content": f"You are a friendly assistant for a home bakery called 'Caked with Love'. Always reply in INR. Use the following menu and pricing for all responses:\n\n{json.dumps(custom_menu)}"
            }
        ] + [
            {"role": role, "content": content}
            for role, content in st.session_state.chat_history
        ]

        try:
            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages
                }
            )
            data = response.json()

            if "choices" not in data:
                raise Exception(f"Groq Error: {data}")

            bot_reply = data["choices"][0]["message"]["content"]
        except Exception as e:
            bot_reply = f"Sorry, something went wrong: {e}"

        st.session_state.chat_history.append(("assistant", bot_reply))

    # Display chat history
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

# --- ORDER FORM TAB ---
with tab2:
    with st.form("order_form"):
        st.subheader("🧾 Custom Cake Order Form")

        name = st.text_input("Your Name")
        phone = st.text_input("Phone Number")
        category = st.selectbox("Select Category", list(custom_menu.keys()))
        item = st.selectbox("Select Item", list(custom_menu[category].keys()))
        price = custom_menu[category][item]
        st.markdown(f"💰 **Price:** ₹{price}")

        occasion = st.selectbox("Occasion", ["Birthday", "Anniversary", "Baby Shower", "Other"])
        delivery_date = st.date_input("Preferred Delivery Date")
        notes = st.text_area("Design/theme request (optional)")

        submitted = st.form_submit_button("Submit Order")

        if submitted:
            order = {
                "Name": name,
                "Phone": phone,
                "Category": category,
                "Item": item,
                "Price": price,
                "Occasion": occasion,
                "Delivery Date": str(delivery_date),
                "Notes": notes,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            df = pd.DataFrame([order])
            try:
                existing = pd.read_csv("orders.csv")
                updated = pd.concat([existing, df], ignore_index=True)
            except FileNotFoundError:
                updated = df

            updated.to_csv("orders.csv", index=False)

            st.success("✅ Order submitted! We'll reach out to confirm.")
            st.download_button("📥 Download All Orders", data=updated.to_csv(index=False), file_name="orders.csv", mime="text/csv")

# --- MENU TAB ---
with tab3:
    st.subheader("📋 Menu & Pricing")
    for category, items in custom_menu.items():
        st.markdown(f"### 🍰 {category}")
        for item, price in items.items():
            st.markdown(f"- **{item}** — ₹{price}")

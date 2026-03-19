import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Enterprise B2B Search", layout="wide")
st.title("Company Search Dashboard")

if "results" not in st.session_state:
    st.session_state.results = []
if "agent_answer" not in st.session_state:
    st.session_state.agent_answer = None
if "tags" not in st.session_state:
    st.session_state.tags = []

def fetch_tags():
    try:
        r = requests.get(f"{API_URL}/tags")
        if r.status_code == 200:
            st.session_state.tags = r.json()
    except Exception:
        pass

def add_tag(company_id, new_tag):
    if new_tag:
        try:
            requests.post(f"{API_URL}/companies/{company_id}/tags", json={"tag": new_tag})
            fetch_tags()
        except Exception as e:
            st.error(f"Error adding tag: {e}")

fetch_tags()

# --- SIDEBAR: Deterministic Filters ---
with st.sidebar:
    st.header("Standard Filters")
    name_filter = st.text_input("Company Name")
    industry_filter = st.text_input("Industry")
    size_filter = st.selectbox("Company Size", ["", "<1000", "1000-10000", "10001+"])
    country_filter = st.text_input("Country")
    year_from = st.number_input("Founded From", min_value=1800, max_value=2026, value=1900)
    year_to = st.number_input("Founded To", min_value=1800, max_value=2026, value=2026)
    
    if st.button("Apply Filters"):
        payload = {}
        if name_filter: payload["name"] = name_filter
        if industry_filter: payload["industry"] = industry_filter
        if size_filter: payload["size_range"] = size_filter
        if country_filter: payload["country"] = country_filter
        if year_from: payload["year_from"] = year_from
        if year_to: payload["year_to"] = year_to
        
        try:
            r = requests.post(f"{API_URL}/search", json=payload)
            if r.status_code == 200:
                data = r.json()
                st.session_state.results = data.get("results", [])
                st.session_state.agent_answer = None
        except Exception as e:
            st.error("Failed to connect to API.")

# --- MAIN COLUMN: Intelligent Search ---
st.subheader("Intelligent Search")
st.caption("E.g., 'tech companies in us' or 'startups that announced fund raising recently'")
intelligent_query = st.chat_input("Search companies...")

if intelligent_query:
    try:
        with st.spinner("Analyzing intent and searching..."):
            r = requests.post(f"{API_URL}/search/intelligent", json={"query": intelligent_query})
            if r.status_code == 200:
                data = r.json()
                st.session_state.results = data.get("search_results", {}).get("results", [])
                st.session_state.agent_answer = data.get("agentic_answer")
    except Exception as e:
        st.error("Failed to connect to Intelligent API.")

# --- RESULTS RENDERING ---
if st.session_state.agent_answer:
    st.info(f"**Agent Insight:** {st.session_state.agent_answer}")

st.subheader(f"Search Results ({len(st.session_state.results)} found)")

for company in st.session_state.results:
    with st.expander(f"{company['name'].title()} - {company.get('industry', 'Unknown')}", expanded=False):
        st.write(f"**Domain:** {company.get('domain')}")
        st.write(f"**Location:** {company.get('locality')}, {company.get('country')}")
        st.write(f"**Founded:** {company.get('year_founded')} | **Size:** {company.get('size_range')}")
        
        tags = company.get("tags", [])
        if tags:
            st.write("**Tags:** " + ", ".join([f"`{t}`" for t in tags]))
            
        new_tag = st.text_input(f"Add Tag for {company['name']}", key=f"tag_{company['id']}")
        if st.button("Save Tag", key=f"btn_{company['id']}"):
            add_tag(company['id'], new_tag)
            st.success(f"Added tag '{new_tag}' to {company['name']}!")
            st.rerun()

# --- All Tags ---
if st.session_state.tags:
    st.sidebar.markdown("---")
    st.sidebar.subheader("All Tags in System")
    for t in st.session_state.tags:
        st.sidebar.caption(t)

"""Streamlit application mappings."""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000") + "/api/v2"

st.set_page_config(page_title="Enterprise B2B Search", layout="wide")
st.title("Company Search Dashboard")

if "results" not in st.session_state:
    st.session_state.results = []
if "agent_answer" not in st.session_state:
    st.session_state.agent_answer = None
if "tags" not in st.session_state:
    st.session_state.tags = []


def fetch_tags() -> None:
    """Retrieve external strings synchronously."""
    try:
        r = requests.get(f"{API_URL}/tags")
        if r.status_code == 200:
            st.session_state.tags = r.json()
    except Exception:
        pass


def add_tag(company_id: str, new_tag: str) -> None:
    """Push tagging successfully accurately neatly dependably."""
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
    size_filter = st.selectbox("Company Size", ["", "1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"])
    country_filter = st.text_input("Country")
    tag_filter = st.selectbox("Filter by Tag", [""] + st.session_state.tags)
    year_from = st.number_input("Founded From", min_value=1800, max_value=2026, value=None, placeholder="YYYY")
    year_to = st.number_input("Founded To", min_value=1800, max_value=2026, value=None, placeholder="YYYY")

    if st.button("Apply Filters"):
        from typing import Any

        payload: dict[str, Any] = {}
        if name_filter:
            payload["name"] = name_filter
        if industry_filter:
            payload["industry"] = industry_filter
        if size_filter:
            payload["size_range"] = size_filter
        if country_filter:
            payload["country"] = country_filter
        if tag_filter:
            payload["tags"] = [tag_filter]
        if year_from:
            payload["year_from"] = year_from
        if year_to:
            payload["year_to"] = year_to

        try:
            r = requests.post(f"{API_URL}/search", json=payload)
            if r.status_code == 200:
                data = r.json()
                st.session_state.results = data.get("results", [])
                st.session_state.agent_answer = None
        except Exception:
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
                st.session_state.results = data.get("results", [])
                st.session_state.agent_answer = None

                task_id = data.get("agentic_task_id")
                if task_id:
                    import time
                    with st.spinner("Waiting for agentic synthesis from Celery..."):
                        for _ in range(15):
                            time.sleep(1.5)
                            status_r = requests.get(f"{API_URL}/search/agentic/{task_id}")
                            if status_r.status_code == 200:
                                status_data = status_r.json()
                                if status_data.get("status") == "SUCCESS":
                                    result_obj = status_data.get("result", {})
                                    if isinstance(result_obj, dict):
                                        st.session_state.agent_answer = result_obj.get("summary")
                                    else:
                                        st.session_state.agent_answer = str(result_obj)
                                    break
                                elif status_data.get("status") in ("FAILURE", "failed"):
                                    st.session_state.agent_answer = "Agent synthesis failed: " + str(status_data.get("result"))
                                    break
    except Exception:
        st.error("Failed to connect to Intelligent API.")

# --- RESULTS RENDERING ---
if st.session_state.agent_answer:
    st.info(f"**Agent Insight:** {st.session_state.agent_answer}")

st.subheader(f"Search Results ({len(st.session_state.results)} found)")

for company in st.session_state.results:
    with st.expander(
        f"{company['name'].title()} - {company.get('industry', 'Unknown')}",
        expanded=False,
    ):
        st.write(f"**Domain:** {company.get('domain')}")
        st.write(f"**Location:** {company.get('locality')}, {company.get('country')}")
        st.write(f"**Founded:** {company.get('year_founded')} | **Size:** {company.get('size_range')}")

        tags = company.get("tags", [])
        if tags:
            st.write("**Tags:** " + ", ".join([f"`{t}`" for t in tags]))

        new_tag = st.text_input(f"Add Tag for {company['name']}", key=f"tag_{company['id']}")
        if st.button("Save Tag", key=f"btn_{company['id']}"):
            add_tag(company["id"], new_tag)
            st.success(f"Added tag '{new_tag}' to {company['name']}!")
            st.rerun()

# --- All Tags ---
if st.session_state.tags:
    st.sidebar.markdown("---")
    st.sidebar.subheader("All Tags in System")
    for t in st.session_state.tags:
        st.sidebar.caption(t)

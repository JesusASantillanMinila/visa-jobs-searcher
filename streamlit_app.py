import streamlit as st
import pandas as pd
from jobspy import scrape_jobs
import time

# --- Page Configuration ---
st.set_page_config(page_title="Job Searcher Pro", layout="wide")
st.title("🔍 Job Search & Visa Filter")
st.write("Enter your search terms and locations below. At least one of each is required.")

# --- Sidebar / Input Section ---
with st.sidebar:
    st.header("Search Parameters")
    
    st.subheader("Roles")
    role1 = st.text_input("Role 1", value="Data Analysis")
    role2 = st.text_input("Role 2")
    role3 = st.text_input("Role 3")
    
    st.subheader("Locations")
    loc1 = st.text_input("Location 1", value="Chicago, IL")
    loc2 = st.text_input("Location 2")
    loc3 = st.text_input("Location 3")
    
    keywords = ['visa', 'sponsorship', 'authorization']
    results_count = st.slider("Results per search", 5, 50, 15)

# --- Logic Setup ---
SEARCH_TERMS = [r.strip() for r in [role1, role2, role3] if r.strip()]
LOCATIONS = [l.strip() for l in [loc1, loc2, loc3] if l.strip()]

def check_visa(description):
    if pd.isna(description): 
        return False
    desc_lower = str(description).lower()
    return any(word in desc_lower for word in keywords)

# --- Main Action ---
if st.button("Run Job Search"):
    if not SEARCH_TERMS or not LOCATIONS:
        st.error("Please provide at least one Search Term and one Location.")
    else:
        all_jobs = []
        total_searches = len(SEARCH_TERMS) * len(LOCATIONS)
        current_search = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for city in LOCATIONS:
            for role in SEARCH_TERMS:
                current_search += 1
                percent_complete = int((current_search / total_searches) * 100)
                
                status_text.text(f"Searching for '{role}' in '{city}' ({current_search}/{total_searches})...")
                progress_bar.progress(percent_complete)
                
                try:
                    jobs = scrape_jobs(
                        site_name=["linkedin", "indeed", "zip_recruiter"],
                        search_term=role,
                        location=city,
                        results_wanted=results_count,
                        hours_old=72,
                        linkedin_fetch_description=True,
                        country_indeed='USA'
                    )
                    
                    if not jobs.empty:
                        all_jobs.append(jobs)
                        
                except Exception as e:
                    st.warning(f"Error searching for {role} in {city}: {e}")
        
        # --- Results Processing ---
        status_text.text("Processing results...")
        
        if all_jobs:
            df = pd.concat(all_jobs, ignore_index=True)
            df['mentions_visa'] = df['description'].apply(check_visa)
            
            # Filter for Visa Mentions
            filtered_df = df[df['mentions_visa'] == True].copy()
            
            if not filtered_df.empty:
                st.success(f"Found {len(filtered_df)} jobs mentioning sponsorship/visa!")
                
                # Display relevant columns
                display_cols = [
                    'site', 'title', 'company', 'location', 
                    'min_amount', 'max_amount', 'currency', 'mentions_visa', 'job_url'
                ]
                # Filter display_cols to only those that exist in df
                existing_cols = [c for c in display_cols if c in filtered_df.columns]
                
                st.dataframe(filtered_df[existing_cols], use_container_width=True)
                
                # Download Option
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Results as CSV",
                    data=csv,
                    file_name='job_search_results.csv',
                    mime='text/csv',
                )
            else:
                st.info("No jobs found mentioning the visa keywords.")
        else:
            st.error("No jobs found for the given criteria.")
        
        progress_bar.empty()
        status_text.empty()

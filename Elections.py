import streamlit as st
import pandas as pd
import schedule
import time
import threading
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# Path to ChromeDriver
driver_path = r'/Users/user2/Downloads/chromedriver-mac-arm64-2/chromedriver'
service = Service(driver_path)

# Global progress variable
progress = 0
progress_placeholder = st.empty()

# Function to update progress
def update_progress(current, total):
    global progress
    progress = int((current / total) * 100)
    progress_placeholder.text(f"Scraping Progress: {progress}%")

# Streamlit UI
st.title("Election Candidates Data Scraper")
st.write("This app scrapes candidate data and allows you to view and download the results.")

# Function to scrape data and save to candidates_data.csv
def scrape_data():
    global progress
    progress = 0  # Reset progress
    st.write("Scraping started...")

    driver = webdriver.Chrome(service=service)
    driver.get('https://affidavit.eci.gov.in/CandidateCustomFilter?electionType=27-AC-GENERAL-3-51&election=27-AC-GENERAL-3-51&states=S13')
    WebDriverWait(driver, 10)

    candidate_names, parties, statuses, states, constituencies = [], [], [], [], []
    round_counter = 1  # Counter for rounds

    while True:
        st.write(f"Round {round_counter} in progress...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        candidates = soup.find_all('tr')[1:]
        page_count = len(candidates)  # Number of rows to parse

        for i, candidate in enumerate(candidates):
            try:
                name = candidate.find('h4').text.strip()
                party = candidate.find('strong', text='Party :').next_sibling.strip()
                status = candidate.find('strong', text='Status :').find_next('font').text.strip()
                state = candidate.find('strong', text='State :').next_sibling.strip()
                constituency = candidate.find('strong', text='Constituency :').next_sibling.strip()
                
                candidate_names.append(name)
                parties.append(party)
                statuses.append(status)
                states.append(state)
                constituencies.append(constituency)
                
                # Update progress for each row parsed
                update_progress(i + 1, page_count)
            except Exception as e:
                print(f"Error parsing row: {e}")

        # Save data to CSV after completing a round
        df = pd.DataFrame({
            'Candidate Name': candidate_names,
            'Party': parties,
            'Status': statuses,
            'State': states,
            'Constituency': constituencies
        })
        df.to_csv('candidates_data.csv', index=False)
        st.write(f"Round {round_counter} completed. Data saved to candidates_data.csv.")

        # Increment the round counter
        round_counter += 1

        try:
            next_button = driver.find_element(By.XPATH, "//a[contains(text(),'Next')]")
            if not next_button.is_displayed() or 'disabled' in next_button.get_attribute('class'):
                break
            next_button.click()
            time.sleep(1)
        except Exception:
            break

    driver.quit()

# Button to start scraping
if st.button("Start Scraping Data"):
    threading.Thread(target=scrape_data).start()  # Run scraping in a separate thread
    st.write("Scraping in progress... Please wait.")

# Display and download the data
if os.path.exists("candidates_data.csv"):
    st.write("### Candidates Data")
    df = pd.read_csv("candidates_data.csv")
    st.dataframe(df)
    
    # Download button
    st.download_button(
        label="Download data as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='candidates_data.csv',
        mime='text/csv'
    )
else:
    st.write("No data available. Please start scraping first.")

# Schedule the task to run periodically (if needed for automation)
# Uncomment the following lines if you want to run the schedule periodically
# schedule.every(2).minutes.do(scrape_data)

# Run schedule in background (only for local testing)
# def run_schedule():
#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# threading.Thread(target=run_schedule).start()
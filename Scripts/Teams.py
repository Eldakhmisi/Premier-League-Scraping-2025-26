from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Configure Selenium Chrome
options = Options()
options.add_argument("--headless")  # Run in background
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Launch Chrome
driver = webdriver.Chrome(options=options)

try:
    url = "https://www.****.com/en/clubs"
    driver.get(url)

    # Wait for JavaScript to load
    time.sleep(5)

    # Find all club links
    club_elements = driver.find_elements(By.CSS_SELECTOR, "a.club-listings-card__team-name")

    data = []
    for club in club_elements:
        name = club.text.strip()
        link = club.get_attribute("href")
        data.append({"Team": name, "URL": link})

    # Create DataFrame
    df = pd.DataFrame(data)
    print(df)

    # Save to CSV
    df.to_csv("premier_league_clubs.csv", index=False)
finally:
    driver.quit()
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

options = Options()
#options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

all_data = []

#df is the DataFrame containing team names and URLs (See Teams.py)


for _, row in df.iterrows():
    print(f"Processing {row['Team']}...")
    print(f"URL: {row['URL']}")

    driver.get(row['URL'])
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("✅ Cookies accepted")
    except:
        print("ℹ No cookies popup")

    time.sleep(5)  # Ensure JS content loads



    # Extract club metadata
    meta_labels = driver.find_elements(By.CSS_SELECTOR, ".club-profile-bio__metadata-label")
    meta_values = driver.find_elements(By.CSS_SELECTOR, ".club-profile-bio__metadata-value")
    metadata = {lbl.text.strip(): val.text.strip() for lbl, val in zip(meta_labels, meta_values)}

    # Click on Squad tab
    try:
        squad_tab = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Squad"))
        )
        squad_tab.click()
        time.sleep(5)  # Wait for squad page load
    except:
        print(f"⚠ Squad tab not found for {row['Team']}")
        continue

    # Step 3: Extract squad data
    sections = driver.find_elements(By.CSS_SELECTOR, "h4.profiles__card-heading")
    for section in sections:
        position_group = section.text.strip()
        # Find all player links under this section
        player_cards = section.find_element(By.XPATH, "./following-sibling::*").find_elements(By.CSS_SELECTOR, "a.squad-list__item-link")
        print(f"Found {len(player_cards)} players in position group: {position_group}")
        
        for player in player_cards:
            player_name = player.find_element(By.CSS_SELECTOR, "span.squad-list__player-name").text.strip()
            player_number = player.find_element(By.CSS_SELECTOR, "span.squad-list__player-number").text.strip()
            player_position = player.find_element(By.CSS_SELECTOR, "div.squad-list__player-details").text.strip().replace(player_number, "").strip()
            player_url = player.get_attribute("href")
            player_img = player.find_element(By.CSS_SELECTOR, "img").get_attribute("src")

            all_data.append({
                "Club": row['Team'],
                "Club URL": row["URL"],
                **metadata,
                "Position Group": position_group,
                "Player Name": player_name,
                "Shirt Number": player_number,
                "Player Position": player_position,
                "Player URL": player_url,
                "Image": player_img
            })

    time.sleep(5)  # Wait before next club

# Step 4: Save DataFrame
df2 = pd.DataFrame(all_data)
df2.to_csv("premier_league_full_squads.csv", index=False)
print("✅ Data saved to premier_league_full_squads.csv")

driver.quit()
import math
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

df2 = pd.read_csv("premier_league_full_squads.csv")

chunk_size = 30  # Number of players per batch
num_chunks = math.ceil(len(df2) / chunk_size)

output_dir = "PlayersFullDatafolder"
os.makedirs(output_dir, exist_ok=True)

for chunk_idx in range(num_chunks):
    chunk_file = os.path.join(output_dir, f"player_chunk_{chunk_idx+1}.csv")

    # ✅ Skip if already processed
    if os.path.exists(chunk_file):
        print(f"Skipping chunk {chunk_idx+1} (already processed)")
        continue

    # ✅ Create new driver for each chunk
    options = Options()
    # options.add_argument("--headless")  # Uncomment if you don't need to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    start_idx = chunk_idx * chunk_size
    end_idx = min((chunk_idx + 1) * chunk_size, len(df2))
    chunk_df = df2.iloc[start_idx:end_idx]

    print(f"Processing chunk {chunk_idx+1}/{num_chunks} ({start_idx} to {end_idx})")

    player_data = []

    for _, row in chunk_df.iterrows():
        try:
            print(f"Processing player: {row['Player Name']} ({row['Club']})")

            driver.get(row["Player URL"])
            time.sleep(5)

            # Accept cookies
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                ).click()
            except:
                pass

            # -----------------------
            # 1. Extract visible bio stats
            # -----------------------
            try:
                bio_section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.player-profile-bio"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", bio_section)
                time.sleep(1)

                bio_labels = bio_section.find_elements(By.CSS_SELECTOR, ".player-profile-bio__item-label")
                bio_values = bio_section.find_elements(By.CSS_SELECTOR, ".player-profile-bio__item-value")
                visible_bio = {lbl.text.strip(): val.text.strip() for lbl, val in zip(bio_labels, bio_values)}
            except Exception as e:
                print(f"⚠ Bio section not found for {row['Player Name']}: {e}")
                visible_bio = {}

            appearances = visible_bio.get("Appearances")
            clean_sheets = visible_bio.get("Clean Sheets")
            saves_made = visible_bio.get("Saves Made")

            # -----------------------
            # 2. Full Bio Data
            # -----------------------
            try:
                full_bio_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div[1]/section/div/article/button'))
                )
                full_bio_btn.click()
                time.sleep(2)

                fb_labels = driver.find_elements(By.CSS_SELECTOR, ".player-profile-bio__item-label")
                fb_values = driver.find_elements(By.CSS_SELECTOR, ".player-profile-bio__item-value")
                full_bio_data = {lbl.text.strip(): val.text.strip() for lbl, val in zip(fb_labels, fb_values)}

                close_btn = driver.find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div[1]/section/div/div/div[2]/div[1]/button')
                close_btn.click()
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except:
                full_bio_data = {}

            # -----------------------
            # 3. Stats Tab
            # -----------------------
            player_stats = []
            try:
                stats_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Stats"))
                )
                stats_tab.click()
                time.sleep(5)

                try:
                    current_season_chip = driver.find_element(By.CSS_SELECTOR, "button.chip .chip__label")
                    current_season = current_season_chip.text.strip()
                except:
                    current_season = ""

                try:
                    no_stats = driver.find_element(By.CSS_SELECTOR, "h3.profiles-no-results__title")
                    if "No stats available" in no_stats.text:
                        filter_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div[2]/section/section/div/div/div/div[2]/div[1]/div/button'))
                        )
                        filter_btn.click()
                        time.sleep(1)

                        season_option = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//label[@for="playerStats_season_2"]'))
                        )
                        season_option.click()
                        time.sleep(1)

                        save_btn = driver.find_element(By.XPATH, '//button[span[text()="Save"]]')
                        save_btn.click()
                        time.sleep(5)

                        current_season_chip = driver.find_element(By.CSS_SELECTOR, "button.chip .chip__label")
                        current_season = current_season_chip.text.strip()
                except:
                    pass

                # Card stats
                card_labels = driver.find_elements(By.CSS_SELECTOR, ".profiles-stat-card__label")
                card_values = driver.find_elements(By.CSS_SELECTOR, ".profiles-stat-card__stat")
                for i in range(len(card_labels)):
                    player_stats.append({
                        "Type": "Card",
                        "Label": card_labels[i].text.strip(),
                        "Value": card_values[i].text.strip(),
                    })

                # List stats
                list_labels = driver.find_elements(By.CSS_SELECTOR, ".profiles-stats-list__stat-label")
                list_values = driver.find_elements(By.CSS_SELECTOR, ".profiles-stats-list__stat-value")
                for i in range(len(list_labels)):
                    player_stats.append({
                        "Type": "List",
                        "Label": list_labels[i].text.strip(),
                        "Value": list_values[i].text.strip(),
                    })

            except:
                current_season = None
                player_stats = []

            # Store results
            player_data.append({
                **row.to_dict(),
                "Career Appearances": appearances,
                "Career Clean Sheets": clean_sheets,
                "Career Saves Made": saves_made,
                "Full Bio": full_bio_data,
                "Stats Season": current_season,
                "Player Stats": player_stats
            })

            time.sleep(2)  # Shorter delay between players

        except Exception as e:
            print(f"❌ Error with {row['Player Name']}: {e}")

    # Save chunk
    chunk_df_out = pd.DataFrame(player_data)
    chunk_df_out.to_csv(chunk_file, index=False)
    print(f"✅ Saved {chunk_file}")

    # ✅ Close driver after each chunk
    driver.quit()
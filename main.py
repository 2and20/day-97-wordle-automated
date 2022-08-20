import pickle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
# import webdriver_manager.chrome
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import random
import smtplib

chrome_driver_path = "/usr/local/bin/chromedriver.exe"
letter_found = {}
json_to_del = []

option = webdriver.ChromeOptions()
option.add_argument("--no-sandbox")

# dir_path = os.getcwd()
# option.add_argument(f'user-data-dir={dir_path}/selenium')
# option.add_argument("user-data-dir=selenium")

# this apparently keeps the window open
option.add_experimental_option("detach", True)
driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

with open('five2.json') as json_file:
    # note i'm now using five2 file...which will delete non-existing wordle
# words at the end
    five_dict = json.load(json_file) # can now use this dict


def load_page_and_cookies():
    driver.get("https://www.nytimes.com/games/wordle/index.html")
    time.sleep(3)
    # load_cookies()
    time.sleep(5)
    # this closes the X icon on explanation box pop up at start
    try:
        driver.find_element(by=By.ID, value="pz-gdpr-btn-accept").click() # cookie accept
    except:
        pass
    time.sleep(1)
    driver.find_element(by=By.CSS_SELECTOR, value=".Modal-module_closeIcon__b4z74").click()
    return driver

def load_cookies():
    dir_path = os.getcwd()
    option.add_argument(f'user-data-dir={dir_path}/selenium')
    if os.path.exists('cookies.pkl'):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(3)
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

def pick_first_word():
    global letter_found
    print(f"letter_found (start) is: {letter_found}")
    first_word = list(random.choice(list(five_dict.keys())))
    print(f"first_word is {first_word}")
    time.sleep(4)
    driver.find_element(by=By.XPATH, value="//body").click()
    time.sleep(1)
    for letter in first_word:
        driver.find_element(by=By.XPATH, value="//body").send_keys(letter)
    time.sleep(1)

    # just here, the letters in current row will say "tbd". Use it to determine row number?
    tile_rows = driver.find_elements(By.CLASS_NAME, "Row-module_row__dEHfN")
    count = 0
    for row in tile_rows:
        if row.find_element(By.CLASS_NAME, "Tile-module_tile__3ayIZ").get_attribute("data-state") == "tbd":
            current_row = count
        count += 1
    print(f"current row from tile tbd before hitting enter is {current_row}")
    driver.find_element(by=By.XPATH, value="//body").send_keys(Keys.RETURN)
    time.sleep(2)
    check_word(first_word, current_row)

    # this section is trying to find all the letter, maybe drop them in a dictionarty
    # along with their values (letter and state)
    # or maybe create a few lists, all 30 long, can pick same #
    # for checking
    time.sleep(2)
    all_tiles = {}
    tile_rows = driver.find_elements(By.CLASS_NAME, "Row-module_row__dEHfN")
    tiles = tile_rows[current_row].find_elements(By.CLASS_NAME, "Tile-module_tile__3ayIZ")

    count=0
    ################### HAPPY WITH THIS GREEN SECTION. DELETES IF CORRECT LETTER NOT AT THAT POINT IN
    # DICT WORD
    correct_delete = []
    for tile in tiles:
        state = tile.get_attribute("data-state")
        if tile.get_attribute("data-state") == "correct":
            print(f"place where letter found: {count}, letter is {first_word[count]}")
            letter_found[count] = first_word[count] # 0 to 4
            if len(letter_found) == 5:
                game_won(first_word, current_row)
            print(f"letter_found[count]: {letter_found[count]}")
            [correct_delete.append(entry) for entry in five_dict if first_word[count] not in entry[count]]
        count += 1
    correct_delete = list(set(correct_delete))
    print(f"correct_delete len2: {len(correct_delete)}")
    for to_del in correct_delete:
        del five_dict[to_del]


    count = 0
    ################### THIS SECTION IS FOR YELLOW TILES
    # Deletes a five_dict entry if letter is at the yellow spot
    yellow_tiles = []
    correct_delete = []
    for tile in tiles:
        state = tile.get_attribute("data-state")
        if tile.get_attribute("data-state") == "present":
            yellow_tiles.append(first_word[count])
            [correct_delete.append(entry) for entry in five_dict if first_word[count] in entry[count]] # deletes any word that has letter in that spot
            [correct_delete.append(entry) for entry in five_dict if first_word[count] not in entry]
            # think you could test for more than 1 of same yellow letter? or yellow and grey?
        count += 1
    correct_delete = list(set(correct_delete))
    print(f"correct_delete len: {len(correct_delete)}")
    try:
        print(f"random correct_delete from yellow is: {random.choice(correct_delete)}")
    except:
        pass
    for to_del in correct_delete:
        del five_dict[to_del]

    print("DOES IT REACH HERE?")

    #### THIS SECTION FOR GREY TILES, REMEMBERING THAT IT COULD BE GREY COS SAME LETTER USED IN A SECOND PLACE...
    ## NEED TO FIX/FINISH THIS SECTION...HARD
    count = 0
    missing_letters2 = []
    dupe_letters = []
    correct_delete = []
    for tile in tiles:
        state = tile.get_attribute("data-state")
        if tile.get_attribute("data-state") == "absent":
            if first_word[count] not in letter_found.values():
                print("no dupe")
                if first_word[count] not in yellow_tiles:
                    missing_letters2.append(first_word[count])
            # else: # want to delete any word that has eg 2 A's if we have 1 A in letter_found and just got a grey A in the first_word
            #     # use count() somehow. this only works on hard mode i think! since i'll have eg 2 A's, versus 1 A stored in letter_found
            #     [correct_delete.append(entry) for entry in five_dict if first_word.count(first_word[count]) <= entry.count(first_word[count])]  # note that above it was "not in"
            #     print("are you here?")
        count += 1
    print(f"first_word in grey is: {first_word}")
    correct_delete = list(set(correct_delete))
    print(f"correct delete length in grey is: {len(correct_delete)}")
    for to_del in correct_delete:
        del five_dict[to_del]
    missing_letters2 = list(set(missing_letters2))
    print(f"missing letters are: {missing_letters2}")
    update_dict(missing_letters2)
    print(f"len(five_dict) = {len(five_dict)}")

    if current_row <5:
        pick_first_word()

    end_function(first_word, row)


def check_word(word, current_row):
    global json_to_del
    time.sleep(1)
    try: # this works if you win
        if driver.find_element(by=By.CLASS_NAME, value="AuthCTA-module_shareText__o7WL-").text == "Share":
            driver.find_element(by=By.XPATH, value="//body").click()
            time.sleep(0.2)
            game_won(word, current_row)
    except:
        pass

    # data-state="tbd" if word wasn't accepted (ie not in word list)
    # so can check this class, and the data_state tbd.
    letter_check = driver.find_elements(By.CSS_SELECTOR, 'div[data-state="tbd"]')
    if len(letter_check) == 5:
        is_word = "not a word"
    else:
        is_word = "is a word"
    print(f"{is_word}")
    if len(letter_check) == 5:
        word_string = ""
        for rpt in range(5):
            word_string += word[rpt]
            driver.find_element(by=By.XPATH, value="//body").send_keys(Keys.BACKSPACE)
        json_to_del.append(word_string)
        del five_dict[word_string] # ideally want these completely deleted from five.json...
        # maybe drop them in a csv file first, then delete, dunno. do later.
        pick_first_word()
    return

def update_dict(letters): # letters is a list of unique letters
    delete_list = []
    print(f"letters is: {letters}")
    for letter in letters:
        [delete_list.append(word) for word in five_dict if letter in word]
    delete_list = list(set(delete_list)) # delete duplicates that were made
    # from words that contained more than one of the letters! bug fix.
    print(f"len(delete_list) = {len(delete_list)}")
    for to_del in delete_list:
        del five_dict[to_del]
    return

def end_function(first_word, row):
    final_word = driver.find_element(by=By.CLASS_NAME, value="Toast-module_toast__Woeb-").text
    print(f"Finished! Your last guess was {''.join(first_word).upper()} but the answer was {final_word}")
    login_and_email()
    time.sleep(1)
    driver.find_element(by=By.XPATH, value="//body").click()
    update_json()
    email_board(first_word, row)

def game_won(first_word, current_row):
    update_json()
    winning_word = ''.join(first_word)
    print(f"You win! You got {winning_word} on row {current_row+1}!")
    final_board_before_login = get_final_board()
    login_and_email()
    time.sleep(5)
    final_board_after_login = get_final_board()
    print(f"first_word near end is {first_word}")
    if final_board_after_login == final_board_before_login:
        print("i'll email you what i did")
        email_board(first_word, current_row)
    else:
        print("no need to email, you did it")
    exit()

def login_and_email():
    # log in element:
    load_cookies()
    # dir_path = os.getcwd()
    # option.add_argument(f'user-data-dir={dir_path}/selenium')
    # if os.path.exists('cookies.pkl'):
    #     cookies = pickle.load(open("cookies.pkl", "rb"))
    #     for cookie in cookies:
    #         driver.add_cookie(cookie)
    #     driver.refresh()
    #     time.sleep(3)
    # pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    # time.sleep(5)

    # driver.find_element(by=By.CLASS_NAME, value="AuthCTA-module_loginButton__0FcEr").click()
    # driver.find_element(by=By.ID, value="email").send_keys(my_email)
    # driver.find_element(by=By.ID, value="email").send_keys(Keys.RETURN)
    # time.sleep(2)
    # driver.find_element(by=By.ID, value="password").send_keys(my_password)
    # driver.find_element(by=By.ID, value="password").send_keys(Keys.RETURN)
    time.sleep(10)
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    # load_cookies()

def get_final_board():
    final_board = []
    tile_rows = driver.find_elements(By.CLASS_NAME, "Row-module_row__dEHfN")
    for row in tile_rows:
        cells = row.find_elements(By.CLASS_NAME, "Tile-module_tile__3ayIZ")
        for cell in cells:
            final_board.append(cell.text)
    print(f"final_board is {final_board}")
    return final_board

def email_board(winning_word, current_row):
    sender_email = os.environ["SENDER_EMAIL"]
    sender_password = os.environ["SENDER_PASSWORD"]
    rec_email = os.environ["REC_EMAIL"]
    final_board = get_final_board()
    for thing in final_board:
        if thing == "":
            final_board.remove(thing)
    final_word = ''.join(final_board[-5:])
    winning_word = ''.join(winning_word)
    if current_row == 5:
        message1 = f"Subject:Wordle Auto-Fail!\nHi! I did Wordle for you automatically.\n\n" \
                   f"But sorry, I failed! The word was {final_word.upper()}."
    else:
        message1 = f"Subject:Wordle Auto-Success!\nHi! I did Wordle for you automatically.\n\n" \
               f"The word was {winning_word.upper()} and I got it in {current_row+1}."

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, rec_email, message1)
    server.quit()

def update_json():
    global json_to_del
    print(f"json_to_del is {json_to_del}")
    if len(json_to_del) > 1:
        with open('five2.json') as json_file:
            five_dict2 = json.load(json_file)
            print(f"len of five_dict2 after opening file is {len(five_dict2)}")
            for to_del in json_to_del:
                del five_dict2[to_del]
            # print(f"five_dict2 is {five_dict2}")
        with open("five2.json", 'w') as file:
            # file.write(json.dumps(five_dict2))
            json.dump(five_dict2, file, indent=4)


load_page_and_cookies()
pick_first_word()



















#this is accept cookie button
# <button id="pz-gdpr-btn-accept">ACCEPT</button>
# driver.find_element(by=By.ID, value="pz-gdpr-btn-accept").send_keys(Keys.RETURN)
# log in element:
# driver.find_element(by=By.CSS_SELECTOR, value=".Help-module_loginText__Osqyn a").send_keys(Keys.RETURN)
# driver.find_element(by=By.ID, value="email").send_keys(my_email)
# driver.find_element(by=By.ID, value="email").send_keys(Keys.RETURN)
# time.sleep(3)
# driver.find_element(by=By.ID, value="password").send_keys(my_password)
# driver.find_element(by=By.ID, value="password").send_keys(Keys.RETURN)
# time.sleep(500)
# try:
#     driver.find_element(by=By.CSS_SELECTOR, value=".recaptcha-checkbox-border").click()
# except:
#     pass


# this is a random google suggestion
# WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
# WebDriverWait(driver, 200).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "iframe[title='reCAPTCHA']")))

# WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.recaptcha-checkbox-border"))).click()
print("all the way at end!")

# iframe = driver.find_element(by=By.XPATH,value="/html/body/div[1]/div[3]/div/div[3]/div/div/div/iframe/html/body/div[1]/div[3]/div/div[3]/div/div/div/iframe")
# driver.switch_to.frame(iframe)
# driver.find_element(by=By.CSS_SELECTOR, value="recaptcha-checkbox-border").click()
# driver.switch_to.default_content()




# keyword = input("enter a character or press enter to continue")
# while keyword != "q":
#     time.sleep(100)
# if keyword == "q":
#     webdriver.quit()

# <button type="button" data-key="r" class="Key-module_key__Rv-Vp Key-module_fade__37Hk8" data-state="correct">r</button>
# data-state="correct"
#
# <button type="button" data-key="g" class="Key-module_key__Rv-Vp Key-module_fade__37Hk8" data-state="present">g</button>
# data-state="present"
#
# <button type="button" data-key="w" class="Key-module_key__Rv-Vp Key-module_fade__37Hk8" data-state="absent">w</button>
# data-state="absent"
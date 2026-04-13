from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pytest
import time
import tempfile


@pytest.fixture()
def driver():
    options = Options()

    # 완전 새 프로필 형성
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    # 비밀번호 팝업 차단
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)

    # 추가 옵션
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.saucedemo.com/")
    yield driver
    driver.quit()


def login(driver, username, password):
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.NAME, "user-name"))
    ).send_keys(username)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.NAME, "password"))
    ).send_keys(password)
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "login-button"))
    ).click()


@pytest.mark.parametrize("username, password, is_success, expected_error", [
    #TC-LOGIN-01
    ("standard_user", "secret_sauce", True, None),
    #TC-LOGIN-06
    ("standard_user", "wrong_password", False, "Username and password"),
    #TC-LOGIN-07
    ("invalid_user", "invalid_password", False, "Username and password"),
    #TC-LOGIN-09
    ("", "secret_sauce", False, "Username is required"),
    #TC-LOGIN-10
    ("standard_user", "", False, "Password is required"),
    #TC-LOGIN-11
    ("", "", False, "Username is required"),
    #TC-LOGIN-14
    ("a", "secret_sauce", False, "Username and password"),
    #TC-LOGIN-25
    ("locked_out_user", "secret_sauce", False, "locked out"),
    #TC-LOGIN-21
    ("<script>alert(1)</script>", "test", False, "Username and password"),
    #TC-LOGIN-20
    ("'OR '1'='1", "test", False, "Username and password"),
])
def test_login(driver, username, password, is_success, expected_error):

    login(driver, username, password)

    if is_success:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "inventory_list"))
        )
        assert element.is_displayed()
    else:
        error_message = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "error-message-container"))
        )
        assert expected_error in error_message.text


# TC-LOGIN-38
def test_access_after_logout(driver):

    # 1. 로그인
    login(driver, "standard_user", "secret_sauce")

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "inventory_list"))
    )
    # 2. 로그아웃 (사이드바 열기 -> 로그아웃 버튼 클릭)
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "react-burger-menu-btn"))
    ).click()

    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))
    ).click()

    # 3. 보호된 페이지 접근
    driver.get("https://www.saucedemo.com/inventory.html")

    # 4. inventory 페이지에서 벗어날 때까지 대기
    WebDriverWait(driver, 5).until(
        lambda d: "inventory" not in d.current_url
    )

    # 5. 로그인 페이지 요소 확인
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.NAME, "user-name"))
    )

    # 6. 검증
    assert "inventory" not in driver.current_url # inventory 문구가 URL에 없는가?
    assert driver.find_element(By.NAME, "user-name").is_displayed() # user-name의 ui가 보여지고 있는가?

# TC-LOGIN-31
def test_login_responds_time(driver):
    start_time = time.time()

    login(driver, "standard_user", "secret_sauce")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "inventory_list"))
    )

    end_time = time.time()
    response_time = end_time - start_time

    print(f" Response time: {response_time:.2f}s")

    assert response_time < 5

# TC-LOGIN-05
def test_back_after_login(driver):
    login(driver, "standard_user", "secret_sauce")

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "inventory_list"))
    )

    # 로그아웃
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "react-burger-menu-btn"))
    ).click()

    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))
    ).click()

    # 뒤로가기
    driver.back()

    # 검증
    assert "inventory" not in driver.current_url # URL 검증
    assert driver.find_element(By.NAME, "user-name").is_displayed() # UI 확인
from .pages.login import LoginPage

def check_user_logged_in(driver, username):
    user_menu = driver.find_element_by_id('user-menu')
    assert user_menu.get_attribute('data-username') == username

def test_login(driver, base_url):
    """
    TC38 - Sign in with valid username and password
    """
    page = LoginPage(driver, base_url)
    page.username_field().send_keys("admin")
    page.password_field().send_keys("password")
    page.signin_button().click()
    check_user_logged_in(driver, 'admin')

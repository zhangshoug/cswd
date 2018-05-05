from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options


def make_headless_browser():
    ## get the Firefox profile object
    firefoxProfile = FirefoxProfile()
    ## Disable CSS
    firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    ## Disable images
    firefoxProfile.set_preference('permissions.default.image', 2)
    ## Disable Flash
    firefoxProfile.set_preference(
        'dom.ipc.plugins.enabled.libflashplayer.so', 'false')

    options = Options()
    options.set_headless()
    browser = webdriver.Firefox(firefoxProfile, options=options)
    return browser

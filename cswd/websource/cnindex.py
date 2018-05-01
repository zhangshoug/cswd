from cswd.websource.selenium import make_headless_browser

url = 'http://www.cnindex.com.cn/syl.html?hy=c'
brower = make_headless_browser()
brower.get(url)
elem = brower.find_elements_by_id('hsls')
elem.click()
brower.page_source



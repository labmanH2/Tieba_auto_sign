from DrissionPage import ChromiumOptions, ChromiumPage
import json
import os
import shutil
import time
import requests

def read_cookie():
    """读取 cookie，优先从环境变量读取"""
    if "TIEBA_COOKIES" in os.environ:
        try:
            return json.loads(os.environ["TIEBA_COOKIES"])
        except Exception as e:
            print(f"Cookie解析失败：{e}，请检查环境变量格式")
            return []
    else:
        print("贴吧Cookie未配置！详细请参考教程！")
        return []

def get_level_exp(page):
    """获取等级和经验，如果找不到返回'未知'"""
    level = "未知"
    exp = "未知"
    try:
        # 定位两个等级元素（不会同时存在）
        level_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]//div/div[1]/div[3]/div[1]/a/div')
        level_ele_new = page.ele('xpath://div[contains(@class, "forum-suffix")]/svg[contains(@class, "level-icon")]/use')
        
        exist_level_ele = level_ele or level_ele_new
    
        if exist_level_ele == level_ele:
            level = level_ele.text.strip() if (level_ele and level_ele.text) else "未知"
        elif exist_level_ele == level_ele_new:
            href_val = level_ele_new.attr("xlink:href")
            level = href_val.replace("#level_", "") if href_val else "未知"
    except Exception as e:
        print(f"提取等级失败：{e}")
        level = "未知"

    try:
        exp_old_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]/div/div[1]/div[3]/div[2]/a/div[2]/span[1]')
        exp_new_ele = page.ele('xpath://div[contains(@class, "bar-info")]/div[contains(@class, "progress-text")]')
        exp_text_old = exp_old_ele.text.strip() if (exp_old_ele and exp_old_ele.text) else ""
        exp_text_new = exp_new_ele.text.strip().replace("经验 ", "") if (exp_new_ele and exp_new_ele.text) else ""
        exp = exp_text_old or exp_text_new or "未知"
    except Exception as e:
        print(f"提取经验失败：{e}")
        exp = "未知"
    return level, exp

if __name__ == "__main__":
    print("程序开始运行")
    notice = ''
    # 极简浏览器配置（只保留GitHub必须参数）
    co = ChromiumOptions()
    co.headless()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--start-maximized')

    chromium_path = shutil.which("chromium-browser")
    if chromium_path:
        co.set_browser_path(chromium_path)
    page = ChromiumPage(co)

    # 反反爬：隐藏webdriver
    page.run_cdp('Page.addScriptToEvaluateOnNewDocument', source='''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    ''')

    # 加载贴吧首页 + Cookie
    url = "https://tieba.baidu.com/"
    page.get(url, timeout=30)
    cookies = read_cookie()
    if cookies:
        page.set.cookies(cookies)
        time.sleep(3)  # 用sleep代替wait.loaded，兼容性最强
        page.refresh()
    time.sleep(3)

    over = False
    yeshu = 0
    count = 0
    while not over:
        yeshu += 1
        print(f"正在爬取第{yeshu}页贴吧列表...")
        page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}", timeout=30)
        time.sleep(3)

        for i in range(2, 22):
            element = page.ele(
                f'xpath://*[@id="like_pagelet"]/div[1]/div[1]/table/tbody/tr[{i}]/td[1]/a/@href'
            )
            if not element:
                if i == 2:
                    msg = f"全部爬取完成！本次总共签到 {count} 个吧..."
                    print(msg)
                    notice += msg + '\n\n'
                    over = True
                break
            try:
                tieba_url = element.attr("href")
                name = element.attr("title")
                if not tieba_url or not name:
                    continue
            except Exception as e:
                print(f"第{yeshu}页第{i}行爬取失败：{e}")
                continue

            print(f"正在处理{name}吧...")
            page.get(tieba_url, timeout=30)
            time.sleep(3)

            is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
            is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
            is_sign = is_sign_ele.text.strip() if (is_sign_ele and is_sign_ele.text) else ""
            is_sign_new = is_sign_ele_new.text.strip() if (is_sign_ele_new and is_sign_ele_new.text) else ""

            if is_sign.startswith("连续") or "连签" in is_sign_new:
                level, exp = get_level_exp(page)
                msg = f"{name}吧：已签到过！等级：{level}，经验：{exp}"
                print(msg)
                notice += msg + '\n\n'
                print("-------------------------------------------------")
            else:
                sign_btn_ele = page.ele('xpath://div[@id="signstar_wrapper"]//a[contains(@class, "j_sign_tip") and @title="签到"]')
                if sign_btn_ele is not None:
                    try:
                        page.wait.eles_loaded('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]', timeout=30)
                        sign_ele = page.ele('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]')
                        if sign_ele:
                            sign_ele.click()
                            time.sleep(2)
                            sign_ele.click()
                            time.sleep(2)
                            page.refresh()
                            time.sleep(3)
                            level, exp = get_level_exp(page)
                            msg = f"{name}吧：成功！等级：{level}，经验：{exp}"
                            print(msg)
                            notice += msg + '\n\n'
                        else:
                            msg = f"错误！{name}吧：旧版本贴吧页面找不到签到按钮"
                            print(msg)
                            notice += msg + '\n\n'
                    except Exception as e:
                        msg = f"错误！{name}吧：旧版签到失败：{e}"
                        print(msg)
                        notice += msg + '\n\n'
                else:
                    sign_btn_ele_new = page.ele('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]')
                    if sign_btn_ele_new is not None:
                        try:
                            page.wait.eles_loaded('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]', timeout=30)
                            sign_ele_new = page.ele('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]')
                            if sign_ele_new:
                                sign_ele_new.click()
                                time.sleep(2)
                                sign_ele_new.click()
                                time.sleep(2)
                                page.refresh()
                                time.sleep(3)
                                level, exp = get_level_exp(page)
                                msg = f"{name}吧：成功！等级：{level}，经验：{exp}"
                                print(msg)
                                notice += msg + '\n\n'
                            else:
                                msg = f"错误！{name}吧：新版本贴吧页面找不到签到按钮"
                                print(msg)
                                notice += msg + '\n\n'
                        except Exception as e:
                            msg = f"错误！{name}吧：新版签到失败：{e}"
                            print(msg)
                            notice += msg + '\n\n'
                    else:
                        msg = f"错误！{name}吧：新旧版签到按钮均未找到，页面结构可能变更"
                        print(msg)
                        notice += msg + '\n\n'
                print("-------------------------------------------------")
            count += 1
            page.back()
            time.sleep(2)
    page.close()
    if "SendKey" in os.environ:
        api = f'https://sc.ftqq.com/{os.environ["SendKey"]}.send'
        title = u"贴吧签到信息"
        data = {"text": title, "desp": notice}
        try:
            req = requests.post(api, data=data, timeout=60)
            if req.status_code == 200:
                print("Server酱通知发送成功")
            else:
                print(f"通知失败，状态码：{req.status_code}，响应：{req.text}")
        except Exception as e:
            print(f"通知发送异常：{e}")
    else:
        print("未配置Server酱服务，跳过通知...")
    print("程序运行结束")

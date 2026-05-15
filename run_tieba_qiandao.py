from DrissionPage import ChromiumOptions, ChromiumPage
import json
import os
import shutil
import time
import requests

def read_cookie(env_name):
    """从环境变量读取cookie"""
    if env_name in os.environ:
        return json.loads(os.environ[env_name])
    return []

def get_level_exp(page):
    """获取等级和经验"""
    level = "未知"
    exp = "未知"
    try:
        level_svg = page.ele('css:svg.level-icon')
        if level_svg:
            use_ele = level_svg.ele('css:use')
            if use_ele:
                href = use_ele.attr('xlink:href')
                level = href.replace('#level_', '') if href else '未知'
        if level == "未知":
            level_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]//div/div[1]/div[3]/div[1]/a/div')
            level_ele_new = page.ele('xpath://div[contains(@class, "forum-suffix")]/svg[contains(@class, "level-icon")]/use')
            exist_level_ele = level_ele or level_ele_new
            if exist_level_ele == level_ele:
                level = level_ele.text.strip() if level_ele.text else "未知"
            elif exist_level_ele == level_ele_new:
                href_val = level_ele_new.attr("xlink:href")
                level = href_val.replace("#level_", "") if href_val else "未知"
    except Exception:
        level = "未知"
    try:
        exp_old_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]/div/div[1]/div[3]/div[2]/a/div[2]/span[1]')
        exp_new_ele = page.ele('xpath://div[contains(@class, "bar-info")]/div[contains(@class, "progress-text")]')
        exp_text_old = exp_old_ele.text if exp_old_ele else ""
        exp_text_new = exp_new_ele.text.replace("经验 ", "") if exp_new_ele else ""
        exp = exp_text_old or exp_text_new
        if not exp:
            exp = "未知"
    except Exception:
        exp = "未知"
    return level, exp

def run_for_account(page, cookies, notice):
    """执行单个账号签到"""
    if not cookies:
        return notice, 0

    print("开始签到当前账号...")
    url = "https://tieba.baidu.com/"
    page.get(url)
    page.set.cookies(cookies)
    page.refresh()
    page._wait_loaded(15)

    over = False
    yeshu = 0
    count = 0
    max_pages = 15
    max_empty_pages = 2
    empty_page_count = 0

    while not over:
        yeshu += 1
        page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}")
        page._wait_loaded(15)
        empty_count = 0
        page_has_content = False
        page_empty = False

        for i in range(2, 100):
            if page_empty:
                break
            try:
                element = page.ele(
                    f'xpath://*[@id="like_pagelet"]/div[1]/div[1]/table/tbody/tr[{i}]/td[1]/a',
                    timeout=1
                )
                if not element:
                    empty_count += 1
                    if empty_count >= 10:
                        page_empty = True
                        break
                    continue
                page_has_content = True
                empty_count = 0
                tieba_url = element.attr("href")
                name = element.attr("title")
            except Exception:
                empty_count += 1
                if empty_count >= 10:
                    page_empty = True
                    break
                continue

            page.get(tieba_url)
            page.wait.eles_loaded('xpath://*[@id="signstar_wrapper"]/a/span[1]', timeout=30)
            is_signed = False
            is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
            if is_sign_ele and is_sign_ele.text.startswith("连续"):
                is_signed = True
            is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
            if is_sign_ele_new and "连签" in is_sign_ele_new.text:
                is_signed = True

            if is_signed:
                level, exp = get_level_exp(page)
                msg = f"{name}吧：已签到！等级：{level}，经验：{exp}"
            else:
                sign_success = False
                try:
                    sign_btn_old = page.ele('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]', timeout=5)
                    if sign_btn_old:
                        sign_btn_old.click()
                        time.sleep(2)
                        page.refresh()
                        page._wait_loaded(10)
                        sign_success = True
                except Exception:
                    pass
                if not sign_success:
                    try:
                        sign_btn_new = page.ele('xpath://div[contains(text(),"签到") and @class="center"]', timeout=5)
                        if sign_btn_new:
                            sign_btn_new.click()
                            time.sleep(2)
                            page.refresh()
                            page._wait_loaded(10)
                            sign_success = True
                    except Exception:
                        pass
                level, exp = get_level_exp(page)
                msg = f"{name}吧：{'签到成功' if sign_success else '签到失败'}！等级：{level}，经验：{exp}"

            print(msg)
            notice += msg + "\n\n"
            count += 1
            page.back()
            page._wait_loaded(10)

        if page_has_content:
            empty_page_count = 0
        else:
            empty_page_count += 1
            if empty_page_count >= max_empty_pages:
                print("✅ 此账号签到完毕")
                over = True
        if yeshu > max_pages:
            print("⚠️ 达到最大页数，停止")
            over = True

    notice += f"🎉 当前账号共签到：{count} 个吧\n\n"
    return notice, count

if __name__ == "__main__":
    print("贴吧双账号签到脚本启动")
    notice = "=== 贴吧双账号自动签到 ===\n\n"

    co = ChromiumOptions().headless()
    chromium_path = shutil.which("chromium-browser")
    if chromium_path:
        co.set_browser_path(chromium_path)
    page = ChromiumPage(co)

    # 账号1
    notice += "【账号 1 签到】\n\n"
    cookies1 = read_cookie("TIEBA_COOKIES")
    notice, count1 = run_for_account(page, cookies1, notice)

    # 账号2
    notice += "【账号 2 签到】\n\n"
    cookies2 = read_cookie("TIEBA_COOKIES2")
    notice, count2 = run_for_account(page, cookies2, notice)

    page.quit()

    total = count1 + count2
    notice += f"✅ 全部完成！总签到：{total}"
    print(f"总签到：{total}")

    # 推送
    if "SendKey" in os.environ:
        try:
            api = f"https://sc.ftqq.com/{os.environ['SendKey']}.send"
            requests.post(api, data={"text": "贴吧双账号签到完成", "desp": notice}, timeout=20)
        except Exception:
            pass

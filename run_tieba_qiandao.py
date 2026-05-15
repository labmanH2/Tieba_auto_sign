from DrissionPage import ChromiumOptions, ChromiumPage
import json
import os
import shutil
import time
import requests

def read_cookie(env_name):
    if env_name in os.environ:
        return json.loads(os.environ[env_name])
    return []

def get_level_exp(page):
    level = "未知"
    exp = "未知"
    try:
        level_svg = page.ele('css:svg.level-icon')
        if level_svg:
            use_ele = level_svg.ele('css:use')
            if use_ele:
                href = use_ele.attr('xlink:href')
                level = href.replace('#level_', '') if href else "未知"
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

def run_for_account(cookies):
    if not cookies:
        print("⚠️ 无Cookie，跳过")
        return 0

    print("\n" + "="*50)
    print("🚀 开始登录账号并签到")
    print("="*50)

    co = ChromiumOptions().headless()
    chromium_path = shutil.which("chromium-browser")
    if chromium_path:
        co.set_browser_path(chromium_path)
    page = ChromiumPage(co)

    url = "https://tieba.baidu.com/"
    page.get(url)
    page.set.cookies(cookies)
    page.get(url)
    time.sleep(3)

    over = False
    yeshu = 0
    count = 0
    max_pages = 15
    max_empty_pages = 2
    empty_page_count = 0

    while not over:
        yeshu += 1
        page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}")
        time.sleep(2)

        empty_count = 0
        page_has_content = False

        for i in range(2, 100):
            try:
                element = page.ele(
                    f'xpath://*[@id="like_pagelet"]/div[1]/div[1]/table/tbody/tr[{i}]/td[1]/a',
                    timeout=1
                )
                if not element:
                    empty_count += 1
                    if empty_count >= 10:
                        break
                    continue

                page_has_content = True
                tieba_url = element.attr("href")
                name = element.attr("title")

                page.get(tieba_url)
                time.sleep(2)

                is_signed = False
                if page.ele('text:已签到', timeout=1) or page.ele('text:连签', timeout=1):
                    is_signed = True

                if is_signed:
                    level, exp = get_level_exp(page)
                    print(f"✅ {name}吧：已签到！等级：{level}")
                else:
                    try:
                        sign_btn = page.ele('text:签到', timeout=2)
                        if sign_btn:
                            sign_btn.click()
                            time.sleep(2)
                            print(f"✅ {name}吧：签到成功！")
                        else:
                            print(f"❌ {name}吧：未找到签到按钮")
                    except:
                        print(f"❌ {name}吧：签到失败")

                count += 1
                page.back()
                time.sleep(1)

            except Exception:
                empty_count += 1
                if empty_count >= 10:
                    break

        if page_has_content:
            empty_page_count = 0
        else:
            empty_page_count += 1
            if empty_page_count >= max_empty_pages:
                print("✅ 此账号签到完成")
                over = True

        if yeshu > max_pages:
            print("⚠️ 已达最大页数，停止")
            over = True

    page.quit()
    print(f"\n🎉 本账号共签到：{count} 个吧")
    return count

if __name__ == "__main__":
    print("贴吧双账号签到脚本（最终修复版）")

    # 账号1
    print("\n📌 【账号 1 开始运行】")
    count1 = run_for_account(read_cookie("TIEBA_COOKIES"))

    # 账号2
    print("\n📌 【账号 2 开始运行】")
    count2 = run_for_account(read_cookie("TIEBA_COOKIES2"))

    total = count1 + count2
    print("\n" + "="*50)
    print(f"🎉 全部签到完毕！总签到数：{total}")
    print("="*50)

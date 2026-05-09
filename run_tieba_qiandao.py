from DrissionPage import ChromiumOptions, ChromiumPage
import json
import os
import shutil
import time
import requests

def read_cookie():
    """读取 cookie，优先从环境变量读取"""
    if "TIEBA_COOKIES" in os.environ:
        return json.loads(os.environ["TIEBA_COOKIES"])
    else:
        print("贴吧Cookie未配置！详细请参考教程！")
        return []

def get_level_exp(page):
    """获取等级和经验，如果找不到返回'未知'"""
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
            else:
                level = "未知"
    except Exception as e:
        level = "未知"
    try:
        exp_old_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]/div/div[1]/div[3]/div[2]/a/div[2]/span[1]')
        exp_new_ele = page.ele('xpath://div[contains(@class, "bar-info")]/div[contains(@class, "progress-text")]')
        exp_text_old = exp_old_ele.text if exp_old_ele else ""
        exp_text_new = exp_new_ele.text.replace("经验 ", "") if exp_new_ele else ""
        exp = exp_text_old or exp_text_new
        if not exp:
            exp = "未知"
    except:
        exp = "未知"
    return level, exp

if __name__ == "__main__":
    print("程序开始运行")
    notice = ''
    co = ChromiumOptions().headless()
    chromium_path = shutil.which("chromium-browser")
    if chromium_path:
        co.set_browser_path(chromium_path)
    page = ChromiumPage(co)
    url = "https://tieba.baidu.com/"
    page.get(url)
    page.set.cookies(read_cookie())
    page.refresh()
    page._wait_loaded(15)

    over = False
    yeshu = 0
    count = 0
    # ========== 双保险停止逻辑 ==========
    max_pages = 20           # 兜底：最多翻20页
    max_empty_pages = 2      # 主逻辑：连续2页空就停止
    empty_page_count = 0     # 连续空页计数器

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
                        print(f"📄 第{yeshu}页已读完，准备翻下一页")
                        page_empty = True
                        break
                    continue
                page_has_content = True
                empty_count = 0
                tieba_url = element.attr("href")
                name = element.attr("title")

            except Exception as e:
                empty_count += 1
                if empty_count >= 10:
                    print(f"📄 第{yeshu}页已读完，准备翻下一页")
                    page_empty = True
                    break
                continue

            # 签到逻辑（完全不变）
            page.get(tieba_url)
            page.wait.eles_loaded('xpath://*[@id="signstar_wrapper"]/a/span[1]',timeout=30)
            is_signed = False
            is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
            if is_sign_ele and is_sign_ele.text.startswith("连续"):
                is_signed = True
            is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
            if is_sign_ele_new and "连签" in is_sign_ele_new.text:
                is_signed = True

            if is_signed:
                level, exp = get_level_exp(page)
                msg = f"{name}吧：已签到过！等级：{level}，经验：{exp}"
                print(msg)
                notice += msg + '\n\n'
                print("-------------------------------------------------")
            else:
                sign_success = False
                try:
                    sign_btn_old = page.ele('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]', timeout=10)
                    if sign_btn_old:
                        sign_btn_old.click()
                        time.sleep(2)
                        page.refresh()
                        page._wait_loaded(15)
                        new_is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
                        new_is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
                        if (new_is_sign_ele and new_is_sign_ele.text.startswith("连续")) or \
                           (new_is_sign_ele_new and "连签" in new_is_sign_ele_new.text):
                            level, exp = get_level_exp(page)
                            msg = f"{name}吧：旧版签到成功！等级：{level}，经验：{exp}"
                            sign_success = True
                except Exception as e:
                    msg = f"{name}吧：旧版签到尝试失败 - {str(e)}"
                    print(msg)
                    notice += msg + '\n\n'
                if not sign_success:
                    try:
                        sign_btn_new = page.ele(
                            'xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]',
                            timeout=10
                        )
                        if sign_btn_new:
                            sign_btn_new.click()
                            time.sleep(2)
                            page.refresh()
                            page._wait_loaded(15)
                            new_is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
                            new_is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
                            if (new_is_sign_ele and new_is_sign_ele.text.startswith("连续")) or \
                               (new_is_sign_ele_new and "连签" in new_is_sign_ele_new.text):
                                level, exp = get_level_exp(page)
                                msg = f"{name}吧：新版签到成功！等级：{level}，经验：{exp}"
                                sign_success = True
                            else:
                                msg = f"{name}吧：新版签到按钮点击后未检测到签到成功"
                        else:
                            msg = f"{name}吧：未找到新版签到按钮"
                    except Exception as e:
                        msg = f"{name}吧：新版签到尝试失败 - {str(e)}"
                if sign_success:
                    print(msg)
                    notice += msg + '\n\n'
                else:
                    print(msg)
                    notice += msg + '\n\n'
                print("-------------------------------------------------")
            count += 1
            page.back()
            page._wait_loaded(10)

        # 停止判断1：连续空页
        if page_has_content:
            empty_page_count = 0
        else:
            empty_page_count += 1
            print(f"📄 第{yeshu}页为空，连续空页数：{empty_page_count}")
            if empty_page_count >= max_empty_pages:
                print("✅ 已连续2页无贴吧，所有关注的贴吧已签完，程序结束")
                over = True
                break

        # 停止判断2：最大页数兜底
        if yeshu > max_pages:
            print(f"⚠️ 已达到最大翻页数{max_pages}，程序结束")
            over = True
            break

    # Server酱通知
    if "SendKey" in os.environ:
        api = f'https://sc.ftqq.com/{os.environ["SendKey"]}.send'
        title = u"贴吧签到信息"
        data = {
            "text": title,
            "desp": notice
        }
        try:
            req = requests.post(api, data=data, timeout=60)
            if req.status_code == 200:
                print("Server酱通知发送成功")
            else:
                print(f"通知失败，状态码：{req.status_code}")
        except Exception as e:
            print(f"通知发送异常：{e}")
    else:
        print("未配置Server酱服务...")

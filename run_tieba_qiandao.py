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
    try:
        # 定位两个等级元素（不会同时存在）
        level_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]//div/div[1]/div[3]/div[1]/a/div')
        level_ele_new = page.ele('xpath://div[contains(@class, "forum-suffix")]/svg[contains(@class, "level-icon")]/use')
        
        # 核心：取存在的那个元素，都不存在则为None
        exist_level_ele = level_ele or level_ele_new
    
        # 提取等级文本（适配新旧版格式）
        if exist_level_ele == level_ele:
            # 旧版：直接取文本
            level = level_ele.text.strip() if level_ele.text else "未知"
        elif exist_level_ele == level_ele_new:
            # 新版：提取属性中的等级数字
            href_val = level_ele_new.attr("xlink:href")
            level = href_val.replace("#level", "") if href_val else "未知"
        else:
            # 都不存在
            level = "未知"
    except:
        # 任何错误都兜底为未知
        level = "未知"

    try:
        exp_old_ele = page.ele('xpath://*[@id="pagelet_aside/pagelet/my_tieba"]/div/div[1]/div[3]/div[2]/a/div[2]/span[1]')
        exp_new_ele = page.ele('xpath://div[contains(@class, "bar-info")]/div[contains(@class, "progress-text")]')
    # 分别取文本
        exp_text_old = exp_old_ele.text if exp_old_ele else ""
        exp_text_new = exp_new_ele.text.replace("经验 ", "") if exp_new_ele else ""
        # 二选一
        exp = exp_text_old or exp_text_new
        if not exp:
            exp = "未知"
    except:
        exp = "未知"

    return level, exp

if __name__ == "__main__":
    print("程序开始运行")

    # 通知信息
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

    while not over:
        yeshu += 1
        page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}")

        page._wait_loaded(15)

        for i in range(2, 22):
            element = page.ele(
                f'xpath://*[@id="like_pagelet"]/div[1]/div[1]/table/tbody/tr[{i}]/td[1]/a/@href'
            )
            try:
                tieba_url = element.attr("href")
                name = element.attr("title")
            except:
                msg = f"全部爬取完成！本次总共签到 {count} 个吧..."
                print(msg)
                notice += msg + '\n\n'
                page.close()
                over = True
                break

            page.get(tieba_url)
            

            page.wait.eles_loaded('xpath://*[@id="signstar_wrapper"]/a/span[1]',timeout=30)


            # 判断是否签到
            is_sign_ele = page.ele('xpath://*[@id="signstar_wrapper"]/a/span[1]')
            is_sign_ele_new = page.ele('xpath://div[contains(@class, "center") and contains(text(), "连签")]')
            is_sign = is_sign_ele.text if is_sign_ele else ""
            is_sign_new = is_sign_ele_new.text if is_sign_ele_new else ""
            if is_sign.startswith("连续") or "连签" in is_sign_new:
                level, exp = get_level_exp(page)
                msg = f"{name}吧：已签到过！等级：{level}，经验：{exp}"
                print(msg)
                notice += msg + '\n\n'
                print("-------------------------------------------------")
            else:
                # ========== 核心修改部分 ==========
                # 先找旧版签到按钮
                sign_btn_ele = page.ele('xpath://div[@id="signstar_wrapper"]//a[contains(@class, "j_sign_tip") and @title="签到"]')
                sign_success = False  # 标记是否签到成功
                
                if sign_btn_ele is not None:
                    # 旧版签到逻辑
                    page.wait.eles_loaded('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]',timeout=30)
                    sign_ele = page.ele('xpath://a[@class="j_signbtn sign_btn_bright j_cansign"]')
                    if sign_ele:
                        sign_ele.click()
                        time.sleep(1)  # 等待签到动作完成
                        sign_ele.click()
                        time.sleep(1)  # 等待签到动作完成
                        page.refresh()
                        page._wait_loaded(15)
                        level, exp = get_level_exp(page)
                        msg = f"{name}吧：成功！等级：{level}，经验：{exp}"
                        print(msg)
                        notice += msg + '\n\n'
                        print("-------------------------------------------------")
                        sign_success = True
                    #else:
                        #msg = f"错误！{name}吧：旧版本贴吧页面找不到签到按钮，尝试新版签到..."
                        #print(msg)
                        #notice += msg + '\n\n'
                
                # 旧版按钮不存在 或 旧版签到失败，执行新版签到逻辑
                if not sign_success:
                    sign_btn_ele_new = page.ele('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]')                    
                    if sign_btn_ele_new is not None:
                        page.wait.eles_loaded('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]', timeout=30)
                        sign_ele_new = page.ele('xpath://div[contains(@class, "button-wrapper") and @aria-describedby]/div[contains(@class, "center") and normalize-space(text())="签到"]')
                        if sign_ele_new:
                            sign_ele_new.click()
                            time.sleep(1)  # 等待签到动作完成
                            sign_ele_new.click()
                            time.sleep(1)  # 等待签到动作完成
                            page.refresh()
                            page._wait_loaded(15)
                            level, exp = get_level_exp(page)
                            msg = f"{name}吧：成功！等级：{level}，经验：{exp}"
                            print(msg)
                            notice += msg + '\n\n'
                            print("-------------------------------------------------")
                        else:
                            msg = f"错误！{name}吧：新版本贴吧界面找不到签到按钮，可能页面结构变了"
                            print(msg)
                            notice += msg + '\n\n'
                            print("-------------------------------------------------")
                # ========== 核心修改结束 ==========

            count += 1
            page.back()
            page._wait_loaded(10)

    if "SendKey" in os.environ:
        api = f'https://sc.ftqq.com/{os.environ["SendKey"]}.send'
        title = u"贴吧签到信息"
        data = {
        "text":title,
        "desp":notice
        }
        try:
            req = requests.post(api, data=data, timeout=60)
            if req.status_code == 200:
                print("Server酱通知发送成功")
            else:
                print(f"通知失败，状态码：{req.status_code}")
                print(api)
        except Exception as e:
            print(f"通知发送异常：{e}")
    else:
        print("未配置Server酱服务...")

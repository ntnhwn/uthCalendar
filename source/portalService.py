# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# portalService.py

import requests
from datetime import datetime
import database as db
import utils
import redisManager

def verifyUthCredentials(user, password):
    try:
        r = requests.post("https://portal.ut.edu.vn/api/v1/user/login", json={"username": user, "password": password}, timeout=15)
        data = r.json()
        if r.status_code == 200 and data.get("token"): return True, "Thành công"
        return False, data.get("message", "Sai tài khoản hoặc mật khẩu")
    except: return False, "Lỗi kết nối server trường"

def getClassesByDate(chatId, user, password, targetDate):
    try:
        tk = getValidPortalToken(chatId, user, password)
        if not tk: return None
        thu = datetime.strptime(targetDate, "%Y-%m-%d").weekday() + 2 
        res = requests.get(f"https://portal.ut.edu.vn/api/v1/lichhoc/lichTuan?date={targetDate}", headers={"authorization": f"Bearer {tk}"}, timeout=20)
        return [c for c in res.json().get("body", []) if c.get("thu") == thu]
    except: return None

def verifyAndSaveUser(chatId, mssv, password):
    isValid, reason = verifyUthCredentials(mssv, password)
    if isValid:
        conn = db.getDbConn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (chat_id, uth_user, uth_pass) VALUES (%s, %s, %s) ON CONFLICT (chat_id) DO UPDATE SET uth_user = EXCLUDED.uth_user, uth_pass = EXCLUDED.uth_pass",
            (str(chatId), utils.encryptData(mssv), utils.encryptData(password))
        )
        conn.commit(); cur.close(); conn.close()
        utils.log("SUCCESS", f"User {chatId} đã đăng ký thành công")
        return True, "🎉 <b>Đăng ký thành công!</b> Mình sẽ tự động nhắc lịch cho bạn."
    
    utils.log("ERROR", f"User {chatId} đăng ký thất bại: {reason}")
    return False, f"❌ Thất bại: {reason}"

def getValidPortalToken(chatId, rawUser, rawPass):
    cachedToken = redisManager.getSession(chatId, 'portal')
    if cachedToken: return cachedToken

    try:
        r = requests.post("https://portal.ut.edu.vn/api/v1/user/login", 
                        json={"username": rawUser, "password": rawPass}, timeout=15)
        token = r.json().get("token")
        if token:
            redisManager.saveSession(chatId, 'portal', token, expire=7200)
            return token
    except: pass
    return None

def formatCalendarMessage(chatId, dateStr, isAuto=False):
    u = db.getUserCredentials(chatId)
    if not u: return "Bạn chưa đăng ký tài khoản!"
    
    rawUser = utils.decryptData(u[1])
    rawPass = utils.decryptData(u[2])

    classes = getClassesByDate(chatId, rawUser, rawPass, dateStr)
    if classes:
        header = f"🔔 <b>NHẮC LỊCH TỰ ĐỘNG ({dateStr})</b>\n" if isAuto else f"📅 <b>LỊCH HỌC {dateStr}</b>\n"
        msg = header + "━━━━━━━━━━━━━━━━━━\n"
        for c in classes:
            courseLink = c.get('link', 'https://courses.ut.edu.vn/')
            msg += f"\n📘 <a href='{courseLink}'>{c['tenMonHoc']}</a>"
            msg += f"\n⏰ {c['tuGio']} - {c['denGio']}"
            msg += f"\n📍 {c['tenPhong']}\n"
        msg += f"\n🔗 <a href='https://portal.ut.edu.vn/'>Portal UTH</a>"
        return msg
    else:
        if not isAuto:
            return f"🎉 Ngày {dateStr} bạn được nghỉ nè!"

def updateNotifyStatus(chatId, newStatus):
    try:
        conn = db.getDbConn(); cur = conn.cursor()
        cur.execute("UPDATE users SET notify_enabled = %s WHERE chat_id = %s", (newStatus, str(chatId)))
        conn.commit(); cur.close(); conn.close()
    except: pass        
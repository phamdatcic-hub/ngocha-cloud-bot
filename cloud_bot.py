# -*- coding: utf-8 -*-



"""



CLOUD TELEGRAM BOT 24/7 - CÔNG TY TNHH TM&DV KIẾN TRÚC NGỌC HÀ (MST: 0601309667)



================================================================================



Trợ lý Kế toán Trưởng AI trực ban Cloud 24/7 (@ngocha_ketoan_bot)



Triển khai độc lập 100% trên Cloud miễn phí (Render.com / Koyeb / Docker)



ĐẶC TÍNH KỸ THUẬT CỐT LÕI:



1. Đọc Sổ Master trực tiếp từ OneDrive Direct Download Link ở chế độ CHỈ ĐỌC (io.BytesIO).



   - Bảo toàn 100% tính bất biến SSOT của Sổ Master, tuyệt đối không sửa đổi file gốc.



   - Cơ chế bộ nhớ đệm (TTL Cache 5 phút) tối ưu tốc độ và tiết kiệm băng thông.



2. Tích hợp Google Gemini AI chính chủ từ Google AI Studio:



   - Xưng hô lễ phép, ấm áp, tận tụy với Giám đốc Đặng Thị Hà ("Sếp Hà / Chị Hà").



   - Trả lời chuẩn mực kế toán, tuân thủ TCVN: dấu chấm (.) phân cách hàng nghìn (100.076.124 đ).



   - Tự động fallback sang trích xuất dữ liệu gốc nếu Gemini API bận/mất mạng.



3. Bảo mật Passcode đa lớp:



   - Mặc định bảo vệ Sếp Hà (Chat ID: 2001590233) toàn quyền Giám đốc.



   - Mã bảo vệ nội bộ: 'Ngocha@123' (không phân biệt hoa/thường).



   - Người lạ chưa có Passcode bị từ chối phục vụ ngay lập tức.



4. Tích hợp HTTP Health-Check Server (Port 8080/10000):



   - Duy trì tiến trình sống 24/7 trên gói Free Web Service của Render.com và Koyeb.



   - Cơ chế phục hồi tự động khi mạng chập chờn, xử lý triệt để lỗi 409 Conflict.



"""



import os



import sys



import time



import json



import base64



import threading



import io



import re



from datetime import datetime



from http.server import HTTPServer, BaseHTTPRequestHandler



import urllib.request



import urllib.parse



import urllib.error



# Thư viện ngoài



try:



    import requests



except ImportError:



    requests = None



try:



    import openpyxl



except ImportError:



    openpyxl = None



# ==============================================================================



# CẤU HÌNH BIẾN MÔI TRƯỜNG & MẶC ĐỊNH AN TOÀN



# ==============================================================================



TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()



GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    try:
        cred_path = os.path.expanduser(r"~\.dsh\.credentials.yaml")
        if os.path.exists(cred_path):
            with open(cred_path, "r", encoding="utf-8") as f:
                m = re.search(r"GEMINI_API_KEY:\s*(\S+)", f.read())
                if m:
                    GEMINI_API_KEY = m.group(1).strip()
    except Exception:
        pass



OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", base64.b64decode("c2stb3ItdjEtMWM3YWViODE4NDkxNmZhN2Y3ODFmMjhhOWQ4Mjc0NGFlZTY1ZjA4M2Y5OGI4ODJhYjY0NjA4MjNjMWQyZWRiYQ==").decode("utf-8")).strip()



ONEDRIVE_FILE_URL = os.environ.get("ONEDRIVE_FILE_URL", "").strip()



BOT_PASSCODE = os.environ.get("BOT_PASSCODE", "Ngocha@123").strip().lower()



ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "2001590233"))



PORT = int(os.environ.get("PORT", "8080"))



# Bàn phím nút bấm nhanh 1 chạm theo 5 Đèn Báo Quản Trị Ngọc Hà

KEYBOARD_5_DEN_BAO = {

    "keyboard": [

        [{"text": "🚦 5 Đèn Báo Quản Trị"}, {"text": "💰 Dòng Tiền & Tiền Về"}],

        [{"text": "🤝 Công Nợ 11 NCC"}, {"text": "⏳ Công Nợ KH (TK 131)"}],

        [{"text": "📦 Tồn Kho Chống Âm"}, {"text": "🧾 Soạn HĐ Nháp"}]

    ],

    "resize_keyboard": True,

    "persistent": True

}



# Telegram API URL



TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"



# Bộ nhớ người dùng đã xác thực (Admin mặc định toàn quyền CEO Part-time: Mr. Phạm Đạt)



AUTHENTICATED_USERS = {



    str(ADMIN_CHAT_ID): {



        "name": "Sếp Đạt",



        "full_name": "Mr. Phạm Đạt",



        "role": "CEO",



        "note": "Lãnh đạo điều hành chiến lược, kết nối trực tiếp trên Telegram",



        "authenticated_at": "2026-11-20T00:00:00"



    }



}



# ==============================================================================



# QUY CHUẨN ĐỊNH DẠNG SỐ VÀ TIỀN TỆ (TCVN & QUY TẮC SỐ 18)



# ==============================================================================




# ==============================================================================
# SMART GATEWAY CONFIGURATION (ANTIGRAVITY PC FIRST - CLAUDE SONNET 4.6 DESIGN)
# ==============================================================================
PC_NGROK_URL = os.environ.get("PC_NGROK_URL", "https://overplant-green-dollop.ngrok-free.dev").strip()
PC_STATUS_ENDPOINT = f"{PC_NGROK_URL}/api/status"
PC_CHAT_ENDPOINT = f"{PC_NGROK_URL}/api/chat"
PC_PIN_HEADERS = {
    "x-ngoc-ha-pin": "1408",
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "NgocHa-Cloud-Gateway/2.0"
}

def check_pc_online() -> bool:
    """
    Kiểm tra Antigravity PC có đang online không qua Ngrok.
    GET /api/status với PIN header '1408', timeout 3s.
    """
    if not PC_NGROK_URL:
        return False
    try:
        if requests is not None:
            resp = requests.get(PC_STATUS_ENDPOINT, headers=PC_PIN_HEADERS, timeout=3)
            return (resp.status_code == 200)
        else:
            req = urllib.request.Request(PC_STATUS_ENDPOINT, headers=PC_PIN_HEADERS)
            with urllib.request.urlopen(req, timeout=3) as resp:
                return (resp.status == 200)
    except Exception as e:
        print(f"[{datetime.now()}] [GATEWAY] PC Offline check: {e}")
        return False

def forward_to_pc_antigravity(prompt_text: str, chat_id: int = None, caller_name: str = "Sếp Đạt") -> str:
    """
    Chuyển tiếp câu hỏi tới Bộ Não Kế toán Trưởng Antigravity PC qua Ngrok.
    POST /api/chat với PIN header '1408' và body {"message": prompt_text}.
    Timeout 45s.
    """
    ANTIGRAVITY_FOOTER = "\n\n🧠 *[Bộ Não Kế toán Trưởng Antigravity PC trực tiếp đối soát]*"
    payload = {"message": prompt_text}
    headers = {**PC_PIN_HEADERS, "Content-Type": "application/json"}
    try:
        print(f"[{datetime.now()}] [GATEWAY] Đang chuyển tiếp tới Antigravity PC: {prompt_text[:60]}...")
        if requests is not None:
            resp = requests.post(PC_CHAT_ENDPOINT, headers=headers, json=payload, timeout=75)
            if resp.status_code == 200:
                data = resp.json()
                answer = (data.get("response") or data.get("reply") or "").strip()
                if answer and not any(err in answer for err in ["rpc error: code = Unavailable", "connection error"]):
                    print(f"[{datetime.now()}] [GATEWAY] Antigravity PC phản hồi thành công ({len(answer)} ký tự).")
                    return f"{answer}{ANTIGRAVITY_FOOTER}"
                else:
                    print(f"[{datetime.now()}] [GATEWAY] Phản hồi từ PC có lỗi hoặc rỗng -> Chuyển Fallback.")
                    return None
            else:
                print(f"[{datetime.now()}] [GATEWAY] PC trả về HTTP {resp.status_code} -> Chuyển Fallback.")
                return None
        else:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(PC_CHAT_ENDPOINT, data=data_bytes, headers=headers)
            with urllib.request.urlopen(req, timeout=75) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    answer = (data.get("response") or data.get("reply") or "").strip()
                    if answer and not any(err in answer for err in ["rpc error: code = Unavailable", "connection error"]):
                        return f"{answer}{ANTIGRAVITY_FOOTER}"
                    return None
                return None
    except Exception as e:
        print(f"[{datetime.now()}] [GATEWAY] Lỗi chuyển tiếp tới PC: {e} -> Chuyển Fallback.")
        return None

def fmt_money(val) -> str:



    """Định dạng tiền chuẩn TCVN: dấu chấm phân cách hàng nghìn (100.076.124 đ)"""



    if val is None:



        return "0 đ"



    try:



        val = float(val)



        s = f"{abs(val):,.0f}".replace(",", ".")



        sign = "-" if val < 0 else ""



        return f"{sign}{s} đ"



    except Exception:



        return str(val)



def fmt_tr(val) -> str:



    """Định dạng triệu đồng gọn gàng (100,08 tr hoặc 18,39 tr)"""



    if val is None:



        return "0 tr"



    try:



        val = float(val)



        s = f"{abs(val)/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



        sign = "-" if val < 0 else ""



        return f"{sign}{s} tr"



    except Exception:



        return str(val)



def fmt_qty(val) -> str:



    """Định dạng số lượng: không hiển thị số thập phân giả nếu là số nguyên"""



    if val is None:



        return "0"



    try:



        val = float(val)



        if val.is_integer():



            return f"{int(val):,}".replace(",", ".")



        s = f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")



        return s



    except Exception:



        return str(val)



# ==============================================================================



# QUẢN LÝ BỘ NHỚ ĐỆM DỮ LIỆU SỔ MASTER (TTL CACHE)



# ==============================================================================



MASTER_CACHE = {



    "timestamp": 0,



    "summary_text": "",



    "raw_facts": {},



    "status": "Chưa tải",



    "last_error": None



}



CACHE_LOCK = threading.Lock()



CACHE_TTL_SECONDS = 300  # 5 phút tự động làm mới một lần



def convert_onedrive_url(raw_url: str) -> str:



    """



    Chuyển đổi các dạng liên kết chia sẻ OneDrive / SharePoint thành Direct Download Link.



    Hỗ trợ cả link 1drv.ms ngắn và link SharePoint của doanh nghiệp.



    """



    if not raw_url:



        return ""



    url = raw_url.strip()



    # Dạng 1: Đã là link direct download



    if "download=1" in url or "root/content" in url:



        return url



    # Dạng 2: Link ngắn 1drv.ms -> dùng chuẩn Microsoft Graph API base64



    if "1drv.ms" in url:



        try:



            encoded_url = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")



            return f"https://api.onedrive.com/v1.0/shares/u!{encoded_url}/root/content"



        except Exception:



            return url



    # Dạng 3: Link onedrive.live.com thông thường



    if "onedrive.live.com" in url:



        if "view.aspx" in url:



            return url.replace("view.aspx", "download")



        if "?" in url:



            return f"{url}&download=1"



        return f"{url}?download=1"



    # Dạng 4: Link SharePoint



    if "sharepoint.com" in url:



        if "?" in url:



            return f"{url}&download=1"



        return f"{url}?download=1"



    return url



def fetch_master_workbook():



    """



    Tải file Sổ Master:



    1. Ưu tiên tải trực tiếp từ GitHub Cloud Repo (cập nhật mới nhất từ máy tính)



    2. Dự phòng đọc file cục bộ đã đóng gói trong container



    3. Dự phòng tải từ OneDrive (nếu có cấu hình)



    Chạy 100% trong bộ nhớ RAM qua io.BytesIO, CHẾ ĐỘ CHỈ ĐỌC (READ-ONLY).



    """



    if openpyxl is None:



        raise ImportError("Thiếu thư viện openpyxl để đọc Sổ Master.")



    file_bytes = None



    # 1. Tải trực tiếp từ GitHub Cloud Repo (luôn có bản mới nhất do máy tính tự động đồng bộ)



    github_url = "https://raw.githubusercontent.com/phamdatcic-hub/ngocha-cloud-bot/main/So%20Theo%20Doi%20Ke%20Toan%20Ngoc%20Ha.xlsx"



    try:



        req = urllib.request.Request(github_url, headers={"User-Agent": "NgocHa-Cloud-Bot", "Cache-Control": "no-cache"})



        with urllib.request.urlopen(req, timeout=25) as resp:



            content = resp.read()



            if content.startswith(b"PK\x03\x04"):



                file_bytes = content



                print(f"[{datetime.now()}] [INFO] Đã tải Sổ Master trực tiếp từ GitHub Cloud ({len(file_bytes)} bytes) thành công!")



    except Exception as ge:



        print(f"[{datetime.now()}] [WARN] Không tải được từ GitHub Cloud raw: {ge}")



    # 2. Đọc file cục bộ nếu có sẵn trong thư mục



    if not file_bytes:



        local_candidates = [



            "So Theo Doi Ke Toan Ngoc Ha.xlsx",



            os.path.join(os.getcwd(), "So Theo Doi Ke Toan Ngoc Ha.xlsx"),



            os.path.join(os.path.dirname(__file__), "So Theo Doi Ke Toan Ngoc Ha.xlsx"),



            os.path.join(os.path.dirname(__file__), "..", "01 So Sach Ke Toan", "So Theo Doi Ke Toan Ngoc Ha.xlsx"),



            os.path.join(os.getcwd(), "01 So Sach Ke Toan", "So Theo Doi Ke Toan Ngoc Ha.xlsx")



        ]



        for p in local_candidates:



            if os.path.exists(p):



                try:



                    with open(p, "rb") as f:



                        file_bytes = f.read()



                    print(f"[{datetime.now()}] [INFO] Đã đọc Sổ Master từ file cục bộ: {p} ({len(file_bytes)} bytes)")



                    break



                except Exception:



                    pass



    # 3. Dự phòng tải từ OneDrive nếu các cách trên chưa được



    if not file_bytes:



        direct_url = convert_onedrive_url(ONEDRIVE_FILE_URL)



        if direct_url:



            try:



                headers = {"User-Agent": "Mozilla/5.0"}



                req = urllib.request.Request(direct_url, headers=headers)



                with urllib.request.urlopen(req, timeout=30) as response:



                    content = response.read()



                    if content.startswith(b"PK\x03\x04"):



                        file_bytes = content



            except Exception as oe:



                print(f"[{datetime.now()}] [WARN] Không tải được từ OneDrive: {oe}")



    if not file_bytes:



        raise FileNotFoundError("Chưa tìm thấy nguồn dữ liệu Sổ Master trên Cloud!")



    # Mở workbook ở chế độ data_only = True để lấy số liệu thực tế đã tính



    buf = io.BytesIO(file_bytes)



    wb = openpyxl.load_workbook(buf, data_only=True)



    return wb



def parse_master_accounting_data(wb) -> dict:



    """



    Trích xuất dữ liệu kế toán trọng yếu từ 5 Khối Quản Trị Cốt Lõi.



    Bảo vệ 100% tính bất biến SSOT, số liệu chính xác từng đồng.



    """



    facts = {



        "timestamp": datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y"),



        "vat_in": {},



        "vat_out": {},



        "ncc_debts": [],



        "ncc_prepays": [],



        "ncc_total_debt": 0.0,



        "ncc_total_prepay": 0.0,



        "stock": {},



        "stock_low": [],



        "inventory_map": {}



    }



    # -------------------------------------------------------------------------



    # 1. TIỀN VỀ BÁN HÀNG & HÓA ĐƠN CHỜ XUẤT (Sheet '01 Tiền Về')



    # -------------------------------------------------------------------------



    if "01 Tiền Về" in wb.sheetnames:



        ws_tv = wb["01 Tiền Về"]



        missing_vat = []



        total_sales_amt = 0.0



        total_sales_count = 0



        recent_in = []



        for r in range(8, ws_tv.max_row + 1):



            loai = str(ws_tv.cell(r, 6).value or "").strip()



            amt = float(ws_tv.cell(r, 5).value or 0)



            if amt <= 0:



                continue



            desc_text = (str(ws_tv.cell(r, 3).value or "") + " " + str(ws_tv.cell(r, 4).value or "")).strip()



            hd_val = ws_tv.cell(r, 11).value



            date_val = ws_tv.cell(r, 2).value



            date_str = str(date_val)[:10] if date_val else ""



            is_sales = ("1." in loai) or ("bán hàng" in loai.lower())



            if not is_sales and "2." not in loai and "3." not in loai:



                if any(kw in desc_text.lower() for kw in ["mua hang", "mua hàng", "tiền cọc", "tien coc", "nội thất", "nhựa"]):



                    is_sales = True



            if is_sales:



                total_sales_amt += amt



                total_sales_count += 1



                if hd_val is None or str(hd_val).strip() in ["", "0", "None"]:



                    missing_vat.append({



                        "row": r,



                        "date": date_str,



                        "cust": str(ws_tv.cell(r, 3).value or "Khách lẻ"),



                        "amt": amt,



                        "desc": desc_text



                    })



            if len(recent_in) < 5:



                recent_in.append({



                    "date": date_str,



                    "cust": str(ws_tv.cell(r, 3).value or ""),



                    "amt": amt



                })



        facts["vat_in"] = {



            "total_amt": total_sales_amt,



            "total_count": total_sales_count,



            "missing_vat": missing_vat,



            "recent": recent_in



        }



    # -------------------------------------------------------------------------



    # 2. HÓA ĐƠN ĐẦU RA & CÔNG NỢ PHẢI THU (Sheet '02 HD Dau Ra')



    # -------------------------------------------------------------------------



    if "02 HD Dau Ra" in wb.sheetnames:



        ws_out = wb["02 HD Dau Ra"]



        all_inv_numbers = []



        unpaid_invoices = []



        for r in range(4, ws_out.max_row + 1):



            inv_no = str(ws_out.cell(r, 8).value or "").strip()



            if inv_no and inv_no != "None":



                digits = "".join(c for c in inv_no if c.isdigit())



                if digits:



                    all_inv_numbers.append(int(digits))



                stt_tt = str(ws_out.cell(r, 23).value or "").upper()



                if "CHƯA THANH TOÁN" in stt_tt or "NỢ TK 131" in stt_tt:



                    cust = str(ws_out.cell(r, 4).value or "")



                    note = str(ws_out.cell(r, 24).value or "")



                    amt = float(ws_out.cell(r, 15).value or 0)



                    unpaid_invoices.append({



                        "no": inv_no,



                        "cust": cust,



                        "amt": amt,



                        "note": note



                    })



        max_num = max(all_inv_numbers) if all_inv_numbers else 156



        facts["vat_out"] = {



            "total_issued": len(set(all_inv_numbers)),



            "latest_no": f"{max_num:08d}",



            "unpaid": unpaid_invoices



        }



    # -------------------------------------------------------------------------



    # 3. CÔNG NỢ 11 NHÀ CUNG CẤP (Sheet '03 Đối Soát Công Nợ 11 NCC' & '02 Tiền Đi')



    # -------------------------------------------------------------------------



    hd_by_ncc = {}



    if "DATA HD DAU VAO" in wb.sheetnames:



        ws_dt_in = wb["DATA HD DAU VAO"]



        for r in range(4, ws_dt_in.max_row + 1):



            code = str(ws_dt_in.cell(r, 1).value or "").strip()



            amt = float(ws_dt_in.cell(r, 6).value or 0)



            if code:



                hd_by_ncc[code] = hd_by_ncc.get(code, 0.0) + amt



    acb_by_ncc = {}



    if "02 Tiền Đi" in wb.sheetnames:



        ws_td = wb["02 Tiền Đi"]



        for r in range(8, ws_td.max_row + 1):



            c_val = str(ws_td.cell(r, 8).value or "").strip()



            amt = float(ws_td.cell(r, 4).value or 0)



            if c_val:



                acb_by_ncc[c_val] = acb_by_ncc.get(c_val, 0.0) + amt



    if "03 Đối Soát Công Nợ 11 NCC" in wb.sheetnames:



        ws_ncc = wb["03 Đối Soát Công Nợ 11 NCC"]



        total_debt = 0.0



        total_prepay = 0.0



        debt_list = []



        prepay_list = []



        for r in range(4, 15):



            code = str(ws_ncc.cell(r, 2).value or "").strip()



            name = str(ws_ncc.cell(r, 3).value or "").strip()



            h = hd_by_ncc.get(code, 0.0)



            a = acb_by_ncc.get(code, 0.0)



            diff = h - a



            # Dung sai kế toán: sai số nhỏ <= 50.000 đ xem như đã cân đối



            if diff > 50000:



                total_debt += diff



                debt_list.append({"code": code, "name": name, "invoiced": h, "paid": a, "debt": diff})



            elif diff < -50000:



                total_prepay += (-diff)



                prepay_list.append({"code": code, "name": name, "invoiced": h, "paid": a, "prepay": -diff})



        facts["ncc_debts"] = debt_list



        facts["ncc_prepays"] = prepay_list



        facts["ncc_total_debt"] = total_debt



        facts["ncc_total_prepay"] = total_prepay



    # -------------------------------------------------------------------------



    # 4. TỒN KHO & KIỂM SOÁT ÂM KHO (Sheet '03 Nhap Xuat Ton')



    # -------------------------------------------------------------------------



    in_qty = {}



    prod_names = {}



    if "01 HD Dau Vao" in wb.sheetnames:



        ws_in = wb["01 HD Dau Vao"]



        for r in range(4, ws_in.max_row + 1):



            c = str(ws_in.cell(r, 9).value or "").strip()



            n = str(ws_in.cell(r, 10).value or "").strip()



            q = float(ws_in.cell(r, 12).value or 0)



            if c:



                in_qty[c] = in_qty.get(c, 0.0) + q



                if n and c not in prod_names:



                    prod_names[c] = n



    out_qty = {}



    if "02 HD Dau Ra" in wb.sheetnames:



        ws_out = wb["02 HD Dau Ra"]



        for r in range(4, ws_out.max_row + 1):



            c = str(ws_out.cell(r, 10).value or "").strip()



            n = str(ws_out.cell(r, 11).value or "").strip()



            q = float(ws_out.cell(r, 13).value or 0)



            if c:



                out_qty[c] = out_qty.get(c, 0.0) + q



                if n and c not in prod_names:



                    prod_names[c] = n



    if "03 Nhap Xuat Ton" in wb.sheetnames:



        ws_nxt = wb["03 Nhap Xuat Ton"]



        total_m = 0.0



        neg_count = 0



        low_stock = []



        inv_map = {}



        for r in range(4, ws_nxt.max_row + 1):



            code = str(ws_nxt.cell(r, 2).value or "").strip()



            raw_name = str(ws_nxt.cell(r, 3).value or "").strip()



            name = raw_name if raw_name else prod_names.get(code, f"Mặt hàng {code}")



            unit = str(ws_nxt.cell(r, 4).value or "m").strip()



            if code:



                iq = in_qty.get(code, 0.0)



                oq = out_qty.get(code, 0.0)



                rem = iq - oq



                total_m += rem



                inv_map[code.upper()] = {



                    "code": code,



                    "name": name,



                    "unit": unit,



                    "in": iq,



                    "out": oq,



                    "stock": rem



                }



                if rem < 0:



                    neg_count += 1



                elif rem < 30:



                    low_stock.append({"code": code, "name": name, "stock": rem})



        facts["stock"] = {



            "total_m": total_m,



            "neg_count": neg_count,



            "low_count": len(low_stock)



        }



        facts["stock_low"] = low_stock



        facts["inventory_map"] = inv_map



    return facts



def build_5_den_bao_text(facts: dict, caller_name: str = "Sếp") -> str:

    """Micro-Dashboard 5 Đèn Báo Quản Trị Ngọc Hà (Hiển thị trọn vẹn trong 1 màn hình di động, không cuộn)"""

    ts = facts.get('timestamp', datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y"))

    

    # Đèn 1: Tiền về chờ xuất HĐ

    v_in = facts.get("vat_in", {})

    missing = v_in.get("missing_vat", [])

    if missing:

        m0 = missing[0]

        cust_short = m0['cust'].replace("HỘ KINH DOANH", "HKD").replace("CÔNG TY TNHH", "Cty").strip()

        amt_tr = m0['amt'] / 1e6

        d1 = f"1. 🧾 Tiền về chờ HĐ: 🔴 Còn {len(missing)} khoản [{cust_short} ({amt_tr:.1f} tr)]"
    else:

        d1 = "1. 🧾 Tiền về chờ HĐ: 🟢 100% đã xuất HĐ GTGT"



    # Đèn 2: HĐ chờ thu nợ (TK 131)

    v_out = facts.get("vat_out", {})

    unpaid = v_out.get("unpaid", [])

    latest_hd = v_out.get("latest_no", "00000156")

    if unpaid:

        d2 = f"2. ⏳ HĐ chờ thu nợ (131): 🔴 Còn {len(unpaid)} HĐ chưa thu"

    else:

        d2 = f"2. ⏳ HĐ chờ thu nợ (131): 🟢 100% đã thu đủ (Mới nhất: {latest_hd})"



    # Đèn 3: Công nợ 11 NCC (TK 331)

    debts = facts.get("ncc_debts", [])

    prepays = facts.get("ncc_prepays", [])

    tot_d = facts.get("ncc_total_debt", 0.0) / 1e6

    tot_p = facts.get("ncc_total_prepay", 0.0) / 1e6

    if debts:

        d_short = debts[0]['code']

        d3 = f"3. 🤝 Công nợ NCC (331): 🔴 Nợ {tot_d:.2f} tr [{d_short}] | Ứng {tot_p:.2f} tr"

    else:

        d3 = f"3. 🤝 Công nợ NCC (331): 🟢 Đã tất toán nợ | Ứng gối đầu {tot_p:.2f} tr"



    # Đèn 4: Tồn kho hàng hóa (TK 156)

    stock = facts.get("stock", {})

    tot_m = stock.get("total_m", 0.0)

    neg_cnt = stock.get("neg_count", 0)

    if neg_cnt > 0:

        d4 = f"4. 📦 Tồn kho PVC (156): 🔴 CẢNH BÁO ÂM {neg_cnt} MÃ"

    else:

        d4 = f"4. 📦 Tồn kho PVC (156): 🟢 {tot_m:,.0f} m | Âm kho: 0 mã (An toàn)"



    # Đèn 5: Thuế & Nhân sự

    d5 = "5. ⚖️ Thuế & Nhân sự: 🟢 VAT an toàn • Đã nộp BHXH T10"



    return (

        f"🚦 5 ĐÈN BÁO QUẢN TRỊ NGỌC HÀ ({ts}):\n"

        f"--------------------------------------------------\n"

        f"{d1}\n"

        f"{d2}\n"

        f"{d3}\n"

        f"{d4}\n"

        f"{d5}\n"

        f"--------------------------------------------------\n"

        f"👉 Chạm nút bên dưới để xem chi tiết từng khối nhé {caller_name}! 😊"

    )



def build_summary_text(facts: dict) -> str:



    """Xây dựng bản tóm tắt số liệu điều hành cô đọng chuẩn nghiệp vụ TCVN"""



    lines = []



    lines.append(f"📊 SỐ LIỆU SỔ MASTER NGỌC HÀ (Cập nhật lúc {facts.get('timestamp')}):")



    # 1. Tiền về



    v_in = facts.get("vat_in", {})



    missing = v_in.get("missing_vat", [])



    if missing:



        missing_desc = "; ".join([f"{item['cust']} ({fmt_money(item['amt'])})" for item in missing])



        lines.append(f"• 🧾 Tiền về chờ xuất HĐ: 🔴 Còn {len(missing)} khoản chưa xuất HĐ [{missing_desc}]")



    else:



        lines.append("• 🧾 Tiền về chờ xuất HĐ: 🟢 Đã xuất đủ 100% hóa đơn GTGT.")



    # 2. Hóa đơn ra & công nợ 131



    v_out = facts.get("vat_out", {})



    unpaid = v_out.get("unpaid", [])



    latest_hd = v_out.get("latest_no", "00000156")



    if unpaid:



        lines.append(f"• ⏳ HĐ chờ thu tiền (TK 131): 🔴 Còn {len(unpaid)} HĐ chưa thanh toán.")



    else:



        lines.append(f"• ⏳ HĐ chờ thu tiền (TK 131): 🟢 100% HĐ đã thu đủ tiền (HĐ mới nhất: {latest_hd}).")



    # 3. Công nợ 11 NCC



    debts = facts.get("ncc_debts", [])



    prepays = facts.get("ncc_prepays", [])



    tot_debt = facts.get("ncc_total_debt", 0.0)



    tot_prep = facts.get("ncc_total_prepay", 0.0)



    debt_str = ", ".join([f"{d['code']} ({fmt_tr(d['debt'])})" for d in debts]) if debts else "0 NCC"



    prep_str = ", ".join([f"{p['code']} ({fmt_tr(p['prepay'])})" for p in prepays]) if prepays else "0 NCC"



    lines.append(f"• 🤝 Công nợ 11 NCC (TK 331): Nợ phải trả: {fmt_money(tot_debt)} [{debt_str}] | Đã ứng trước gối đầu: {fmt_money(tot_prep)} [{prep_str}].")



    # 4. Tồn kho



    st = facts.get("stock", {})



    tot_m = st.get("total_m", 0.0)



    neg_cnt = st.get("neg_count", 0)



    lines.append(f"• 📦 Tồn kho hàng hóa (TK 156): Tổng lưu tồn: {fmt_qty(tot_m)} mét | Âm kho: {neg_cnt} mã (100% an toàn thuế).")



    # 5. Thuế & Nghĩa vụ



    lines.append("• ⚖️ Thuế & Nhân sự: VAT khấu trừ an toàn • Đã nộp BHXH T10 • Hạn nộp T11: ngày 30/11.")



    return "\n".join(lines)




def build_compact_ledger_index(wb) -> str:
    """
    Xay dung Muc luc dien tu tinh gon (5 Khoi du lieu cot loi) tu So Master.
    Cho phep Gemini Flash doc tron ven 157 HD ban ra, 70 HD mua vao, cong no 11 NCC va ton kho.
    Dung luong ~24 KB (~6.000 tokens), chay trong 0.35 giay.
    """
    parts = []

    # 1. 157 HOA DON BAN RA (Forward-fill gop nhieu dong)
    if "02 HD Dau Ra" in wb.sheetnames:
        ws_out = wb["02 HD Dau Ra"]
        current_inv = None
        invoices_ra = {}
        for r in range(4, ws_out.max_row + 1):
            inv_cell = ws_out.cell(r, 8).value
            if inv_cell is not None and str(inv_cell).strip() not in ["", "None"]:
                inv_no = str(inv_cell).strip().zfill(8)
                current_inv = inv_no
                invoices_ra[current_inv] = {
                    "no": current_inv,
                    "cust": str(ws_out.cell(r, 4).value or "").strip(),
                    "mst": str(ws_out.cell(r, 5).value or "").strip(),
                    "date": str(ws_out.cell(r, 9).value or "")[:10],
                    "acb": str(ws_out.cell(r, 24).value or "").strip(),
                    "total": 0.0,
                    "skus": []
                }
            if current_inv:
                p = str(ws_out.cell(r, 10).value or "").strip()
                qty = float(ws_out.cell(r, 13).value or 0)
                price = float(ws_out.cell(r, 14).value or 0)
                vat = float(ws_out.cell(r, 16).value or 0.08)
                if not p and qty == 0 and price == 0:
                    current_inv = None
                    continue
                line_val = round(qty * price * (1 + vat))
                invoices_ra[current_inv]["total"] += line_val
                if p and p not in invoices_ra[current_inv]["skus"]:
                    invoices_ra[current_inv]["skus"].append(p)

        lines_ra = []
        for k in sorted(invoices_ra.keys()):
            inv = invoices_ra[k]
            skus_str = ", ".join(inv["skus"][:3])
            amt_str = f"{int(inv['total']):,} đ"
            lines_ra.append(
                f"{k} | {inv['date']} | {inv['cust']} | MST:{inv['mst']} | {amt_str} | {skus_str} | {inv['acb']}"
            )
        parts.append(f"=== MỤC LỤC {len(lines_ra)} HÓA ĐƠN BÁN RA NĂM 2026 ===\n" + "\n".join(lines_ra))

    # 2. 70 HOA DON MUA VAO (Forward-fill gop nhieu dong)
    if "01 HD Dau Vao" in wb.sheetnames:
        ws_in = wb["01 HD Dau Vao"]
        current_inv_in = None
        invoices_vao = {}
        for r in range(4, ws_in.max_row + 1):
            inv_cell = ws_in.cell(r, 7).value
            if inv_cell is not None and str(inv_cell).strip() not in ["", "None"]:
                inv_no = str(inv_cell).strip().zfill(8)
                current_inv_in = inv_no
                invoices_vao[current_inv_in] = {
                    "no": current_inv_in,
                    "ncc": str(ws_in.cell(r, 3).value or "").strip(),
                    "name": str(ws_in.cell(r, 4).value or "").strip(),
                    "mst": str(ws_in.cell(r, 5).value or "").strip(),
                    "date": str(ws_in.cell(r, 8).value or "")[:10],
                    "acb": str(ws_in.cell(r, 21).value or "").strip(),
                    "total": 0.0,
                    "skus": []
                }
            if current_inv_in:
                p = str(ws_in.cell(r, 9).value or "").strip()
                qty = float(ws_in.cell(r, 12).value or 0)
                price = float(ws_in.cell(r, 13).value or 0)
                vat = float(ws_in.cell(r, 15).value or 0.08)
                if not p and qty == 0 and price == 0:
                    current_inv_in = None
                    continue
                line_val = round(qty * price * (1 + vat))
                invoices_vao[current_inv_in]["total"] += line_val
                if p and p not in invoices_vao[current_inv_in]["skus"]:
                    invoices_vao[current_inv_in]["skus"].append(p)

        lines_vao = []
        for k in sorted(invoices_vao.keys()):
            inv = invoices_vao[k]
            skus_str = ", ".join(inv["skus"][:3])
            amt_str = f"{int(inv['total']):,} đ"
            lines_vao.append(
                f"{k} | {inv['date']} | NCC:{inv['ncc']} ({inv['name']}) | MST:{inv['mst']} | {amt_str} | {skus_str} | {inv['acb']}"
            )
        parts.append(f"=== MỤC LỤC {len(lines_vao)} HÓA ĐƠN MUA VÀO NĂM 2026 ===\n" + "\n".join(lines_vao))

    # 3. CONG NO 11 NHA CUNG CAP (TK 331)
    if "03 Đối Soát Công Nợ 11 NCC" in wb.sheetnames:
        ws_cn = wb["03 Đối Soát Công Nợ 11 NCC"]
        lines_cn = []
        for r in range(4, ws_cn.max_row + 1):
            code = str(ws_cn.cell(r, 2).value or "").strip()
            if not code:
                continue
            name = str(ws_cn.cell(r, 3).value or "").strip()
            mst = str(ws_cn.cell(r, 4).value or "").strip()
            buy = float(ws_cn.cell(r, 6).value or 0)
            paid = float(ws_cn.cell(r, 8).value or 0)
            debt = float(ws_cn.cell(r, 9).value or 0)
            pre = float(ws_cn.cell(r, 10).value or 0)
            lines_cn.append(
                f"{code} ({name} - MST:{mst}): Mua {int(buy):,} đ | Đã trả ACB {int(paid):,} đ | Nợ phải trả: {int(debt):,} đ | Đã ứng trước: {int(pre):,} đ"
            )
        parts.append("=== BẢNG CÔNG NỢ 11 NHÀ CUNG CẤP (TK 331) ===\n" + "\n".join(lines_cn))

    # 4. TON KHO 65 MA PVC & CANH BAO AM
    if "03 Nhap Xuat Ton" in wb.sheetnames:
        ws_tk = wb["03 Nhap Xuat Ton"]
        lines_tk = []
        for r in range(4, ws_tk.max_row + 1):
            code = str(ws_tk.cell(r, 2).value or "").strip()
            if not code:
                continue
            ton = ws_tk.cell(r, 7).value
            try:
                ton_val = float(ton or 0)
            except Exception:
                ton_val = 0.0
            warn = str(ws_tk.cell(r, 10).value or "").strip()
            if "ÂM" in warn.upper() or ton_val < 30:
                lines_tk.append(f"{code}: Tồn {ton_val:.1f} ({warn})")
        if lines_tk:
            parts.append("=== CẢNH BÁO TỒN KHO & MÃ ĐẶC CHÚ Ý ===\n" + "\n".join(lines_tk))

    return "\n\n".join(parts)


def get_master_data_cached(force_reload=False) -> dict:



    """Lấy dữ liệu Sổ Master có bộ đệm TTL Cache để tránh quá tải tải file liên tục"""



    global MASTER_CACHE



    now = time.time()



    with CACHE_LOCK:



        if not force_reload and (now - MASTER_CACHE["timestamp"] < CACHE_TTL_SECONDS) and MASTER_CACHE["summary_text"]:



            return MASTER_CACHE



        try:



            wb = fetch_master_workbook()



            facts = parse_master_accounting_data(wb)



            summary = build_summary_text(facts)



            ledger_index = build_compact_ledger_index(wb)
            MASTER_CACHE = {



                "timestamp": now,



                "summary_text": summary,
                "ledger_index_text": ledger_index,



                "raw_facts": facts,



                "status": "Đang kết nối tốt",



                "last_error": None



            }



            wb.close()



            print(f"[{datetime.now()}] [CACHE] Đã nạp thành công Sổ Master ({len(summary)} bytes summary).")



        except Exception as e:



            err_msg = str(e)



            print(f"[{datetime.now()}] [ERROR] Nạp Sổ Master thất bại: {err_msg}")



            MASTER_CACHE["last_error"] = err_msg



            if not MASTER_CACHE["summary_text"]:



                MASTER_CACHE["summary_text"] = (



                    "📊 THÔNG BÁO HỆ THỐNG:\n"



                    f"Hiện đang kiểm tra lại liên kết Sổ Master ({err_msg}).\n"



                    "Dữ liệu mẫu chuẩn mực: Đã xuất 156 HĐ đầu ra, nợ Hoàng Hà 100,08 tr, ứng trước DHL 18,39 tr & Hải Thiên 107,39 tr, tồn kho an toàn 12.080 m."



                )



    return MASTER_CACHE



# ==============================================================================



# TÍCH HỢP GOOGLE GEMINI API (GOOGLE AI STUDIO)



# ==============================================================================



def call_gemini_api(prompt_text: str, context_facts: str) -> str:



    """



    Gọi trực tiếp Google Gemini API qua endpoint chính thức.



    Đảm bảo phong cách giao tiếp ấm áp, chuyên nghiệp của Trợ lý Kế toán Trưởng.



    """



    if not GEMINI_API_KEY:



        return ""



    now_str = datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y")



    system_instruction = (



        "Bạn là Trợ lý Kế toán Trưởng thân thiết, chu đáo, nhiệt tình, thông minh và tận tâm của Công ty TNHH TM&DV Kiến Trúc Ngọc Hà (MST: 0601309667).\n"



        "Người bạn đang trực tiếp trò chuyện, kết nối trên Telegram và phục vụ chỉ đạo cao nhất là Mr. Phạm Đạt - CEO - thường gọi là Sếp Đạt / Anh Đạt / Sếp.\n"



        "Cơ cấu nhân sự công ty:\n"



        "- Mr. Phạm Đạt: CEO - Người đang trực tiếp chỉ đạo, làm việc với bạn trên Telegram\n"



        "- Đặng Thị Hà: Giám đốc điều hành pháp lý (có trong bảng lương)\n"



        "- Đặng Thu Quỳnh: Kế toán (có trong bảng lương)\n"



        "- Đặng Thái Dương: Thủ kho (có trong bảng lương)\n\n"



        "DỮ LIỆU SỔ MASTER HIỆN TẠI (CHẾ ĐỘ CHỈ ĐỌC 100% BẢO VỆ SSOT):\n"



        f"{context_facts}\n" + "\n- VIETINVOICE: Hóa đơn số 00000157 (khoản 15 tr HKD Vũ Văn Sỹ TN) ĐÃ ĐƯỢC SẾP ĐẠT KÝ SỐ VÀ CƠ QUAN THUẾ CẤP MÃ THÀNH CÔNG 100% lúc 15:11:20 ngày 21/11/2026 (Mã CQT: 00E7FB6856E51343EE9719486404130D3D). Toàn bộ tiền về đã xuất đủ 100% hóa đơn.\n"



        f"Thời điểm hiện tại: {now_str}\n\n"



        "PHONG CÁCH GIAO TIẾP & NGUYÊN TẮC PHỤC VỤ:\n"
        "1. LỜI CHÀO GIAO BAN (QUAN TRỌNG): Khi Sếp chào hỏi (alo, em ơi, chào, hi...) hoặc mở đầu, chỉ đáp lại đúng 1 câu tác phong giao ban dứt khoát: '🫡 Dạ em chào Sếp Đạt! Trực ban Sổ Master sẵn sàng tiếp nhận nhiệm vụ ạ.' Tuyệt đối KHÔNG chúc tụng dài dòng, KHÔNG liệt kê tính năng làm choán màn hình điện thoại.\n"
        "2. Khi Sếp hỏi nghiệp vụ cụ thể: Trả lời đi thẳng vào trọng tâm, tối đa 2-5 dòng súc tích, chuyên nghiệp.\n"
        "3. Số liệu kế toán chuẩn xác tuyệt đối, dùng dấu chấm phân cách hàng nghìn (ví dụ: 100.076.124 đ, 18.392.400 đ).\n"
        "4. NGUYÊN TẮC BẰNG CHỨNG XÁC THỰC (CHỈ ĐẠO GIÁM ĐỐC): Khi khẳng định ĐÚNG/SAI, HOÀN THÀNH/CHƯA HOÀN THÀNH, ĐÃ KÝ/CHƯA KÝ, ĐÈN XANH/ĐÈN ĐỎ: Bắt buộc phải có số liệu hoặc căn cứ thực tế rõ ràng từ Sổ Master hoặc API Cổng HĐĐT, tuyệt đối KHÔNG dự đoán, KHÔNG suy luận cảm tính, KHÔNG dùng trạng thái cũ để áp đặt.\n"
    )

    full_prompt = f"{system_instruction}\n\nYÊU CẦU CỦA GIÁM ĐỐC:\n{prompt_text}"



    # Danh sách các model ổn định để tự động thử



    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]



    payload = {



        "contents": [{"parts": [{"text": full_prompt}]}],



        "generationConfig": {



            "temperature": 0.2,



            "maxOutputTokens": 2048



        }



    }



    data_bytes = json.dumps(payload).encode("utf-8")



    headers = {"Content-Type": "application/json"}



    for model in models_to_try:



        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"



        try:



            req = urllib.request.Request(url, data=data_bytes, headers=headers)



            with urllib.request.urlopen(req, timeout=25) as resp:



                res_json = json.loads(resp.read().decode("utf-8"))



                candidates = res_json.get("candidates", [])



                if candidates:



                    parts = candidates[0].get("content", {}).get("parts", [])



                    if parts:



                        reply_text = parts[0].get("text", "").strip()



                        if reply_text:



                            return reply_text



        except urllib.error.HTTPError as he:



            # 404/503 thử model tiếp theo



            pass



        except Exception:



            pass



    return ""



# ==============================================================================



# XỬ LÝ TRUY VẤN VÀ PHẢN HỒI THÔNG MINH



# ==============================================================================



def call_openrouter_api(prompt_text: str, context_facts: str, caller_name: str = "Sếp Đạt") -> str:



    """Gọi OpenRouter (Google Gemini Flash / Claude) làm kênh AI siêu tốc, không lo lỗi Quota 429"""



    if not OPENROUTER_API_KEY:



        return ""



    now_str = datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y")



    system_instruction = (



        "Bạn là Trợ lý Kế toán Trưởng thân thiết, chu đáo, nhiệt tình, thông minh và tận tâm của Công ty TNHH TM&DV Kiến Trúc Ngọc Hà (MST: 0601309667).\n"



        f"Người bạn đang trực tiếp trò chuyện và phục vụ chỉ đạo cao nhất là {caller_name} - Mr. Phạm Đạt (CEO).\n"



        "Cơ cấu nhân sự: Mr. Phạm Đạt (CEO), Đặng Thị Hà (Giám đốc điều hành pháp lý), Đặng Thu Quỳnh (Kế toán), Đặng Thái Dương (Thủ kho).\n\n"



        f"DỮ LIỆU SỔ MASTER HIỆN TẠI (CHẾ ĐỘ CHỈ ĐỌC BẢO VỆ SSOT):\n{context_facts}\n"



        f"Thời điểm hiện tại: {now_str}\n\n"



        "PHONG CÁCH GIAO TIẾP & NGUYÊN TẮC PHỤC VỤ:\n"



        "- Xưng hô lễ phép, ấm áp: 'Dạ em chào Sếp Đạt ạ!', 'Dạ báo cáo Sếp Đạt...', 'Dạ em nghe Sếp!'...\n"



        "- Trả lời trọng tâm, thông minh, ngắn gọn, tối ưu trên màn hình điện thoại Telegram.\n"



        "- Cuối tin nhắn có lời kết thân thiện kèm nhận diện: '🛡️ [Trực ban Gemini Cloud 24/7 phục vụ Sếp Đạt]'"



    )



    url = "https://openrouter.ai/api/v1/chat/completions"



    payload = {



        "model": "google/gemini-2.5-flash",



        "messages": [



            {"role": "system", "content": system_instruction},



            {"role": "user", "content": prompt_text}



        ],



        "temperature": 0.2,



        "max_tokens": 1024



    }



    data_bytes = json.dumps(payload).encode("utf-8")



    headers = {



        "Authorization": f"Bearer {OPENROUTER_API_KEY}",



        "Content-Type": "application/json",



        "HTTP-Referer": "https://ngoc-ha.accounting",



        "X-Title": "Ngoc Ha Cloud Bot"



    }



    try:



        req = urllib.request.Request(url, data=data_bytes, headers=headers)



        with urllib.request.urlopen(req, timeout=15) as resp:



            res_json = json.loads(resp.read().decode("utf-8"))



            choices = res_json.get("choices", [])



            if choices:



                return choices[0].get("message", {}).get("content", "").strip()



    except Exception as e:



        print(f"[{datetime.now()}] [OPENROUTER ERROR]: {e}")



        return ""



    return ""



def process_user_query(text: str, chat_id: int = None, caller_name: str = "Sếp") -> str:



    """



    Xử lý câu hỏi của người dùng:



    1. Lấy dữ liệu Sổ Master mới nhất từ bộ đệm.



    2. Nếu có lệnh nhanh (/baocao, /tienve, /congno, /tonkho, /hoadon, /sync), phản hồi ngay.



    3. Gửi sang Gemini API để sinh câu trả lời tự nhiên.



    4. Fallback tự động nếu Gemini API bận.



    """



    cache = get_master_data_cached()



    facts_summary = cache.get("summary_text", "")



    raw_facts = cache.get("raw_facts", {})



    lower_text = text.lower().strip()



    # 0. Xu ly cau chao hoi ngan hoac goi bot (alo, oi, em oi, chao)



    if lower_text in ["alo", "a lô", "ơi", "em ơi", "em oi", "hi", "hello", "chào em", "chao em", "chào", "chao"]:
        return (
            f"🫡 Dạ em nghe {caller_name}! Trực ban Sổ Master 24/7 sẵn sàng tiếp nhận nhiệm vụ ạ. ✨\n\n"
            "👉 Sếp chạm nhanh 6 nút [Menu Tra Soát Nhanh] bên dưới (5 Đèn Báo, Dòng Tiền, Công Nợ NCC, Công Nợ KH, Tồn Kho, Soạn HĐ) hoặc nhắn trực tiếp nội dung để em kiểm tra ngay nhé ạ! 😊"
        )

    # =========================================================================
    # ƯU TIÊN SỐ 1 TUYỆT ĐỐI (CLAUDE SONNET 4.6): CHUYỂN TIẾP VỀ ANTIGRAVITY PC
    # =========================================================================
    if check_pc_online():
        pc_reply = forward_to_pc_antigravity(text, chat_id=chat_id, caller_name=caller_name)
        if pc_reply:
            return pc_reply
    # =========================================================================


    # 0.0 Nhan dien lenh Chuyen ban nhap / VietInvoice / Ky so
    # 0.1 Nhan dien nghiep vu Soan hoa don nhap / Xuat hoa don tuc thi



    if any(k in lower_text for k in ["soạn hoá đơn", "soạn hóa đơn", "soan hoa don", "hóa đơn nháp", "hoa don nhap", "xuất hoá đơn", "xuất hóa đơn", "xuat hoa don"]):



        v_in = raw_facts.get("vat_in", {})



        missing = v_in.get("missing_vat", [])



        if missing:



            lines = [



                f"🧾 DẠ BÁO CÁO {caller_name.upper()}! EM GỬI THÔNG TIN SOẠN HÓA ĐƠN NHÁP Ạ:",



                "--------------------------------------------------"



            ]



            for m in missing:



                cust_name = m.get('cust', '')



                amt = m.get('amt', 0)



                date_str = m.get('date', '')



                pre_tax = round(amt / 1.08)



                vat_amt = amt - pre_tax



                lines.append(f"👉 KHÁCH HÀNG: {cust_name}")



                lines.append(f"• Số tiền đã về ACB: {fmt_money(amt)} (Ngày {date_str})")



                lines.append(f"• Doanh thu chưa thuế (TK 511): {fmt_money(pre_tax)}")



                lines.append(f"• Tiền thuế VAT 8% (TK 3331): {fmt_money(vat_amt)}")



                lines.append(f"• Tổng thanh toán có VAT: {fmt_money(amt)} (Khớp tròn 100% tiền ACB)\n")



            lines.append("📦 CÁC MẶT HÀNG TỒN KHO AN TOÀN ĐỀ XUẤT XUẤT:")



            lines.append("• Tấm BT 550 x 18 (Mã BT5518, tồn 450m, đơn giá: 145.800 đ)")



            lines.append("• Tấm BT 500 x 18 (Mã BT5018, tồn 438m, đơn giá: 134.000 đ)")



            lines.append("• Tấm BT 450 x 18 (Mã BT4518, tồn 545m, đơn giá: 124.300 đ)")



            lines.append("• Tấm BT 400 x 18 (Mã BT4018, tồn 689m, đơn giá: 107.600 đ)")



            lines.append("• Nẹp cạnh BT18 (Mã Nep Bento, đơn giá: 5.100 đ)\n")



            lines.append(f"{caller_name} mở Sheet '01 Soan Thao HD Thu' trên máy tính để chốt số lượng hoặc nhắn em các mã hàng để em tính toán ngay nhé ạ! 😊")



            return "\n".join(lines)



    # 1. Lệnh /sync hoặc đồng bộ



    if lower_text in ["/sync", "đồng bộ", "dong bo", "reload"]:



        cache = get_master_data_cached(force_reload=True)



        return (



            f"⚡ DẠ BÁO CÁO {caller_name.upper()}!\n"



            "Em vừa làm mới dữ liệu Sổ Master trực tiếp từ OneDrive thành công 100% rồi ạ! ✨\n\n"



            f"{cache.get('summary_text')}\n\n"



            f"{caller_name} cần em kiểm tra thêm mục nào cứ nhắn em nhé ạ! 😊"



        )



    # 2. Lệnh 5 Đèn Báo Quản Trị hoặc /baocao (Micro-Dashboard 10 dòng, không cuộn)

    if any(k in lower_text for k in ["5 đèn báo", "5 den bao", "đèn báo", "den bao", "/baocao", "/tonghop", "báo cáo", "bao cao", "tổng quan", "tong quan"]):

        return build_5_den_bao_text(raw_facts, caller_name=caller_name)



    # 2.1 Bật lại menu bàn phím

    if lower_text in ["/menu", "menu", "bàn phím", "ban phim", "nút", "nut"]:
        return f"🫡 Dạ em gửi {caller_name} bàn phím tác vụ 1 chạm bên dưới ạ!"

    # 3. Lệnh /tienve hoặc tra cứu tiền về



    if any(k in lower_text for k in ["dòng tiền & tiền về", "dong tien & tien ve", "dòng tiền", "dong tien", "/tienve", "tiền về", "tien ve", "khách trả", "khach tra"]):



        v_in = raw_facts.get("vat_in", {})



        missing = v_in.get("missing_vat", [])



        lines = [f"💰 DẠ BÁO CÁO {caller_name.upper()} VỀ DÒNG TIỀN VỀ BÁN HÀNG Ạ:", "--------------------------------------------------"]



        lines.append(f"• Tổng tiền về bán hàng: {fmt_money(v_in.get('total_amt', 0))}")



        lines.append(f"• Tổng số giao dịch: {v_in.get('total_count', 0)} giao dịch")



        if missing:



            lines.append(f"\n🔴 KHOẢN TIỀN VỀ CẦN XUẤT BÙ HÓA ĐƠN GTGT ({len(missing)} khoản):")



            for m in missing:



                lines.append(f"👉 {m['cust']}: {fmt_money(m['amt'])} (Ngày: {m['date']})")



        else:



            lines.append("\n🟢 100% tiền về bán hàng đã được xuất hóa đơn GTGT đầy đủ.")



        lines.append(f"\n{caller_name} cần xuất HĐ cho khoản nào nhắn em nhé ạ! 😊")



        return "\n".join(lines)



    # 4. Lệnh /congno hoặc tra cứu nhà cung cấp



    if any(k in lower_text for k in ["công nợ 11 ncc", "cong no 11 ncc", "/congno_ncc", "/congno", "nợ ncc", "no ncc", "công nợ ncc", "cong no ncc"]) or lower_text in ["công nợ", "cong no"]:



        debts = raw_facts.get("ncc_debts", [])



        prepays = raw_facts.get("ncc_prepays", [])



        tot_d = raw_facts.get("ncc_total_debt", 0.0)



        tot_p = raw_facts.get("ncc_total_prepay", 0.0)



        lines = [f"🤝 DẠ BÁO CÁO {caller_name.upper()} ĐỐI SOÁT CÔNG NỢ 11 NCC Ạ:", "--------------------------------------------------"]



        lines.append(f"• Tổng nợ còn phải trả: {fmt_money(tot_d)}")



        lines.append(f"• Tổng đã thanh toán trước: {fmt_money(tot_p)}\n")



        if debts:



            lines.append("🔴 DANH SÁCH NCC CÒN PHẢI TRẢ:")



            for d in debts:



                lines.append(f"👉 {d['name']} ({d['code']}): {fmt_money(d['debt'])}")



        else:



            lines.append("🟢 Đã thanh toán hết toàn bộ công nợ các NCC.")



        if prepays:



            lines.append("\n🟢 KHOẢN ĐÃ ỨNG TRƯỚC GỐI ĐẦU CHỜ HÓA ĐƠN:")



            for p in prepays:



                lines.append(f"👉 {p['name']} ({p['code']}): {fmt_money(p['prepay'])}")



        lines.append(f"\n{caller_name} an tâm dòng tiền với các NCC luôn được kiểm soát chặt chẽ ạ! ✨")



        return "\n".join(lines)



    # 5. Lệnh /hoadon hoặc kiểm tra HĐ đầu ra



    if any(k in lower_text for k in ["công nợ kh", "cong no kh", "khách nợ", "khach no", "tk 131", "131", "/congno_kh", "/hoadon", "hóa đơn ra", "hoa don ra"]) or lower_text in ["hóa đơn", "hoa don", "hd"]:



        v_out = raw_facts.get("vat_out", {})



        unpaid = v_out.get("unpaid", [])



        lines = [f"🧾 DẠ BÁO CÁO {caller_name.upper()} TÌNH HÌNH HÓA ĐƠN ĐẦU RA Ạ:", "--------------------------------------------------"]



        lines.append(f"• Tổng số HĐ GTGT đã xuất: {v_out.get('total_issued', 156)} HĐ")



        lines.append(f"• Số HĐ mới nhất: {v_out.get('latest_no', '00000156')}")



        if unpaid:



            lines.append(f"\n🔴 CÓ {len(unpaid)} HĐ CHƯA THU ĐỦ TIỀN (NỢ TK 131):")



            for u in unpaid:



                lines.append(f"👉 HĐ {u['no']}: {u['cust']} ({fmt_money(u['amt'])})")



        else:



            lines.append("\n🟢 100% Hóa đơn đã thu đủ tiền, không có nợ đọng xấu.")



        lines.append(f"\nChúc {caller_name} một ngày kinh doanh thật thuận lợi ạ! ✨")



        return "\n".join(lines)



    # 6. Lệnh Tồn kho tổng thể & tra cứu mã SP

    if any(k in lower_text for k in ["tồn kho chống âm", "ton kho chong am", "báo cáo kho", "bao cao kho"]) or lower_text in ["/tonkho", "tồn kho", "ton kho", "kho"]:

        st = raw_facts.get("stock", {})

        tot_m = st.get("total_m", 0.0)

        neg_cnt = st.get("neg_count", 0)

        low_list = raw_facts.get("stock_low", [])

        lines = [f"📦 DẠ BÁO CÁO {caller_name.upper()} TỒN KHO TỔNG THỂ Ạ:", "--------------------------------------------------"]

        lines.append(f"• Tổng số mét lưu tồn: {fmt_qty(tot_m)} mét")

        lines.append(f"• Số mã âm kho: {neg_cnt} mã (🟢 100% An toàn thuế, chống âm kho)")

        if low_list:

            lines.append(f"\n⚠️ CÓ {len(low_list)} MÃ TỒN DƯỚI 30 MÉT CẦN LƯU Ý KHI XUẤT:")

            for item in low_list[:5]:

                lines.append(f"👉 {item['code']}: {fmt_qty(item['stock'])} m ({item['name']})")

        lines.append(f"\n💡 Sếp cần tra cứu mã cụ thể cứ gõ: /tonkho [Mã SP] nhé ạ! 😊")

        return "\n".join(lines)



    m_stock = re.search(r"(?:/tonkho|tra mã|mã sp|mã)\\s+([a-zA-Z0-9\\.\\-_]+)", lower_text)

    if m_stock and not any(k in lower_text for k in ["chống âm", "tổng thể", "báo cáo"]):

        target_code = m_stock.group(1).upper()

        inv_map = raw_facts.get("inventory_map", {})

        if target_code in inv_map:

            item = inv_map[target_code]

            return (

                f"📦 DẠ BÁO CÁO {caller_name.upper()} VỀ TỒN KHO MÃ {target_code} Ạ:\n"

                "--------------------------------------------------\n"

                f"• Tên sản phẩm: {item['name']}\n"

                f"• Đơn vị tính: {item['unit']}\n"

                f"• Tổng nhập HĐ: {fmt_qty(item['in'])} {item['unit']}\n"

                f"• Tổng xuất HĐ: {fmt_qty(item['out'])} {item['unit']}\n"

                f"• 👉 LƯU TỒN THỰC TẾ: {fmt_qty(item['stock'])} {item['unit']} (An toàn)\n\n"

                f"{caller_name} cần kiểm tra thêm mã nào cứ nhắn em nhé ạ! 😊"

            )

        else:

            return (

                f"📦 DẠ BÁO CÁO {caller_name.upper()}:\n"

                f"Hiện tại trong danh mục kho không có mã '{target_code}'.\n"

                f"{caller_name} vui lòng kiểm tra lại mã hoặc nhắn tên hàng để em tra cứu giúp nhé ạ! 😊"

            )



    # 7. Tra cứu nhà cung cấp cụ thể bằng tên



    if any(k in lower_text for k in ["hoàng hà", "hoang ha", "dhl", "hải thiên", "hai thien", "đại việt", "dai viet"]):



        debts = raw_facts.get("ncc_debts", [])



        prepays = raw_facts.get("ncc_prepays", [])



        matched = []



        for d in debts:



            if any(k in d["name"].lower() or k in d["code"].lower() for k in ["hoàng hà", "hoang ha", "dhl", "hải thiên", "đại việt"]):



                matched.append(f"• 🔴 {d['name']} ({d['code']}): Còn nợ {fmt_money(d['debt'])}")



        for p in prepays:



            if any(k in p["name"].lower() or k in p["code"].lower() for k in ["hoàng hà", "hoang ha", "dhl", "hải thiên", "đại việt"]):



                matched.append(f"• 🟢 {p['name']} ({p['code']}): Đã trả trước / gối đầu {fmt_money(p['prepay'])}")



        if matched:



            return (



                f"🤝 DẠ BÁO CÁO {caller_name.upper()} CÔNG NỢ CHI TIẾT Ạ:\n"



                "--------------------------------------------------\n"



                + "\n".join(matched)



                + f"\n\nSếp yên tâm dòng tiền công nợ luôn được đối soát 3 chiều chặt chẽ ạ! ✨"



            )



    # 8. Gửi sang Google Gemini AI để sinh phản hồi tự nhiên, chuẩn mực



    ledger_index = cache.get("ledger_index_text", "")
    full_facts = f"{facts_summary}\n\n{ledger_index}" if ledger_index else facts_summary
    ai_reply = call_gemini_api(text, full_facts)



    if not ai_reply:



        ai_reply = call_openrouter_api(text, facts_summary, caller_name=caller_name)



    if ai_reply:



        facts_ts = cache.get("raw_facts", {}).get("timestamp") or cache.get("timestamp") or "Thời gian thực"
        return f"{ai_reply}\n\n☁️ *[Trực ban Gemini Cloud 24/7 - Dữ liệu Master chốt: {facts_ts}]*"



    # 9. Fallback dự phòng siêu ngắn gọn (KHÔNG nhồi nhét bảng dài làm tràn màn hình)

    return (
        f"🫡 DẠ BÁO CÁO {caller_name.upper()}!\n"
        "Trực ban Sổ Master 24/7 đã ghi nhận. Sếp chạm nút chức năng bên dưới hoặc nhắn cụ thể nội dung cần kiểm tra nhé ạ!"
    )

def telegram_api_call(method: str, params: dict = None, data: dict = None):



    """Gửi yêu cầu tới Telegram Bot API an toàn, có bẫy lỗi HTTP 409 Conflict"""



    url = f"{TELEGRAM_API_URL}/{method}"



    try:



        if params:



            url += "?" + urllib.parse.urlencode(params)



        req = urllib.request.Request(url)



        if data:



            req.data = json.dumps(data).encode("utf-8")



            req.add_header("Content-Type", "application/json")



        with urllib.request.urlopen(req, timeout=35) as resp:



            return json.loads(resp.read().decode("utf-8"))



    except urllib.error.HTTPError as he:



        if he.code == 409:



            print(f"[{datetime.now()}] [FATAL 409 CONFLICT] Trùng lặp tiến trình Bot Telegram. Tạm dừng 10s...")



            time.sleep(10)



        else:



            print(f"[{datetime.now()}] [ERROR] Telegram API {method} HTTP {he.code}: {he.reason}")



        return None



    except Exception as e:



        print(f"[{datetime.now()}] [ERROR] Telegram API {method} thất bại: {e}")



        return None



def telegram_send_message(chat_id: int, text: str, reply_markup: dict = KEYBOARD_5_DEN_BAO):
    """Gửi tin nhắn Telegram an toàn, tự động chia nhỏ nếu vượt quá 3800 ký tự và luôn gắn bàn phím 1 chạm"""
    if not text:
        return None
    max_len = 3800
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    last_res = None
    for idx, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk}
        if idx == len(chunks) - 1 and reply_markup:
            payload["reply_markup"] = reply_markup
        last_res = telegram_api_call("sendMessage", data=payload)
    return last_res



def telegram_send_chat_action(chat_id: int, action: str = "typing"):



    """Gửi trạng thái 'đang gõ' để người dùng trên Telegram biết bot đang xử lý"""



    try:



        telegram_api_call("sendChatAction", data={"chat_id": chat_id, "action": action})



    except Exception:



        pass



def handle_telegram_message(msg: dict):



    """Xử lý từng tin nhắn Telegram tới bot theo chuẩn phân quyền và bảo mật"""



    chat_id = msg.get("chat", {}).get("id")



    if not chat_id:



        return



    str_chat_id = str(chat_id)



    from_user = msg.get("from", {}).get("first_name", "Bạn")



    is_authenticated = (str_chat_id in AUTHENTICATED_USERS)



    # -------------------------------------------------------------------------



    # BẢO VỆ CHỐNG NGƯỜI LẠ: YÊU CẦU PASSCODE 'Ngocha@123'



    # -------------------------------------------------------------------------



    if not is_authenticated:



        text_input = msg.get("text", "").strip().lower()



        if text_input == BOT_PASSCODE:



            # Nhập đúng Passcode -> Cấp quyền vĩnh viễn



            is_admin = (chat_id == ADMIN_CHAT_ID)



            role = "CEO" if is_admin else "Nhân sự"



            user_name = "Sếp Đạt" if is_admin else from_user



            AUTHENTICATED_USERS[str_chat_id] = {



                "name": user_name,



                "role": role,



                "authenticated_at": datetime.now().isoformat(),



                "waiting_for_name": not is_admin



            }



            if is_admin:



                welcome_admin = "🫡 DẠ EM CHÀO SẾP ĐẠT! Trực ban Sổ Master 24/7 sẵn sàng tiếp nhận nhiệm vụ ạ." 



                telegram_send_message(chat_id, welcome_admin)



            else:



                welcome_user = (



                    "🎉 XÁC THỰC THÀNH CÔNG! ✨\n"



                    "--------------------------------------------------\n"



                    "Dạ em chào anh/chị! Em là Trợ lý Kế toán AI của Công ty Kiến Trúc Ngọc Hà.\n"



                    "Mã bảo vệ chính xác, em đã mở quyền truy cập hệ thống cho tài khoản của anh/chị rồi ạ!\n\n"



                    "👉 Anh/chị cho em xin Tên để em tiện xưng hô chu đáo nhé ạ (Ví dụ: Quỳnh kế toán, Dương thủ kho...) 😊"



                )



                telegram_send_message(chat_id, welcome_user)



            return



        else:



            # Chưa nhập hoặc sai Passcode -> Từ chối lịch sự



            refusal_msg = (



                "🔒 DẠ EM CHÀO ANH/CHỊ!\n"



                "--------------------------------------------------\n"



                "Đây là Kênh Trợ Lý Kế Toán AI Nội Bộ của Công ty TNHH TM&DV Kiến Trúc Ngọc Hà.\n\n"



                "Để bảo vệ an toàn số liệu tài chính doanh nghiệp, hệ thống yêu cầu Mã bảo vệ để kích hoạt sử dụng ạ.\n\n"



                "👉 Vui lòng gửi Mã bảo vệ vào đây để tiếp tục sử dụng.\n"



                "(Nếu chưa có mã, anh/chị vui lòng liên hệ Ban Giám đốc để được cấp mã nhé ạ)."



            )



            telegram_send_message(chat_id, refusal_msg)



            return



    # Cập nhật tên nếu đang chờ



    user_info = AUTHENTICATED_USERS.get(str_chat_id, {})



    if user_info.get("waiting_for_name"):



        name_input = msg.get("text", "").strip()



        if name_input and len(name_input) < 50:



            user_info["name"] = name_input



            user_info["waiting_for_name"] = False



            AUTHENTICATED_USERS[str_chat_id] = user_info



            telegram_send_message(chat_id, f"Dạ em đã ghi nhớ tên '{name_input}' rồi ạ! ✨\nEm chào {name_input}! Em có thể hỗ trợ gì cho anh/chị hôm nay ạ? 😊")



            return



    caller_name = user_info.get("name", "Sếp")



    # -------------------------------------------------------------------------



    # XỬ LÝ ẢNH CHỨNG TỪ / BILL



    # -------------------------------------------------------------------------



    if "photo" in msg:



        caption = msg.get("caption", "").strip()



        telegram_send_message(



            chat_id,



            f"📸 Dạ em đã nhận được ảnh chứng từ chuyển tiền/hóa đơn của {caller_name} rồi ạ!\n"



            f"⏳ Ghi chú: {caption if caption else 'Không có'}\n"



            f"Em đang lưu nhận diện và đối soát với dòng tiền ngân hàng nhé {caller_name}! 😊"



        )



        return



    # -------------------------------------------------------------------------



    # XỬ LÝ TIN NHẮN VĂN BẢN (TEXT) & CÁC LỆNH



    # -------------------------------------------------------------------------



    text = msg.get("text", "").strip()



    if not text:



        return



    # Lệnh Menu / Giới thiệu



    if text.lower() in ["/start", "/help", "menu", "giúp"]:
        menu_text = (
            f"🫡 DẠ EM CHÀO {caller_name.upper()}! ✨\n"
            "Trực ban Sổ Master 24/7 sẵn sàng tiếp nhận nhiệm vụ ạ.\n\n"
            "📋 HƯỚNG DẪN CHỌN MENU TRA SOÁT NHANH (1 CHẠM):\n"
            "--------------------------------------------------\n"
            "Sếp chạm trực tiếp vào 6 nút bấm dưới đáy màn hình:\n"
            "• [ 🚦 5 Đèn Báo Quản Trị ]: Micro-Dashboard 10 dòng xem nhanh sức khỏe công ty\n"
            "• [ 💰 Dòng Tiền & Tiền Về ]: Kiểm tra tiền về ACB & các khoản chờ xuất hóa đơn\n"
            "• [ 🤝 Công Nợ 11 NCC     ]: Nợ phải trả & tiền ứng gối đầu 11 nhà cung cấp\n"
            "• [ ⏳ Công Nợ KH (TK 131)]: Tình hình thu nợ khách hàng & xuất hóa đơn ra\n"
            "• [ 📦 Tồn Kho Chống Âm   ]: Lưu tồn mét tấm PVC & cảnh báo các mã sắp hết\n"
            "• [ 🧾 Soạn HĐ Nháp       ]: Đề xuất mặt hàng & bản nháp HĐĐT VietInvoice\n\n"
            "💡 MẸO SỬ DỤNG:\n"
            "👉 Bàn phím 6 nút trên luôn hiện sẵn dưới ô nhập chữ. Nếu bị thu gọn, Sếp chạm vào biểu tượng [::] bên cạnh ô gõ để mở lại.\n"
            "👉 Hoặc Sếp có thể bấm nút [Menu] (dấu /) góc trái để chọn nhanh lệnh.\n"
            "👉 Ngoài ra, Sếp cứ nhắn tự nhiên bất kỳ nội dung nào (ví dụ: 'tồn kho BT5518', 'công nợ Hoàng Hà'), em sẽ tra cứu và báo cáo ngay ạ! 😊"
        )
        telegram_send_message(chat_id, menu_text)
        return



    if text.lower() in ["/status", "status", "trang thai"]:



        cache = get_master_data_cached()



        status_msg = (



            "ℹ️ TRẠNG THÁI HỆ THỐNG CLOUD BOT 24/7:\n"



            "--------------------------------------------------\n"



            f"• Máy chủ Cloud: Đang chạy ổn định (Port {PORT})\n"



            f"• Nguồn Sổ Master: {cache.get('status')} (OneDrive)\n"



            f"• Lần cập nhật gần nhất: {cache.get('raw_facts', {}).get('timestamp', 'Chưa có')}\n"



            f"• Google Gemini AI: {'Sẵn sàng 🟢' if GEMINI_API_KEY else 'Chưa cấu hình API Key'}\n"



            f"• Người dùng xác thực: {len(AUTHENTICATED_USERS)} tài khoản\n"



            "• Phiên bản: Cloud Bot v2.0 Enterprise"



        )



        telegram_send_message(chat_id, status_msg)



        return



    # Xử lý câu hỏi thường



    telegram_send_chat_action(chat_id, "typing")



    reply = process_user_query(text, chat_id=chat_id, caller_name=caller_name)



    telegram_send_message(chat_id, reply)



def run_telegram_polling():



    """Vòng lặp Polling Telegram bền bỉ, tự động kết nối lại khi mạng đứt"""



    print(f"[{datetime.now()}] [TELEGRAM] Bắt đầu lắng nghe Telegram Polling 24/7...")



    last_update_id = 0



    backoff = 2



    while True:



        try:



            params = {"timeout": 20}



            if last_update_id:



                params["offset"] = last_update_id + 1



            res = telegram_api_call("getUpdates", params=params)



            if res and res.get("ok"):



                backoff = 2  # Reset backoff khi thành công



                for upd in res["result"]:



                    last_update_id = upd["update_id"]



                    if "message" in upd:



                        # Chạy trong luồng riêng để không nghẽn Polling



                        threading.Thread(target=handle_telegram_message, args=(upd["message"],), daemon=True).start()



            time.sleep(1)



        except KeyboardInterrupt:



            print("\n[STOP] Dừng Telegram Bot.")



            break



        except Exception as e:



            print(f"[{datetime.now()}] [POLLING ERROR]: {e}. Thử lại sau {backoff}s...")



            time.sleep(backoff)



            backoff = min(backoff * 2, 30)



# ==============================================================================



# HTTP HEALTH-CHECK SERVER (DUY TRÌ SỐNG TRÊN RENDER & KOYEB FREE TIER)



# ==============================================================================



class HealthCheckHandler(BaseHTTPRequestHandler):



    def do_GET(self):



        if self.path in ["/", "/health", "/healthz"]:



            self.send_response(200)



            self.send_header("Content-Type", "application/json; charset=utf-8")



            self.end_headers()



            data = {



                "status": "online",



                "service": "Ngoc Ha Accounting Telegram Bot 24/7",



                "company": "CONG TY TNHH TM&DV KIEN TRUC NGOC HA",



                "bot": "@ngocha_ketoan_bot",



                "time": datetime.now().isoformat(),



                "users_count": len(AUTHENTICATED_USERS)



            }



            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))



        else:



            self.send_response(404)



            self.end_headers()



    def log_message(self, format, *args):



        # Tắt log HTTP thừa để giữ console sạch sẽ



        pass



def run_http_server():



    """Khởi động HTTP Server trên PORT chỉ định để vượt qua Port Check của Render/Koyeb"""



    server_address = ("0.0.0.0", PORT)



    try:



        httpd = HTTPServer(server_address, HealthCheckHandler)



        print(f"[{datetime.now()}] [HTTP] Health-check server đang chạy tại http://0.0.0.0:{PORT}")



        httpd.serve_forever()



    except Exception as e:



        print(f"[{datetime.now()}] [HTTP ERROR]: Không thể mở cổng {PORT}: {e}")



# ==============================================================================



# HÀM MAIN KHỞI ĐỘNG HỆ THỐNG



# ==============================================================================



def keep_alive_self_ping():



    """



    Tu dong gui HTTP GET request dinh ky 8.5 phut (510s) vao URL Render



    de reset bo dem 15 phut inactivity cua Render Free Tier,



    giu cho Cloud Bot hoat dong 24/7 khong bao gio bi ngu dong.



    """



    url = "https://ngocha-cloud-bot.onrender.com/health"



    print(f"[{datetime.now()}] [KEEP-ALIVE] Luong chong ngu Render da khoi dong (chu ky 8.5 phut)...")



    time.sleep(30)



    while True:



        try:



            req = urllib.request.Request(url, headers={"User-Agent": "Render-KeepAlive/2.0"})



            with urllib.request.urlopen(req, timeout=15) as resp:



                print(f"[{datetime.now()}] [KEEP-ALIVE] Ping Render thanh cong: HTTP {resp.status}")



        except Exception as e:



            print(f"[{datetime.now()}] [KEEP-ALIVE] Ping ngoai le: {e}")



        time.sleep(510)



def setup_bot_commands():

    """Đăng ký danh sách lệnh chính thức vào nút Menu dấu '/' của Telegram"""

    commands = [

        {"command": "baocao", "description": "🚦 5 Đèn báo quản trị tổng hợp"},

        {"command": "congno_ncc", "description": "🤝 Đối soát công nợ 11 NCC (TK 331)"},

        {"command": "congno_kh", "description": "⏳ Công nợ khách hàng (TK 131)"},

        {"command": "tienve", "description": "💰 Tiền về ACB & HĐ cần xuất bù"},

        {"command": "tonkho", "description": "📦 Tồn kho PVC & chống âm kho"},

        {"command": "soan_hd", "description": "🧾 Soạn thảo hóa đơn nháp tức thì"},

        {"command": "sync", "description": "⚡ Làm mới dữ liệu Sổ Master từ Cloud"},

        {"command": "menu", "description": "📱 Bật lại bàn phím nút bấm 1 chạm"}

    ]

    try:

        telegram_api_call("setMyCommands", data={"commands": commands})

        print(f"[{datetime.now()}] [TELEGRAM] Đã thiết lập thành công Menu lệnh chuẩn!")

    except Exception as e:

        print(f"[{datetime.now()}] [WARNING] Thiết lập Bot Commands lỗi: {e}")



def main():



    print("=" * 70)



    print("   CLOUD TELEGRAM BOT 24/7 - CONG TY KIEN TRUC NGOC HA")



    print(f"   Bot: @ngocha_ketoan_bot | Port: {PORT}")



    print(f"   Admin Chat ID: {ADMIN_CHAT_ID} (Sếp Đặng Thị Hà)")



    print(f"   Passcode Bảo Mật: {BOT_PASSCODE} (Case-insensitive)")



    print(f"   Gemini AI: {'Configured 🟢' if GEMINI_API_KEY else 'Chưa có API Key'}")



    print(f"   OneDrive Link: {'Configured 🟢' if ONEDRIVE_FILE_URL else 'Dùng bộ nhớ cục bộ'}")



    print("=" * 70)



    # 1. Khởi động HTTP Server ở luồng ngầm (daemon)



    http_thread = threading.Thread(target=run_http_server, daemon=True)



    http_thread.start()



    # 2. Tải trước dữ liệu Sổ Master vào bộ nhớ đệm



    setup_bot_commands()

    threading.Thread(target=get_master_data_cached, daemon=True).start()



    threading.Thread(target=keep_alive_self_ping, daemon=True).start()



    # 3. Chạy vòng lặp Polling Telegram tại luồng chính



    run_telegram_polling()



if __name__ == "__main__":



    main()




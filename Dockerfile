# ==============================================================================
# DOCKERFILE - CLOUD TELEGRAM BOT 24/7 (CÔNG TY KIẾN TRÚC NGỌC HÀ)
# ==============================================================================
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Tối ưu hóa môi trường Python chạy trên Cloud
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Cài đặt các thư viện phụ thuộc gọn nhẹ
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn bot vào container
COPY cloud_bot.py .

# Mở cổng HTTP phục vụ Health-Check của Render.com và Koyeb
EXPOSE 8080

# Khởi chạy Bot trực ban 24/7
CMD ["python", "cloud_bot.py"]

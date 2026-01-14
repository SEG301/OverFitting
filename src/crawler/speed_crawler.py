from .spider import start_spider

if __name__ == "__main__":
    # Đây là file shortcut để người dùng có thể tiếp tục chạy crawler bằng lệnh quen thuộc.
    # Toàn bộ logic lõi đã được module hóa vào spider.py, parser.py và utils.py
    # giúp dự án tuân thủ yêu cầu module hóa của đồ án SEG301.
    start_spider()

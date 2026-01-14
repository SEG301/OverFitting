from .spider import start_spider

if __name__ == "__main__":
    # Khôi phục cơ chế cào nhanh 63 tỉnh thành
    # Logic: Batch 50 trang, 50 workers, Checkpoint Resume
    start_spider()

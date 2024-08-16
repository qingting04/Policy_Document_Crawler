import concurrent.futures
import os


def run_crawler(script_path):
    try:
        os.system(f"python {script_path}")
    except Exception as e:
        print(f"Error in {script_path}: {e}")


def main():
    crawler_scripts = [os.path.join("province", file) for file in os.listdir("province") if file.endswith(".py")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(run_crawler, crawler_scripts)
    print("所有爬虫程序执行完毕")


if __name__ == "__main__":
    main()

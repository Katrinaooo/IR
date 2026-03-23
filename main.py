import argparse

from crawler import crawl_papers, parse_date, save_papers
from download_pdf import download_pdfs
from pdf_to_txt import pdfs_to_txt


def parse_args():
    parser = argparse.ArgumentParser(description="运行完整的 arXiv 论文处理流程")
    parser.add_argument("--category", nargs="+", default=["cs.CL"], help="论文分类，可以写多个")
    parser.add_argument("--start-date", default="2026-3-14", help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-3-21", help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--max-papers", type=int, default=200, help="最多抓取多少篇")
    parser.add_argument("--output", default="papers.json", help="输出 json 文件")
    parser.add_argument("--batch-size", type=int, default=100, help="每次请求数量")
    parser.add_argument("--sleep-seconds", type=float, default=3, help="每次请求后的休眠时间")
    parser.add_argument("--pdf-dir", default="paper_pdf", help="PDF 保存目录")
    parser.add_argument("--txt-dir", default="paper_txt", help="TXT 保存目录")
    parser.add_argument("--limit", type=int, default=2, help="下载和转换阶段最多处理多少篇")
    parser.add_argument("--timeout", type=int, default=20, help="请求超时时间")
    return parser.parse_args()


def main():
    args = parse_args()
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)

    papers = crawl_papers(
        category_list=args.category,
        start_date=start_date,
        end_date=end_date,
        max_papers=args.max_papers,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep_seconds,
        timeout=args.timeout,
    )
    save_papers(papers, args.output)

    download_pdfs(
        input_path=args.output,
        pdf_dir=args.pdf_dir,
        limit=args.limit,
        timeout=max(args.timeout, 30),
    )

    pdfs_to_txt(
        input_path=args.output,
        pdf_dir=args.pdf_dir,
        txt_dir=args.txt_dir,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import requests
import xml.etree.ElementTree as ET


ARXIV_API_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_args():
    parser = argparse.ArgumentParser(description="抓取 arXiv 论文元数据")
    parser.add_argument("--category", nargs="+", default=["cs.CL"], help="论文分类，可以写多个")
    parser.add_argument("--start-date", default="2026-3-14", help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", default="2026-3-21", help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--max-papers", type=int, default=200, help="最多抓取多少篇论文")
    parser.add_argument("--output", default="papers.json", help="输出的 json 文件路径")
    parser.add_argument("--batch-size", type=int, default=100, help="每次请求的数量")
    parser.add_argument("--sleep-seconds", type=float, default=3, help="每次请求后休眠几秒")
    parser.add_argument("--timeout", type=int, default=20, help="请求超时时间")
    return parser.parse_args()


def parse_date(text):
    return datetime.strptime(text, "%Y-%m-%d").date()


def build_search_query(category_list):
    names = []
    for item in category_list:
        item = item.strip()
        if item:
            names.append(f"cat:{item}")
    if not names:
        raise ValueError("分类不能为空")
    return " OR ".join(names)


def fetch_one_page(search_query, start, batch_size, timeout):
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": batch_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    response = requests.get(ARXIV_API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.text


def normalize_arxiv_id(arxiv_url):
    paper_id = arxiv_url.rstrip("/").split("/")[-1]
    return paper_id.split("v")[0]


def parse_entry(entry):
    id_node = entry.find("atom:id", NS)
    title_node = entry.find("atom:title", NS)
    summary_node = entry.find("atom:summary", NS)
    published_node = entry.find("atom:published", NS)

    if id_node is None or title_node is None or summary_node is None or published_node is None:
        return None

    arxiv_url = (id_node.text or "").strip()
    if not arxiv_url:
        return None

    arxiv_id = normalize_arxiv_id(arxiv_url)
    authors = []
    for author in entry.findall("atom:author", NS):
        name_node = author.find("atom:name", NS)
        if name_node is not None and name_node.text:
            authors.append(name_node.text.strip())

    categories = []
    for category in entry.findall("atom:category", NS):
        term = category.attrib.get("term", "").strip()
        if term:
            categories.append(term)

    return {
        "arxiv_id": arxiv_id,
        "title": " ".join((title_node.text or "").split()),
        "authors": authors,
        "abstract": " ".join((summary_node.text or "").split()),
        "published": (published_node.text or "").strip()[:10],
        "categories": sorted(set(categories)),
        "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def is_in_date_range(published_text, start_date, end_date):
    try:
        current = parse_date(published_text)
    except ValueError:
        return False
    return start_date <= current <= end_date


def crawl_papers(category_list, start_date, end_date, max_papers, batch_size, sleep_seconds, timeout):
    search_query = build_search_query(category_list)
    result_map = {}
    start = 0

    print("开始抓取论文信息")
    while len(result_map) < max_papers:
        print(f"正在请求第 {start} 条开始的一页数据")
        xml_text = fetch_one_page(search_query, start, batch_size, timeout)
        root = ET.fromstring(xml_text)
        entries = root.findall("atom:entry", NS)

        if not entries:
            print("没有更多结果了，提前结束")
            break

        added_count = 0
        for entry in entries:
            paper = parse_entry(entry)
            if paper is None:
                continue
            if not is_in_date_range(paper["published"], start_date, end_date):
                continue
            if paper["arxiv_id"] not in result_map:
                result_map[paper["arxiv_id"]] = paper
                added_count += 1
            if len(result_map) >= max_papers:
                break

        print(f"当前已抓取 {len(result_map)} 篇")
        if added_count == 0:
            print("这一页没有新增论文，结束抓取")
            break

        start += batch_size
        time.sleep(sleep_seconds)

    return list(result_map.values())[:max_papers]


def save_papers(papers, output_path):
    output_file = Path(output_path)
    output_file.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"结果已保存到 {output_file}")


def main():
    args = parse_args()
    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")

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
        print(f"抓取完成，一共保存 {len(papers)} 篇论文")
    except Exception as exc:
        print(f"抓取失败：{exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

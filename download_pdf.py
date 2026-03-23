import argparse
import json
from pathlib import Path

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="下载论文 PDF")
    parser.add_argument("--input", default="papers.json", help="输入的 papers.json 路径")
    parser.add_argument("--pdf-dir", default="paper_pdf", help="PDF 保存目录")
    parser.add_argument("--limit", type=int, default=2, help="最多下载多少篇")
    parser.add_argument("--timeout", type=int, default=30, help="下载超时时间")
    return parser.parse_args()


def load_papers(input_path):
    return json.loads(Path(input_path).read_text(encoding="utf-8"))


def save_papers(papers, input_path):
    for paper in papers:
        paper.pop("pdf_url", None)
        paper.pop("pdf_path", None)
        paper.pop("txt_path", None)
    Path(input_path).write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")


def download_one_pdf(pdf_url, save_path, timeout):
    response = requests.get(pdf_url, timeout=timeout)
    response.raise_for_status()
    save_path.write_bytes(response.content)


def download_pdfs(input_path, pdf_dir, limit=None, timeout=30):
    papers = load_papers(input_path)
    pdf_dir = Path(pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    done = 0
    for paper in papers:
        if limit is not None and done >= limit:
            break

        arxiv_id = paper.get("arxiv_id", "").strip()
        if not arxiv_id:
            continue
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        save_path = pdf_dir / f"{arxiv_id}.pdf"
        if save_path.exists():
            print(f"PDF 已存在，跳过：{save_path.name}")
            done += 1
            continue

        try:
            download_one_pdf(pdf_url, save_path, timeout)
            done += 1
            print(f"下载成功：{save_path.name}")
        except Exception as exc:
            print(f"下载失败：{arxiv_id}，原因：{exc}")

    save_papers(papers, input_path)
    print("PDF 下载流程结束")


def main():
    args = parse_args()
    download_pdfs(
        input_path=args.input,
        pdf_dir=args.pdf_dir,
        limit=args.limit,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()

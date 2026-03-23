import argparse
import json
from pathlib import Path


try:
    from pdfminer.high_level import extract_text
except ImportError:
    extract_text = None


def parse_args():
    parser = argparse.ArgumentParser(description="把 PDF 转成 TXT")
    parser.add_argument("--input", default="papers.json", help="输入的 papers.json 路径")
    parser.add_argument("--pdf-dir", default="paper_pdf", help="PDF 所在目录")
    parser.add_argument("--txt-dir", default="paper_txt", help="TXT 输出目录")
    parser.add_argument("--limit", type=int, default=2, help="最多处理多少篇")
    return parser.parse_args()


def load_papers(input_path):
    return json.loads(Path(input_path).read_text(encoding="utf-8"))


def save_papers(papers, input_path):
    for paper in papers:
        paper.pop("pdf_path", None)
        paper.pop("txt_path", None)
    Path(input_path).write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")


def convert_pdf_to_txt(pdf_path, txt_path):
    if extract_text is None:
        raise ImportError("没有安装 pdfminer.six，请先执行 pip install -r requirements.txt")

    text = extract_text(str(pdf_path))
    txt_path.write_text(text, encoding="utf-8")


def pdfs_to_txt(input_path, pdf_dir, txt_dir, limit=None):
    papers = load_papers(input_path)
    pdf_dir = Path(pdf_dir)
    txt_dir = Path(txt_dir)
    txt_dir.mkdir(parents=True, exist_ok=True)

    done = 0
    for paper in papers:
        if limit is not None and done >= limit:
            break

        arxiv_id = paper.get("arxiv_id", "").strip()
        if not arxiv_id:
            continue

        pdf_path = pdf_dir / f"{arxiv_id}.pdf"
        if not pdf_path.exists():
            print(f"PDF 不存在，跳过：{arxiv_id}")
            continue

        txt_path = txt_dir / f"{arxiv_id}.txt"
        if txt_path.exists():
            print(f"TXT 已存在，跳过：{txt_path.name}")
            done += 1
            continue

        try:
            convert_pdf_to_txt(pdf_path, txt_path)
            done += 1
            print(f"转换成功：{txt_path.name}")
        except Exception as exc:
            print(f"文本提取失败：{arxiv_id}，原因：{exc}")

    save_papers(papers, input_path)
    print("PDF 转 TXT 流程结束")


def main():
    args = parse_args()
    pdfs_to_txt(
        input_path=args.input,
        pdf_dir=args.pdf_dir,
        txt_dir=args.txt_dir,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

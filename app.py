from ast import pattern
import json
import re
import requests
import pdfplumber
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import parser as citation_parser
import semantic_agent as sa
import openalex_indexer as oai
import dotenv

dotenv.load_dotenv()

def download_pdf(url):
    print("Downloading PDF...")
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def extract_text_from_pdf(pdf_bytes):
    full_text = ""

    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    return full_text


def extract_references_from_text(text):
    print(text)
    """
    Extracts numbered references accurately from academic papers.
    """
    match = re.split(r"\nreferences\n|\nREFERENCES\n|\nbibliography\n|\nBIBLIOGRAPHY\n|\nReferences\n", text)
    print("Match:", match)
    print(f"Number of sections found: {len(match)}")
    print("The References are:", match[-1])
    if len(match) < 2:
        return []

    refs_block = match[-1]

    pattern = re.compile(
        r"\[\d+\]\s+(.*?)(?=\n\[\d+\]|\Z)",
        re.DOTALL
    )

    raw_refs = pattern.findall(refs_block)

    clean_refs = []
    for ref in raw_refs:
        ref = " ".join(ref.split())
        clean_refs.append(ref)

    return clean_refs

def extract_exact_title(reference_text):
    """
    Extracts exact title from a citation line.
    """
    quoted = re.search(r'"([^"]+)"', reference_text)
    if quoted:
        return quoted.group(1).strip()

    url_split = reference_text.split("http")
    if len(url_split) > 1:
        left = url_split[0]
        parts = left.split(",")
        if len(parts) >= 2:
            return parts[-1].strip()

    return reference_text.strip()


def build_citation_graph(paper_title, references):
    G = nx.DiGraph()
    G.add_node(paper_title, type="paper")

    for i, ref in enumerate(references):
        title = extract_exact_title(ref)
        if not title or title.lower() == paper_title.lower():
            continue
        G.add_node(title, type="reference")
        G.add_edge(paper_title, title)

    return G
    #     match = re.search(r'[“"](.*?)[”"]', ref)

    #     if match:
    #         cited_title = match.group(1).strip()
    #     else:
    #         words = ref.split()
    #         cited_title = " ".join(words[:10]) + "..."

    #     if not cited_title or cited_title.strip() == "":
    #         cited_title = f"Reference {i+1}"

    #     G.add_node(cited_title, type="reference")
    #     G.add_edge(paper_title, cited_title)

    # return G



def visualize_graph(G):
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(G, k=0.7)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1200,
        node_color="lightblue",
        font_size=8,
        edge_color="gray"
    )

    plt.title("Paper Citation Graph")
    plt.show()


if __name__ == "__main__":
    pdf_url = input("Enter PDF URL: ").strip()
    paper_title = input("Enter paper title: ").strip()

    pdf_data = download_pdf(pdf_url)
    full_text = extract_text_from_pdf(pdf_data)
    references = extract_references_from_text(full_text)
    
    with open("references.json", "w") as f:
        json.dump(references, f, indent=4)

    parsed_references = [citation_parser.smart_parse_citation(ref) for ref in references]
    print("Parsed References:")
    for parsed in parsed_references:
        with open("parsed_references.json", "a") as f:
            f.write(json.dumps(parsed, indent=4) + "\n")
    
    normalized_references = sa.process_references(parsed_references)

    # Fact-check normalized references using OpenAlex
    fact_checked_references = []
    for norm in normalized_references:
        if norm.get("title"):
            oa_data = oai.check_openalex(norm["title"], norm.get("year"))
        else:
            oa_data = None
        fact_checked_references.append({
                "normalized": norm,
                "openalex": oa_data
            })
    with open("normalized_references.json", "w", encoding="utf-8") as f:
        json.dump(fact_checked_references, f, indent=2, ensure_ascii=False)


    print(f"Found {len(references)} references.")

    graph = build_citation_graph(paper_title, references)
    visualize_graph(graph)

import json
from pathlib import Path

from minsearch import Index

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "docs.json"


def load_faq_data(data_path: Path = DATA_PATH):
    """Load the HMRC manual sections shipped in this repo's data/docs.json."""
    return json.loads(data_path.read_text())


def build_index(documents):
    index = Index(
        text_fields=["title", "text"],
        keyword_fields=["manual"],
    )

    index.fit(documents)
    return index

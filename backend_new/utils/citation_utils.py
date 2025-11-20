"""Citation extraction utilities"""
import re
from typing import Dict


def extract_citation_info(paper_info: Dict) -> str:
    """Extract citation string: (Author et al., Year)"""
    authors = paper_info.get('authors', '')
    year = paper_info.get('year', '')

    if not authors:
        return f"({year})" if year else ""

    # Split by common delimiters
    author_list = re.split(r',\s*|;\s*', authors)
    first_author = author_list[0].strip()

    # Extract last name
    if ',' in first_author:
        last_name = first_author.split(',')[0].strip()
    else:
        name_parts = first_author.split()
        last_name = name_parts[-1] if name_parts else first_author

    # Format citation
    if len(author_list) > 1:
        citation = f"({last_name} et al., {year})" if year else f"({last_name} et al.)"
    else:
        citation = f"({last_name}, {year})" if year else f"({last_name})"

    return citation


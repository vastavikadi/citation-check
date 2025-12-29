import requests
import urllib.parse

def check_openalex(title, year=None, email="vastavikadi@gmail.com"):
    import requests, urllib.parse
    from difflib import SequenceMatcher

    def similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    url = (
        "https://api.openalex.org/works"
        f"?filter=title.search:{urllib.parse.quote(title)}"
        f"&mailto={email}"
    )

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        if not data.get("results"):
            return None

        top = data["results"][0]

        if similarity(title, top["title"]) < 0.65:
            return None

        if year and top.get("publication_year"):
            if abs(int(top["publication_year"]) - int(year)) > 2:
                return None

        return {
            "title": top["title"],
            "authors": [a["author"]["display_name"] for a in top.get("authorships", [])],
            "year": top.get("publication_year"),
            "citations": top.get("cited_by_count"),
            "openalex_id": top["id"],
        }

    except Exception as e:
        return None

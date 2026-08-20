import re

# Chaque motif : (regex, remplacement). L'ordre compte (email avant token).
PATTERNS = [
    ("IP",       r"\b(?:\d{1,3}\.){3}\d{1,3}\b",                         "<IP_REDACTED>"),
    ("EMAIL",    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "<EMAIL_REDACTED>"),
    ("PHONE_MA", r"\b0[5-7][0-9]{8}\b",                                   "<PHONE_REDACTED>"),
    ("TOKEN",    r"\b(?=[A-Za-z0-9_]*\d)[A-Za-z0-9_]{32,}\b",             "<TOKEN_REDACTED>"),
]


def anonymize(text):
    """Masque les PII et renvoie (texte_anonymisé, rapport {type: nb_occurrences})."""
    report = {}
    for name, pattern, placeholder in PATTERNS:
        text, n = re.subn(pattern, placeholder, text)
        if n:
            report[name] = n
    return text, report


if __name__ == "__main__":
    exemple = ("Client 192.168.1.42, contact jean@vala.ma, "
               "tel 0612345678, token abcdef0123456789abcdef0123456789ab")
    propre, rapport = anonymize(exemple)
    print("Avant :", exemple)
    print("Après :", propre)
    print("Rapport :", rapport)
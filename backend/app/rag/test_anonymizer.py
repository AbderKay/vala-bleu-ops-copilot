from anonymizer import anonymize


def test_ip_est_masquee():
    out, rep = anonymize("Le serveur 192.168.1.42 est en panne")
    assert "<IP_REDACTED>" in out
    assert "192.168.1.42" not in out
    assert rep["IP"] == 1


def test_email_est_masque():
    out, rep = anonymize("Écris à support@vala.ma stp")
    assert "<EMAIL_REDACTED>" in out
    assert "@vala.ma" not in out


def test_telephone_marocain():
    out, rep = anonymize("Appelle le 0612345678")
    assert "<PHONE_REDACTED>" in out


def test_token_long():
    out, rep = anonymize("clé=abcdef0123456789abcdef0123456789ab")
    assert "<TOKEN_REDACTED>" in out


def test_texte_sans_pii_inchange():
    texte = "Comment configurer un enregistrement MX ?"
    out, rep = anonymize(texte)
    assert out == texte
    assert rep == {}
def test_slug_url_non_masque():
    # un slug d'URL long ne doit PAS être pris pour un token
    texte = "Voir https://www.myvala.com/info/comment-utiliser-le-cdn-pour-un-site-wordpress"
    out, rep = anonymize(texte)
    assert "REDACTED" not in out
    assert "TOKEN" not in rep    
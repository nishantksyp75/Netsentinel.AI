from __future__ import annotations
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import KNOWLEDGE_DIR

DEFAULT = [
    {"source":"NIST SP 800-61r2","topic":"incident response","url":"https://csrc.nist.gov/pubs/sp/800/61/r2/final","text":"Use an incident-handling process that documents detection, analysis, containment, eradication, recovery, and lessons learned. Preserve evidence and record decision authority."},
    {"source":"MITRE ATT&CK Enterprise","topic":"threat techniques","url":"https://attack.mitre.org/","text":"Map observed behavior to techniques only when evidence supports it. Use technique context to guide investigation, not to replace validated telemetry."},
    {"source":"OWASP Logging Cheat Sheet","topic":"evidence","url":"https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html","text":"Collect sufficient security-event data for investigation while protecting sensitive values. Correlate event timestamps and maintain an auditable record."},
    {"source":"CISA DDoS Guidance","topic":"DDoS","url":"https://www.cisa.gov/topics/cyber-threats-and-advisories/malware-botnets-and-ddos","text":"For suspected denial-of-service activity, validate traffic patterns, preserve evidence, and coordinate approved mitigation through authorized teams."},
]
class KnowledgeBase:
    def __init__(self, directory: str|Path=KNOWLEDGE_DIR):
        docs=list(DEFAULT); root=Path(directory)
        for f in root.glob("*.md") if root.exists() else []: docs.append({"source":f.name,"topic":"local", "text":f.read_text(encoding="utf-8")})
        self.docs=docs; self.vectorizer=TfidfVectorizer(stop_words="english"); self.matrix=self.vectorizer.fit_transform(d["text"] for d in docs)
    def search(self, query: str, k: int=3) -> list[dict]:
        scores=cosine_similarity(self.vectorizer.transform([query]),self.matrix)[0]; ids=scores.argsort()[::-1][:k]
        return [{**self.docs[i],"score":round(float(scores[i]),4)} for i in ids if scores[i]>0]

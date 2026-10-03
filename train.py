import csv
import json
import os
import random

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from app.features import FEATURE_NAMES, extract_features

random.seed(42)

LEGIT_DOMAINS = ["google.com", "wikipedia.org", "github.com", "amazon.in", "flipkart.com",
                 "irctc.co.in", "sbi.co.in", "hdfcbank.com", "linkedin.com", "youtube.com",
                 "microsoft.com", "python.org", "stackoverflow.com", "timesofindia.com",
                 "nptel.ac.in", "zomato.com", "paytm.com", "apple.com", "bbc.com", "medium.com"]
BRANDS = ["paypal", "sbi", "hdfc", "amazon", "netflix", "paytm", "icici", "google", "apple", "upi"]
WORDS = ["login", "verify", "secure", "account", "update", "kyc", "confirm", "signin", "wallet"]


def make_legit():
    scheme = random.choices(["https", "http"], [9, 1])[0]
    sub = random.choice(["www.", "", "www.", "blog.", "help.", "docs."])
    path = random.choice(["", "/", "/about", "/careers", "/login", "/user/settings",
                          "/help/account", f"/search?q={random.randint(1, 999)}",
                          f"/products/{random.randint(1000, 99999)}"])
    return f"{scheme}://{sub}{random.choice(LEGIT_DOMAINS)}{path}"


def make_phish():
    b, w, n = random.choice(BRANDS), random.choice(WORDS), random.randint(1, 99)
    kind = random.randint(1, 5)
    if kind == 1:
        ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
        return f"http://{ip}/{w}/{b}.php?id={random.randint(1, 9999)}"
    if kind == 2:
        tld = random.choice(["xyz", "top", "tk", "click", "work", "ml"])
        return f"http://{b}-{w}-{n}.{tld}/{w}"
    if kind == 3:
        return f"https://{b}.{w}.secure-{random.randint(100, 999)}.com/index.html?user={random.randint(1, 99999)}"
    if kind == 4:
        return f"https://www.{b}.com@{random.choice(['evil', 'free-gift', 'claim'])}-{n}.top/{w}"
    return f"https://{b}{random.randint(10, 99)}.com/{w}"


def load_data():
    if os.path.exists("data/urls.csv"):
        with open("data/urls.csv", newline="", encoding="utf-8") as f:
            rows = [(r["url"], int(r["label"])) for r in csv.DictReader(f)]
        return rows, "data/urls.csv"
    rows = [(make_legit(), 0) for _ in range(3000)] + [(make_phish(), 1) for _ in range(3000)]
    return rows, "synthetic"


rows, source = load_data()
X, y = [], []
for url, label in rows:
    try:
        f = extract_features(url)
    except ValueError:
        continue
    X.append([f[n] for n in FEATURE_NAMES])
    y.append(label)

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_tr, y_tr)
pred = model.predict(X_te)

metrics = {
    "data_source": source,
    "samples": len(X),
    "accuracy": round(accuracy_score(y_te, pred), 4),
    "precision": round(precision_score(y_te, pred), 4),
    "recall": round(recall_score(y_te, pred), 4),
}
joblib.dump(model, "model.joblib")
with open("metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print(metrics)
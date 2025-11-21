# scripts/generate_synthetic_data.py
"""
Professional synthetic data generator for SecuAgentNet+ capstone.
Generates a CSV with realistic incidents covering:
 - email, sms, document, social, upload (media)
 - phishing/scam labels, deepfake flags, manual severity, categories
 - metadata: sender, recipient, attachment_name, domain, pii_present
 - timestamps spanning recent 90 days
 - ground truth fields for evaluation (label_category, ground_truth_severity)
Output: data/synthetic_incidents_professional.csv
"""

import csv
import random
import uuid
import datetime
from pathlib import Path
import hashlib

OUT = Path("data")
OUT.mkdir(exist_ok=True)
F = OUT / "synthetic_incidents_professional.csv"

# Templates and pools
phishing_templates = [
    "Urgent: Your account will be suspended. Click {link} to verify now.",
    "Action required: Confirm your payment method at {link}. Invoice attached: {attachment}",
    "Security alert: New sign-in from unknown device. Reset here: {link}",
    "Scholarship awarded! Apply here: {link} — limited seats.",
    "Payroll issue: update your bank details: {link}"
]

sms_templates = [
    "Free voucher! Redeem at {link}",
    "Your exam result updated. Login at {link}",
    "Loan approved! Complete KYC at {link}",
    "Package delivery failed. Confirm at {link}",
]

fake_doc_templates = [
    "Hospital discharge summary - Patient: {name} - MRN: {id}",
    "Government ID correction letter - Ref: {id}",
    "Offer letter - Company: {company} - Candidate: {name}",
    "Medical test report - Patient: {name} - Result: Pending - Ref {id}"
]

social_templates = [
    "Watch this shocking reveal video (see attachment)",
    "Viral video: unbelievable transformation - shared by {name}",
    "Interview leaked - audio attached"
]

attachment_types = ["pdf", "docx", "jpg", "png", "mp4", "none"]

domains = [
    "secure-bank.com", "uni-scholar.org", "docverify.net", "loanfast.info",
    "trusted-health.org", "payments-update.com", "gov-id.org", "parcel-track.net"
]

companies = ["Acme Corp", "MediLife Hospital", "Global Uni", "FinTrust Ltd", "JobHub Pvt Ltd"]
names = ["Aisha Khan", "Rahul Verma", "John Smith", "Meera Patel", "Sana Ahmed", "Vikram Rao"]

categories = [
    "phishing", "scam_sms", "fake_doc", "deepfake_media", "benign", "invoice_fraud",
    "job_scam", "scholarship_scam", "harassment", "social_engineering"
]

def deterministic_seed(i):
    # Produces reproducible results if needed
    seed = int(hashlib.sha1(str(i).encode()).hexdigest()[:8], 16)
    random.seed(seed)

def gen_incident(i):
    deterministic_seed(i)
    kind = random.choices(
        ["email", "sms", "document", "social", "upload"],
        weights=[0.4, 0.25, 0.15, 0.15, 0.05]
    )[0]
    idstr = str(uuid.uuid4())[:12]
    # recent 90 days
    ts = (datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 90),
                                                         seconds=random.randint(0, 86400))).isoformat() + "Z"
    sender = ""
    recipient = ""
    domain = ""
    content = ""
    attachment = "none"
    has_link = False
    link = ""
    label = "benign"
    deepfake_flag = 0
    pii_present = False
    manual_severity = random.choices(["low","medium","high","critical"], weights=[0.5,0.3,0.15,0.05])[0]
    ground_truth_severity = manual_severity  # for now; can be adjusted below
    # choose pattern by kind
    if kind == "email":
        sender = f"user{random.randint(100,999)}@{random.choice(domains)}"
        recipient = f"user{random.randint(1000,1999)}@example.com"
        domain = random.choice(domains)
        template = random.choice(phishing_templates + ["Hello, please review attached report"])
        # 70% chance of link in phishing templates, otherwise none
        if "{link}" in template:
            link = f"https://{domain}/?id={idstr}"
            has_link = True
        attachment = random.choice(attachment_types)
        if "{attachment}" in template:
            att_name = f"invoice_{idstr}.pdf"
            content = template.format(link=link, attachment=att_name)
            attachment = "pdf"
        else:
            content = template.format(link=link) if "{link}" in template else template
        # label selection
        label = random.choices(["phishing","benign","invoice_fraud","job_scam","scholarship_scam"],
                               weights=[0.25,0.55,0.08,0.06,0.06])[0]
        # PII presence (names, account numbers) sometimes
        if random.random() < 0.15:
            content += f" Patient: {random.choice(names)}, Acc: XXXX-XXXX-{random.randint(1000,9999)}"
            pii_present = True
        # adjust ground truth severity for phishing/invoice_fraud
        if label in ("phishing","invoice_fraud"):
            manual_severity = random.choices(["medium","high","critical"], weights=[0.4,0.45,0.15])[0]
            ground_truth_severity = manual_severity

    elif kind == "sms":
        sender = f"+91{random.randint(6000000000,9999999999)}"
        recipient = f"+91{random.randint(6000000000,9999999999)}"
        domain = random.choice(domains)
        template = random.choice(sms_templates + ["Your OTP is 123456 - never share it"])
        if "{link}" in template:
            link = f"http://{domain}/surveys?id={idstr}"
            has_link = True
        content = template.format(link=link)
        label = random.choices(["scam_sms","benign","loan_scam"], weights=[0.35,0.6,0.05])[0]
        if label == "scam_sms":
            manual_severity = random.choice(["low","medium","high"])
            ground_truth_severity = manual_severity

    elif kind == "document":
        sender = f"{random.choice(companies).replace(' ','').lower()}@{random.choice(domains)}"
        recipient = f"records@{random.choice(['hospital.org','gov.org','company.com'])}"
        template = random.choice(fake_doc_templates + ["Certified true copy - see attached"])
        attachment = random.choice(["pdf","docx"])
        content = template.format(id=idstr, name=random.choice(names), company=random.choice(companies))
        label = random.choices(["fake_doc","legit_doc"], weights=[0.35,0.65])[0]
        # fake docs occasionally carry PII
        if random.random() < 0.5:
            content += f" | DOB: {random.randint(1970,2010)}-0{random.randint(1,9)}-{random.randint(10,28)}"
            pii_present = True
        if label == "fake_doc":
            deepfake_flag = 1 if random.random() < 0.6 else 0
            manual_severity = random.choices(["medium","high"], weights=[0.5,0.5])[0]
            ground_truth_severity = manual_severity

    elif kind == "social":
        sender = random.choice(names)
        recipient = "public"
        template = random.choice(social_templates)
        content = template.format(name=random.choice(names))
        attachment = random.choice(["mp4","jpg","none"])
        label = random.choices(["deepfake_media","benign","harassment"], weights=[0.25,0.65,0.1])[0]
        if label == "deepfake_media":
            deepfake_flag = 1 if random.random() < 0.8 else 0
            manual_severity = random.choices(["medium","high"], weights=[0.6,0.4])[0]
            ground_truth_severity = manual_severity

    else:  # upload / media
        sender = random.choice(names)
        recipient = "admin"
        content = "Uploaded media for review"
        attachment = random.choice(["mp4","jpg","png"])
        label = random.choice(["benign","deepfake_media"])
        deepfake_flag = 1 if label == "deepfake_media" and random.random() < 0.5 else 0

    # derived fields
    attachment_name = f"{attachment}_{idstr}.{attachment}" if attachment != "none" else "none"
    hash_content = hashlib.sha1((content + idstr).encode()).hexdigest()[:12]

    return {
        "incident_id": idstr,
        "kind": kind,
        "timestamp": ts,
        "sender": sender,
        "recipient": recipient,
        "domain": domain,
        "content": content,
        "attachment_type": attachment,
        "attachment_name": attachment_name,
        "has_link": has_link,
        "link": link,
        "label_category": label,
        "deepfake_flag": deepfake_flag,
        "pii_present": int(pii_present),
        "manual_severity": manual_severity,
        "ground_truth_severity": ground_truth_severity,
        "evidence_hash": hash_content
    }

def generate(n=2000, out_file=F):
    with open(out_file, "w", newline="", encoding="utf8") as fh:
        # get a sample row for headers
        row0 = gen_incident(0)
        writer = csv.DictWriter(fh, fieldnames=list(row0.keys()))
        writer.writeheader()
        for i in range(n):
            writer.writerow(gen_incident(i))
    print(f"Generated {n} incidents -> {out_file.resolve()}")

if __name__ == "__main__":
    generate(2000)

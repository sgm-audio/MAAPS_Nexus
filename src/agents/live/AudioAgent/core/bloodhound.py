import re
from typing import Set
from bs4 import BeautifulSoup


class Bloodhound:
    """
    The Digital Bloodhound.
    Responsible for sniffing out contact details from raw HTML bytes.
    """

    # Regex for standard emails
    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    # Words that indicate a contact page
    CONTACT_KEYWORDS = ["contact", "about", "connect", "team", "staff"]

    @staticmethod
    def extract_emails(html_content: str) -> Set[str]:
        """Scans raw HTML for email patterns."""
        if html_content is None:
            return set()

        # 1. Regex Scan
        found = set(re.findall(Bloodhound.EMAIL_REGEX, html_content))

        # 2. Filter Junk
        clean = set()
        junk_domains = [
            "wix.com",
            "squarespace.com",
            "sentry.io",
            "example.com",
            "domain.com",
            "email.com",
            "wixpress.com",
        ]
        junk_extensions = ["png", "jpg", "jpeg", "gif", "svg", "webp", "js", "css"]

        for email in found:
            email = email.lower()
            if any(d in email for d in junk_domains):
                continue
            if email.split(".")[-1] in junk_extensions:
                continue
            clean.add(email)

        return clean

    @staticmethod
    def find_contact_link(soup: BeautifulSoup, base_url: str) -> str:
        """Finds the most likely contact page URL."""
        if not soup:
            return None

        for keyword in Bloodhound.CONTACT_KEYWORDS:
            # Case insensitive search for link text or href
            link = soup.find("a", href=True, string=re.compile(keyword, re.I))
            if not link:
                link = soup.find("a", href=re.compile(keyword, re.I))

            if link:
                href = link["href"]
                if href.startswith("http"):
                    return href
                elif href.startswith("/"):
                    return base_url.rstrip("/") + href
                else:
                    return base_url.rstrip("/") + "/" + href

        return None

    @staticmethod
    def rank_emails(emails: Set[str]) -> str:
        """Prioritizes the best email for a studio."""
        if not emails:
            return ""

        # Priority list
        gold = [
            e
            for e in emails
            if any(x in e for x in ["info", "hello", "studio", "booking", "contact"])
        ]
        silver = [e for e in emails if "gmail" in e]  # Small studios often use gmail
        bronze = list(emails)

        if gold:
            return gold[0]
        if silver:
            return silver[0]
        return bronze[0]

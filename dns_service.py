"""
DNS lookup helper for the DNS Query Analyzer.

This module uses the dnspython library to send real DNS queries.
Each record type is queried separately so a missing type (for example CNAME)
does not fail the whole analysis.
"""

import re
import time

import dns.exception
import dns.resolver

# Record types required by the project, in display order.
RECORD_TYPES = ["A", "AAAA", "MX", "NS", "CNAME", "TXT"]

RECORD_DESCRIPTIONS = {
    "A": "IPv4 addresses associated with the domain",
    "AAAA": "IPv6 addresses associated with the domain",
    "MX": "Mail servers responsible for receiving email",
    "NS": "Authoritative name servers",
    "CNAME": "Canonical / alias name",
    "TXT": "Text-based DNS information",
}

# Simple domain pattern: labels of letters, digits, and hyphens.
DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


class DnsQueryError(Exception):
    """Raised when the overall DNS analysis cannot be completed."""

    def __init__(self, title, message, status_code=400):
        super().__init__(message)
        self.title = title
        self.message = message
        self.status_code = status_code


def clean_domain(raw_value):
    """Remove extra spaces and common URL prefixes from user input."""
    if raw_value is None:
        return ""

    domain = str(raw_value).strip().lower()
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.split("/")[0]
    domain = domain.split("?")[0]
    domain = domain.split(":")[0]
    domain = domain.strip(".")
    return domain


def validate_domain(domain):
    """Check that the domain is not empty and looks like a valid hostname."""
    if not domain:
        raise DnsQueryError(
            "Invalid Input",
            "Please enter a domain name before analyzing DNS records.",
            status_code=400,
        )

    if domain in ("localhost",) or domain.replace(".", "").isdigit():
        raise DnsQueryError(
            "Invalid Domain",
            "Please enter a valid domain name such as google.com or example.com.",
            status_code=400,
        )

    if not DOMAIN_PATTERN.match(domain):
        raise DnsQueryError(
            "Invalid Domain",
            "The entered value does not look like a valid domain name. "
            "Example: google.com",
            status_code=400,
        )


def _format_record(record_type, answer):
    """Convert a dnspython answer object into a readable string."""
    if record_type == "MX":
        exchange = str(answer.exchange).rstrip(".")
        if not exchange:
            exchange = "."  # Null MX (RFC 7505): domain does not accept email
        return f"{answer.preference} {exchange}"
    if record_type == "TXT":
        parts = []
        for item in answer.strings:
            if isinstance(item, bytes):
                parts.append(item.decode("utf-8", errors="replace"))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(answer).rstrip(".")


def query_record_type(resolver, domain, record_type):
    """
    Query one DNS record type.

    Returns (values, timed_out).
    An empty values list means no records were found for that type,
    which is normal for many domains.

    A timeout on a single type does not stop the remaining queries.
    If every record type times out, the caller reports a timeout error.
    """
    try:
        answers = resolver.resolve(domain, record_type)
        values = [_format_record(record_type, item) for item in answers]
        # Keep unique values while preserving order.
        unique_values = list(dict.fromkeys(values))
        return unique_values, False
    except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return [], False
    except dns.resolver.NXDOMAIN:
        # NXDOMAIN means the domain itself does not exist.
        raise
    except dns.exception.Timeout:
        return [], True
    except dns.exception.DNSException:
        # Other record-specific DNS errors should not crash the whole analysis.
        return [], False


FRIENDLY_TYPE_NAMES = {
    "A": "IPv4 (A)",
    "AAAA": "IPv6 (AAAA)",
    "MX": "mail server (MX)",
    "NS": "name server (NS)",
    "CNAME": "CNAME",
    "TXT": "TXT",
}

# Public resolvers used only for the performance comparison feature.
COMPARISON_RESOLVERS = [
    {"id": "google", "name": "Google DNS", "nameservers": ["8.8.8.8"]},
    {"id": "cloudflare", "name": "Cloudflare DNS", "nameservers": ["1.1.1.1"]},
    {"id": "system", "name": "System DNS", "nameservers": None},
]


def make_resolver(nameservers=None, timeout=4.0, lifetime=8.0):
    """
    Create a dnspython Resolver.

    nameservers=None means use the computer's default/system DNS settings.
    Passing ['8.8.8.8'] or ['1.1.1.1'] sends queries to that public resolver.
    """
    resolver = dns.resolver.Resolver()
    if nameservers is not None:
        resolver.nameservers = nameservers
    resolver.timeout = timeout
    resolver.lifetime = lifetime
    return resolver


def timed_simple_lookup(domain, nameservers=None):
    """
    Time a real A-record query against one resolver.

    Returns a dict with success, response_time_ms, and status text.
    Failures are returned as data so other resolvers can still be compared.
    """
    resolver = make_resolver(nameservers=nameservers, timeout=2.5, lifetime=3.0)
    start_time = time.perf_counter()
    try:
        resolver.resolve(domain, "A")
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": True,
            "response_time_ms": elapsed_ms,
            "status": "Successful",
        }
    except dns.resolver.NoAnswer:
        # Resolver answered; this domain simply has no A record.
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": True,
            "response_time_ms": elapsed_ms,
            "status": "Successful",
        }
    except dns.exception.Timeout:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "response_time_ms": elapsed_ms,
            "status": "Timed out",
        }
    except dns.resolver.NXDOMAIN:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "response_time_ms": elapsed_ms,
            "status": "Domain not found",
        }
    except dns.exception.DNSException:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "response_time_ms": elapsed_ms,
            "status": "Query failed",
        }
    except Exception:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "success": False,
            "response_time_ms": elapsed_ms,
            "status": "Query failed",
        }


def compare_resolvers(domain):
    """
    Compare Google DNS, Cloudflare DNS, and the system DNS resolver.

    Each lookup is independent. One failed resolver does not stop the others.
    Fastest server is chosen only among successful queries.
    """
    results = []
    for item in COMPARISON_RESOLVERS:
        lookup = timed_simple_lookup(domain, item["nameservers"])
        address = item["nameservers"][0] if item["nameservers"] else "System/Default"
        results.append(
            {
                "id": item["id"],
                "name": item["name"],
                "address": address,
                "success": lookup["success"],
                "status": lookup["status"],
                "response_time_ms": lookup["response_time_ms"],
            }
        )

    successful = [row for row in results if row["success"]]
    fastest = None
    if successful:
        fastest_row = min(successful, key=lambda row: row["response_time_ms"])
        fastest = {
            "name": fastest_row["name"],
            "response_time_ms": fastest_row["response_time_ms"],
            "label": f"{fastest_row['name']} — {fastest_row['response_time_ms']} ms",
        }

    return {
        "results": results,
        "fastest": fastest,
        "note": (
            "These times are measured by this application for one A-record lookup "
            "per resolver. They can vary with network conditions and caching. "
            "The fastest result here is not permanently the best DNS server."
        ),
    }


def build_interpretation(domain, records):
    """Create a short, student-friendly summary. No security claims."""
    found_types = [name for name in RECORD_TYPES if records[name]["values"]]
    missing_types = [name for name in RECORD_TYPES if not records[name]["values"]]

    if not found_types:
        return (
            f"DNS queries completed for {domain}, but no A, AAAA, MX, NS, "
            "CNAME, or TXT records were returned."
        )

    found_parts = [FRIENDLY_TYPE_NAMES[name] for name in found_types]
    if len(found_parts) == 1:
        found_text = found_parts[0] + " records"
    elif len(found_parts) == 2:
        found_text = f"{found_parts[0]} and {found_parts[1]} records"
    else:
        found_text = ", ".join(found_parts[:-1]) + f", and {found_parts[-1]} records"

    sentence = (
        f"DNS resolution was successful. The domain returned {found_text}."
    )
    if missing_types:
        missing_parts = [FRIENDLY_TYPE_NAMES[name] for name in missing_types]
        if len(missing_parts) == 1:
            missing_text = missing_parts[0]
        elif len(missing_parts) == 2:
            missing_text = f"{missing_parts[0]} and {missing_parts[1]}"
        else:
            missing_text = ", ".join(missing_parts[:-1]) + f", and {missing_parts[-1]}"
        sentence += f" No {missing_text} record was found."

    return sentence


def summarize_records(records, response_time_ms, domain):
    """Build the analysis-summary dashboard data from the record results."""
    availability = []
    for record_type in RECORD_TYPES:
        found = bool(records[record_type]["values"])
        availability.append(
            {
                "type": record_type,
                "found": found,
                "label": "Found" if found else "Not Found",
            }
        )

    types_found = sum(1 for item in availability if item["found"])
    total_records = sum(len(records[name]["values"]) for name in RECORD_TYPES)

    return {
        "query_status": "Successful",
        "response_time_ms": response_time_ms,
        "record_types_found": types_found,
        "record_types_total": len(RECORD_TYPES),
        "total_records": total_records,
        "availability": availability,
        "interpretation": build_interpretation(domain, records),
    }


def analyze_domain(raw_domain):
    """
    Validate the domain, query all required record types, and return
    a structured result dictionary for the API.
    """
    domain = clean_domain(raw_domain)
    validate_domain(domain)

    # System/default resolver for the full record-type analysis.
    resolver = make_resolver(nameservers=None, timeout=4.0, lifetime=8.0)

    start_time = time.perf_counter()

    try:
        records = {}
        timeout_count = 0
        for record_type in RECORD_TYPES:
            values, timed_out = query_record_type(resolver, domain, record_type)
            if timed_out:
                timeout_count += 1
            records[record_type] = {
                "type": record_type,
                "description": RECORD_DESCRIPTIONS[record_type],
                "values": values,
            }
        if timeout_count == len(RECORD_TYPES):
            raise dns.exception.Timeout()
    except dns.resolver.NXDOMAIN:
        raise DnsQueryError(
            "DNS Query Failed",
            "The domain could not be resolved. Please check the domain name and try again.",
            status_code=404,
        )
    except dns.exception.Timeout:
        raise DnsQueryError(
            "DNS Query Failed",
            "The DNS lookup timed out. Please check your internet connection and try again.",
            status_code=504,
        )
    except dns.resolver.NoNameservers:
        raise DnsQueryError(
            "DNS Query Failed",
            "DNS resolution failed because no usable name servers responded. Please try again later.",
            status_code=502,
        )
    except dns.exception.DNSException:
        raise DnsQueryError(
            "DNS Query Failed",
            "The domain could not be resolved. Please check the domain name and try again.",
            status_code=502,
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    response_time_ms = round(elapsed_ms, 2)

    summary = summarize_records(records, response_time_ms, domain)

    # Comparison is independent of the full record analysis. A failed
    # public resolver must not hide the DNS records that were already found.
    try:
        comparison = compare_resolvers(domain)
    except Exception:
        comparison = {
            "results": [],
            "fastest": None,
            "note": (
                "DNS server comparison could not be completed. "
                "The DNS record results below are still valid."
            ),
        }

    return {
        "success": True,
        "domain": domain,
        "status": "Successful",
        "response_time_ms": response_time_ms,
        "records": records,
        "summary": summary,
        "comparison": comparison,
    }

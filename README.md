# DNS Query Analyzer

A beginner-friendly Computer Networks academic project that analyzes DNS records of a domain using **real DNS queries**.

The user enters a domain name such as `google.com`, clicks **Analyze DNS**, and the application displays A, AAAA, MX, NS, CNAME, and TXT records, along with query status and response time.

---

## Project Description

The Domain Name System (DNS) is like the phone book of the Internet. Humans remember names such as `github.com`, but computers communicate using IP addresses. DNS converts a domain name into useful records.

This project is a small web application:

- The **frontend** is a simple HTML/CSS/JavaScript page.
- The **backend** is a Python Flask server.
- The server uses the **dnspython** library to send real DNS queries (not fake or stored data).

---

## Problem Statement

Students often learn DNS theory (A records, MX records, name servers) without seeing how a real lookup looks. Manually using command-line tools can be confusing for a viva demonstration.

This project solves that by providing a clear web interface that:

1. Accepts a domain name.
2. Performs live DNS lookups.
3. Shows each record type in a readable card.
4. Explains the result in simple language.

---

## Objectives

- Understand how DNS record types work.
- Perform live DNS queries using Python.
- Measure the time taken for the lookup process.
- Handle missing records and invalid domains without crashing.
- Present results in a clean academic dashboard.

---

## Features

- Domain input and **Analyze DNS** button
- Real DNS queries for A, AAAA, MX, NS, CNAME, and TXT
- Response time measurement in milliseconds
- Loading indicator while analysis is running
- Separate result cards for each record type
- Analysis summary with a short human-readable interpretation
- Friendly error messages for empty input, invalid domains, and unresolved names
- Responsive layout for desktop and mobile
- No database and no API keys required

---

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Flask |
| DNS lookups | dnspython |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | Not used (not needed for this version) |

---

## DNS Concepts Used

### What is DNS?

DNS (Domain Name System) maps a domain name to information such as IP addresses, mail servers, and name servers.

### Record types in this project

| Record | Meaning in simple words |
| --- | --- |
| **A** | IPv4 address of the website/server |
| **AAAA** | IPv6 address of the website/server |
| **MX** | Mail servers that receive email for the domain |
| **NS** | Authoritative name servers that answer DNS questions for the domain |
| **CNAME** | An alias that points the name to another domain name |
| **TXT** | Text data, often used for verification or email-related settings |

A domain does **not** need to have every record type. For example, `google.com` usually has A, AAAA, MX, NS, and TXT records, but it may not have a CNAME at the main domain. That is normal.

### Response time

The application measures the time taken by **our program** to complete the DNS lookup process.

This is **not** a guaranteed network latency value. It can change because of:

- Internet speed
- DNS resolver used by the computer
- Cached answers
- Temporary network delays

---

## System Workflow

1. The user opens the web page in a browser.
2. The user types a domain and clicks **Analyze DNS**.
3. JavaScript sends a `POST` request to `/api/analyze`.
4. Flask validates the input.
5. `dnspython` queries each record type separately.
6. The backend builds a JSON response with records, timing, and a short summary.
7. The frontend displays the results in cards.
8. If a record type is missing, that card shows **No records found.**
9. If the domain is invalid or does not exist, a friendly error is shown.

---

## Project Structure

```text
DNS-Query-Analyzer/
├── app.py              # Flask routes and API
├── dns_service.py      # Domain validation and DNS lookups
├── requirements.txt    # Python packages
├── README.md
├── .gitignore
├── templates/
│   └── index.html      # Main web page
└── static/
    ├── style.css       # Page design
    └── script.js       # Frontend logic
```

---

## Installation Steps

1. Install **Python 3.10+**.
2. Open a terminal in this project folder.
3. (Optional but recommended) Create a virtual environment:

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On Linux/macOS:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to Run Locally

From the project folder:

```bash
python app.py
```

Then open a browser and visit:

```text
http://127.0.0.1:5000
```

You should see the **DNS Query Analyzer** page.

---

## Example Usage

1. Enter `google.com`
2. Click **Analyze DNS**
3. Wait for “Analyzing DNS records...”
4. View:
   - Domain, status, and response time
   - Analysis summary
   - Cards for A, AAAA, MX, NS, CNAME, and TXT

Try also:

- `github.com`
- `example.com`
- a fake name such as `thisdomaindoesnotexist12345.com`

---

## API Endpoint Explanation

### `POST /api/analyze`

**Request body**

```json
{
  "domain": "google.com"
}
```

**Successful response (shape)**

```json
{
  "success": true,
  "domain": "google.com",
  "status": "Successful",
  "response_time_ms": 24.12,
  "records": {
    "A": {
      "type": "A",
      "description": "IPv4 addresses associated with the domain",
      "values": ["142.x.x.x"]
    }
  },
  "summary": {
    "query_status": "DNS Resolution Successful",
    "response_time_ms": 24.12,
    "record_types_found": 5,
    "record_types_total": 6,
    "total_records": 12,
    "interpretation": "DNS resolution was successful. The domain google.com has ..."
  }
}
```

**Error response (shape)**

```json
{
  "success": false,
  "error": "DNS Query Failed",
  "message": "The domain could not be resolved. Please check the domain name and try again."
}
```

The frontend also rejects empty input before calling the API.

---

## DNS Record Explanation (Viva Notes)

- **A record**: “This domain’s IPv4 address is ...”
- **AAAA record**: “This domain’s IPv6 address is ...”
- **MX record**: shown as `preference hostname`. A lower preference number is tried first.
- **NS record**: the official DNS servers for the domain.
- **CNAME record**: “this name is an alias of another name.” The main/root domain often has A/AAAA instead of CNAME.
- **TXT record**: readable text stored in DNS. This project only displays the text. It does **not** claim that a website is safe or unsafe.

---

## Error Handling

The application handles these cases without crashing:

| Situation | User message (idea) |
| --- | --- |
| Empty input | Please enter a domain name |
| Invalid format | Does not look like a valid domain |
| Domain does not exist | The domain could not be resolved |
| DNS timeout | The DNS lookup timed out |
| Missing record type | No records found (for that card only) |
| Unexpected server error | Something went wrong... (no Python traceback) |

---

## Future Enhancements

- DNSSEC information
- SOA and PTR record support
- Choice of a custom DNS resolver (for example 8.8.8.8)
- Query history using a small database
- Export results as PDF or CSV
- WHOIS lookup (separate from DNS)

---

## Academic Note

This is a learning project for Computer Networks. DNS answers can change over time and may differ between resolvers. The analyzer never invents records; it only shows what DNS returns at the time of the query.

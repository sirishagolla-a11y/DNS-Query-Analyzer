"""
DNS Query Analyzer - Flask backend.

Serves the web page and a JSON API that performs real DNS lookups.
"""

from flask import Flask, jsonify, render_template, request

from dns_service import DnsQueryError, analyze_domain

app = Flask(__name__)


@app.route("/")
def index():
    """Render the main analyzer page."""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyze DNS records for a domain.

    Expected JSON body:
        { "domain": "google.com" }
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise DnsQueryError(
                "Invalid Input",
                "Please enter a domain name before analyzing DNS records.",
                status_code=400,
            )

        domain = data.get("domain", "")
        result = analyze_domain(domain)
        return jsonify(result)

    except DnsQueryError as error:
        return jsonify(
            {
                "success": False,
                "error": error.title,
                "message": error.message,
            }
        ), error.status_code

    except Exception:
        # Do not send Python stack traces to the browser.
        return jsonify(
            {
                "success": False,
                "error": "Unexpected Server Error",
                "message": "Something went wrong while analyzing DNS records. Please try again.",
            }
        ), 500


if __name__ == "__main__":
    # Local development server for the academic project.
    app.run(host="127.0.0.1", port=5000, debug=True)

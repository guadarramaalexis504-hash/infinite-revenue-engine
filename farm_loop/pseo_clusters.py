"""Programmatic SEO clusters: a static page per emoji, CSS color, and network port.

Each cluster turns a bounded, authoritative dataset into hundreds of indexable
long-tail pages ("what color is #FF6347", "what runs on port 5432", "🔥 emoji
meaning"). Every page is generated deterministically, costs nothing to host on
GitHub Pages, and funnels the reader toward the interactive tools and offers —
the same funnel pattern as the cron schedule pages.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class PseoPage:
    slug: str
    title: str          # used for <title> and meta description
    h1: str
    lead: str
    body: str           # inner HTML of the article (already rendered)
    related_label: str  # short link text used by the index and sibling pages


@dataclass(frozen=True)
class PseoCluster:
    key: str            # url segment, e.g. "emoji"
    title: str
    intro: str
    pages: tuple[PseoPage, ...]


# Registry consumed by main.py for the build step AND the homepage nav/sitemap.
CLUSTER_NAV: list[tuple[str, str]] = [
    ("Emoji", "emoji/"),
    ("Colors", "color/"),
    ("Ports", "port/"),
    ("ASCII", "ascii/"),
    ("HTML entities", "html-entity/"),
    ("HTTP codes", "http-status/"),
    ("MIME types", "mime/"),
    ("HTTP headers", "header/"),
    ("Exit codes", "exit/"),
    ("Country codes", "country/"),
    ("Currencies", "currency/"),
    ("Git recipes", "git/"),
    ("Regex", "regex/"),
    ("Linux", "linux/"),
]


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def _meta_description(text: str, *, limit: int = 155) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:")
    return f"{clipped}…"


# ---------------------------------------------------------------------------
# Colors — the 148 CSS named colors
# ---------------------------------------------------------------------------

CSS_COLORS: dict[str, str] = {
    "aliceblue": "F0F8FF", "antiquewhite": "FAEBD7", "aqua": "00FFFF",
    "aquamarine": "7FFFD4", "azure": "F0FFFF", "beige": "F5F5DC",
    "bisque": "FFE4C4", "black": "000000", "blanchedalmond": "FFEBCD",
    "blue": "0000FF", "blueviolet": "8A2BE2", "brown": "A52A2A",
    "burlywood": "DEB887", "cadetblue": "5F9EA0", "chartreuse": "7FFF00",
    "chocolate": "D2691E", "coral": "FF7F50", "cornflowerblue": "6495ED",
    "cornsilk": "FFF8DC", "crimson": "DC143C", "cyan": "00FFFF",
    "darkblue": "00008B", "darkcyan": "008B8B", "darkgoldenrod": "B8860B",
    "darkgray": "A9A9A9", "darkgreen": "006400", "darkgrey": "A9A9A9",
    "darkkhaki": "BDB76B", "darkmagenta": "8B008B", "darkolivegreen": "556B2F",
    "darkorange": "FF8C00", "darkorchid": "9932CC", "darkred": "8B0000",
    "darksalmon": "E9967A", "darkseagreen": "8FBC8F", "darkslateblue": "483D8B",
    "darkslategray": "2F4F4F", "darkslategrey": "2F4F4F", "darkturquoise": "00CED1",
    "darkviolet": "9400D3", "deeppink": "FF1493", "deepskyblue": "00BFFF",
    "dimgray": "696969", "dimgrey": "696969", "dodgerblue": "1E90FF",
    "firebrick": "B22222", "floralwhite": "FFFAF0", "forestgreen": "228B22",
    "fuchsia": "FF00FF", "gainsboro": "DCDCDC", "ghostwhite": "F8F8FF",
    "gold": "FFD700", "goldenrod": "DAA520", "gray": "808080",
    "green": "008000", "greenyellow": "ADFF2F", "grey": "808080",
    "honeydew": "F0FFF0", "hotpink": "FF69B4", "indianred": "CD5C5C",
    "indigo": "4B0082", "ivory": "FFFFF0", "khaki": "F0E68C",
    "lavender": "E6E6FA", "lavenderblush": "FFF0F5", "lawngreen": "7CFC00",
    "lemonchiffon": "FFFACD", "lightblue": "ADD8E6", "lightcoral": "F08080",
    "lightcyan": "E0FFFF", "lightgoldenrodyellow": "FAFAD2", "lightgray": "D3D3D3",
    "lightgreen": "90EE90", "lightgrey": "D3D3D3", "lightpink": "FFB6C1",
    "lightsalmon": "FFA07A", "lightseagreen": "20B2AA", "lightskyblue": "87CEFA",
    "lightslategray": "778899", "lightslategrey": "778899", "lightsteelblue": "B0C4DE",
    "lightyellow": "FFFFE0", "lime": "00FF00", "limegreen": "32CD32",
    "linen": "FAF0E6", "magenta": "FF00FF", "maroon": "800000",
    "mediumaquamarine": "66CDAA", "mediumblue": "0000CD", "mediumorchid": "BA55D3",
    "mediumpurple": "9370DB", "mediumseagreen": "3CB371", "mediumslateblue": "7B68EE",
    "mediumspringgreen": "00FA9A", "mediumturquoise": "48D1CC", "mediumvioletred": "C71585",
    "midnightblue": "191970", "mintcream": "F5FFFA", "mistyrose": "FFE4E1",
    "moccasin": "FFE4B5", "navajowhite": "FFDEAD", "navy": "000080",
    "oldlace": "FDF5E6", "olive": "808000", "olivedrab": "6B8E23",
    "orange": "FFA500", "orangered": "FF4500", "orchid": "DA70D6",
    "palegoldenrod": "EEE8AA", "palegreen": "98FB98", "paleturquoise": "AFEEEE",
    "palevioletred": "DB7093", "papayawhip": "FFEFD5", "peachpuff": "FFDAB9",
    "peru": "CD853F", "pink": "FFC0CB", "plum": "DDA0DD",
    "powderblue": "B0E0E6", "purple": "800080", "rebeccapurple": "663399",
    "red": "FF0000", "rosybrown": "BC8F8F", "royalblue": "4169E1",
    "saddlebrown": "8B4513", "salmon": "FA8072", "sandybrown": "F4A460",
    "seagreen": "2E8B57", "seashell": "FFF5EE", "sienna": "A0522D",
    "silver": "C0C0C0", "skyblue": "87CEEB", "slateblue": "6A5ACD",
    "slategray": "708090", "slategrey": "708090", "snow": "FFFAFA",
    "springgreen": "00FF7F", "steelblue": "4682B4", "tan": "D2B48C",
    "teal": "008080", "thistle": "D8BFD8", "tomato": "FF6347",
    "turquoise": "40E0D0", "violet": "EE82EE", "wheat": "F5DEB3",
    "white": "FFFFFF", "whitesmoke": "F5F5F5", "yellow": "FFFF00",
    "yellowgreen": "9ACD32",
}


def _hex_to_rgb(hex6: str) -> tuple[int, int, int]:
    return tuple(int(hex6[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[int, int, int]:
    rf, gf, bf = r / 255, g / 255, b / 255
    high, low = max(rf, gf, bf), min(rf, gf, bf)
    light = (high + low) / 2
    if high == low:
        return 0, 0, round(light * 100)
    delta = high - low
    sat = delta / (2 - high - low) if light > 0.5 else delta / (high + low)
    if high == rf:
        hue = (gf - bf) / delta + (6 if gf < bf else 0)
    elif high == gf:
        hue = (bf - rf) / delta + 2
    else:
        hue = (rf - gf) / delta + 4
    return round(hue * 60), round(sat * 100), round(light * 100)


def _rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100
    rf, gf, bf = r / 255, g / 255, b / 255
    k = 1 - max(rf, gf, bf)
    c = (1 - rf - k) / (1 - k)
    m = (1 - gf - k) / (1 - k)
    y = (1 - bf - k) / (1 - k)
    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)


def _text_on(hex6: str) -> str:
    r, g, b = _hex_to_rgb(hex6)
    # Perceived luminance; pick black or white text for the swatch label.
    return "#000" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#fff"


def build_color_cluster() -> PseoCluster:
    pages: list[PseoPage] = []
    for name, hex6 in CSS_COLORS.items():
        r, g, b = _hex_to_rgb(hex6)
        h, s, light = _rgb_to_hsl(r, g, b)
        c, m, y, k = _rgb_to_cmyk(r, g, b)
        rgb = f"rgb({r}, {g}, {b})"
        hsl = f"hsl({h}, {s}%, {light}%)"
        cmyk = f"cmyk({c}%, {m}%, {y}%, {k}%)"
        hexv = f"#{hex6}"
        pretty = name.title()
        body = f"""
        <div class="swatch" style="background:{hexv};color:{_text_on(hex6)}">{escape(hexv)}</div>
        <h2>Hex</h2>
        <pre class="expr">{escape(hexv)}</pre>
        <button class="copy" onclick="navigator.clipboard.writeText('{hexv}')">Copy hex</button>
        <h2>Conversions</h2>
        <table>
          <tr><th>RGB</th><td>{escape(rgb)}</td></tr>
          <tr><th>HSL</th><td>{escape(hsl)}</td></tr>
          <tr><th>CMYK</th><td>{escape(cmyk)}</td></tr>
        </table>
        <h2>CSS</h2>
        <pre>color: {escape(name)};   /* or {escape(hexv)} */
background-color: {escape(hexv)};</pre>
        <p class="notice">Need this exact color in your UI? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=name,
                title=f"{pretty} color — {hexv} hex, RGB, HSL & CMYK codes",
                h1=f"{pretty} — {hexv}",
                lead=f"The CSS color “{name}” is {hexv}. Here are its RGB, HSL, and CMYK values, a live swatch, and copy-paste CSS.",
                body=body,
                related_label=name,
            )
        )
    return PseoCluster(
        key="color",
        title="CSS color reference",
        intro=f"{len(pages)} CSS named colors with hex, RGB, HSL, and CMYK values plus copy-paste CSS for each.",
        pages=tuple(pages),
    )


# ---------------------------------------------------------------------------
# Ports — common TCP/UDP ports
# ---------------------------------------------------------------------------

# (port, protocol, service, description)
COMMON_PORTS: list[tuple[int, str, str, str]] = [
    (20, "TCP", "FTP (data)", "File Transfer Protocol data channel."),
    (21, "TCP", "FTP (control)", "File Transfer Protocol command channel — unencrypted."),
    (22, "TCP", "SSH", "Secure Shell remote login, SCP, and SFTP."),
    (23, "TCP", "Telnet", "Unencrypted remote login. Legacy and insecure."),
    (25, "TCP", "SMTP", "Sending mail between servers."),
    (53, "TCP/UDP", "DNS", "Domain Name System name resolution."),
    (67, "UDP", "DHCP (server)", "Dynamic Host Configuration Protocol server."),
    (68, "UDP", "DHCP (client)", "DHCP client."),
    (69, "UDP", "TFTP", "Trivial File Transfer Protocol."),
    (80, "TCP", "HTTP", "Unencrypted web traffic."),
    (110, "TCP", "POP3", "Retrieving email (download-and-delete)."),
    (111, "TCP/UDP", "RPCbind", "ONC RPC portmapper."),
    (123, "UDP", "NTP", "Network Time Protocol clock synchronization."),
    (135, "TCP", "MS RPC", "Microsoft RPC endpoint mapper."),
    (137, "UDP", "NetBIOS Name", "NetBIOS name service."),
    (138, "UDP", "NetBIOS Datagram", "NetBIOS datagram service."),
    (139, "TCP", "NetBIOS Session", "NetBIOS session service."),
    (143, "TCP", "IMAP", "Reading email with server-side sync."),
    (161, "UDP", "SNMP", "Simple Network Management Protocol."),
    (162, "UDP", "SNMP Trap", "SNMP notifications."),
    (179, "TCP", "BGP", "Border Gateway Protocol routing."),
    (194, "TCP", "IRC", "Internet Relay Chat."),
    (389, "TCP", "LDAP", "Directory services (unencrypted)."),
    (443, "TCP", "HTTPS", "Encrypted web traffic over TLS."),
    (445, "TCP", "SMB", "Windows file sharing (CIFS/SMB)."),
    (465, "TCP", "SMTPS", "SMTP over implicit TLS."),
    (500, "UDP", "IKE / IPsec", "VPN key exchange."),
    (514, "UDP", "Syslog", "Remote system logging."),
    (515, "TCP", "LPD", "Line Printer Daemon."),
    (520, "UDP", "RIP", "Routing Information Protocol."),
    (548, "TCP", "AFP", "Apple Filing Protocol."),
    (554, "TCP", "RTSP", "Streaming media control."),
    (587, "TCP", "SMTP (submission)", "Mail submission with STARTTLS."),
    (631, "TCP", "IPP / CUPS", "Internet Printing Protocol."),
    (636, "TCP", "LDAPS", "LDAP over TLS."),
    (873, "TCP", "rsync", "rsync file synchronization daemon."),
    (989, "TCP", "FTPS (data)", "FTP data over TLS."),
    (990, "TCP", "FTPS (control)", "FTP control over TLS."),
    (993, "TCP", "IMAPS", "IMAP over TLS."),
    (995, "TCP", "POP3S", "POP3 over TLS."),
    (1025, "TCP", "MailHog SMTP", "Common local mail-catcher SMTP port."),
    (1080, "TCP", "SOCKS proxy", "SOCKS proxy server."),
    (1194, "UDP", "OpenVPN", "OpenVPN tunnel."),
    (1433, "TCP", "MS SQL Server", "Microsoft SQL Server database."),
    (1521, "TCP", "Oracle DB", "Oracle database listener."),
    (1723, "TCP", "PPTP", "Point-to-Point Tunneling Protocol VPN."),
    (1883, "TCP", "MQTT", "Lightweight IoT messaging broker."),
    (1900, "UDP", "SSDP / UPnP", "Service discovery for UPnP devices."),
    (2049, "TCP", "NFS", "Network File System."),
    (2082, "TCP", "cPanel", "cPanel web hosting control panel."),
    (2083, "TCP", "cPanel (SSL)", "cPanel over TLS."),
    (2181, "TCP", "ZooKeeper", "Apache ZooKeeper client port."),
    (2375, "TCP", "Docker API", "Unencrypted Docker daemon — dangerous if exposed."),
    (2376, "TCP", "Docker API (TLS)", "Docker daemon over TLS."),
    (3000, "TCP", "Dev server", "Common Node/React/Next.js/Rails/Grafana dev port."),
    (3001, "TCP", "Dev server (alt)", "Alternate local development server."),
    (3306, "TCP", "MySQL", "MySQL / MariaDB database server."),
    (3389, "TCP", "RDP", "Windows Remote Desktop Protocol."),
    (3478, "UDP", "STUN / TURN", "WebRTC NAT traversal."),
    (4000, "TCP", "Dev server", "Common Phoenix / dev HTTP server."),
    (4200, "TCP", "Angular dev server", "ng serve default port."),
    (5000, "TCP", "Dev server", "Flask default and macOS AirPlay Receiver."),
    (5060, "UDP", "SIP", "VoIP call signaling."),
    (5061, "TCP", "SIP-TLS", "Encrypted SIP signaling."),
    (5173, "TCP", "Vite dev server", "Default Vite development server."),
    (5432, "TCP", "PostgreSQL", "PostgreSQL database server."),
    (5439, "TCP", "Amazon Redshift", "Redshift data warehouse."),
    (5601, "TCP", "Kibana", "Elastic Kibana dashboard."),
    (5672, "TCP", "AMQP / RabbitMQ", "RabbitMQ message broker."),
    (5900, "TCP", "VNC", "Virtual Network Computing remote desktop."),
    (5984, "TCP", "CouchDB", "Apache CouchDB HTTP API."),
    (6379, "TCP", "Redis", "Redis in-memory data store — never expose publicly."),
    (6443, "TCP", "Kubernetes API", "Kubernetes API server."),
    (6667, "TCP", "IRC", "Internet Relay Chat."),
    (7077, "TCP", "Spark master", "Apache Spark master."),
    (8000, "TCP", "Dev / HTTP alt", "Django runserver and general dev HTTP."),
    (8025, "TCP", "MailHog UI", "MailHog web interface."),
    (8080, "TCP", "HTTP alt / proxy", "Alternate HTTP, proxies, Tomcat, dev servers."),
    (8081, "TCP", "HTTP alt", "Secondary HTTP / Nexus / dev."),
    (8086, "TCP", "InfluxDB", "InfluxDB HTTP API."),
    (8443, "TCP", "HTTPS alt", "Alternate HTTPS (Tomcat SSL, dev)."),
    (8500, "TCP", "Consul", "HashiCorp Consul HTTP API."),
    (8888, "TCP", "Jupyter / HTTP alt", "Jupyter Notebook and alternate HTTP."),
    (9000, "TCP", "PHP-FPM / MinIO", "PHP-FPM, SonarQube, MinIO."),
    (9090, "TCP", "Prometheus", "Prometheus metrics server."),
    (9092, "TCP", "Kafka", "Apache Kafka broker."),
    (9100, "TCP", "Node Exporter", "Prometheus node exporter / raw printing."),
    (9200, "TCP", "Elasticsearch", "Elasticsearch HTTP API."),
    (9300, "TCP", "Elasticsearch (transport)", "Elasticsearch node transport."),
    (9418, "TCP", "Git protocol", "Native git:// protocol."),
    (10000, "TCP", "Webmin", "Webmin server administration."),
    (11211, "TCP", "Memcached", "Memcached cache — never expose publicly."),
    (15672, "TCP", "RabbitMQ UI", "RabbitMQ management interface."),
    (27017, "TCP", "MongoDB", "MongoDB database server."),
    (27018, "TCP", "MongoDB (shard)", "MongoDB shard server."),
    (50000, "TCP", "SAP / Dev", "SAP and assorted dev services."),
    (88, "TCP", "Kerberos", "Kerberos network authentication."),
    (119, "TCP", "NNTP", "Usenet news transfer."),
    (1812, "UDP", "RADIUS", "RADIUS authentication."),
    (2222, "TCP", "SSH (alt)", "Common alternate SSH port."),
    (3260, "TCP", "iSCSI", "iSCSI storage target."),
    (5353, "UDP", "mDNS", "Multicast DNS / Bonjour service discovery."),
    (5555, "TCP", "ADB / Dev", "Android Debug Bridge and dev servers."),
    (7474, "TCP", "Neo4j", "Neo4j graph database HTTP browser."),
    (8161, "TCP", "ActiveMQ UI", "ActiveMQ web console."),
    (9999, "TCP", "Dev / misc", "Common miscellaneous and dev port."),
]

# Ports that should essentially never be exposed to the public internet.
_DANGEROUS_PORTS = {23, 2375, 3389, 5432, 3306, 6379, 11211, 27017, 9200, 5984, 1433}


def build_port_cluster() -> PseoCluster:
    pages: list[PseoPage] = []
    for port, proto, service, desc in COMMON_PORTS:
        if port in _DANGEROUS_PORTS:
            safety = (
                f"Port {port} exposes {service}, which has no authentication boundary "
                "suitable for the open internet. Bind it to localhost or put it behind "
                "a firewall/VPN — never expose it publicly."
            )
        else:
            safety = (
                f"Opening port {port} is only safe if you intend to run {service} there. "
                "Close it on hosts that don't need it and prefer the encrypted variant where one exists."
            )
        body = f"""
        <h2>What runs on port {port}?</h2>
        <p>Port <strong>{port}/{escape(proto)}</strong> is the standard port for <strong>{escape(service)}</strong>. {escape(desc)}</p>
        <table>
          <tr><th>Port</th><td>{port}</td></tr>
          <tr><th>Protocol</th><td>{escape(proto)}</td></tr>
          <tr><th>Service</th><td>{escape(service)}</td></tr>
        </table>
        <h2>Is port {port} safe to open?</h2>
        <p>{escape(safety)}</p>
        <h2>Check it</h2>
        <pre># is anything listening on {port}?
nc -vz HOST {port}
# what is using it locally?
lsof -i :{port}</pre>
        <p class="notice">Wiring up a server, firewall, or webhook? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=f"port-{port}",
                title=f"Port {port} ({proto}) — what runs on it and is it safe?",
                h1=f"Port {port}: {service}",
                lead=f"Port {port}/{proto} is the standard port for {service}. {desc}",
                body=body,
                related_label=f"port {port} — {service}",
            )
        )
    return PseoCluster(
        key="port",
        title="Network port reference",
        intro=f"{len(pages)} common TCP/UDP ports — what service runs on each, and whether it is safe to expose.",
        pages=tuple(pages),
    )


# ---------------------------------------------------------------------------
# Emoji — common emoji meanings
# ---------------------------------------------------------------------------

# (character, name, keywords)
COMMON_EMOJI: list[tuple[str, str, str]] = [
    ("\U0001F525", "fire", "hot, lit, flame, trending"),
    ("\U0001F602", "face with tears of joy", "laughing, lol, haha, funny"),
    ("❤️", "red heart", "love, like, romance"),
    ("\U0001F60D", "smiling face with heart-eyes", "love, crush, adore"),
    ("\U0001F64F", "folded hands", "please, thank you, pray, high five"),
    ("\U0001F62D", "loudly crying face", "sob, bawling, crying"),
    ("\U0001F60A", "smiling face with smiling eyes", "happy, blush, content"),
    ("✨", "sparkles", "shiny, clean, magic, new"),
    ("\U0001F618", "face blowing a kiss", "kiss, love, flirt"),
    ("\U0001F44D", "thumbs up", "ok, approve, yes, good"),
    ("\U0001F44E", "thumbs down", "no, disapprove, bad"),
    ("\U0001F389", "party popper", "celebrate, congrats, tada"),
    ("\U0001F480", "skull", "dead, dying laughing, scared"),
    ("\U0001F605", "grinning face with sweat", "nervous, phew, relief"),
    ("\U0001F914", "thinking face", "hmm, thinking, doubt"),
    ("\U0001F970", "smiling face with hearts", "adore, love, in love"),
    ("\U0001F60E", "smiling face with sunglasses", "cool, confident, deal with it"),
    ("\U0001F644", "face with rolling eyes", "annoyed, whatever, sarcasm"),
    ("\U0001F60F", "smirking face", "smug, flirt, suggestive"),
    ("\U0001F622", "crying face", "sad, tear, disappointed"),
    ("\U0001F621", "enraged face", "angry, mad, furious"),
    ("\U0001F923", "rolling on the floor laughing", "rofl, lmao, hilarious"),
    ("\U0001F440", "eyes", "looking, watching, suspicious"),
    ("\U0001F494", "broken heart", "heartbreak, sad, breakup"),
    ("\U0001F495", "two hearts", "love, like, affection"),
    ("\U0001F64C", "raising hands", "praise, celebrate, hooray"),
    ("\U0001F44F", "clapping hands", "applause, bravo, well done"),
    ("\U0001F937", "person shrugging", "idk, whatever, no idea"),
    ("\U0001F634", "sleeping face", "tired, sleep, boring"),
    ("\U0001F926", "person facepalming", "facepalm, ugh, disbelief"),
    ("\U0001F4AA", "flexed biceps", "strong, gym, power"),
    ("\U0001FAF6", "heart hands", "love, support, care"),
    ("\U0001F91D", "handshake", "deal, agreement, partnership"),
    ("\U0001F973", "partying face", "birthday, celebrate, party"),
    ("\U0001F62C", "grimacing face", "awkward, yikes, eek"),
    ("\U0001F629", "weary face", "tired, ugh, done"),
    ("\U0001F624", "face with steam from nose", "frustrated, proud, triumph"),
    ("\U0001F97A", "pleading face", "puppy eyes, please, beg"),
    ("\U0001F606", "grinning squinting face", "laugh, haha, joy"),
    ("\U0001F609", "winking face", "wink, joking, flirt"),
    ("\U0001F60B", "face savoring food", "yum, tasty, delicious"),
    ("\U0001F61C", "winking face with tongue", "playful, silly, joking"),
    ("\U0001F92A", "zany face", "crazy, goofy, wild"),
    ("\U0001F607", "smiling face with halo", "innocent, angel, good"),
    ("\U0001F979", "face holding back tears", "touched, proud, emotional"),
    ("\U0001F631", "face screaming in fear", "shocked, scared, home alone"),
    ("\U0001F633", "flushed face", "embarrassed, shocked, blushing"),
    ("\U0001F976", "cold face", "freezing, cold, frozen"),
    ("\U0001F975", "hot face", "hot, sweating, overheated"),
    ("\U0001F92F", "exploding head", "mind blown, shocked, wow"),
    ("\U0001F917", "smiling face with open hands", "hug, embrace, comfort"),
    ("\U0001F910", "zipper-mouth face", "secret, quiet, sealed lips"),
    ("\U0001F610", "neutral face", "meh, blank, no comment"),
    ("\U0001F636", "face without mouth", "speechless, silent, blank"),
    ("\U0001F643", "upside-down face", "sarcasm, irony, silly"),
    ("\U0001F600", "grinning face", "smile, happy, cheerful"),
    ("\U0001F604", "grinning face with smiling eyes", "happy, joy, laugh"),
    ("\U0001F601", "beaming face with smiling eyes", "grin, happy, cheesy"),
    ("\U0001F929", "star-struck", "amazed, wow, starry eyes"),
    ("\U0001F608", "smiling face with horns", "mischief, devil, sly"),
    ("\U0001F47B", "ghost", "spooky, boo, halloween"),
    ("\U0001F916", "robot", "bot, ai, machine"),
    ("\U0001F4A9", "pile of poo", "poop, crap, bad"),
    ("\U0001F44C", "OK hand", "ok, perfect, great"),
    ("\U0001F919", "call me hand", "hang loose, shaka, call"),
    ("✌️", "victory hand", "peace, victory, two"),
    ("\U0001F91E", "crossed fingers", "good luck, hope, wish"),
    ("\U0001F44B", "waving hand", "hi, bye, hello, wave"),
    ("\U0001F4AF", "hundred points", "100, perfect, agree, keep it real"),
    ("✅", "check mark button", "done, yes, correct, complete"),
    ("❌", "cross mark", "no, wrong, cancel, error"),
    ("⭐", "star", "favorite, rating, like"),
    ("\U0001F31F", "glowing star", "shine, special, sparkle"),
    ("⚡", "high voltage", "fast, power, energy, lightning"),
    ("\U0001F680", "rocket", "launch, fast, growth, to the moon"),
    ("\U0001F4A1", "light bulb", "idea, insight, bright"),
    ("\U0001F4CC", "pushpin", "pin, important, note"),
    ("\U0001F4CD", "round pushpin", "location, place, here"),
    ("\U0001F3AF", "direct hit", "target, goal, bullseye"),
    ("\U0001F3C6", "trophy", "win, champion, award"),
    ("\U0001F947", "1st place medal", "gold, winner, first"),
    ("\U0001F4B0", "money bag", "money, rich, cash"),
    ("\U0001F4B8", "money with wings", "spending, lost money, expensive"),
    ("\U0001F911", "money-mouth face", "rich, greedy, cash"),
    ("\U0001F381", "wrapped gift", "present, gift, birthday"),
    ("\U0001F4C8", "chart increasing", "growth, up, profit, gains"),
    ("\U0001F4C9", "chart decreasing", "loss, down, decline"),
    ("\U0001F512", "locked", "secure, private, closed"),
    ("\U0001F513", "unlocked", "open, insecure, unlock"),
    ("\U0001F511", "key", "password, access, unlock"),
    ("⚠️", "warning", "caution, alert, danger"),
    ("\U0001F6A8", "police car light", "alert, emergency, urgent"),
    ("\U0001F6D1", "stop sign", "stop, halt, no"),
    ("\U0001F4A5", "collision", "boom, explosion, impact"),
    ("\U0001F451", "crown", "king, queen, best, royalty"),
    ("\U0001F308", "rainbow", "pride, colorful, hope"),
    ("☀️", "sun", "sunny, weather, hot"),
    ("\U0001F319", "crescent moon", "night, sleep, moon"),
    ("⏰", "alarm clock", "time, wake up, reminder"),
    ("\U0001F4F1", "mobile phone", "phone, mobile, smartphone"),
    ("\U0001F4BB", "laptop", "computer, work, coding"),
    ("\U0001F5A5️", "desktop computer", "computer, pc, monitor"),
    ("⌨️", "keyboard", "typing, keys, input"),
    ("\U0001F41B", "bug", "bug, error, defect, insect"),
    ("\U0001F30D", "globe showing europe-africa", "world, earth, global"),
    ("\U0001F3B5", "musical note", "music, song, sound"),
    ("\U0001F50A", "speaker high volume", "loud, sound, volume"),
    ("\U0001F4E2", "loudspeaker", "announce, shout, news"),
    ("☕", "hot beverage", "coffee, tea, break"),
    ("\U0001F355", "pizza", "food, pizza, hungry"),
    ("\U0001F37A", "beer mug", "beer, drink, cheers"),
    ("\U0001F382", "birthday cake", "birthday, cake, celebrate"),
    ("\U0001F339", "rose", "flower, love, romance"),
    ("\U0001F436", "dog face", "dog, puppy, pet"),
    ("\U0001F431", "cat face", "cat, kitten, pet"),
    ("\U0001F914", "thinking", "hmm, doubt, consider"),
]


def _codepoints(char: str) -> str:
    return " ".join(f"U+{ord(c):04X}" for c in char)


def build_emoji_cluster() -> PseoCluster:
    pages: list[PseoPage] = []
    seen: set[str] = set()
    for char, name, keywords in COMMON_EMOJI:
        slug = _slug(name)
        if slug in seen:
            continue
        seen.add(slug)
        codepoints = _codepoints(char)
        html_entity = "".join(f"&#x{ord(c):X};" for c in char)
        body = f"""
        <div class="emoji-hero">{char}</div>
        <button class="copy" onclick="navigator.clipboard.writeText('{char}')">Copy {char}</button>
        <h2>Meaning</h2>
        <p>The {escape(name)} emoji {char} commonly means: {escape(keywords)}.</p>
        <h2>Details</h2>
        <table>
          <tr><th>Name</th><td>{escape(name)}</td></tr>
          <tr><th>Code points</th><td>{escape(codepoints)}</td></tr>
          <tr><th>HTML</th><td><code>{escape(html_entity)}</code></td></tr>
          <tr><th>Keywords</th><td>{escape(keywords)}</td></tr>
        </table>
        <p class="notice">Building something with text, search, or unicode? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{char} {name} emoji — meaning, copy & paste, code points",
                h1=f"{char} {name}",
                lead=f"The {name} emoji {char} ({codepoints}) means {keywords}. Copy and paste it, or grab its unicode and HTML code.",
                body=body,
                related_label=f"{char} {name}",
            )
        )
    return PseoCluster(
        key="emoji",
        title="Emoji meanings",
        intro=f"{len(pages)} common emoji with their meaning, code points, and one-click copy.",
        pages=tuple(pages),
    )


# ---------------------------------------------------------------------------
# ASCII — one page per ASCII code (0-127)
# ---------------------------------------------------------------------------

_ASCII_CONTROL: dict[int, str] = {
    0: "NUL (null)", 1: "SOH (start of heading)", 2: "STX (start of text)",
    3: "ETX (end of text)", 4: "EOT (end of transmission)", 5: "ENQ (enquiry)",
    6: "ACK (acknowledge)", 7: "BEL (bell)", 8: "BS (backspace)",
    9: "HT (horizontal tab)", 10: "LF (line feed / newline)", 11: "VT (vertical tab)",
    12: "FF (form feed)", 13: "CR (carriage return)", 14: "SO (shift out)",
    15: "SI (shift in)", 16: "DLE (data link escape)", 17: "DC1 (device control 1)",
    18: "DC2 (device control 2)", 19: "DC3 (device control 3)", 20: "DC4 (device control 4)",
    21: "NAK (negative acknowledge)", 22: "SYN (synchronous idle)", 23: "ETB (end of block)",
    24: "CAN (cancel)", 25: "EM (end of medium)", 26: "SUB (substitute)",
    27: "ESC (escape)", 28: "FS (file separator)", 29: "GS (group separator)",
    30: "RS (record separator)", 31: "US (unit separator)", 127: "DEL (delete)",
}


def build_ascii_cluster() -> PseoCluster:
    pages: list[PseoPage] = []
    for code in range(128):
        if code in _ASCII_CONTROL:
            name = _ASCII_CONTROL[code]
            display = name.split(" ", 1)[0]
            printable = False
        elif code == 32:
            name, display, printable = "Space", "(space)", True
        else:
            name = display = chr(code)
            printable = True
        char_cell = display if printable else f"<em>{escape(display)}</em>"
        html_entity = f"&#{code};"
        kind = "printable character" if printable else "control character"
        body = f"""
        <h2>ASCII {code}</h2>
        <p>Decimal <strong>{code}</strong> is the {escape(kind)} <strong>{escape(name)}</strong>.</p>
        <table>
          <tr><th>Character</th><td>{char_cell}</td></tr>
          <tr><th>Decimal</th><td>{code}</td></tr>
          <tr><th>Hex</th><td>0x{code:02X}</td></tr>
          <tr><th>Octal</th><td>0o{code:03o}</td></tr>
          <tr><th>Binary</th><td>{code:08b}</td></tr>
          <tr><th>HTML</th><td><code>{escape(html_entity)}</code></td></tr>
        </table>
        <h2>In code</h2>
        <pre>chr({code})   # Python
String.fromCharCode({code})   // JavaScript
'\\x{code:02x}'   # escape</pre>
        <p class="notice">Working with text, encoding, or unicode? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=f"ascii-{code}",
                title=f"ASCII {code} — {name}: hex, binary, octal & HTML code",
                h1=f"ASCII {code}: {name}",
                lead=f"ASCII code {code} is {name}. Decimal {code}, hex 0x{code:02X}, binary {code:08b}, HTML &#{code};.",
                body=body,
                related_label=f"{code} — {display}",
            )
        )
    return PseoCluster(
        key="ascii",
        title="ASCII table reference",
        intro=f"{len(pages)} ASCII codes (0-127) with the character, decimal, hex, octal, binary, and HTML code for each.",
        pages=tuple(pages),
    )


# ---------------------------------------------------------------------------
# HTML entities — one page per named HTML entity (from Python's built-in table)
# ---------------------------------------------------------------------------

def build_html_entity_cluster() -> PseoCluster:
    from html.entities import codepoint2name

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for codepoint, name in sorted(codepoint2name.items()):
        slug = f"entity-{name.lower()}"
        if slug in seen or not name.isalnum():
            continue
        seen.add(slug)
        char = chr(codepoint)
        visible = char.strip() != "" and codepoint not in (160, 173)
        display = char if visible else f"({name})"
        named_ref = f"&{name};"
        numeric_ref = f"&#{codepoint};"
        hex_ref = f"&#x{codepoint:X};"
        body = f"""
        <div class="emoji-hero">{escape(char) if visible else escape(display)}</div>
        <button class="copy" onclick="navigator.clipboard.writeText('{escape(char)}')">Copy {escape(display)}</button>
        <h2>The {escape(named_ref)} HTML entity</h2>
        <p>The named character reference <code>{escape(named_ref)}</code> renders the character <strong>{escape(display)}</strong> (Unicode U+{codepoint:04X}).</p>
        <table>
          <tr><th>Named entity</th><td><code>{escape(named_ref)}</code></td></tr>
          <tr><th>Numeric (decimal)</th><td><code>{escape(numeric_ref)}</code></td></tr>
          <tr><th>Numeric (hex)</th><td><code>{escape(hex_ref)}</code></td></tr>
          <tr><th>Unicode</th><td>U+{codepoint:04X}</td></tr>
        </table>
        <p class="notice">Building web pages or escaping text? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{named_ref} HTML entity — the {display} character ({numeric_ref})",
                h1=f"{named_ref} ({display})",
                lead=f"The HTML entity {named_ref} renders {display} (U+{codepoint:04X}). Use {named_ref}, {numeric_ref}, or {hex_ref}.",
                body=body,
                related_label=f"{named_ref} {display}",
            )
        )
    return PseoCluster(
        key="html-entity",
        title="HTML entity reference",
        intro=f"{len(pages)} HTML named character entities with their symbol, named, decimal, and hex references.",
        pages=tuple(pages),
    )


# ---------------------------------------------------------------------------
# Reference clusters from vetted datasets (HTTP codes, MIME, headers, exit codes)
# ---------------------------------------------------------------------------

def build_http_status_cluster() -> PseoCluster:
    from .pseo_data_batch_a import HTTP_STATUS

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in HTTP_STATUS:
        code, name = entry["code"], entry["name"]
        slug = f"http-{code}"
        if slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>What does HTTP {code} mean?</h2>
        <p><strong>{code} {escape(name)}</strong> — {escape(entry["description"])}</p>
        <table>
          <tr><th>Status code</th><td>{code}</td></tr>
          <tr><th>Reason phrase</th><td>{escape(name)}</td></tr>
          <tr><th>Category</th><td>{escape(entry["category"])}</td></tr>
        </table>
        <p class="notice">Debugging an API, redirect, or webhook? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"HTTP {code} {name} — what it means and when it happens",
                h1=f"HTTP {code} — {name}",
                lead=f"HTTP status code {code} {name}: {entry['description']}",
                body=body,
                related_label=f"{code} {name}",
            )
        )
    return PseoCluster(
        key="http-status",
        title="HTTP status code reference",
        intro=f"{len(pages)} HTTP status codes explained — what each means and when a server returns it.",
        pages=tuple(pages),
    )


def build_mime_cluster() -> PseoCluster:
    from .pseo_data_batch_a import MIME_TYPES

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in MIME_TYPES:
        ext = entry["ext"].lower().lstrip(".")
        mime = entry["mime"]
        slug = _slug(ext)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>What is the .{escape(ext)} MIME type?</h2>
        <p>The MIME type (media type) for a <strong>.{escape(ext)}</strong> file is <strong>{escape(mime)}</strong>. {escape(entry["description"])}</p>
        <pre class="expr">{escape(mime)}</pre>
        <button class="copy" onclick="navigator.clipboard.writeText('{mime}')">Copy MIME type</button>
        <table>
          <tr><th>Extension</th><td>.{escape(ext)}</td></tr>
          <tr><th>MIME type</th><td>{escape(mime)}</td></tr>
          <tr><th>Kind</th><td>{escape(entry["kind"])}</td></tr>
        </table>
        <h2>Serve it with the right header</h2>
        <pre>Content-Type: {escape(mime)}</pre>
        <p class="notice">Setting up uploads, downloads, or a server? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f".{ext} MIME type — {mime}",
                h1=f".{ext} files — {mime}",
                lead=f"The MIME type for .{ext} files is {mime}. {entry['description']}",
                body=body,
                related_label=f".{ext} — {mime}",
            )
        )
    return PseoCluster(
        key="mime",
        title="MIME type reference",
        intro=f"{len(pages)} file extensions mapped to their MIME (media) type for Content-Type headers, uploads, and downloads.",
        pages=tuple(pages),
    )


def build_http_header_cluster() -> PseoCluster:
    from .pseo_data_batch_a import HTTP_HEADERS

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in HTTP_HEADERS:
        name = entry["name"]
        slug = _slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>The {escape(name)} header</h2>
        <p>{escape(entry["description"])}</p>
        <table>
          <tr><th>Header</th><td>{escape(name)}</td></tr>
          <tr><th>Direction</th><td>{escape(entry["direction"])}</td></tr>
        </table>
        <h2>Example</h2>
        <pre>{escape(name)}: {escape(entry["example"])}</pre>
        <p class="notice">Configuring CORS, caching, or security headers? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{name} header — what it does, with an example",
                h1=f"{name}",
                lead=f"The {name} HTTP header ({entry['direction'].lower()}): {entry['description']}",
                body=body,
                related_label=name,
            )
        )
    return PseoCluster(
        key="header",
        title="HTTP header reference",
        intro=f"{len(pages)} HTTP request and response headers explained with real examples.",
        pages=tuple(pages),
    )


def build_exit_code_cluster() -> PseoCluster:
    from .pseo_data_batch_a import EXIT_SIGNALS

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in EXIT_SIGNALS:
        number, label, kind = entry["number"], entry["label"], entry["kind"]
        if kind == "signal":
            slug = f"signal-{_slug(label)}"
            title = f"{label} (signal {number}) — meaning and cause"
            h1 = f"{label} — signal {number}"
            heading = f"What is {label} (signal {number})?"
            lead = f"{label} is Unix signal {number}: {entry['description']}"
            related = f"{label} (sig {number})"
            row_label = "Signal number"
        else:
            slug = f"exit-code-{number}"
            title = f"Exit code {number} — {label}"
            h1 = f"Exit code {number}: {label}"
            heading = f"What does exit code {number} mean?"
            lead = f"Exit code {number} ({label}): {entry['description']}"
            related = f"exit {number} — {label}"
            row_label = "Exit code"
        if slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>{escape(heading)}</h2>
        <p>{escape(entry["description"])}</p>
        <table>
          <tr><th>{row_label}</th><td>{number}</td></tr>
          <tr><th>Name</th><td>{escape(label)}</td></tr>
        </table>
        <p class="notice">Debugging a crash, container, or CI failure? {{cta}}</p>
        """
        pages.append(
            PseoPage(slug=slug, title=title, h1=h1, lead=lead, body=body, related_label=related)
        )
    return PseoCluster(
        key="exit",
        title="Exit codes & signals reference",
        intro=f"{len(pages)} Unix exit codes and signals explained — what each means and what causes it.",
        pages=tuple(pages),
    )


def build_country_cluster() -> PseoCluster:
    from .pseo_data_iso import COUNTRIES

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in COUNTRIES:
        name = entry["name"]
        slug = _slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        iso2, iso3, dialing = entry["iso2"], entry["iso3"], entry["dialing"]
        body = f"""
        <h2>{escape(name)} country codes</h2>
        <table>
          <tr><th>ISO alpha-2</th><td>{escape(iso2)}</td></tr>
          <tr><th>ISO alpha-3</th><td>{escape(iso3)}</td></tr>
          <tr><th>ISO numeric</th><td>{escape(str(entry["numeric"]))}</td></tr>
          <tr><th>Dialing code</th><td>{escape(dialing)}</td></tr>
          <tr><th>Capital</th><td>{escape(entry["capital"])}</td></tr>
          <tr><th>Region</th><td>{escape(entry["region"])}</td></tr>
        </table>
        <button class="copy" onclick="navigator.clipboard.writeText('{escape(iso2)}')">Copy {escape(iso2)}</button>
        <p class="notice">Building a form, address field, or phone input? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{name} country code — {iso2}, {iso3}, dialing {dialing}",
                h1=f"{name} — {iso2}",
                lead=f"{name}: ISO country code {iso2} (alpha-3 {iso3}), dialing code {dialing}, capital {entry['capital']}.",
                body=body,
                related_label=f"{name} ({iso2})",
            )
        )
    return PseoCluster(
        key="country",
        title="Country code reference",
        intro=f"{len(pages)} countries with ISO 3166 codes (alpha-2, alpha-3, numeric), dialing codes, and capitals.",
        pages=tuple(pages),
    )


def build_currency_cluster() -> PseoCluster:
    from .pseo_data_iso import CURRENCIES

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in CURRENCIES:
        code, name = entry["code"], entry["name"]
        slug = _slug(code)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        symbol = entry["symbol"]
        body = f"""
        <h2>{escape(code)} — {escape(name)}</h2>
        <table>
          <tr><th>Code</th><td>{escape(code)}</td></tr>
          <tr><th>Name</th><td>{escape(name)}</td></tr>
          <tr><th>Symbol</th><td>{escape(symbol)}</td></tr>
          <tr><th>ISO numeric</th><td>{escape(str(entry["numeric"]))}</td></tr>
          <tr><th>Used in</th><td>{escape(entry["used_in"])}</td></tr>
        </table>
        <button class="copy" onclick="navigator.clipboard.writeText('{escape(code)}')">Copy {escape(code)}</button>
        <p class="notice">Pricing, invoicing, or a checkout in {escape(code)}? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{code} — {name} currency code & symbol ({symbol})",
                h1=f"{code} — {name}",
                lead=f"{code} is the ISO 4217 currency code for the {name} ({symbol}), used in {entry['used_in']}.",
                body=body,
                related_label=f"{code} — {name}",
            )
        )
    return PseoCluster(
        key="currency",
        title="Currency code reference",
        intro=f"{len(pages)} world currencies with their ISO 4217 code, symbol, and where each is used.",
        pages=tuple(pages),
    )


def build_git_cluster() -> PseoCluster:
    from .pseo_data_devref import GIT_RECIPES

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in GIT_RECIPES:
        task, command = entry["task"], entry["command"]
        slug = _slug(task)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>{escape(task)}</h2>
        <p>{escape(entry["explanation"])}</p>
        <pre>{escape(command)}</pre>
        <p class="notice">Stuck in a git mess, or wiring up CI? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"How to {task[:1].lower()}{task[1:]} in Git",
                h1=task,
                lead=f"{task}: {entry['explanation']}",
                body=body,
                related_label=task,
            )
        )
    return PseoCluster(
        key="git",
        title="Git command recipes",
        intro=f"{len(pages)} copy-paste Git recipes for what developers actually google — undo, reset, branches, history, and recovery.",
        pages=tuple(pages),
    )


def build_regex_cluster() -> PseoCluster:
    from .pseo_data_devref import REGEX_PATTERNS

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in REGEX_PATTERNS:
        name, pattern = entry["name"], entry["pattern"]
        slug = _slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>Regex for {escape(name)}</h2>
        <p>{escape(entry["explanation"])}</p>
        <pre>{escape(pattern)}</pre>
        <table>
          <tr><th>Matches</th><td>{escape(name)}</td></tr>
          <tr><th>Example match</th><td><code>{escape(entry["example"])}</code></td></tr>
        </table>
        <p class="notice">Validating or extracting text? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"Regex for {name} — pattern and example",
                h1=f"Regex: {name}",
                lead=f"Regular expression to match {name.lower()}. {entry['explanation']}",
                body=body,
                related_label=name,
            )
        )
    return PseoCluster(
        key="regex",
        title="Regex pattern reference",
        intro=f"{len(pages)} ready-to-use regular expressions (email, URL, dates, and more) with examples and explanations.",
        pages=tuple(pages),
    )


def build_linux_cluster() -> PseoCluster:
    from .pseo_data_devref import LINUX_COMMANDS

    pages: list[PseoPage] = []
    seen: set[str] = set()
    for entry in LINUX_COMMANDS:
        name, command = entry["name"], entry["command"]
        slug = _slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        body = f"""
        <h2>{escape(name)}</h2>
        <p>{escape(entry["explanation"])}</p>
        <pre>{escape(command)}</pre>
        <p class="notice">Automating servers or CI on Linux? {{cta}}</p>
        """
        pages.append(
            PseoPage(
                slug=slug,
                title=f"{name} — Linux command explained",
                h1=name,
                lead=f"{name}: {entry['explanation']}",
                body=body,
                related_label=name,
            )
        )
    return PseoCluster(
        key="linux",
        title="Linux command reference",
        intro=f"{len(pages)} common Linux/Unix commands explained with copy-paste examples.",
        pages=tuple(pages),
    )


def build_all_clusters() -> list[PseoCluster]:
    return [
        build_emoji_cluster(),
        build_color_cluster(),
        build_port_cluster(),
        build_ascii_cluster(),
        build_html_entity_cluster(),
        build_http_status_cluster(),
        build_mime_cluster(),
        build_http_header_cluster(),
        build_exit_code_cluster(),
        build_country_cluster(),
        build_currency_cluster(),
        build_git_cluster(),
        build_regex_cluster(),
        build_linux_cluster(),
    ]


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------

class PseoClusterExporter:
    def __init__(
        self,
        output_dir: str | Path,
        cluster: PseoCluster,
        *,
        site_base_url: str = "",
        tools_path: str = "",
        offers_path: str = "",
        related_count: int = 8,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.cluster = cluster
        self.site_base_url = site_base_url.rstrip("/")
        self.tools_path = tools_path
        self.offers_path = offers_path
        self.related_count = related_count

    def export(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        pages = self.cluster.pages
        written: list[str] = []

        total = len(pages)
        for index, page in enumerate(pages):
            related = [pages[(index + offset) % total] for offset in range(1, self.related_count + 1)]
            page_dir = self.output_dir / page.slug
            page_dir.mkdir(parents=True, exist_ok=True)
            page_path = page_dir / "index.html"
            page_path.write_text(self._detail_page(page, related), encoding="utf-8")
            written.append(str(page_path))

        index_path = self.output_dir / "index.html"
        index_path.write_text(self._index_page(), encoding="utf-8")

        sitemap_path = self.output_dir / "sitemap.xml"
        sitemap_path.write_text(self._sitemap(), encoding="utf-8")

        return [str(index_path), str(sitemap_path), *written]

    def _detail_page(self, page: PseoPage, related: list[PseoPage]) -> str:
        body = page.body.replace("{cta}", self._tools_cta())
        related_html = "".join(
            f'<li><a href="../{escape(p.slug)}/">{escape(p.related_label)}</a></li>' for p in related
        )
        nav = self._nav(prefix="../")
        return self._page(
            page.title,
            f"""
            <main class="shell">
              <header class="topbar"><a href="../">{escape(self.cluster.title)}</a>{nav}</header>
              <article class="detail">
                <p class="channel">{escape(self.cluster.title)}</p>
                <h1>{page.h1}</h1>
                <p class="lead">{page.lead}</p>
                {body}
                <h2>Related</h2>
                <ul class="related">{related_html}</ul>
              </article>
            </main>
            """,
            description=_meta_description(page.lead),
            canonical=self._absolute_url(f"{page.slug}/"),
        )

    def _index_page(self) -> str:
        links = "".join(
            f'<li><a href="{escape(p.slug)}/">{escape(p.related_label)}</a></li>' for p in self.cluster.pages
        )
        nav = self._nav(prefix="")
        return self._page(
            f"{self.cluster.title} — {self.cluster.intro}",
            f"""
            <main class="shell">
              <header class="topbar"><strong>{escape(self.cluster.title)}</strong>{nav}</header>
              <section class="hero"><div>
                <h1>{escape(self.cluster.title)}</h1>
                <p>{escape(self.cluster.intro)}</p>
              </div></section>
              <section><ul class="list">{links}</ul></section>
            </main>
            """,
            description=_meta_description(self.cluster.intro),
            canonical=self._absolute_url(""),
        )

    def _nav(self, *, prefix: str) -> str:
        links = ['<a class="nav-link" href="' + prefix + '../">Home</a>'] if prefix else []
        if self.tools_path:
            links.append(f'<a class="nav-link" href="{escape(prefix + self.tools_path.lstrip("/"))}">Tools</a>')
        if self.offers_path:
            links.append(f'<a class="nav-link" href="{escape(prefix + self.offers_path.lstrip("/"))}">Offers</a>')
        return "".join(links)

    def _tools_cta(self) -> str:
        parts = []
        if self.tools_path:
            parts.append(f'<a href="../{escape(self.tools_path.lstrip("/"))}">try the free tools</a>')
        if self.offers_path:
            parts.append(f'<a href="../{escape(self.offers_path.lstrip("/"))}">see the setup offers</a>')
        return " or ".join(parts) if parts else "Explore the rest of the site."

    def _sitemap(self) -> str:
        paths = [""] + [f"{p.slug}/" for p in self.cluster.pages]
        urls = "\n".join(f"  <url><loc>{escape(self._absolute_url(path))}</loc></url>" for path in paths)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""

    def _absolute_url(self, path: str) -> str:
        normalized = path.strip().lstrip("/")
        if self.site_base_url:
            return f"{self.site_base_url}/{normalized}" if normalized else f"{self.site_base_url}/"
        return f"/{normalized}" if normalized else "/"

    def _head_meta(self, title: str, description: str, canonical: str) -> str:
        lines: list[str] = []
        if canonical:
            lines.append(f'  <link rel="canonical" href="{escape(canonical)}">')
            lines.append(f'  <meta property="og:url" content="{escape(canonical)}">')
        lines.append('  <meta property="og:type" content="article">')
        lines.append(f'  <meta property="og:title" content="{escape(title)}">')
        lines.append(f'  <meta property="og:description" content="{escape(description)}">')
        lines.append('  <meta name="twitter:card" content="summary">')
        ld: dict[str, str] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
        }
        if canonical:
            ld["url"] = canonical
            ld["mainEntityOfPage"] = canonical
        ld_json = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
        lines.append(f'  <script type="application/ld+json">{ld_json}</script>')
        return "\n".join(lines)

    def _page(self, title: str, body: str, *, description: str = "", canonical: str = "") -> str:
        desc = description or title
        head = self._head_meta(title, desc, canonical)
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(desc)}">
{head}
  <style>
    :root {{ color-scheme: light; --bg:#f7f7f3; --ink:#17201b; --muted:#5c665f; --line:#d8ddd5; --surface:#fff; --accent:#116a5b; --accent-soft:#e2f3ee; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Arial,Helvetica,sans-serif; line-height:1.5; }}
    a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    .shell {{ max-width:1000px; margin:0 auto; padding:24px 20px 56px; }}
    .topbar {{ display:flex; gap:16px; flex-wrap:wrap; padding:12px 0 24px; color:var(--muted); }}
    .nav-link {{ margin-left:auto; }} .topbar .nav-link ~ .nav-link {{ margin-left:0; }}
    .hero {{ padding:40px 0 28px; border-top:1px solid var(--line); }}
    h1 {{ margin:0; font-size:clamp(1.8rem,4vw,3.2rem); line-height:1.02; }}
    .lead {{ color:var(--muted); font-size:1.05rem; max-width:720px; }}
    .detail {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:26px; }}
    pre {{ background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:14px; white-space:pre-wrap; font-family:Consolas,monospace; }}
    pre.expr {{ font-size:1.3rem; font-weight:700; color:var(--accent); }}
    .channel {{ margin:0 0 8px; color:var(--accent); text-transform:uppercase; font-size:.78rem; font-weight:700; }}
    .related, .list {{ padding-left:20px; }}
    .list {{ columns:3; }}
    table {{ border-collapse:collapse; margin:8px 0; }}
    td, th {{ border:1px solid var(--line); padding:6px 12px; text-align:left; }}
    th {{ background:var(--bg); }}
    .swatch {{ display:flex; align-items:flex-end; padding:14px; height:120px; border-radius:8px; border:1px solid var(--line); font-weight:700; }}
    .emoji-hero {{ font-size:5rem; line-height:1.2; }}
    button.copy {{ background:var(--accent); color:#fff; border:0; border-radius:6px; padding:8px 14px; cursor:pointer; font-size:.9rem; margin:6px 0; }}
    .notice {{ background:var(--accent-soft); border:1px solid #b6dbd2; border-radius:8px; padding:14px 16px; }}
    section {{ margin-top:26px; }}
    @media (max-width:640px) {{ .list {{ columns:1; }} }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

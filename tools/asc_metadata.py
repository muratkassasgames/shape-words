#!/usr/bin/env python3
"""Fill the App Store Connect listing for Shape Words through the App Store Connect API.

Runs on Codemagic (workflow ios-metadata). The App Store Connect integration exposes
APP_STORE_CONNECT_ISSUER_ID, APP_STORE_CONNECT_KEY_IDENTIFIER and APP_STORE_CONNECT_PRIVATE_KEY.
Every step is best-effort: a failure is logged and the script moves on.
"""
import hashlib, json, os, runpy, sys, time
import jwt, requests

BUNDLE = "com.muratkassasgames.shapewords"
API = "https://api.appstoreconnect.apple.com"
PRIVACY = "https://muratkassasgames.github.io/shapewords/privacy.html"
SUPPORT = "https://muratkassasgames.github.io/shapewords/"
COPYRIGHT = "2026 Murat Kassas"
SHOTS = [f"store/ios/{i}.png" for i in range(1, 7)]

LOCALES = {  # App Store locale -> key in tools/listing.py
    "en-US": "en", "tr": "tr", "pt-BR": "pt", "es-ES": "es", "es-MX": "es",
    "de-DE": "de", "fr-FR": "fr", "zh-Hans": "zh",
}
TEXT = runpy.run_path("tools/listing.py")["L"]
NAME = runpy.run_path("tools/listing.py")["NAME"]

problems = []


def load_key():
    import base64, re
    raw = os.environ["APP_STORE_CONNECT_PRIVATE_KEY"].strip()
    for _ in range(3):  # Codemagic may pass @env:NAME / @file:PATH references
        if raw.startswith("@env:"):
            raw = os.environ[raw[5:]].strip()
        elif raw.startswith("@file:"):
            raw = open(os.path.expanduser(raw[6:])).read().strip()
        elif os.path.isfile(os.path.expanduser(raw)):
            raw = open(os.path.expanduser(raw)).read().strip()
    raw = raw.strip('"').strip("'").replace("\\n", "\n").replace("\r", "")
    if "BEGIN" not in raw:
        try:
            dec = base64.b64decode(raw).decode()
            if "BEGIN" in dec:
                raw = dec
        except Exception:
            pass
    body = re.sub(r"-----[A-Z ]+-----", "", raw)
    body = "".join(body.split())
    pem = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(body[i:i + 64] for i in range(0, len(body), 64)) + "\n-----END PRIVATE KEY-----\n"
    print("key: length", len(body), "chars", flush=True)
    return pem


KEY = load_key()


def token():
    key = KEY
    now = int(time.time())
    return jwt.encode({"iss": os.environ["APP_STORE_CONNECT_ISSUER_ID"], "iat": now, "exp": now + 1100,
                       "aud": "appstoreconnect-v1"}, key, algorithm="ES256",
                      headers={"kid": os.environ["APP_STORE_CONNECT_KEY_IDENTIFIER"], "typ": "JWT"})


def call(method, path, body=None, ok=(200, 201, 204)):
    r = requests.request(method, API + path, json=body, timeout=60,
                         headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    if r.status_code not in ok:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:600]}")
    return r.json() if r.text else {}


def step(name, fn):
    print(f"\n== {name}", flush=True)
    try:
        out = fn()
        print("   ok", flush=True)
        return out
    except Exception as e:  # keep going
        print("   FAILED:", e, flush=True)
        problems.append(f"{name}: {e}")


app = call("GET", f"/v1/apps?filter[bundleId]={BUNDLE}")["data"][0]
APP = app["id"]
print("app", APP, app["attributes"]["name"])


def content_rights():
    call("PATCH", f"/v1/apps/{APP}", {"data": {"type": "apps", "id": APP,
         "attributes": {"contentRightsDeclaration": "USES_THIRD_PARTY_CONTENT"}}})


step("Content rights", content_rights)

infos = call("GET", f"/v1/apps/{APP}/appInfos")["data"]
INFO = next((i for i in infos if i["attributes"].get("appStoreState") not in ("READY_FOR_SALE",)), infos[0])["id"]


def categories():
    rel = {"primaryCategory": {"data": {"type": "appCategories", "id": "EDUCATION"}},
           "secondaryCategory": {"data": {"type": "appCategories", "id": "GAMES"}},
           "secondarySubcategoryOne": {"data": {"type": "appCategories", "id": "GAMES_WORD"}},
           "secondarySubcategoryTwo": {"data": {"type": "appCategories", "id": "GAMES_PUZZLE"}}}
    call("PATCH", f"/v1/appInfos/{INFO}", {"data": {"type": "appInfos", "id": INFO, "relationships": rel}})


step("Categories (Education + Games/Word, Puzzle)", categories)


def info_localizations():
    have = {l["attributes"]["locale"]: l["id"] for l in
            call("GET", f"/v1/appInfos/{INFO}/appInfoLocalizations?limit=50")["data"]}
    for loc, k in LOCALES.items():
        attrs = {"name": NAME, "subtitle": TEXT[k]["sub"], "privacyPolicyUrl": PRIVACY}
        try:
            if loc in have:
                call("PATCH", f"/v1/appInfoLocalizations/{have[loc]}",
                     {"data": {"type": "appInfoLocalizations", "id": have[loc], "attributes": attrs}})
            else:
                call("POST", "/v1/appInfoLocalizations", {"data": {"type": "appInfoLocalizations",
                     "attributes": dict(locale=loc, **attrs),
                     "relationships": {"appInfo": {"data": {"type": "appInfos", "id": INFO}}}}})
            print("   ", loc, "name/subtitle/privacy ok")
        except Exception as e:
            print("   ", loc, "FAILED", e); problems.append(f"app info {loc}: {e}")


step("Name, subtitle, privacy URL (8 locales)", info_localizations)


def age_rating():
    decl = call("GET", f"/v1/appInfos/{INFO}/ageRatingDeclaration")["data"]
    did = decl["id"]
    none = ["alcoholTobaccoOrDrugUseOrReferences", "contests", "gamblingSimulated", "horrorOrFearThemes",
            "matureOrSuggestiveThemes", "medicalOrTreatmentInformation", "profanityOrCrudeHumor",
            "sexualContentGraphicAndNudity", "sexualContentOrNudity", "violenceCartoonOrFantasy",
            "violenceRealistic", "violenceRealisticProlongedGraphicOrSadistic", "gunsOrOtherWeapons"]
    false = ["unrestrictedWebAccess", "gambling", "lootBox", "messagingAndChat", "parentalControls",
             "healthOrWellnessTopics", "userGeneratedContent", "advertising", "ageAssurance"]
    current = decl.get("attributes", {})
    wanted = {k: "NONE" for k in none}
    wanted.update({k: False for k in false})
    try:
        call("PATCH", f"/v1/ageRatingDeclarations/{did}",
             {"data": {"type": "ageRatingDeclarations", "id": did, "attributes": wanted}})
        return
    except Exception as e:
        print("   bulk patch failed, trying one by one:", str(e)[:200])
    for k, v in wanted.items():
        if k not in current and current:
            continue
        try:
            call("PATCH", f"/v1/ageRatingDeclarations/{did}",
                 {"data": {"type": "ageRatingDeclarations", "id": did, "attributes": {k: v}}})
        except Exception as e:
            print("   ", k, "FAILED", str(e)[:200]); problems.append(f"age rating {k}")


step("Age rating (all None -> 4+)", age_rating)

versions = call("GET", f"/v1/apps/{APP}/appStoreVersions?filter[platform]=IOS")["data"]
VER = versions[0]["id"]
print("version", versions[0]["attributes"]["versionString"], versions[0]["attributes"]["appStoreState"])


def version_attrs():
    call("PATCH", f"/v1/appStoreVersions/{VER}", {"data": {"type": "appStoreVersions", "id": VER,
         "attributes": {"copyright": COPYRIGHT}}})


step("Copyright", version_attrs)


def version_localizations():
    have = {l["attributes"]["locale"]: l["id"] for l in
            call("GET", f"/v1/appStoreVersions/{VER}/appStoreVersionLocalizations?limit=50")["data"]}
    for loc, k in LOCALES.items():
        t = TEXT[k]
        attrs = {"description": t["desc"], "keywords": t["kw"], "promotionalText": t["promo"],
                 "supportUrl": SUPPORT, "marketingUrl": SUPPORT}
        try:
            if loc in have:
                call("PATCH", f"/v1/appStoreVersionLocalizations/{have[loc]}",
                     {"data": {"type": "appStoreVersionLocalizations", "id": have[loc], "attributes": attrs}})
            else:
                r = call("POST", "/v1/appStoreVersionLocalizations", {"data": {"type": "appStoreVersionLocalizations",
                         "attributes": dict(locale=loc, **attrs),
                         "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": VER}}}}})
                have[loc] = r["data"]["id"]
            print("   ", loc, "description/keywords ok")
        except Exception as e:
            print("   ", loc, "FAILED", e); problems.append(f"version text {loc}: {e}")
    return have


LOCS = step("Description, keywords, promo text, support URL (8 locales)", version_localizations) or {}


def upload_shots(loc_id, display="APP_IPHONE_67"):
    sets = call("GET", f"/v1/appStoreVersionLocalizations/{loc_id}/appScreenshotSets")["data"]
    sset = next((s["id"] for s in sets if s["attributes"]["screenshotDisplayType"] == display), None)
    if sset:
        for old in call("GET", f"/v1/appScreenshotSets/{sset}/appScreenshots")["data"]:
            call("DELETE", f"/v1/appScreenshots/{old['id']}")
    else:
        sset = call("POST", "/v1/appScreenshotSets", {"data": {"type": "appScreenshotSets",
                    "attributes": {"screenshotDisplayType": display},
                    "relationships": {"appStoreVersionLocalization": {"data": {
                        "type": "appStoreVersionLocalizations", "id": loc_id}}}}})["data"]["id"]
    for path in SHOTS:
        data = open(path, "rb").read()
        res = call("POST", "/v1/appScreenshots", {"data": {"type": "appScreenshots",
                   "attributes": {"fileName": os.path.basename(path), "fileSize": len(data)},
                   "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": sset}}}}})["data"]
        for op in res["attributes"]["uploadOperations"]:
            chunk = data[op["offset"]:op["offset"] + op["length"]]
            h = {x["name"]: x["value"] for x in op.get("requestHeaders", [])}
            r = requests.request(op["method"], op["url"], data=chunk, headers=h, timeout=120)
            r.raise_for_status()
        call("PATCH", f"/v1/appScreenshots/{res['id']}", {"data": {"type": "appScreenshots", "id": res["id"],
             "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
        print("    uploaded", path)


if "en-US" in LOCS:
    step("iPhone 6.9\" screenshots (English, used for all languages)", lambda: upload_shots(LOCS["en-US"]))


def price_free():
    pts = call("GET", f"/v1/apps/{APP}/appPricePoints?filter[territory]=USA&limit=200")["data"]
    free = next(p for p in pts if float(p["attributes"]["customerPrice"]) == 0)
    call("POST", "/v1/appPriceSchedules", {
        "data": {"type": "appPriceSchedules", "relationships": {
            "app": {"data": {"type": "apps", "id": APP}},
            "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
            "manualPrices": {"data": [{"type": "appPrices", "id": "${p0}"}]}}},
        "included": [{"type": "appPrices", "id": "${p0}", "attributes": {"startDate": None},
                      "relationships": {"appPricePoint": {"data": {"type": "appPricePoints", "id": free["id"]}}}}]})


step("Price: Free", price_free)


def availability():
    terr, url = [], "/v1/territories?limit=200"
    while url:
        r = call("GET", url)
        terr += [t["id"] for t in r["data"]]
        nxt = r.get("links", {}).get("next")
        url = nxt.replace(API, "") if nxt else None
    inc, refs = [], []
    for i, t in enumerate(terr):
        lid = "${t%d}" % i
        refs.append({"type": "territoryAvailabilities", "id": lid})
        inc.append({"type": "territoryAvailabilities", "id": lid, "attributes": {"available": True},
                    "relationships": {"territory": {"data": {"type": "territories", "id": t}}}})
    call("POST", "/v2/appAvailabilities", {"data": {"type": "appAvailabilities",
         "attributes": {"availableInNewTerritories": True},
         "relationships": {"app": {"data": {"type": "apps", "id": APP}},
                           "territoryAvailabilities": {"data": refs}}}, "included": inc})
    print("   territories:", len(terr))


step("Availability: all countries", availability)


def review_details():
    attrs = {"contactFirstName": "Murat", "contactLastName": "Kassas", "contactEmail": "patipals.destek@gmail.com",
             "demoAccountRequired": False,
             "notes": "Offline word-search game. No account, no ads, no purchases, no data collection. "
                      "Progress is stored only on the device."}
    try:
        cur = call("GET", f"/v1/appStoreVersions/{VER}/appStoreReviewDetail")["data"]
    except Exception:
        cur = None
    if cur:
        call("PATCH", f"/v1/appStoreReviewDetails/{cur['id']}",
             {"data": {"type": "appStoreReviewDetails", "id": cur["id"], "attributes": attrs}})
    else:
        call("POST", "/v1/appStoreReviewDetails", {"data": {"type": "appStoreReviewDetails", "attributes": attrs,
             "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": VER}}}}})


step("App Review contact (phone still needed)", review_details)


def attach_build():
    builds = call("GET", f"/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=5")["data"]
    valid = [b for b in builds if b["attributes"].get("processingState") == "VALID"]
    if not valid:
        raise RuntimeError("no processed build yet: " + ", ".join(b["attributes"].get("processingState", "?") for b in builds))
    b = valid[0]
    call("PATCH", f"/v1/appStoreVersions/{VER}/relationships/build", {"data": {"type": "builds", "id": b["id"]}})
    print("   build", b["attributes"]["version"])


step("Attach latest build to version 1.0", attach_build)

print("\n================ SUMMARY ================")
print("problems:", len(problems))
for p in problems:
    print(" -", p[:300])
print("Still to do in App Store Connect website: App Privacy -> 'Data Not Collected', review phone number, Submit.")

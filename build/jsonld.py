"""JSON-LD builders. All URLs are production URLs so the markup can move to the live site."""
PROD = "https://www.insureonthespot.com"
ORG_ID = f"{PROD}/#organization"
DAY_SCHEMA = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
              "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}


def organization():
    return {"@context": "https://schema.org", "@type": "Organization", "@id": ORG_ID,
            "name": "Insure On The Spot", "url": f"{PROD}/", "telephone": "+1-773-202-5060",
            "logo": f"{PROD}/wp-content/themes/orbit-media/images/logo.png", "foundingDate": "1986"}


def breadcrumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": name, "item": url}
                                for i, (name, url) in enumerate(items, start=1)]}


def opening_hours(hours):
    groups = {}
    for day, (opens, closes) in hours.items():
        groups.setdefault((opens, closes), []).append(DAY_SCHEMA[day])
    return [{"@type": "OpeningHoursSpecification", "dayOfWeek": days, "opens": o, "closes": c}
            for (o, c), days in groups.items()]


def agency(b):
    return {"@context": "https://schema.org", "@type": "InsuranceAgency", "@id": f"{b['url']}#branch",
            "name": f"Insure On The Spot, {b['name']}", "url": b["url"], "telephone": b["tel"],
            "parentOrganization": {"@id": ORG_ID},
            "address": {"@type": "PostalAddress", "streetAddress": b["street"], "addressLocality": b["city"],
                        "addressRegion": b["state"], "postalCode": b["zip"], "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": b["lat"], "longitude": b["lng"]},
            "openingHoursSpecification": opening_hours(b["hours"])}


def blog_collection(url, posts):
    return {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Tips & Resources",
            "url": url, "isPartOf": {"@id": f"{PROD}/#website"},
            "mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i, "url": p["link"], "name": p["title"]}
                for i, p in enumerate(posts, start=1)]}}


def contact_page():
    return {"@context": "https://schema.org", "@type": "ContactPage", "url": f"{PROD}/contact/",
            "about": {"@id": ORG_ID},
            "mainEntity": {"@id": ORG_ID, "@type": "Organization", "name": "Insure On The Spot",
                           "contactPoint": [{"@type": "ContactPoint", "telephone": "+1-773-202-5060",
                                             "contactType": "customer service", "areaServed": "US-IL",
                                             "availableLanguage": ["English", "Spanish"]}]}}

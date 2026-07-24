# Shopware Plugins

Übersicht der Shopware-6-Plugins für **Sellermax** — entwickelt von Orga Consult in Teamarbeit mit Seller Max GmbH.

## Live & Demo

- **Live:** [www.sellermax.de](https://www.sellermax.de)
- **Demo:** Eine Demo kann auf Anfrage bereitgestellt werden.

## Compiler / ZIP-Builds

Im Ordner [`Compiler/`](./Compiler/) liegt der **Shopware Plugin Builder ENTERPRISE** zum Erzeugen uploadfähiger Plugin-ZIPs.

- Anleitung (Windows, macOS, Linux): [`Compiler/README.md`](./Compiler/README.md)
- Voraussetzung: **Docker** mit Image `shopware/shopware-cli` (unter Windows Pflicht; natives shopware-cli ist dort nicht verfügbar)

Fertige Release-ZIPs werden als **GitHub Releases** in den jeweiligen Plugin-Repos veröffentlicht.

## Plugin-Übersicht

| Plugin | Version | Kurzbeschreibung | Repository | Release |
|--------|---------|------------------|------------|---------|
| [Sellermax GitHub Plugin Manager](#sellermax-github-plugin-manager) | 1.0.3 | Plugins aus GitHub im Admin installieren/updaten | [Repo](https://github.com/teris/SellermaxGithubPlugins) | [v1.0.3](https://github.com/teris/SellermaxGithubPlugins/releases/tag/v1.0.3) |
| [Sellermax Infinite Scroll](#sellermax-infinite-scroll) | 0.2.2 | Infinite Scroll für Kategorie-Listings | [Repo](https://github.com/teris/SellermaxInfiniteScroll) | [v0.2.2](https://github.com/teris/SellermaxInfiniteScroll/releases/tag/v0.2.2) |
| [Sellermax Optimize Listing](#sellermax-optimize-listing) | 1.0.7 | Kategoriebaum- & Filter-Optimierung | [Repo](https://github.com/teris/SellermaxOptimizeListing) | [v1.0.7](https://github.com/teris/SellermaxOptimizeListing/releases/tag/v1.0.7) |
| [Sellermax Custom Navigation](#sellermax-custom-navigation) | 1.1.4 | Konfigurierbare zweite Header-Navigation | [Repo](https://github.com/teris/SellermaxCustomNavigation) | [v1.1.4](https://github.com/teris/SellermaxCustomNavigation/releases/tag/v1.1.4) |
| [Sellermax Listing Quick Buy](#sellermax-listing-quick-buy) | 1.3.4 | Direktkauf, Staffelpreise, Lageranzeige | [Repo](https://github.com/teris/SellermaxListingQuickBuy) | [v1.3.4](https://github.com/teris/SellermaxListingQuickBuy/releases/tag/v1.3.4) |
| [Sellermax Cross-Selling Enhance](#sellermax-cross-selling-enhance) | 1.2.2 | Cross-Selling Design & Animationen | [Repo](https://github.com/teris/SellermaxCrossSellingEnhance) | [v1.2.2](https://github.com/teris/SellermaxCrossSellingEnhance/releases/tag/v1.2.2) |
| [Sellermax Product Custom Tabs](#sellermax-product-custom-tabs) | 1.1.5 | Produkt-Tabs aus Zusatzfeldern | [Repo](https://github.com/teris/SellermaxProductCustomTabs) | [v1.1.5](https://github.com/teris/SellermaxProductCustomTabs/releases/tag/v1.1.5) |
| [Sellermax Product Downloads](#sellermax-product-downloads) | 1.7.7 | PDF-/Medien-Downloads pro Produkt | [Repo](https://github.com/teris/SellermaxProductDownloads) | [v1.7.7](https://github.com/teris/SellermaxProductDownloads/releases/tag/v1.7.7) |
| [Sellermax Form Builder](#sellermax-form-builder) | 1.3.6 | Formulare mit Flow-Builder-Anbindung | [Repo](https://github.com/teris/SellermaxFormBuilder) | [v1.3.6](https://github.com/teris/SellermaxFormBuilder/releases/tag/v1.3.6) |
| [Sellermax Subscription](#sellermax-subscription) | 1.2.2 | Abo-Pläne & Wiederholungsbestellungen | [Repo](https://github.com/teris/SellermaxSubscription) | [v1.2.2](https://github.com/teris/SellermaxSubscription/releases/tag/v1.2.2) |
| [Sellermax Product Labels](#sellermax-product-labels) | 1.0.2 | Produkt-Labels/Badges mit Positionssteuerung | [Repo](https://github.com/teris/SellermaxProductLabels) | [v1.0.2](https://github.com/teris/SellermaxProductLabels/releases/tag/v1.0.2) |

---

### Sellermax Infinite Scroll

Lädt auf Kategorieseiten automatisch weitere Produkte beim Scrollen nach. Optional mit „Mehr laden“-Button, Skeleton/Spinner und URL-History.

| | |
|---|---|
| Composer | `sellermax/infinite-scroll` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront` |
| Repo | https://github.com/teris/SellermaxInfiniteScroll |

---

### Sellermax Optimize Listing

Optimiert Kategorie-Listings: aufklappbarer Kategoriebaum mit Pfeilen sowie begrenzte Filter mit „Weitere Filter“.

| | |
|---|---|
| Composer | `sellermax/optimize-listing` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront`, **`sellermax/infinite-scroll` (^0.2)** |
| Repo | https://github.com/teris/SellermaxOptimizeListing |

---

### Sellermax Custom Navigation

Zweite Navigationsebene im Header aus konfigurierbarem Kategorie-Einstiegspunkt inkl. Flyout und Mobile-Accordion.

| | |
|---|---|
| Composer | `sellermax/custom-navigation` |
| Shopware | `~6.5 \|\| ~6.6 \|\| ~6.7` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront` |
| Repo | https://github.com/teris/SellermaxCustomNavigation |

---

### Sellermax Listing Quick Buy

Erweitert Produktlisten um Direktkauf, Mengenwahl und Staffelpreise; auf der PDP Lagerbestand und Lieferzeit abhängig vom Bestand.

| | |
|---|---|
| Composer | `sellermax/listing-quick-buy` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront` |
| Repo | https://github.com/teris/SellermaxListingQuickBuy |

---

### Sellermax Cross-Selling Enhance

Verbessert Darstellung, Tab-Navigation und Animationen der Cross-Selling-Bereiche auf der Produktseite.

| | |
|---|---|
| Composer | `sellermax/cross-selling-enhance` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront` |
| Repo | https://github.com/teris/SellermaxCrossSellingEnhance |

---

### Sellermax Product Custom Tabs

Zusätzliche Produkt-Detail-Tabs aus Zusatzfeldern; optional eigene Tabs für Maße und Eigenschaften sowie Steuerung von Beschreibung/Bewertungen.

| | |
|---|---|
| Composer | `sellermax/product-custom-tabs` |
| Shopware | `^6.5` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront` |
| Repo | https://github.com/teris/SellermaxProductCustomTabs |

---

### Sellermax Product Downloads

Produkt-Downloads mit Kategorien, Sortierung, globalen Dokumenten und eigenem Medienordner; optional PDF-/Druck-Buttons in der Buy-Box.

| | |
|---|---|
| Composer | `sellermax/product-downloads` |
| Shopware | `~6.7 \|\| ~6.8` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront`, `shopware/administration` |
| Empfohlen | `sellermax/product-custom-tabs` |
| Repo | https://github.com/teris/SellermaxProductDownloads |

---

### Sellermax Form Builder

Mehrere Formulare in der Administration, Ausgabe als CMS-Element, Events für Flow-/Rule-Builder bei Einsendung.

| | |
|---|---|
| Composer | `sellermax/form-builder` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront`, `shopware/administration`, `symfony/process` |
| Repo | https://github.com/teris/SellermaxFormBuilder |

---

### Sellermax Subscription

Produkt-Abonnements mit Plänen, Folgeorders, Reminder-Mails, Kundenkonto-Verwaltung und Flow-Builder-Triggern.

| | |
|---|---|
| Composer | `sellermax/subscription` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront`, `shopware/administration` |
| Betrieb | Messenger-/Scheduled-Task-Worker erforderlich |
| Repo | https://github.com/teris/SellermaxSubscription |

---

### Sellermax Product Labels

Konfigurierbare Produkt-Labels/Badges für Listing und Detailseite inkl. Position links/rechts, dynamische Produktgruppen, Zeitraum und Styling.

| | |
|---|---|
| Composer | `sellermax/product-labels` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/storefront`, `shopware/administration` |
| Repo | https://github.com/teris/SellermaxProductLabels |

---

### Sellermax GitHub Plugin Manager

Admin-Oberfläche zum Installieren, Aktivieren, Deaktivieren und Aktualisieren der Sellermax-Plugins aus GitHub Releases (ohne Shopware Store). Einmal manuell installieren; danach Verwaltung der übrigen Plugins über die UI.

| | |
|---|---|
| Composer | `sellermax/github-plugins` |
| Shopware | `~6.7.0` |
| Abhängigkeiten | `shopware/core`, `shopware/administration`, `symfony/process`, PHP `curl`/`zip` |
| Repo | https://github.com/teris/SellermaxGithubPlugins |

---

## Empfohlene Installationsreihenfolge (Auszug)

1. `SellermaxGithubPlugins` (manuell) – danach weitere Plugins über die Admin-UI
2. `SellermaxInfiniteScroll`
3. `SellermaxOptimizeListing` (hängt von Infinite Scroll ab)
4. Weitere Storefront-/Listing-Plugins nach Bedarf
5. `SellermaxProductCustomTabs` vor bzw. zusammen mit `SellermaxProductDownloads` (empfohlen)
6. `SellermaxSubscription` inkl. Worker/Cron

Details und Konfiguration stehen in den jeweiligen Plugin-READMEs.

## Copyright

© Orga Consult – in Teamarbeit mit Seller Max GmbH

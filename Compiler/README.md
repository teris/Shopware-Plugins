# Shopware Plugin Builder (Compiler)

GUI-Tool zum Bauen von Shopware-6-Plugin-Assets und zum Erzeugen uploadfähiger **ZIP**-Dateien (Admin-/Storefront-Build + Release-Paket).

Skript: [`ShopwarePluginBuilder_ENTERPRISE.py`](./ShopwarePluginBuilder_ENTERPRISE.py)

## Voraussetzungen

| Komponente | Pflicht | Hinweis |
|---|---|---|
| **Python 3** | ja | inkl. `tkinter` (GUI) |
| **Docker** | stark empfohlen | Image `shopware/shopware-cli:latest` |
| **shopware-cli** (nativ) | optional | unter Windows i. d. R. **nicht** verfügbar → Docker nutzen |
| **Node.js / npm** | Fallback | nur wenn weder CLI noch Docker greifen und `package.json` ein `build`-Script hat |

Der Builder ruft intern auf:

```bash
docker run --rm -v "<PluginRoot>:/ext" shopware/shopware-cli:latest extension build /ext
```

Optional anderes Image per Umgebungsvariable:

```bash
SHOPWARE_CLI_DOCKER_IMAGE=shopware/shopware-cli:latest
```

---

## Schnellstart (alle Plattformen)

1. Docker starten und Image einmal laden (siehe OS-Abschnitte unten).
2. Python mit Tkinter bereitstellen.
3. Builder starten:

```bash
python ShopwarePluginBuilder_ENTERPRISE.py
```

4. **Hinzufügen** → Plugin-Ordner wählen (Ordner mit `composer.json`).
5. Plugin(s) in der Liste markieren (Strg+Klick / Strg+A).
6. **Build** → Assets bauen und ZIP erzeugen  
   oder **Build & V+1** → Version in `composer.json` erhöhen, dann bauen.

Fertige ZIPs landen typischerweise neben dem Plugin bzw. im konfigurierten Release-Ziel (siehe Protokoll im Builder). Jedes ZIP enthält u. a. `RELEASE_INFO.txt` (composer + CHANGELOG-Auszug).

### Wichtige Buttons

| Aktion | Wirkung |
|--------|---------|
| **Build** | shopware-cli (Docker/nativ) → ZIP |
| **Build & V+1** | Patch-Version +1, dann Build |
| **Version +1** | nur `composer.json`-Version erhöhen |
| **Store Validator** | Store-/Paket-Checks |
| **Deep Debug 6.4–6.7** | erweiterte Diagnose |
| **Release Notes** | Hinweise/Notizen zum Release |
| Checkbox **Zeitstempel im ZIP-Namen** | ZIP-Name mit Timestamp |

---

## Windows (Schritt für Schritt)

### 1. Docker Desktop

1. [Docker Desktop für Windows](https://www.docker.com/products/docker-desktop/) installieren.
2. WSL2-Backend aktivieren (Installer-Empfehlung folgen).
3. Docker Desktop starten, bis Status „Running“.
4. PowerShell prüfen:

```powershell
docker version
docker pull shopware/shopware-cli:latest
```

### 2. Python + Tkinter

1. [Python 3](https://www.python.org/downloads/) installieren.
2. Bei der Installation **„tcl/tk and IDLE“** bzw. Tcl/Tk mit auswählen.
3. „Add python.exe to PATH“ aktivieren.
4. Prüfen:

```powershell
python --version
python -c "import tkinter; print('tkinter OK')"
```

### 3. Builder starten

```powershell
cd "Pfad\zu\Shopware-Plugins\Compiler"
python .\ShopwarePluginBuilder_ENTERPRISE.py
```

### 4. Plugin bauen

1. **Hinzufügen** → z. B. `SellermaxInfiniteScroll` wählen.
2. Eintrag markieren → **Build**.
3. Im Protokoll muss `Docker: shopware/shopware-cli:… → extension build /ext` erscheinen.
4. ZIP für den Shopware-Upload / GitHub-Release verwenden.

> **Hinweis:** Natives `shopware-cli` gibt es unter Windows praktisch nicht. Ohne laufendes Docker schlägt der Admin-/Storefront-Build fehl.

---

## macOS (Schritt für Schritt)

### 1. Docker

1. [Docker Desktop für Mac](https://www.docker.com/products/docker-desktop/) installieren und starten.
2. Terminal:

```bash
docker version
docker pull shopware/shopware-cli:latest
```

### 2. Python + Tkinter

Empfohlen über Homebrew:

```bash
brew install python-tk
python3 --version
python3 -c "import tkinter; print('tkinter OK')"
```

Alternativ: offizielles python.org-Installer-Paket (enthält Tk).

### 3. Builder starten

```bash
cd /pfad/zu/Shopware-Plugins/Compiler
python3 ShopwarePluginBuilder_ENTERPRISE.py
```

### 4. Optional: natives shopware-cli

Unter macOS kann zusätzlich natives `shopware-cli` im PATH liegen; der Builder bevorzugt dann die native CLI vor Docker. Docker bleibt die einfachste, einheitliche Variante.

```bash
# falls gewünscht – siehe aktuelle Shopware-CLI-Doku
# shopware-cli version
```

---

## Linux (Schritt für Schritt)

### 1. Docker Engine

Ubuntu/Debian-Beispiel:

```bash
sudo apt update
sudo apt install -y docker.io
sudo usermod -aG docker "$USER"
# neu anmelden, damit die Gruppe greift
docker version
docker pull shopware/shopware-cli:latest
```

Andere Distributionen: Docker Engine laut Distro-Doku installieren.

### 2. Python + Tkinter

```bash
# Debian/Ubuntu
sudo apt install -y python3 python3-tk

python3 --version
python3 -c "import tkinter; print('tkinter OK')"
```

### 3. Builder starten

```bash
cd /pfad/zu/Shopware-Plugins/Compiler
python3 ShopwarePluginBuilder_ENTERPRISE.py
```

### 4. Optional: natives shopware-cli

Wenn `shopware-cli` im PATH ist, nutzt der Builder diese zuerst. Ansonsten Docker-Image `shopware/shopware-cli`.

---

## Typischer Workflow (Release)

1. Plugin-Code fertigstellen, `CHANGELOG.md` aktualisieren.
2. Builder öffnen → Plugin hinzufügen → **Build** (oder **Build & V+1**).
3. Entstandene ZIP prüfen (Inhalt: Plugin-Root ohne `node_modules` / `.git` / `vendor` …).
4. ZIP als **GitHub Release**-Asset am jeweiligen Plugin-Repo hochladen (Tag = `composer.json`-Version, z. B. `v1.2.2`).
5. Shopware-Admin: Erweiterung hochladen / aktualisieren.

Vorgebaute Pakete können auch im lokalen Ordner `release/` neben den Plugin-Repos liegen.

---

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `docker: command not found` | Docker Desktop/Engine installieren, neu starten, PATH prüfen |
| Build bricht ohne ZIP ab | Docker muss laufen; Image `shopware/shopware-cli:latest` pullen |
| `import tkinter` schlägt fehl | Python mit Tcl/Tk neu installieren (`python3-tk` / `python-tk`) |
| Administration-Build nicht erkannt | shopware-cli-Build muss `public/administration` bzw. Dist erzeugen |
| Falsches CLI-Image | `SHOPWARE_CLI_DOCKER_IMAGE` setzen |

---

## Copyright

© Orga Consult – in Teamarbeit mit Seller Max GmbH

**Live:** [www.sellermax.de](https://www.sellermax.de)  
**Demo:** auf Anfrage

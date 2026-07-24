
import os
import re
import shutil
import subprocess
import threading
import traceback
import zipfile
import time
import json
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk

# Verzeichnisse, die nicht ins Release-ZIP (Store-typisch)
_ZIP_SKIP_DIR_NAMES = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__",
    "var", "vendor", ".ddev",
}

# Native shopware-cli gibt es für Windows nicht; Standard ist Docker (wie composer extension:build).
_DEFAULT_SHOPWARE_CLI_IMAGE = "shopware/shopware-cli:latest"

# Icon-Pfade relativ zum Plugin-Root (Shopware-üblich + Fallback)
_PLUGIN_ICON_REL_PATHS = (
    os.path.join("src", "Resources", "config", "plugin.png"),
    os.path.join("Resources", "config", "plugin.png"),
    "plugin.png",
)


class Builder:

    def __init__(self, root):
        self.root = root
        self.root.title("Shopware Plugin Builder ENTERPRISE")
        self.root.minsize(860, 520)
        self.root.geometry("1100x720")

        self.plugins = []
        self.watch = False
        self._tree_images = {}

        tree_font = ("Segoe UI", 10) if os.name == "nt" else None
        self._ttk_style = ttk.Style()
        try:
            if os.name == "nt":
                self._ttk_style.theme_use("vista")
            if tree_font:
                self._ttk_style.configure("Treeview", font=tree_font, rowheight=26)
        except Exception:
            pass

        menubar = Menu(root)
        root.config(menu=menubar)
        m_file = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=m_file)
        m_file.add_command(label="Plugin-Ordner hinzufügen…", command=self.add)
        m_file.add_command(label="Markierte aus Liste entfernen", command=self.remove_selected)
        m_file.add_separator()
        m_file.add_command(label="Beenden", command=root.destroy)
        m_help = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=m_help)
        m_help.add_command(label="Über…", command=self._about)

        outer = ttk.Frame(root, padding=10)
        outer.pack(fill=BOTH, expand=True)

        bar = ttk.Frame(outer)
        bar.pack(fill=X, pady=(0, 8))

        row1 = ttk.Frame(bar)
        row1.pack(fill=X)
        ttk.Button(row1, text="Hinzufügen", command=self.add, width=11).pack(side=LEFT, padx=(0, 4))
        ttk.Button(row1, text="Entfernen", command=self.remove_selected, width=10).pack(
            side=LEFT, padx=2
        )
        ttk.Button(row1, text="Build", command=self.build_all, width=8).pack(side=LEFT, padx=2)
        ttk.Button(row1, text="Build & V+1", command=self.build_all_bump_first, width=14).pack(
            side=LEFT, padx=2
        )
        ttk.Button(row1, text="Version +1", command=self.bump, width=11).pack(side=LEFT, padx=2)
        ttk.Button(row1, text="Release Notes", command=self.notes, width=14).pack(side=LEFT, padx=2)
        self.watchBtn = ttk.Button(row1, text="Watch OFF", command=self.toggle, width=11)
        self.watchBtn.pack(side=RIGHT, padx=(8, 0))

        row2 = ttk.Frame(bar)
        row2.pack(fill=X, pady=(6, 0))
        ttk.Button(row2, text="Store Validator", command=self.validate, width=14).pack(
            side=LEFT, padx=(0, 4)
        )
        ttk.Button(row2, text="Deep Debug 6.4–6.7", command=self.debug, width=18).pack(
            side=LEFT, padx=2
        )

        opts = ttk.Frame(row2)
        opts.pack(side=LEFT, padx=(16, 0))
        self.bump_before_build = IntVar(value=0)
        ttk.Checkbutton(
            opts,
            text="Version +1 vor jedem Build",
            variable=self.bump_before_build,
        ).pack(side=LEFT, padx=(0, 10))
        self.zip_add_timestamp = IntVar(value=1)
        ttk.Checkbutton(
            opts,
            text="Zeitstempel im ZIP-Namen",
            variable=self.zip_add_timestamp,
        ).pack(side=LEFT)

        paned = ttk.PanedWindow(outer, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, pady=(0, 8))

        top_frame = ttk.Frame(paned)
        paned.add(top_frame)
        ttk.Label(
            top_frame,
            text="Plugins: Strg+Klick Mehrfachauswahl, Strg+A alle — Build / Build & V+1 nur für Markierte; Entfernen löscht aus der Liste (nicht vom Datenträger).",
            font=("Segoe UI", 9) if os.name == "nt" else None,
        ).pack(anchor=W, pady=(0, 4))
        list_wrap = ttk.Frame(top_frame)
        list_wrap.pack(fill=BOTH, expand=True)
        sb_y = ttk.Scrollbar(list_wrap)
        sb_y.pack(side=RIGHT, fill=Y)
        sb_x = ttk.Scrollbar(list_wrap, orient=HORIZONTAL)
        sb_x.pack(side=BOTTOM, fill=X)
        self.tree = ttk.Treeview(
            list_wrap,
            columns=("path", "ver"),
            show="tree headings",
            selectmode="extended",
            yscrollcommand=sb_y.set,
            xscrollcommand=sb_x.set,
        )
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb_y.config(command=self.tree.yview)
        sb_x.config(command=self.tree.xview)
        self.tree.heading("#0", text="Plugin")
        self.tree.column("#0", width=200, minwidth=80, stretch=True)
        self.tree.heading("ver", text="Version")
        self.tree.column("ver", width=72, minwidth=50, stretch=False)
        self.tree.heading("path", text="Pfad")
        self.tree.column("path", width=380, minwidth=120, stretch=True)
        self.tree.bind("<Control-a>", self._select_all_plugins_evt)

        log_frame = ttk.LabelFrame(paned, text="Protokoll", padding=6)
        paned.add(log_frame)
        _log_font = ("Consolas", 10) if os.name == "nt" else ("TkFixedFont", 10)
        self.log = scrolledtext.ScrolledText(
            log_frame,
            height=14,
            wrap=WORD,
            font=_log_font,
        )
        self.log.pack(fill=BOTH, expand=True)

        self.status_var = StringVar(value="Bereit.")
        ttk.Label(
            outer,
            textvariable=self.status_var,
            relief=SUNKEN,
            anchor=W,
            padding=(8, 5),
        ).pack(fill=X)

    def logmsg(self, msg):
        """Tkinter: nur im Main-Thread Widgets anfassen."""

        def _append():
            self.log.insert(END, msg + "\n")
            self.log.see(END)

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.root.after(0, _append)

    def _set_status(self, text):
        def _do():
            self.status_var.set(text)

        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.root.after(0, _do)

    def _about(self):
        messagebox.showinfo(
            "Über",
            "Shopware Plugin Builder ENTERPRISE\n\n"
            "Build nur für markierte Plugins; Icons aus plugin.png (config).\n"
            "Jedes Release-ZIP enthält RELEASE_INFO.txt (composer + CHANGELOG-Auszug).\n"
            "Toolchain: shopware-cli, Docker oder npm (Admin/Storefront).",
        )

    def _selected_indices(self):
        idxs = []
        for iid in self.tree.selection():
            try:
                idxs.append(int(iid))
            except (TypeError, ValueError):
                continue
        return sorted(set(idxs))

    def _selected_plugin_paths_ordered(self):
        out = []
        for i in self._selected_indices():
            if 0 <= i < len(self.plugins):
                out.append(os.path.normpath(self.plugins[i]))
        return out

    def _selected_plugin(self):
        paths = self._selected_plugin_paths_ordered()
        return paths[0] if paths else None

    def _refresh_plugin_tree(self):
        for c in self.tree.get_children():
            self.tree.delete(c)
        for i, p in enumerate(self.plugins):
            p = os.path.normpath(p)
            base = os.path.basename(p)
            ver = self._plugin_version(p) or "—"
            icon = self._plugin_icon_photo(p)
            text = base if icon else ("◆ " + base)
            kw = {"iid": str(i), "text": text, "values": (p, ver)}
            if icon:
                kw["image"] = icon
            self.tree.insert("", END, **kw)

    def _select_all_plugins_evt(self, _event=None):
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items)
        return "break"

    def _plugin_icon_photo(self, plugin_root):
        for rel in _PLUGIN_ICON_REL_PATHS:
            fp = os.path.join(plugin_root, rel)
            if not os.path.isfile(fp):
                continue
            try:
                mtime = os.path.getmtime(fp)
            except OSError:
                continue
            key = "%s|%s" % (fp, mtime)
            cached = self._tree_images.get(key)
            if cached is not None:
                return cached
            try:
                im = PhotoImage(file=fp)
                w, h = im.width(), im.height()
                factor = 1
                while max(w // factor, h // factor) > 24:
                    factor += 1
                if factor > 1:
                    im = im.subsample(factor, factor)
            except Exception:
                continue
            self._tree_images[key] = im
            return im
        return None

    @staticmethod
    def _changelog_sections(plugin_root):
        path = os.path.join(plugin_root, "CHANGELOG.md")
        if not os.path.isfile(path):
            return []
        try:
            with open(path, encoding="utf-8", errors="replace") as fp:
                text = fp.read()
        except OSError:
            return []
        parts = re.split(r"(?m)^##\s+", text)
        if len(parts) < 2:
            return []
        out = []
        for part in parts[1:]:
            lines = part.splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            out.append((title, body))
        return out

    def _changelog_body_for_version(self, plugin_root, version):
        if not version:
            return ""
        sections = self._changelog_sections(plugin_root)
        vnorm = str(version).strip().lstrip("vV")
        for title, body in sections:
            t = title.strip()
            if vnorm in t or t.strip("[]") == vnorm:
                return "## %s\n%s" % (title, body)
        return ""

    def _changelog_latest_excerpt(self, plugin_root, max_chars=6000):
        sections = self._changelog_sections(plugin_root)
        if not sections:
            return ""
        title, body = sections[0]
        s = "## %s\n%s" % (title, body)
        if len(s) > max_chars:
            s = s[: max_chars - 3] + "..."
        return s

    def _format_release_info(self, plugin_root):
        comp = os.path.join(plugin_root, "composer.json")
        folder_name = os.path.basename(os.path.normpath(plugin_root))
        version = self._plugin_version(plugin_root) or ""
        pkg_label = folder_name
        desc = ""
        if os.path.isfile(comp):
            try:
                with open(comp, encoding="utf-8") as fp:
                    data = json.load(fp)
                pkg_label = str(data.get("name", pkg_label))
                cv = str(data.get("version", "")).strip()
                if cv:
                    version = cv
                desc = str(data.get("description", "") or "").strip()
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        cl = self._changelog_body_for_version(plugin_root, version)
        if not cl:
            cl = self._changelog_latest_excerpt(plugin_root)
        if not cl:
            cl = "(Kein CHANGELOG.md oder keine passende ##-Sektion zur Version gefunden.)"
        lines = [
            "Release-Information (Shopware Plugin Builder)",
            "=============================================",
            "Paket: %s" % pkg_label,
            "Ordner: %s" % folder_name,
            "Version: %s" % (version or "—"),
            "",
        ]
        if desc:
            lines.extend(["Beschreibung (composer):", desc, ""])
        lines.extend(
            [
                "--- CHANGELOG (Auszug) ---",
                cl,
                "",
                "Nach Deployment: plugin:update, Cache leeren, Admin Hard-Reload (Strg+F5).",
            ]
        )
        return "\n".join(lines)

    def _admin_path(self, plugin_root):
        for rel in (
            os.path.join("src", "Resources", "app", "administration"),
            os.path.join("Resources", "app", "administration"),
        ):
            p = os.path.join(plugin_root, rel)
            if os.path.isdir(p):
                return p
        return None

    def _storefront_path(self, plugin_root):
        for rel in (
            os.path.join("src", "Resources", "app", "storefront"),
            os.path.join("Resources", "app", "storefront"),
        ):
            p = os.path.join(plugin_root, rel)
            if os.path.isdir(p):
                return p
        return None

    def _public_admin_path(self, plugin_root):
        for rel in (
            os.path.join("src", "Resources", "public", "administration"),
            os.path.join("Resources", "public", "administration"),
        ):
            p = os.path.join(plugin_root, rel)
            if os.path.isdir(p):
                return p
        return None

    def _public_storefront_path(self, plugin_root):
        for rel in (
            os.path.join("src", "Resources", "public", "storefront"),
            os.path.join("Resources", "public", "storefront"),
        ):
            p = os.path.join(plugin_root, rel)
            if os.path.isdir(p):
                return p
        return None

    def _admin_built(self, plugin_root):
        """Webpack: app/administration/dist. Vite/CLI: public/administration mit Manifest/Assets."""
        admin = self._admin_path(plugin_root)
        if admin:
            dist = os.path.join(admin, "dist")
            if os.path.isdir(dist):
                try:
                    if any(os.scandir(dist)):
                        return True
                except OSError:
                    pass
        pub = self._public_admin_path(plugin_root)
        if pub:
            vite_m = os.path.join(pub, ".vite", "manifest.json")
            if os.path.isfile(vite_m):
                return True
            assets = os.path.join(pub, "assets")
            if os.path.isdir(assets):
                try:
                    if any(os.scandir(assets)):
                        return True
                except OSError:
                    pass
            try:
                for n in os.listdir(pub):
                    if n not in (".vite",) and not n.startswith("."):
                        return True
            except OSError:
                pass
        return False

    def _storefront_built(self, plugin_root):
        store = self._storefront_path(plugin_root)
        if store:
            dist = os.path.join(store, "dist")
            if os.path.isdir(dist):
                try:
                    if any(os.scandir(dist)):
                        return True
                except OSError:
                    pass
        pub = self._public_storefront_path(plugin_root)
        if pub:
            try:
                if any(os.scandir(pub)):
                    return True
            except OSError:
                pass
        return False

    @staticmethod
    def _storefront_requires_built_assets(storefront_path):
        """
        Prüft, ob für Storefront ein echter Asset-Build erwartet wird.
        Bei reinen Twig/Snippet-Plugins ohne package.json/main.js soll kein False-Positive-Abbruch passieren.
        """
        if not storefront_path or not os.path.isdir(storefront_path):
            return False

        if os.path.isfile(os.path.join(storefront_path, "package.json")):
            return True

        src = os.path.join(storefront_path, "src")
        if not os.path.isdir(src):
            return False

        for rel in ("main.js", "main.ts", os.path.join("main", "index.js"), os.path.join("main", "index.ts")):
            if os.path.isfile(os.path.join(src, rel)):
                return True

        return False

    def _notify_no_selection(self):
        messagebox.showwarning(
            "Kein Plugin gewählt",
            "Bitte in der Plugin-Tabelle mindestens eine Zeile markieren, dann die Aktion erneut ausführen.",
        )

    @staticmethod
    def _bump_version_string(ver):
        """Erhöht die letzte numerische Komponente (z. B. 1.0.3 → 1.0.4)."""
        if not ver or not isinstance(ver, str):
            return "1.0.1"
        s = ver.strip().lstrip("vV")
        parts = s.split(".")
        if not parts:
            return s + ".1"
        last = parts[-1]
        m = re.match(r"^(\d+)(.*)$", last)
        if not m:
            parts.append("1")
            return ".".join(parts)
        n = int(m.group(1)) + 1
        parts[-1] = str(n) + m.group(2)
        return ".".join(parts)

    def add(self):
        p = filedialog.askdirectory()
        if not p:
            return
        p = os.path.normpath(p)
        if p in self.plugins:
            messagebox.showinfo("Hinzufügen", "Dieser Ordner ist bereits in der Liste.")
            return
        self.plugins.append(p)
        self._refresh_plugin_tree()
        self.tree.selection_set(str(len(self.plugins) - 1))
        self.tree.see(str(len(self.plugins) - 1))

    def remove_selected(self):
        idxs = sorted(self._selected_indices(), reverse=True)
        if not idxs:
            self._notify_no_selection()
            return
        for i in idxs:
            if 0 <= i < len(self.plugins):
                del self.plugins[i]
        self._refresh_plugin_tree()

    @staticmethod
    def _win_node_path_prefixes():
        """GUI-Starts unter Windows haben oft kein Node im PATH – typische Installationspfade voranstellen."""
        if os.name != "nt":
            return []
        out = []
        for env_key in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env_key)
            if not base:
                continue
            nd = os.path.join(base, "nodejs")
            if os.path.isfile(os.path.join(nd, "npm.cmd")):
                out.append(nd)
        return out

    def _subprocess_env(self):
        env = os.environ.copy()
        if os.name == "nt":
            extra = self._win_node_path_prefixes()
            if extra:
                prefix = os.pathsep.join(dict.fromkeys(extra))
                env["PATH"] = prefix + os.pathsep + env.get("PATH", "")
        return env

    def run(self, cmd, cwd):
        cwd = os.path.normpath(cwd)
        if not os.path.isdir(cwd):
            self.logmsg("ERROR cwd fehlt oder kein Verzeichnis: " + cwd)
            return False
        env = self._subprocess_env()
        shell_cmd = ("cmd /c " + cmd) if os.name == "nt" else cmd
        try:
            proc = subprocess.run(
                shell_cmd,
                cwd=cwd,
                shell=True,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as e:
            self.logmsg("ERROR Start fehlgeschlagen: %s – %s" % (cmd, e))
            return False
        rc = proc.returncode
        rc_signed = rc - (1 << 32) if rc is not None and rc > 2 ** 31 - 1 else rc
        if rc != 0:
            self.logmsg(
                "ERROR Befehl fehlgeschlagen (exit %s, signed %s): %s in %s"
                % (rc, rc_signed, cmd, cwd)
            )
            err = (proc.stderr or "").strip()
            out = (proc.stdout or "").strip()
            if err:
                self.logmsg("— stderr —")
                for line in err.splitlines():
                    self.logmsg("  " + line)
            if out:
                self.logmsg("— stdout —")
                for line in out.splitlines():
                    self.logmsg("  " + line)
            return False
        return True

    def _run_argv(self, argv, label=None):
        """subprocess ohne Shell (z. B. docker), gleiche Logik wie run()."""
        env = self._subprocess_env()
        disp = label or " ".join(argv)
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
        except OSError as e:
            self.logmsg("ERROR Start fehlgeschlagen: %s – %s" % (disp, e))
            return False
        rc = proc.returncode
        rc_signed = rc - (1 << 32) if rc is not None and rc > 2 ** 31 - 1 else rc
        if rc != 0:
            self.logmsg(
                "ERROR Befehl fehlgeschlagen (exit %s, signed %s): %s"
                % (rc, rc_signed, disp)
            )
            err = (proc.stderr or "").strip()
            out = (proc.stdout or "").strip()
            if err:
                self.logmsg("— stderr —")
                for line in err.splitlines():
                    self.logmsg("  " + line)
            if out:
                self.logmsg("— stdout —")
                for line in out.splitlines():
                    self.logmsg("  " + line)
            return False
        return True

    @staticmethod
    def _shopware_cli_docker_image():
        return os.environ.get("SHOPWARE_CLI_DOCKER_IMAGE", _DEFAULT_SHOPWARE_CLI_IMAGE).strip() or _DEFAULT_SHOPWARE_CLI_IMAGE

    def _run_shopware_cli_docker_build(self, plugin_root):
        """shopware-cli im Container – empfohlen unter Windows (Docker Desktop)."""
        plugin_root = os.path.abspath(os.path.normpath(plugin_root))
        if not os.path.isdir(plugin_root):
            self.logmsg("ERROR Plugin-Pfad ungültig: " + plugin_root)
            return False
        img = self._shopware_cli_docker_image()
        mount = plugin_root + ":/ext"
        argv = [
            "docker",
            "run",
            "--rm",
            "-v",
            mount,
            img,
            "extension",
            "build",
            "/ext",
        ]
        self.logmsg("Docker: %s → extension build /ext" % img)
        return self._run_argv(argv)

    @staticmethod
    def _which_shopware_cli():
        return shutil.which("shopware-cli")

    @staticmethod
    def _which_docker():
        return shutil.which("docker")

    @staticmethod
    def _package_json_has_build(folder):
        pj = os.path.join(folder, "package.json")
        if not os.path.isfile(pj):
            return False
        try:
            with open(pj, encoding="utf-8") as fp:
                data = json.load(fp)
            scripts = data.get("scripts") or {}
            return bool((scripts.get("build") or "").strip())
        except Exception:
            return False

    def _should_skip_zip_dir(self, dirname):
        base = os.path.basename(dirname)
        return base in _ZIP_SKIP_DIR_NAMES

    @staticmethod
    def _plugin_version(plugin_root):
        comp = os.path.join(plugin_root, "composer.json")
        if not os.path.isfile(comp):
            return ""
        try:
            with open(comp, encoding="utf-8") as fp:
                data = json.load(fp)
            v = str(data.get("version", "")).strip()
            return re.sub(r"[^0-9A-Za-z._-]", "_", v)
        except Exception:
            return ""

    def _bump_version_silent(self, plugin_root):
        """Erhöht composer.json version ohne Dialog (für Build-Pipeline)."""
        fpath = os.path.join(plugin_root, "composer.json")
        if not os.path.isfile(fpath):
            self.logmsg("WARN Keine composer.json – Version +1 übersprungen.")
            return False
        try:
            with open(fpath, encoding="utf-8") as fp:
                data = json.load(fp)
            old = str(data.get("version", "1.0.0"))
            data["version"] = self._bump_version_string(old)
            with open(fpath, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=4)
            self.logmsg(
                "%s: composer.json Version %s → %s"
                % (os.path.basename(plugin_root), old, data["version"])
            )
            return True
        except (ValueError, OSError, json.JSONDecodeError) as ex:
            self.logmsg("WARN Version +1 fehlgeschlagen: %s" % ex)
            return False

    @staticmethod
    def _markers_from_admin_detail_twig(admin_path):
        """Eindeutige Strings aus der Detail-Twig, die nach shopware-cli im JS-Bundle stehen sollten."""
        markers = []
        if not admin_path or not os.path.isdir(admin_path):
            return markers
        for r, _d, fnames in os.walk(admin_path):
            for fn in fnames:
                if not fn.endswith("sellermax-stock-sync-detail.html.twig"):
                    continue
                twpath = os.path.join(r, fn)
                try:
                    with open(twpath, encoding="utf-8", errors="ignore") as fp:
                        txt = fp.read()
                except OSError:
                    continue
                for key in (
                    "sourceProductNumberPrefix",
                    "sourceProductNumberSuffix",
                    "targetProductNumberPrefix",
                    "targetProductNumberSuffix",
                ):
                    if key in txt and key not in markers:
                        markers.append(key)
                break
            if markers:
                break
        return markers

    @staticmethod
    def _public_admin_newest_js_mtime(pub_path):
        """Neuester Zeitstempel einer *.js (ohne .map) unter public/administration."""
        newest = 0.0
        if not pub_path or not os.path.isdir(pub_path):
            return newest
        for r, _d, fnames in os.walk(pub_path):
            for fn in fnames:
                if not fn.endswith(".js") or fn.endswith(".map"):
                    continue
                fp = os.path.join(r, fn)
                try:
                    newest = max(newest, os.path.getmtime(fp))
                except OSError:
                    pass
        return newest

    @staticmethod
    def _admin_source_newest_mtime(admin_path):
        """Neuester Zeitstempel unter app/administration (Quell-Änderung)."""
        newest = 0.0
        if not admin_path or not os.path.isdir(admin_path):
            return newest
        for r, _d, fnames in os.walk(admin_path):
            for fn in fnames:
                if fn.endswith((".js", ".twig", ".scss", ".vue")):
                    fp = os.path.join(r, fn)
                    try:
                        newest = max(newest, os.path.getmtime(fp))
                    except OSError:
                        pass
        return newest

    def _verify_admin_bundle_matches_source(self, plugin_root):
        """
        Prüft nach dem Build: gebündelte JS enthalten erwartete Merkmale aus der Twig-Quelle.
        Verhindert ZIPs, in denen die Administration veraltet ist.
        """
        admin = self._admin_path(plugin_root)
        pub = self._public_admin_path(plugin_root)
        if not admin or not pub:
            return True, ""
        markers = self._markers_from_admin_detail_twig(admin)
        if not markers:
            return True, ""
        js_new = self._public_admin_newest_js_mtime(pub)
        src_new = self._admin_source_newest_mtime(admin)
        if src_new > js_new + 2:
            return (
                False,
                "Admin-Quelle ist neuer als public/administration/*.js (Quelle-Zeit %.1f > Bundle-Zeit %.1f). "
                "Build hat vermutlich nicht alle Dateien aktualisiert – Docker-Volumen/Pfad prüfen, dann erneut Build."
                % (src_new, js_new),
            )
        for m in markers:
            found = False
            for r, _d, fnames in os.walk(pub):
                for fn in fnames:
                    if not fn.endswith(".js") or fn.endswith(".map"):
                        continue
                    fp = os.path.join(r, fn)
                    try:
                        with open(fp, encoding="utf-8", errors="ignore") as f:
                            if m in f.read():
                                found = True
                                break
                    except OSError:
                        pass
                if found:
                    break
            if not found:
                return (
                    False,
                    "Im Admin-Bundle fehlt erwarteter String „%s“ (laut sellermax-stock-sync-detail.html.twig). "
                    "extension build / shopware-cli lieferte eine veraltete oder falsche Ausgabe."
                    % m,
                )
        return True, ""

    def _make_zip_basename(self, plugin_root):
        plugin_name = os.path.basename(plugin_root)
        plugin_version = self._plugin_version(plugin_root)
        ts = ""
        if self.zip_add_timestamp.get():
            ts = "-" + time.strftime("%Y%m%d-%H%M%S")
        if plugin_version:
            return f"{plugin_name}-{plugin_version}{ts}.zip"
        return f"{plugin_name}{ts}.zip"

    def build(self, plugin, force_version_bump=False):
        plugin = os.path.normpath(plugin)
        self._set_status("Build: %s …" % os.path.basename(plugin))
        ok_zip = ""
        try:
            self.logmsg("Build " + plugin)

            if force_version_bump or self.bump_before_build.get():
                self._bump_version_silent(plugin)

            admin = self._admin_path(plugin)
            store = self._storefront_path(plugin)
            cli = self._which_shopware_cli()
            docker = self._which_docker()

            build_ok = True

            # Wie GitHub-Action: ein Aufruf baut Admin/Storefront (ohne lokale package.json).
            # Unter Windows: kein natives shopware-cli → Docker Desktop mit shopware/shopware-cli.
            if cli:
                q = '"' if " " in cli else ""
                self.logmsg("shopware-cli (nativ): extension build …")
                build_ok = self.run("%s%s%s extension build ." % (q, cli, q), plugin)
            elif docker:
                build_ok = self._run_shopware_cli_docker_build(plugin)
            else:
                if admin:
                    if self._package_json_has_build(admin):
                        self.logmsg("Administration: npm install / npm run build …")
                        ok1 = self.run("npm install", admin)
                        ok2 = self.run("npm run build", admin) if ok1 else False
                        build_ok = build_ok and ok1 and ok2
                    elif os.path.isfile(os.path.join(admin, "package.json")):
                        self.logmsg(
                            'Hinweis: Administration hat package.json, aber kein "build"-Script. '
                            "Docker Desktop installieren (docker im PATH) oder shopware-cli unter WSL2 / scripts.build."
                        )
                        build_ok = False
                    else:
                        self.logmsg(
                            "Hinweis: Keine package.json unter Administration. "
                            "Unter Windows: Docker Desktop starten – der Builder nutzt dann "
                            "shopware/shopware-cli wie eure composer-Scripts. "
                            "Alternativ: shopware-cli unter WSL2 installieren oder npm mit package.json + build."
                        )
                        build_ok = False
                else:
                    self.logmsg(
                        "(kein Administration-Unterordner unter src/Resources oder Resources – npm übersprungen)"
                    )

                if store:
                    if self._package_json_has_build(store):
                        self.logmsg("Storefront: npm install / npm run build …")
                        ok1 = self.run("npm install", store)
                        ok2 = self.run("npm run build", store) if ok1 else False
                        build_ok = build_ok and ok1 and ok2
                    elif os.path.isfile(os.path.join(store, "package.json")):
                        self.logmsg(
                            'Hinweis: Storefront package.json ohne "build"-Script – Docker shopware-cli oder build-Script.'
                        )
                        build_ok = False

            if not build_ok:
                self.logmsg("ABBRUCH: Build fehlgeschlagen – es wird kein ZIP erstellt.")
                return

            if admin and not self._admin_built(plugin):
                self.logmsg(
                    "ABBRUCH: Administration-Build nicht erkannt (public/administration oder dist fehlt)."
                )
                return

            if store:
                if self._storefront_requires_built_assets(store):
                    if not self._storefront_built(plugin):
                        self.logmsg(
                            "ABBRUCH: Storefront-Build nicht erkannt (public/storefront oder dist fehlt)."
                        )
                        return
                elif not self._storefront_built(plugin):
                    self.logmsg(
                        "Hinweis: Storefront-Quellen erkannt, aber kein Build-Entrypoint (package.json/main.js). "
                        "Kein Storefront-Build erzwungen."
                    )

            ok_verify, verify_msg = self._verify_admin_bundle_matches_source(plugin)
            if not ok_verify:
                self.logmsg("ABBRUCH: Admin-Bundle-Verifikation: " + verify_msg)
                return

            self._set_status("ZIP packen: %s …" % os.path.basename(plugin))

            rel = os.path.join(os.getcwd(), "release")
            os.makedirs(rel, exist_ok=True)

            zip_name = self._make_zip_basename(plugin)
            zipf = os.path.join(rel, zip_name)

            with zipfile.ZipFile(zipf, "w", zipfile.ZIP_DEFLATED) as z:
                for r, dnames, fnames in os.walk(plugin):
                    dnames[:] = [
                        x for x in dnames if not self._should_skip_zip_dir(os.path.join(r, x))
                    ]
                    for file in fnames:
                        full = os.path.join(r, file)
                        relp = os.path.relpath(full, plugin)
                        z.write(full, os.path.basename(plugin) + "/" + relp)
                info_arc = os.path.basename(plugin) + "/RELEASE_INFO.txt"
                z.writestr(info_arc, self._format_release_info(plugin).encode("utf-8"))
            self.logmsg("RELEASE_INFO.txt (CHANGELOG & composer) ins ZIP: %s" % info_arc)

            try:
                zsize = os.path.getsize(zipf)
                self.logmsg("ZIP %s (%.1f MiB)" % (zipf, zsize / (1024 * 1024)))
            except OSError:
                self.logmsg("ZIP " + zipf)
            ok_zip = zip_name
            self.logmsg(
                "Hinweis: Nach Upload im Zielshop plugin:update / cache:clear – im Admin Hard-Reload (Strg+F5)."
            )
        finally:

            def _finish_build_ui():
                if ok_zip:
                    self._set_status("Bereit. – ZIP: %s" % ok_zip)
                else:
                    self._set_status("Bereit.")
                self._refresh_plugin_tree()

            if threading.current_thread() is threading.main_thread():
                _finish_build_ui()
            else:
                self.root.after(0, _finish_build_ui)

    def build_all(self):
        threading.Thread(target=self._build, daemon=True).start()

    def build_all_bump_first(self):
        """Version für jedes Plugin +1, dann bauen (unabhängig vom Checkbox „vor Build“)."""
        threading.Thread(target=self._build_with_version_bump, daemon=True).start()

    def _build(self):
        paths = self._selected_plugin_paths_ordered()
        if not paths:

            def _warn():
                messagebox.showwarning(
                    "Build",
                    "Keine Plugins markiert. Bitte in der Tabelle die gewünschten Zeilen auswählen "
                    "(Strg+Klick für mehrere). Nur markierte Plugins werden gebaut.",
                )

            self.root.after(0, _warn)
            return
        for p in paths:
            self.build(p)

    def _build_with_version_bump(self):
        paths = self._selected_plugin_paths_ordered()
        if not paths:

            def _warn():
                messagebox.showwarning(
                    "Build",
                    "Keine Plugins markiert. Bitte in der Tabelle die gewünschten Zeilen auswählen "
                    "(Strg+Klick für mehrere).",
                )

            self.root.after(0, _warn)
            return
        for p in paths:
            self.build(p, force_version_bump=True)

    def bump(self):
        plugin = self._selected_plugin()
        if not plugin:
            self._notify_no_selection()
            return

        fpath = os.path.join(plugin, "composer.json")
        if not os.path.isfile(fpath):
            messagebox.showerror("Version", "Keine composer.json im Plugin-Ordner.")
            return

        try:
            with open(fpath, encoding="utf-8") as fp:
                data = json.load(fp)
            old = data.get("version", "1.0.0")
            data["version"] = self._bump_version_string(str(old))
            with open(fpath, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=4)
            self.logmsg("Version %s → %s" % (old, data["version"]))
            self._refresh_plugin_tree()
            messagebox.showinfo("Version", "Neue Version: %s" % data["version"])
        except (ValueError, OSError, json.JSONDecodeError) as ex:
            messagebox.showerror("Version", "Konnte Version nicht setzen:\n%s" % ex)

    def notes(self):
        plugin = self._selected_plugin()
        if not plugin:
            self._notify_no_selection()
            return

        comp = os.path.join(plugin, "composer.json")
        v = "unknown"
        if os.path.isfile(comp):
            try:
                with open(comp, encoding="utf-8") as fp:
                    v = json.load(fp).get("version", "unknown")
            except Exception:
                pass

        win = Toplevel(self.root)
        win.title("Release Notes – %s" % os.path.basename(plugin))
        win.geometry("720x420")
        win.transient(self.root)
        Label(
            win,
            text="Version %s — CHANGELOG.md: vorhandener Abschnitt als Referenz; darunter neue Bullet-Zeilen anhängen."
            % v,
            anchor="w",
        ).pack(fill="x", padx=8, pady=(8, 0))

        body = scrolledtext.ScrolledText(win, wrap=WORD, height=14)
        body.pack(fill=BOTH, expand=True, padx=8, pady=8)
        excerpt = ""
        if str(v).strip() and str(v) != "unknown":
            excerpt = self._changelog_body_for_version(plugin, v)
        if not excerpt:
            excerpt = self._changelog_latest_excerpt(plugin, max_chars=4500)
        if excerpt:
            body.insert(END, "# Vorhandener CHANGELOG (Referenz, wird nicht doppelt gespeichert)\n\n")
            body.insert(END, excerpt + "\n\n")
        body.insert(END, "# --- NEUE_EINTRÄGE_UNTEN ---\n")
        body.insert(
            END,
            "# Nur dieser Block wird an CHANGELOG.md angehängt (Zeilen mit # ignorieren):\n\n"
            "- Fix: …\n"
            "- Feature: …\n",
        )

        def append_changelog():
            raw_full = body.get("1.0", END)
            marker = "# --- NEUE_EINTRÄGE_UNTEN ---"
            if marker in raw_full:
                raw = raw_full.split(marker, 1)[1].strip()
            else:
                raw = raw_full.strip()
            if not raw:
                messagebox.showwarning("Release Notes", "Bitte unter „NEUE_EINTRÄGE“ Text eingeben.")
                return
            bullets = []
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "," in line:
                    for part in line.split(","):
                        p = part.strip()
                        if p:
                            bullets.append(p)
                else:
                    bullets.append(line)
            if not bullets:
                messagebox.showwarning("Release Notes", "Keine nutzbaren Zeilen gefunden.")
                return
            path = os.path.join(plugin, "CHANGELOG.md")
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n## " + v + "\n")
                    for b in bullets:
                        if b.startswith("-"):
                            f.write(b + "\n")
                        else:
                            f.write("- " + b + "\n")
                self.logmsg("Release Notes → " + path)
                messagebox.showinfo("Release Notes", "An CHANGELOG.md angehängt.")
                win.destroy()
            except OSError as ex:
                messagebox.showerror("Release Notes", str(ex))

        bf = Frame(win)
        bf.pack(fill="x", padx=8, pady=(0, 8))
        Button(bf, text="Abbrechen", command=win.destroy).pack(side=RIGHT, padx=4)
        Button(bf, text="An CHANGELOG anhängen", command=append_changelog).pack(side=RIGHT, padx=4)

    def validate(self):
        p = self._selected_plugin()
        if not p:
            self._notify_no_selection()
            return

        errors = []

        comp = os.path.join(p, "composer.json")
        if not os.path.exists(comp):
            errors.append("composer.json missing")
        else:
            try:
                with open(comp, encoding="utf-8") as fp:
                    data = json.load(fp)
                if data.get("type") != "shopware-platform-plugin":
                    errors.append('composer type should be "shopware-platform-plugin"')
                extra = data.get("extra") or {}
                if not extra.get("shopware-plugin-class"):
                    errors.append('extra.shopware-plugin-class fehlt')
            except Exception as ex:
                errors.append("composer.json unlesbar: %s" % ex)

        if not os.path.exists(os.path.join(p, "src")):
            errors.append("src missing")

        main_php = os.path.join(p, "src", os.path.basename(os.path.normpath(p)) + ".php")
        if not os.path.isfile(main_php):
            errors.append("Plugin-Hauptklasse fehlt: %s" % main_php)
        else:
            try:
                with open(main_php, encoding="utf-8", errors="ignore") as fp:
                    txt = fp.read()
                if "getAdministrationEntryPath" not in txt:
                    errors.append("Plugin-Hauptklasse ohne getAdministrationEntryPath()")
            except OSError as ex:
                errors.append("Plugin-Hauptklasse unlesbar: %s" % ex)

        if self._admin_path(p) and not self._admin_built(p):
            errors.append(
                "Administration: kein Build erkannt (weder app/.../dist noch public/administration mit Ausgabe)"
            )

        if self._storefront_path(p) and not self._storefront_built(p):
            errors.append(
                "Storefront: kein Build erkannt (weder app/.../dist noch public/storefront mit Inhalt)"
            )

        if errors:
            messagebox.showerror("Store Validator", "\n".join(errors))
        else:
            messagebox.showinfo("Store Validator", "OK – Pflichtpunkte und gebaute Assets erkannt.")

    @staticmethod
    def _shopware_core_ok(constraint):
        """Grobe Prüfung: Shopware 6.4+ in der Constraint."""
        if not constraint or not isinstance(constraint, str):
            return False
        s = constraint.strip()
        # ^6.5, ~6.5.0, >=6.4, 6.4.*, etc.
        if re.search(r"(\^|~|>=|>|<=|<)?\s*6\.[4-9]", s):
            return True
        if re.search(r"(\^|~|>=|>)\s*6\.[1-3]", s):
            return False
        if "dev" in s.lower():
            return True
        return bool(re.search(r"6\.\d+", s))

    def _debug_worker(self, p):
        try:
            self._debug_worker_impl(p)
        except Exception:
            tb = traceback.format_exc()
            self.logmsg("Deep Debug Fehler:\n" + tb)

            def _err():
                messagebox.showerror(
                    "Deep Debug",
                    "Interner Fehler – Details stehen im Log.\n\n" + tb[:1200],
                )

            self.root.after(0, _err)

    def _debug_worker_impl(self, p):
        report = []
        report.append("Shopware Debug 6.4-6.7")
        report.append("--------------------")

        comp = os.path.join(p, "composer.json")
        if os.path.exists(comp):
            try:
                with open(comp, encoding="utf-8") as fp:
                    data = json.load(fp)
                req = data.get("require") or {}
                core = req.get("shopware/core", "")
                if self._shopware_core_ok(core):
                    report.append("✔ shopware/core Constraint sieht nach 6.4+ aus: %s" % core)
                else:
                    report.append("⚠ shopware/core prüfen: %s" % core)
            except Exception as ex:
                report.append("⚠ composer.json: %s" % ex)
        else:
            report.append("⚠ composer.json fehlt")

        php_ok = False
        try:
            subprocess.run(
                ["php", "-v"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            php_ok = True
        except FileNotFoundError:
            report.append("⚠ php nicht im PATH – Syntaxcheck übersprungen")
        except Exception as ex:
            report.append("⚠ php -v fehlgeschlagen: %s" % ex)

        if php_ok:
            for r, _dnames, fnames in os.walk(p):
                for name in fnames:
                    if not name.endswith(".php"):
                        continue
                    full = os.path.join(r, name)
                    try:
                        rproc = subprocess.run(
                            ["php", "-l", full],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        if rproc.returncode != 0:
                            err = (rproc.stderr or rproc.stdout or "").strip()
                            report.append("PHP error " + full + (": " + err if err else ""))
                    except Exception as ex:
                        report.append("PHP check " + full + ": " + str(ex))

        deprecated = [
            "Context::createDefaultContext",
            "EntityRepositoryInterface",
            "renderStorefront",
        ]

        for r, _dnames, fnames in os.walk(p):
            for name in fnames:
                if not name.endswith(".php"):
                    continue
                fpath = os.path.join(r, name)
                try:
                    with open(fpath, encoding="utf-8", errors="ignore") as fp:
                        txt = fp.read()
                except OSError:
                    continue
                for dep in deprecated:
                    if dep in txt:
                        report.append("Deprecated " + dep + " in " + name)

        admin = self._admin_path(p)
        if admin:
            report.append("Administration (Quelle): " + admin)
            report.append(
                "  gebaut: %s" % ("ja" if self._admin_built(p) else "nein (dist/public prüfen)")
            )
        pub_adm = self._public_admin_path(p)
        if pub_adm:
            report.append("public/administration: " + pub_adm)
        store = self._storefront_path(p)
        if store:
            report.append("Storefront (Quelle): " + store)
            report.append(
                "  gebaut: %s" % ("ja" if self._storefront_built(p) else "nein")
            )
        pub_sf = self._public_storefront_path(p)
        if pub_sf:
            report.append("public/storefront: " + pub_sf)

        out = "\n".join(report)
        self.logmsg(out)
        try:
            out_path = os.path.join(os.getcwd(), "debug-report.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out)
        except OSError as ex:
            self.logmsg("debug-report.txt konnte nicht geschrieben werden: %s" % ex)

        def _done():
            messagebox.showinfo("Debug", "Report erstellt (siehe Log und debug-report.txt)")

        self.root.after(0, _done)

    def debug(self):
        p = self._selected_plugin()
        if not p:
            self._notify_no_selection()
            return
        threading.Thread(target=self._debug_worker, args=(p,), daemon=True).start()

    def toggle(self):
        self.watch = not self.watch
        self.watchBtn.configure(text="Watch ON" if self.watch else "Watch OFF")

        if self.watch:
            threading.Thread(target=self.watch_loop, daemon=True).start()

    def watch_loop(self):
        times = {}
        while self.watch:
            for p in self.plugins:
                t = os.path.getmtime(p)
                if p not in times:
                    times[p] = t
                elif times[p] != t:
                    times[p] = t
                    self.build(p)
            time.sleep(2)


root = Tk()
Builder(root)
root.mainloop()

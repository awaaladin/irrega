/* Routine Irrigation Technology: interaction + motion layer (Alpine + Motion).
   Rules: springs for movement, short tweens only for opacity/colour, animate transform/opacity only,
   everything interruptible, and a full prefers-reduced-motion fallback (quick fades, no count-ups). */
(function () {
  const M = window.Motion || {};
  // The farmer's own choice wins; "system" follows the device setting.
  const reduce = () => {
    const pref = document.documentElement.dataset.motion;
    if (pref === "reduce") return true;
    if (pref === "full") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  };

  // Spring tokens (mirrors the design tokens: snappy / gentle / bouncy-soft)
  const SPRING = {
    snappy: { type: "spring", stiffness: 520, damping: 34 },
    gentle: { type: "spring", stiffness: 220, damping: 26 },
    soft: { type: "spring", stiffness: 300, damping: 18 },
  };
  const FADE = { duration: 0.12, ease: "easeOut" };

  function csrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }
  async function api(url, body, method = "POST") {
    const r = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf(), Accept: "application/json" },
      body: body ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(data.error || "Something went wrong."), { status: r.status });
    return data;
  }
  window.RIT = { api, SPRING, reduce };

  // Move with a spring; under reduced motion just fade.
  function enter(el, from = { y: 12 }, spring = "gentle", delay = 0) {
    if (!M.animate) return;
    if (reduce()) return M.animate(el, { opacity: [0, 1] }, { ...FADE, delay });
    return M.animate(el, { opacity: [0, 1], transform: [`translateY(${from.y}px)`, "translateY(0px)"] }, { ...SPRING[spring], delay, opacity: FADE });
  }

  document.documentElement.classList.add("js");
  window.addEventListener("error", () => document.documentElement.classList.add("no-motion"));
  if (!M.animate) document.documentElement.classList.add("no-motion");

  document.addEventListener("alpine:init", () => {
    const Alpine = window.Alpine;

    // ---------- global store ----------
    Alpine.store("ui", {
      theme: (() => { try { return localStorage.getItem("rit-theme") || "dark"; } catch { return "dark"; } })(),
      online: navigator.onLine,
      motion: document.documentElement.dataset.motion || "system", // system | reduce | full
      setMotion(m) {
        this.motion = m;
        document.documentElement.dataset.motion = m;
        try { localStorage.setItem("rit-motion", m); } catch {}
      },
      toasts: [],
      palette: false,
      tour: false,
      setTheme(t) {
        this.theme = t;
        document.documentElement.dataset.theme = t;
        try { localStorage.setItem("rit-theme", t); } catch {}
      },
      toggleTheme() { this.setTheme(this.theme === "dark" ? "light" : "dark"); },
      toast(text, tone = "info", ms = 4200) {
        const id = Math.random().toString(36).slice(2);
        this.toasts.push({ id, text, tone });
        setTimeout(() => this.dismiss(id), ms);
      },
      dismiss(id) { this.toasts = this.toasts.filter((t) => t.id !== id); },
    });
    window.addEventListener("online", () => (Alpine.store("ui").online = true));
    window.addEventListener("offline", () => (Alpine.store("ui").online = false));
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); Alpine.store("ui").palette = true; }
    });

    // ---------- directives ----------
    // Press feedback: compress on press, spring release. Interruptible.
    Alpine.directive("press", (el) => {
      if (!M.animate) return;
      let a;
      const to = (s, sp) => { a?.stop?.(); if (!reduce()) a = M.animate(el, { transform: `scale(${s})` }, SPRING[sp]); };
      el.addEventListener("pointerdown", () => to(0.97, "snappy"));
      ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => el.addEventListener(ev, () => to(1, "soft")));
    });

    // Stagger children in (30-50ms apart).
    Alpine.directive("stagger", (el, { expression }) => {
      const kids = Array.from(el.children);
      if (!M.animate) return;
      kids.forEach((k, i) => enter(k, { y: 14 }, "gentle", 0.04 * i));
    });

    // Count up with tabular figures; skipped under reduced motion.
    Alpine.directive("count", (el, { expression }, { evaluate, cleanup }) => {
      const target = Number(evaluate(expression));
      const dec = Number(el.dataset.decimals || 0);
      const delay = Number(el.dataset.delay || 0);
      const fmt = (v) => v.toLocaleString("en", { minimumFractionDigits: dec, maximumFractionDigits: dec });
      el.textContent = fmt(target);
      if (!M.animate || reduce() || !isFinite(target) || target === 0) return;
      const c = M.animate(0, target, { duration: 0.9, delay, ease: [0.22, 1, 0.36, 1], onUpdate: (v) => (el.textContent = fmt(v)) });
      el.textContent = fmt(0);
      cleanup(() => c.stop?.());
    });

    // Grow a bar from the left, in sequence (data-delay seconds).
    Alpine.directive("grow", (el) => {
      el.style.transformOrigin = "left center";
      if (!M.animate || reduce()) return;
      M.animate(el, { transform: ["scaleX(0)", "scaleX(1)"] }, { ...SPRING.gentle, delay: Number(el.dataset.delay || 0) });
    });

    // Draw an SVG line once (first view this session only).
    Alpine.directive("draw", (el) => {
      const key = "draw:" + (el.dataset.drawId || "");
      let seen = false;
      try { seen = sessionStorage.getItem(key); sessionStorage.setItem(key, "1"); } catch {}
      if (!M.animate || reduce() || seen || !el.getTotalLength) return;
      const len = el.getTotalLength();
      el.style.strokeDasharray = len;
      M.animate(el, { strokeDashoffset: [len, 0] }, { duration: 0.9, ease: [0.22, 1, 0.36, 1] });
    });

    // Rain dial: fills like water, bottom to top.
    Alpine.directive("fill", (el, { expression }, { evaluate }) => {
      const pct = Math.max(0, Math.min(100, Number(evaluate(expression)) || 0));
      const to = `translateY(${100 - pct}%)`;
      el.style.transform = to;
      if (!M.animate || reduce()) return;
      M.animate(el, { transform: ["translateY(100%)", to] }, { ...SPRING.gentle, delay: 0.1 });
    });

    // Entrance for a single element.
    Alpine.directive("rise", (el) => enter(el, { y: 10 }));

    // ---------- components ----------
    Alpine.data("sheet", (name = "sheet") => ({
      open: false,
      origin: "50% 100%",
      startY: 0, lastY: 0, lastT: 0, vy: 0,
      show(ev) {
        if (ev?.currentTarget?.getBoundingClientRect) {
          const r = ev.currentTarget.getBoundingClientRect();
          this.origin = `${r.left + r.width / 2}px ${r.top + r.height / 2}px`;
          this.trigger = ev.currentTarget;
        }
        this.open = true;
        this.$nextTick(() => {
          const p = this.$refs.panel;
          if (!p) return;
          p.style.transformOrigin = window.innerWidth >= 768 ? this.origin : "50% 100%";
          if (M.animate) {
            if (reduce()) M.animate(p, { opacity: [0, 1] }, FADE);
            else if (window.innerWidth >= 768) M.animate(p, { opacity: [0, 1], transform: ["scale(.94)", "scale(1)"] }, { ...SPRING.snappy, opacity: FADE });
            else M.animate(p, { transform: ["translateY(100%)", "translateY(0%)"] }, SPRING.gentle);
          }
          (p.querySelector("[data-autofocus]") || p).focus();
        });
      },
      async close() {
        if (!this.open) return;
        const p = this.$refs.panel;
        if (p && M.animate && !reduce()) await M.animate(p, { transform: "translateY(100%)", opacity: 0 }, { ...SPRING.snappy, opacity: FADE }).finished.catch(() => {});
        this.open = false;
        this.trigger?.focus?.();
      },
      dragStart(e) { this.startY = this.lastY = e.clientY; this.lastT = performance.now(); this.vy = 0; e.target.setPointerCapture?.(e.pointerId); },
      dragMove(e) {
        if (!this.startY) return;
        const dy = Math.max(0, e.clientY - this.startY);
        const now = performance.now();
        this.vy = (e.clientY - this.lastY) / Math.max(now - this.lastT, 1);
        this.lastY = e.clientY; this.lastT = now;
        this.$refs.panel.style.transform = `translateY(${dy}px)`;
      },
      async dragEnd(e) {
        const dy = e.clientY - this.startY;
        this.startY = 0;
        if (dy > 120 || this.vy > 0.6) return this.close();
        if (M.animate) M.animate(this.$refs.panel, { transform: "translateY(0px)" }, SPRING.soft);
        else this.$refs.panel.style.transform = "";
      },
      trap(e) {
        const f = [...this.$refs.panel.querySelectorAll('a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      },
    }));

    // Accept / snooze / override with optimistic UI and graceful rollback.
    Alpine.data("decision", (cfg) => ({
      state: cfg.decided ? "done" : "idle", // idle | loading | done | error
      kind: cfg.kind || "",
      error: "",
      override: { action: "SKIP", litres: cfg.litres || 0, reason: "", note: "" },
      step: Math.max(1, Math.round((cfg.litres || 0) / 10) * 5) || 50,
      async send(kind, extra = {}) {
        const prev = { state: this.state, kind: this.kind };
        this.state = "loading"; this.kind = kind; this.error = "";
        try {
          await api(cfg.url, { recommendation: cfg.rec, kind, ...extra });
          this.state = "done";
          Alpine.store("ui").toast(kind === "accept" ? "Recorded. Thank you." : kind === "snooze" ? "We will remind you in 3 hours." : "Your choice is saved. You are in control.", "success");
          this.$dispatch("decided", { kind });
        } catch (e) {
          this.state = prev.state; this.kind = prev.kind;
          this.error = e.message || "We could not save that. Check your connection and try again.";
          Alpine.store("ui").toast(this.error, "error");
        }
      },
      accept() { return this.send("accept"); },
      snooze() { return this.send("snooze"); },
      async saveOverride() {
        await this.send("override", { farmer_action: this.override.action, litres: this.override.action === "IRRIGATE" ? Number(this.override.litres) : null, reason: this.override.reason, note: this.override.note });
        if (this.state === "done") this.$dispatch("close-sheet");
      },
      bump(n) { this.override.litres = Math.max(0, Math.round((Number(this.override.litres) || 0) + n)); },
    }));

    // Soil moisture slider with weight and a magnetic snap at threshold bands.
    Alpine.data("moisture", (cfg) => ({
      value: cfg.value, min: cfg.min, max: cfg.max, snaps: cfg.snaps || [], url: cfg.url, saving: false, saved: false, snapped: "",
      get pct() { return ((this.value - this.min) / (this.max - this.min)) * 100; },
      pos(v) { return ((v - this.min) / (this.max - this.min)) * 100; },
      onInput() {
        const near = this.snaps.find((s) => Math.abs(this.value - s.at) <= 0.8);
        if (near) { if (this.value !== near.at) this.value = near.at; if (this.snapped !== near.label) { this.snapped = near.label; navigator.vibrate?.(8); this.ripple(); } }
        else this.snapped = "";
        this.saved = false;
      },
      ripple() {
        const el = this.$refs.ripple;
        if (!el || !M.animate || reduce()) return;
        M.animate(el, { transform: ["scale(.6)", "scale(1.6)"], opacity: [0.45, 0] }, { duration: 0.55, ease: "easeOut" });
      },
      step(n) { this.value = Math.min(this.max, Math.max(this.min, Math.round((Number(this.value) + n) * 10) / 10)); this.onInput(); },
      async save() {
        this.saving = true;
        try {
          await api(this.url, { value: Number(this.value) });
          this.saved = true; this.ripple();
          Alpine.store("ui").toast("Soil reading saved. Updating your advice.", "success");
          setTimeout(() => location.reload(), 700);
        } catch (e) { Alpine.store("ui").toast(e.message, "error"); }
        this.saving = false;
      },
    }));

    // Ask-a-question assistant with streaming.
    Alpine.data("ask", (cfg) => ({
      messages: cfg.history || [], input: "", busy: false, error: "",
      async send(q) {
        q = (q ?? this.input).trim();
        if (!q || this.busy) return;
        if (!navigator.onLine) { this.error = "You are offline. Questions need a connection. Your last advice is still saved above."; return; }
        this.input = ""; this.error = ""; this.busy = true;
        this.messages.push({ role: "user", text: q });
        const reply = { role: "assistant", text: "" };
        this.messages.push(reply);
        const idx = this.messages.length - 1;
        this.scroll();
        try {
          const r = await fetch(cfg.url, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() }, body: JSON.stringify({ field: cfg.field, question: q }), credentials: "same-origin" });
          if (!r.ok || !r.body) throw new Error("The assistant could not answer just now. Please try again in a moment.");
          const reader = r.body.getReader(); const dec = new TextDecoder();
          for (;;) { const { done, value } = await reader.read(); if (done) break; this.messages[idx].text += dec.decode(value, { stream: true }); this.scroll(); }
        } catch (e) {
          this.messages.splice(idx, 1);
          this.error = e.message || "Something went wrong.";
        }
        this.busy = false;
      },
      scroll() { this.$nextTick(() => { const l = this.$refs.log; if (l) l.scrollTop = l.scrollHeight; }); },
    }));

    // Command palette (Ctrl/Cmd+K)
    Alpine.data("palette", (items) => ({
      q: "", sel: 0, items,
      get results() { const q = this.q.toLowerCase(); return this.items.filter((i) => i.label.toLowerCase().includes(q)); },
      go(i) { if (i) { Alpine.store("ui").palette = false; location.href = i.href; } },
      move(n) { this.sel = (this.sel + n + Math.max(this.results.length, 1)) % Math.max(this.results.length, 1); },
    }));

    // Judge walkthrough overlay
    Alpine.data("tour", (steps) => ({
      i: 0, steps,
      get step() { return this.steps[this.i]; },
      next() { if (this.i < this.steps.length - 1) { this.i++; this.nav(); } else this.end(); },
      prev() { if (this.i > 0) { this.i--; this.nav(); } },
      nav() { const s = this.step; if (s.href && location.pathname + location.search !== s.href) { try { sessionStorage.setItem("rit-tour", this.i); } catch {} location.href = s.href; } },
      end() { Alpine.store("ui").tour = false; try { sessionStorage.removeItem("rit-tour"); } catch {} },
      init() {
        let saved = null; try { saved = sessionStorage.getItem("rit-tour"); } catch {}
        if (saved !== null) { this.i = Number(saved); Alpine.store("ui").tour = true; }
      },
    }));

    Alpine.data("tabs", (initial) => ({ tab: initial, set(t) { this.tab = t; } }));
  });

  // Register the service worker (PWA shell + cached last recommendations)
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }
})();

/* Nova Diabolo Team — site behaviour. Plain ES2017, no dependencies. */
(function () {
  "use strict";

  /* current year in the footer */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* hairline under the top bar once you scroll */
  var topbar = document.getElementById("topbar");
  var onScroll = function () { topbar.classList.toggle("is-stuck", window.scrollY > 4); };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* mobile menu */
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("topnav");

  function closeNav() {
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open menu");
  }

  toggle.addEventListener("click", function () {
    var open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  });

  nav.addEventListener("click", function (e) { if (e.target.closest("a")) closeNav(); });

  /* close the mobile menu on Escape */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && nav.classList.contains("is-open")) { closeNav(); toggle.focus(); }
  });

  /* ------------------------------------------------------------------
     Forms. Both the booking and the join form post over fetch so the
     visitor stays on the page; if anything fails we fall back to a normal
     form POST, which still delivers.
     ------------------------------------------------------------------ */
  /* Show the event fields only when someone is actually booking, and label the
     notification email with what they picked. Hidden fields are disabled so the
     browser skips validating them and they stay out of the payload. */
  var reason = document.getElementById("reason");
  var bookingFields = document.getElementById("bookingFields");
  var subject = document.getElementById("formSubject");

  if (reason && bookingFields && subject) {
    var SUBJECTS = {
      "Booking a performance":   "Booking inquiry from the website",
      "Lessons or a workshop":   "Lessons / workshop inquiry from the website",
      "Coming to yoyo with you": "Someone wants to come yoyo with us",
      "Something else":          "Message from the Nova Diabolo site"
    };
    reason.addEventListener("change", function () {
      var booking = reason.value === "Booking a performance";
      bookingFields.hidden = !booking;
      bookingFields.querySelectorAll("input, select").forEach(function (el) {
        el.disabled = !booking;
      });
      subject.value = SUBJECTS[reason.value] || SUBJECTS["Something else"];
    });
  }

  document.querySelectorAll("form.relay-form").forEach(function (form) {
    var statusEl = form.querySelector(".form-status");
    var btn = form.querySelector(".submit");
    var btnLabel = btn.textContent;

    form.addEventListener("submit", function (e) {
      var key = form.querySelector('[name="access_key"]');

      // No key yet: let the browser POST normally rather than fail silently.
      if (!key || key.value.indexOf("YOUR_ACCESS_KEY") !== -1) return;

      e.preventDefault();
      statusEl.className = "form-status";
      statusEl.textContent = "";
      btn.disabled = true;
      btn.textContent = "Sending";

      fetch(form.action, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: new FormData(form)
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          // Web3Forms answers 200 with {success:false} on a rejected submission,
          // so the flag matters more than the status code.
          if (!data.success) throw new Error(data.message || "rejected");
          form.reset();
          // reset() restores the select but doesn't fire change, so the
          // booking-only fields would stay open and enabled
          var sel = form.querySelector("#reason");
          if (sel) sel.dispatchEvent(new Event("change"));
          statusEl.className = "form-status is-ok";
          statusEl.textContent = "Thanks, that's sent. We'll be in touch.";
          btn.textContent = "Sent";
        })
        .catch(function () {
          statusEl.className = "form-status is-error";
          statusEl.innerHTML = "That didn't send. Try us on " +
            '<a href="https://www.instagram.com/novadiaboloteam/" target="_blank" rel="noopener">Instagram</a> instead.';
          btn.disabled = false;
          btn.textContent = btnLabel;
        });
    });
  });
})();

/* ---------------------------------------------------------------------------
   Dev-only live reload. Runs ONLY on localhost, so it is inert on the live
   site. Watches the page, the stylesheet and this script, and reloads when any
   of them changes. Safe to delete.
   --------------------------------------------------------------------------- */
(function () {
  var host = location.hostname;
  if (host !== "127.0.0.1" && host !== "localhost" && host !== "[::1]") return;

  var WATCH = [location.pathname, "assets/css/styles.css", "assets/js/main.js"];
  var seen = {};

  setInterval(function () {
    WATCH.forEach(function (url) {
      fetch(url + "?_=" + Date.now(), { method: "HEAD", cache: "no-store" })
        .then(function (r) {
          var tag = r.headers.get("last-modified") || r.headers.get("etag");
          if (!tag) return;
          if (seen[url] && tag !== seen[url]) location.reload(true);
          seen[url] = tag;
        })
        .catch(function () { /* server restarting — ignore */ });
    });
  }, 1200);
})();

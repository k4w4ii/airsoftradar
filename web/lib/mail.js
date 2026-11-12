// E-mail küldés az ár- és készletfigyelőhöz. Szolgáltató: Resend (RESEND_API_KEY) vagy Brevo (BREVO_API_KEY) –
// mindkettőnek van ingyenes kerete. Worker-titokként kell megadni (TELEPITES.md 12. pont); nélküle az értesítő ki van kapcsolva.
// Feladó: MAIL_FROM (pl. „AirsoftHunter <ertesito@airsofthunter.com>”), a domain legyen hitelesítve a szolgáltatónál.
const env = () => (typeof process !== "undefined" ? process.env : {}) || {};

export function mailProvider() {
  const e = env();
  if (String(e.RESEND_API_KEY || "").trim()) return "resend";
  if (String(e.BREVO_API_KEY || "").trim()) return "brevo";
  return null;
}

export const mailEnabled = () => Boolean(mailProvider());

export function mailFrom() {
  return String(env().MAIL_FROM || "AirsoftHunter <ertesito@airsofthunter.com>").trim();
}

function splitFrom(from) {
  const m = /^\s*(.*?)\s*<([^>]+)>\s*$/.exec(from);
  return m ? { name: m[1] || "AirsoftHunter", email: m[2] } : { name: "AirsoftHunter", email: from };
}

/** Egy e-mail. headers: pl. { "List-Unsubscribe": "<https://…>" }. Visszaad: true, ha a szolgáltató elfogadta. */
export async function sendMail({ to, subject, html, text, headers = {} }, fetcher = fetch) {
  const provider = mailProvider();
  if (!provider) return false;
  const e = env();
  const from = mailFrom();
  let res;
  if (provider === "resend") {
    res = await fetcher("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${String(e.RESEND_API_KEY).trim()}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from, to: [to], subject, html, text, headers }),
    });
  } else {
    res = await fetcher("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": String(e.BREVO_API_KEY).trim(), "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ sender: splitFrom(from), to: [{ email: to }], subject, htmlContent: html, textContent: text, headers }),
    });
  }
  if (!res.ok) console.error(`mail ${provider} ${res.status}: ${(await res.text()).slice(0, 300)}`);
  return res.ok;
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** Egyszerű, levelezőbarát HTML-sablon: cím, bekezdések, egy gomb, lábléc. */
export function mailHtml({ title, paragraphs, button, footer }) {
  return `<!doctype html><html><body style="margin:0;background:#f4f3ef;font-family:Arial,Helvetica,sans-serif;color:#1f1f1c">
<div style="max-width:560px;margin:0 auto;padding:24px">
<p style="font-weight:bold;font-size:18px;margin:0 0 16px">AIRSOFT<span style="color:#b38b3c">HUNTER</span></p>
<div style="background:#fff;border-radius:10px;padding:24px">
<h1 style="font-size:20px;margin:0 0 12px">${esc(title)}</h1>
${paragraphs.map((p) => `<p style="line-height:1.5;margin:0 0 12px">${esc(p)}</p>`).join("\n")}
${button ? `<p style="margin:20px 0"><a href="${esc(button.href)}" style="background:#b38b3c;color:#fff;text-decoration:none;padding:12px 20px;border-radius:8px;display:inline-block;font-weight:bold">${esc(button.label)}</a></p>` : ""}
</div>
<p style="font-size:12px;color:#77756d;line-height:1.5;margin:16px 0 0">${footer}</p>
</div></body></html>`;
}

export { esc };

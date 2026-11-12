// A Cloudflare Worker belépési pontja: a Next.js oldal (OpenNext) + időzített indító.
// Az időzítő (wrangler.jsonc → triggers.crons, 02:17 UTC) pontosan indítja a GitHub „daily-scrape” futást –
// a GitHub saját ütemezője órákat késhet. Kell hozzá a GH_TOKEN Worker-titok (TELEPITES.md 3/b pont).
// @ts-ignore – a .open-next/worker.js a build során készül
import { default as handler } from "./.open-next/worker.js";

const REPO = "k4w4ii/airsoftradar";
const WORKFLOW = "daily-scrape.yml";

export default {
  fetch: handler.fetch,

  async scheduled(_event, env, ctx) {
    if (!env.GH_TOKEN) {
      console.error("GH_TOKEN hiányzik: a napi letöltés nem indult el (Worker → Settings → Variables and Secrets)");
      return;
    }
    ctx.waitUntil((async () => {
      const res = await fetch(`https://api.github.com/repos/${env.GH_REPO || REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "airsofthunter-cron",
        },
        body: JSON.stringify({ ref: "main" }),
      });
      if (!res.ok) console.error(`GitHub indítás sikertelen: ${res.status} ${(await res.text()).slice(0, 300)}`);
      else console.log("daily-scrape elindítva");
    })());
  },
};

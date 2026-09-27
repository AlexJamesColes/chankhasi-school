# Chankhasi Primary School website

A one-page website for Chankhasi Primary School, a community school near the shore of Lake Malawi, about 15 km south of Nkhotakota town.

Hand-written static HTML and CSS with no build step, so it can be hosted free on GitHub Pages. Before any photos, the first visit is about 70 KB, which matters in Malawi where mobile data is slow and expensive. Photos are lazy-loaded WebP, sized for phones and desktops separately.

**Status: draft for review.** Facts still to be confirmed are wrapped in `<span class="tbc" data-note="...">`. While `<html>` carries the `draft` class they show in yellow, and hovering or tapping one shows the note explaining what needs checking.

## Preview locally

Run:

```bash
python3 -m http.server 8940
```

then open http://localhost:8940. 

## Files

| Path | What it is |
| --- | --- |
| `index.html` | The whole site: hero, about, story, school life, friends, how to help, contact |
| `404.html` | Page-not-found. Its `<base href>` is `/`, since the site sits at the root of its address |
| `assets/site.css` | All styles |
| `assets/site.js` | Menu, share button, contact form, draft review notes. The page works without it |
| `assets/fonts/` | Fraunces, subset to Latin and trimmed to about 47 KB (SIL Open Font Licence) |
| `assets/img/` | Favicon, home-screen icon and the link-preview card (`og.jpg`) |
| `assets/img/photos/` | The site's photos, cropped and compressed, at two or three sizes each |
| `tools/build_map.py` | Draws the map of Malawi from Natural Earth data and writes it into `index.html` between the `MAP:START` and `MAP:END` markers |
| `tools/render_images.py` | Renders `og.jpg` and the icons with headless Chrome (needs the preview server running) |
| `tools/process_photos.py` | Crops and compresses cleared originals from `tools/photos-src/` (kept out of git) into `assets/img/photos/` |
| `tools/build_preview.py` | Bundles the page into one self-contained HTML file (inline CSS, JS and fonts) for sharing as a single file |

Rebuild the map after changing its labels or the school's position:

```bash
python3 tools/build_map.py
```

Re-render the link preview and icons after changing the hero art or title:

```bash
python3 tools/render_images.py
```

## Staging

The draft is served by Cloudflare Pages at https://chankhasi-school.pages.dev. Only the website files are uploaded (`index.html`, `404.html`, `robots.txt` and `assets/`), not the tools or notes:

```bash
rm -rf .deploy && mkdir .deploy && cp -R index.html 404.html robots.txt assets .deploy/
npx wrangler pages deploy .deploy --project-name chankhasi-school --branch main
```

It carries the draft banner and a `noindex` tag, so search engines should not list it.

## Screens tested

Checked for layout and sideways scrolling at 360, 390 and 430 px phones (portrait and landscape), iPad mini, iPad Air and iPad Pro in both orientations, and 1366 to 1920 px desktops. Text and map sit side by side from 700 px, cards reflow from one to two to four columns, and the menu collapses below 920 px.

## To confirm before launch

Everything below is highlighted on the draft.

**About the school**
- [ ] Nothing outstanding

**Our story**
- [ ] Kingswood School (Bath) summer visits through Open Arms Malawi: still happening?
- [ ] World Servants teachers' houses: which year?
- [ ] Lancing College, 2024: their reports say the work was at Chankhasi Secondary School. Keep it or take it out?

**School life** (several lines come from the school's 2016 website)
- [ ] The garden plot, the painted tiles and "a brick a day": still true?
- [ ] Curriculum and sport lines ring true
- [ ] Whether to mention the two pupils' essays published by The Young Darwinian. Taken off the page until the school and the families agree

**How to help**
- [ ] The school's real needs, in order of priority
- [ ] Today's cost of a roof truss (£420 in 2016) and a desk (£40 in 2016), and whether both schemes still run
- [ ] Whether online giving is wanted (the page only says to get in touch)

**Contact**
- [ ] Postal address (Nkhandwe Village, P.O. Box 460, Nkhotakota, from 2016)
- [ ] Whether donations@chankhasi-school.org still works, and who reads it
- [ ] WhatsApp number (optional)

**Also useful**
- [ ] The school's badge or logo, if it has one (the sun-over-the-lake mark is a stand-in)
- [ ] Photos for the two dashed spaces: a lesson, and visitors with pupils. Only the school sign and school buildings photos are cleared. No photos of people go on the site without explicit approval, and families should agree to any photo showing children's faces.

## The old website and domain

chankhasi-school.org is still registered (GoDaddy, since June 2014, paid up to 3 June 2027) and still has GoDaddy email records, but the web server it points to no longer answers, so the old site has been offline for years. Whoever holds that GoDaddy account can point the domain at this site: change only the website records (A and CNAME) to GitHub Pages and leave the email (MX) records alone.

## Launch checklist

1. Fill in or remove every `tbc` item. `grep -n 'class="tbc' index.html` lists them. The spans are harmless once the draft class is gone, so they can stay.
2. Remove `class="draft"` from `<html>` and delete the `noindex` line in `index.html`.
3. Connect the contact form: create a form at Formspree (or similar) sending to the school's inbox, and paste its endpoint into `data-endpoint` on `#contact-form`. Until then the form politely says it is not connected.
4. Move from staging to chankhasi-school.org: add it as a custom domain on the Cloudflare Pages project and point the domain's website records (A/CNAME) where Cloudflare says, leaving the MX email records alone.
5. At the same time: change `og:url` and `og:image` in `index.html` to `https://chankhasi-school.org/...`, and add `<link rel="canonical" href="https://chankhasi-school.org/">`.
6. Optional: an email address on the domain (for example hello@) that forwards to any inbox, using Cloudflare Email Routing or the registrar's forwarding.

## Photo guidance

Photos will make the biggest difference to the site. A few rules keep the children safe and the pages fast:

- Get permission from parents or guardians for any photo of a child, and from staff for photos of them.
- Never put a child's full name next to their photo. First names only, and only with permission.
- Show pupils learning, playing and achieving, with dignity. Avoid anything that shows a child in distress.
- Strip location data from every photo before publishing (re-saving through the image pipeline does this).
- Resize to about 1600 px on the long edge and compress to roughly 150 to 250 KB each.

To add a photo, put the original in `tools/photos-src/`, add its crop and sizes to `tools/process_photos.py`, run it, and reference the sizes with `srcset` like the existing ones.

## Sources

The current pupil and teacher numbers and the two photos were provided for the site (September 2026). Other information the draft uses:

- The school's own website, chankhasi-school.org, as it stood in 2016

- Lancing College, [Adventures in Malawi](https://www.lancingcollege.co.uk/news/adventures-malawi) and [2024 Malawi Adventures](https://www.lancingcollege.co.uk/news/2024-malawi-adventures/)
- Open Arms Malawi, [School visitors make a lasting impression](https://www.openarmsmalawi.org/news/school-visitors-make-a-lasting-impression) (2016)
- Morna International College, [blog, September 2009](https://mornainternationalibiza.blogspot.com/2009/09/)
- World Servants, [Chankhazi project page](https://www.worldservants.nl/malawi/MA124) (no longer online)
- Map data: [Natural Earth](https://www.naturalearthdata.com/) (public domain)

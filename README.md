# Elemental AI Lab website

Jekyll site (built on the Greene Lab Website Template), deployed to GitHub Pages by
`.github/workflows/pages.yml` on every push to `main` and every Friday (08:00 Singapore
time), so deadlines and the move note stay current without new commits.

Run locally: `bundle install && bundle exec jekyll serve`, then open http://localhost:4000.

## Maintaining the site

| Task | Where |
|---|---|
| Recruiting line, emails, PhD subject line, admissions deadline | `_config.yaml` → `lab` |
| Move date and affiliations (wording switches automatically) | `_config.yaml` → `move` |
| PI position line before/after the move | `_config.yaml` → `pi` |
| Group photo (shown on Home when set) | `_config.yaml` → `group_photo` |
| Research areas and selected work | `_data/research.yaml` |
| News | `_data/news.yaml` (newest first, Markdown links allowed) |
| Funding schemes | `_data/funding.yaml` |
| PI bio | `team/christian-naesseth.md` |

**Add a member.** Create `_members/first-last.md` with `name`, `family` (for sorting), `role`
(a key from `_data/roles.yaml`), `group: current`, `initials`, and optionally `image`
(`/images/people/first-last.webp`, square, about 160 px), `cosupervisor`, `institution`
(only if based at another university) and `links` (`home-page`, `google-scholar`, …).
A card links to the person's own page or Google Scholar if one is given.

**Move someone to alumni.** Change `group: current` to `group: alum`. The card then shows
the former role ("Former PhD student").

**Add a news item.** Add `- date: 'YYYY-MM-DD'` and `text:` at the top of `_data/news.yaml`;
optional `papers:` with `title`, `url`, `note`.

**Update a funding scheme.** Edit its entry in `_data/funding.yaml`. Only add a `deadline`
that the official page states; after that date the page shows "Closed – check for the next
call". Update `checked` when you compare an entry with its official page.

**Add a page.** Create `name/index.md` with `title` and front matter `nav: { order: 4 }`;
it appears in the navigation automatically.

**Change the move note or recruiting text.** Edit `lab.recruiting`, `lab.join_lead` or
`move` in `_config.yaml`; leave `recruiting` empty to hide the recruiting line everywhere.

## Masthead artwork

The banner is generated, not drawn: `tools/banner/generate.py` (Python 3.9+, `numpy`,
`contourpy`) writes every composition to `images/banner/` from fixed seeds. A soft stream
of sample paths flows from a Gaussian cloud along a time axis (dotted slices mark the
particles at successive moments), fades behind the logo and the navigation, and converges
on a molecule, a contour map and a sampled signal.

- From 1024 px the Home masthead is one proportional picture (`masthead-wide.svg`).
- Below 1024 px its height changes smoothly with the width (300 px down to 273 px) and the
  artwork is drawn at that height and cropped at the sides (`masthead-medium.svg` for
  tablets, `masthead-narrow.svg` for phones); the cloud and the end of the signal may run
  off the edges, everything else stays in view.
- Sub-pages use `masthead-compact.svg`: the ribbon and the violet path only.

    python3 tools/banner/generate.py --check

`--check` prints, per composition, the number of paths and dots (always equal), the number
of nodes, the fewest paths reaching any node, and any point outside the edge margin.

## Single-file preview

    bundle exec jekyll build
    python3 tools/preview/build_preview.py --site _site --out preview.html --variants

`--variants` adds a Primary/Sparse switch for the Home banner (review only).

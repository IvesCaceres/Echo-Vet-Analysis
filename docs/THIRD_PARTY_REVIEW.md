# Dependency licensing and provenance review

MIT is adopted for original project software only, following the owner's explicit authorship/licensing declaration. This is a technical inventory, not a legal opinion or proof of original-code ownership.

No third-party environment, library source/binary, font file or original Git history is vendored. requirements.txt requests separately installed packages. Upstream licenses and notices remain applicable to those packages and are not replaced by this project proposal.

## Exact installed runtime metadata reviewed

| Distribution | Version | Observed license metadata |
|---|---|---|
| matplotlib | 3.10.9 | Python Software Foundation License |
| python-dateutil | 2.9.0.post0 | BSD License; Apache Software License |
| six | 1.17.0 | MIT License |
| pyparsing | 3.3.2 | MIT |
| pillow | 12.2.0 | MIT-CMU |
| packaging | 26.1 | Apache-2.0 OR BSD-2-Clause |
| numpy | 2.4.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| kiwisolver | 1.5.0 | BSD License |
| fonttools | 4.62.1 | MIT |
| cycler | 0.12.1 | BSD License |
| contourpy | 1.3.3 | BSD License |
| pandas | 3.0.2 | BSD License |
| tzdata | 2026.1 | Apache-2.0 |

The active installed dependency closure contains 13 distributions. Exact installed notice-file locations, sizes and hashes were inspected privately. Classifiers are metadata evidence, not complete grants; NumPy wheels and other distributions can contain additional component notices. Python, installers, optional extras, future platforms and bundled distributions are outside this source-only inventory.

No obvious runtime-import licensing blocker to the software MIT scope was observed. This is not exhaustive compatibility certification. Before vendoring packages, fonts, wheels or installers, preserve and review complete upstream notices and component terms. Matplotlib-rendered aggregate PNGs are included; Matplotlib/font software files are not.

## Source-code rights gate

The four previously allowlisted source notebook hashes still match. Their code cells contain no detected copyright/SPDX, explicit attribution or external-URL markers. That does not prove exclusive authorship or a right to remove notices from unexamined upstream sources. The owner has now confirmed original code authorship with Claude assistance and authorized MIT, naming Ives Cáceres as copyright holder for 2026. No additional third-party fragments were identified in the reviewed source; this is not a certification of unexamined upstream rights. Installed dependency notice hashes were reverified unchanged at adoption.

## References

- NumPy: https://numpy.org/doc/stable/license.html
- Matplotlib: https://matplotlib.org/stable/project/license.html
- MIT template: https://choosealicense.com/licenses/mit/

Online stable documentation may describe newer versions than the installed versions above. Exact-version conclusions use the installed distribution metadata/notices. See LICENSING.md and RESULTS_PROVENANCE.md.

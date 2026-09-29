# Browser assets for the extraction report

These files are pinned and embedded in the extraction HTML report so it works offline. The report builder converts PatternFly's relative font and image URLs to data URLs. No React package or build step is used.

| Asset | Version | Source | License |
| --- | --- | --- | --- |
| PatternFly core CSS and referenced assets | 6.6.1 | [`@patternfly/patternfly`](https://www.npmjs.com/package/@patternfly/patternfly/v/6.6.1) | MIT; see `patternfly-6.6.1/LICENSE.txt` |
| Alpine browser bundle | 3.17.4 | [`alpinejs`](https://www.npmjs.com/package/alpinejs/v/3.17.4) | MIT; see `alpine-3.17.4/LICENSE.md` |
| Red Hat Display, Text and Mono fonts | Bundled with PatternFly 6.6.1 | [Red Hat Font](https://github.com/RedHatOfficial/RedHatFont) | SIL OFL 1.1; see `patternfly-6.6.1/REDHAT-FONT-OFL.txt` |
| Font Awesome webfont | Bundled with PatternFly 6.6.1 | [Font Awesome Free](https://github.com/FortAwesome/Font-Awesome) | SIL OFL 1.1; see `patternfly-6.6.1/FONT-AWESOME-LICENSE.txt` |

The license notices are also embedded in generated extraction HTML reports. When upgrading PatternFly, review the CSS `url(...)` references and update the vendored files and notices together.

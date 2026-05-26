# Notyf 3.10.0 (vendored)

Local copy of the [Notyf](https://github.com/caroso1222/notyf) toast library used by
ExamMaker's `NotificationManager` so the offline LAN deployment never needs to reach
out to a CDN. See the `notyf-notification-system` spec for the full design.

## Version

- **Library:** `notyf`
- **Version:** `3.10.0`
- **Source:** https://github.com/caroso1222/notyf
- **npm package:** https://www.npmjs.com/package/notyf/v/3.10.0

## Files

| File           | Bytes | SHA-256                                                            |
| -------------- | ----- | ------------------------------------------------------------------ |
| `notyf.min.css`| 5159  | `23092f64d442ff74b6e8ed605b08c120d9ab3d9e3362f3d7e33ffdf0e2961e44` |
| `notyf.min.js` | 7646  | `52796990c2dab1a4f1d99aa8bf105751c4398eade829769967569610d3451131` |

The bytes match both `https://cdn.jsdelivr.net/npm/notyf@3.10.0/` and
`https://unpkg.com/notyf@3.10.0/`. Neither file ships a
`//# sourceMappingURL=...` comment in version 3.10.0, so no stripping is required
to satisfy spec requirement 1.4 (DevTools will not try to fetch a source map).

The CSS uses inline SVG `mask-image` glyphs only; there are no external font, image,
or icon URLs. Verified with the regexes `https?://`, `//cdn.`, and `//fonts.` against
both files.

## Loading

Both files are referenced from `templates/base.html` through Django's `{% static %}`
tag and resolved through `STATIC_URL`. They must be loaded before
`static/css/main.css` (CSS) and before `static/js/utils.js` (JS) so that the
`NotificationManager` wrapper can construct a `Notyf` instance on first use.

## Upgrading

When bumping versions:

1. Place new minified bundles under `static/vendor/notyf/notyf-<new-version>/`
   (a fresh directory, do not overwrite this one until the new version ships).
2. Re-run the SHA-256 checks and update this README.
3. Verify there are no `sourceMappingURL`, `http://`, `https://`, `//cdn.`, or
   `//fonts.` substrings in either file. Strip any `sourceMappingURL` comment from
   the JS bundle if a future release reintroduces one.
4. Bump the path inside `templates/base.html` and run the asset and template smoke
   tests in `tests/test_notyf_assets.py` and `tests/test_base_template_load_order.py`.

## License

Notyf is distributed under the MIT License. The upstream license text is bundled in
the npm package and reproduced verbatim at
https://github.com/caroso1222/notyf/blob/master/LICENSE.

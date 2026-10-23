# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
...

## [v0.3.0] - 2026-10-23

### Changed

- Author email changed.

### Fixed

- Links to repo and issues corrected.

## [v0.2.0] - 2026-10-23

### Added

- Unit tests covering field rendering, widget media, the scoped CSS view, URL rewriting, and the template tag.
- Playwright integration tests for the full add-block workflow (text, rich text, image).
- Demo project updated to use django-crispy-forms with Bootstrap 5, showing how `helper.include_media = False` prevents media from being injected before the editor scripts are ready.

### Changed

- Widget JavaScript and CSS are now served as static files loaded via Django's `Media` class, so they are included only once per page even when multiple fields appear in the same form.

### Fixed

- Block chooser popup now positions correctly when the form sits inside a centred container (e.g. a Bootstrap layout) instead of overflowing past the container's left edge.
- Draftail rich-text toolbar correction now activates whenever the toolbar is shifted left of the text selection, not only when it is clipped to within 10 px of the viewport edge.
- Tippy-based popups (block chooser, Draftail toolbar) now receive Wagtail's scoped CSS because they are wrapped in the scope class when appended to `<body>`.
- Django 6.1 compatibility: `Media._js` returns `Script` objects rather than strings in Django 6.1+.

## [v0.1.0] - 2026-10-18

### Added

- Initial release with StreamField editor support outside the Wagtail admin.

<!--
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
-->

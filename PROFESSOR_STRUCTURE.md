# Professor-style structure reference

This project should follow the organization observed in the reference project
`Esame-WebApp-main.zip`, adapting the topic from podcasts to Prague tours.

## File organization

- Keep the Flask application simple and explicit.
- Prefer one main route file, like `app.py` in the reference project.
- Prefer one DAO/database file, like `db_dao.py`, for SQLite access.
- Keep user/session representation in a small model file when login is needed.
- Keep templates flat and named by page: `homepage.html`, `login.html`,
  `profilo.html`, etc.
- Group static files by type and page/domain:
  - `static/_style-css/` for CSS
  - `static/_javascript/` for JavaScript
  - domain folders for uploaded or displayed media

## Code style

- Route functions should gather form/request data, call DAO functions, flash or
  redirect on invalid input, and render templates with simple dictionaries/lists.
- SQL should live in DAO functions with clear names such as `recupera_*`,
  `aggiungi_*`, `modifica_*`, `elimina_*`, or their English equivalents if the
  rest of this project stays English.
- DAO functions should open a SQLite connection, enable foreign keys, execute
  the query, close cursor/connection, and return either rows, dictionaries, or a
  boolean success flag.
- Avoid hiding important behavior behind unnecessary abstractions.

## Database modeling rules for this project

- Do not store the same meaning in two tables unless it has a different purpose.
- A tour owns general marketing data: title, description, meeting point,
  duration, capacity, accessibility flags, guide.
- A tour stop owns stop-specific data: stop order, stop title, and stop-specific
  description. This description must not duplicate the tour description.
- A schedule owns recurring rules: weekday, start time, language, duration,
  capacity, active flag.
- An occurrence owns one concrete date/time generated from a schedule:
  `starts_at`, `ends_at`, status, and any occurrence-specific capacity override.
- If both schedule and occurrence appear to have a time column, use schedule time
  for the recurring rule and occurrence datetime for the actual booked instance.
- Templates and dashboard queries should read from the normalized source rather
  than from duplicated static dictionaries.

## Refactor target

When cleaning this project, make it look closer to the professor example:

- Replace large mixed backend modules with a route layer plus DAO layer.
- Move schema creation and seed data into clear database functions.
- Remove or reduce hardcoded dashboard dictionaries once equivalent database
  queries exist.
- Keep the implementation understandable for an exam-style Flask/SQLite project.

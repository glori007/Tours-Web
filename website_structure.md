# Walk Prague — Website structure

Here the description of the main pages of the web application and the elements on each are displayed in details . 

## Homepage (`/`) — visible to everyone, including unregistered users
- **Header / navbar:**
  - Site name + logo (Walk Prague);
  - When logged out: **Sign in**, **Register**;
  - When logged in: **My profile / dashboard** link and **Sign out** (adapts to participant / guide / admin).
- **Hero section:** rotating background images and a short introduction.
- **Filters (aside):** explore tours by:
  - **Date** (date-range picker);
  - **Duration**;
  - **Language**;
  - Tour theme / category, accessibility, start time, and **availability status**.
- **Main — the tours (brief version):**
  - A card per tour: cover image, language flags, title, rating, duration, short description;
  - Pagination ("Load more tours").
- **Footer:** social icons and quick links.

## Register (`/register`) — no login
- Choice of account type: **Participant** or **Guide**.
- Form: **first name**, **last name**, **email** (unique), **password** (+ confirm).
- Additional fields for a **guide**: **languages spoken** (from the five allowed), specialties, and a profile photo.

## Login (`/signin`, and `/admin-access` for the administrator) — no login
- Account-type toggle (Participant / Guide).
- Form: **email**, **password**.
- The administrator logs in separately at `/admin-access` (admin email + password).

## Tour page (`/tours/<slug>`) — visible to everyone (full version)
- **Photo gallery** (the 5 promotional photos), title, rating, "provided by" (guide), free-tour / 24h-cancellation note.
- **Tour facts:** duration, languages, meeting point.
- **Overview** (description) and the **list of stops**.
- **Tour conditions:** accessibility, group size, suitability for children, pets.
- **Availability & booking panel:**
  - A weekly **calendar** to pick a date (built from the tour's weekly schedule);
  - The available departures for that date (time + language) with **places left**;
  - "Book spots" — reserve for yourself and **add up to 3 named guests** (1–4 people), then **Book Now**;
  - Guides/admins see a notice instead (booking is for participants only).
- **Your guide** section, **reviews**, and **"More tours by this guide"**.

## Participant profile (`/participant-dashboard`) — login required (participant)
- Welcome message with name, email, and **total reservations** count.
- **List of reserved tours**, each showing: date, start time, meeting point, number of people, names of additional participants, status, and a **Cancel** button (available only up to 24 h before start).
- Link to **browse tours**.

## Guide dashboard (`/guide-dashboard`) — login required (guide)
- **Profile header:** name, rating, photo, and key statistics (active tours, total participants, etc.).
- **My tours:** the tours the guide created, with **"More details"** (view, and edit while the tour has no reservations) and **"Add tour"** (create a new tour: title, weekly schedule, meeting point, duration, language, max participants, ≥4 stops, description, 5 photos).
- **Timetable & expected reservations:** for each booked date — the expected participants, **"View participants"**, and **"Mark as done"** once the tour has taken place (otherwise "Upcoming").
- **Tours history** (completed tours) and **Reports:** file a post-tour report — actual attendance + one evidence photo (and view past reports).

## Administrator dashboard (`/admin-dashboard`) — login required (admin)
- **Overview / statistics:** totals of guides, participants, tours, reservations, and **reservations per language**.
- **Registered guides:** each with name, email, spoken languages, photo, and a details view.
- **All tours:** table (title, guide, number of reservations, link to view).
- **Reservations:** table of all bookings (participant, tour, guide, date, extra guests, status — including cancelled).

## Logout
- Available from every logged-in page; ends the session and returns to the homepage.

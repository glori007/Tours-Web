# Walk Prague

A web application for managing **Free Walking Tours** in Prague. Guides create and
manage tours; participants browse, filter, and reserve places; an administrator
reviews platform statistics. The frontend is built with **HTML5**, **custom CSS3**
(no external framework) and **JavaScript**, while the backend is built with
**Flask**, **SQLite**, and **Flask-Login**. The application is designed for
**desktop**.

## Setup
To install all the requirements needed to deploy this website, run the following
commands in the terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run.py run --debug
```

Open `http://127.0.0.1:5000`.

The SQLite database (`instance/walk_prague.sqlite3`) ships pre-seeded with the sample data below .

## Sample accounts

All sample accounts can be used to test the application. Sign in at `/signin`
(participants and guides) or `/admin-access` (administrator).

### Guides
| Name | Email | Password |
| --- | --- | --- |
| Tomas Novak | `tomas.novak@gmail.com` | `tomas1234` |
| Klara Vesela | `veselaklara344@yahoo.com` | `chicken1234` |
| Petru Svobodova | `petrusvb@icloud.com` | `petruelectronics1234` |

### Participants
| Name | Email | Password |
| --- | --- | --- |
| Anna Walker | `annawalker@gmail.com` | `annaaa1111` |
| Martin Cerny | `martincerny@gmail.com` | `ghostmarty007` |
| Teresa Dvorazoka | `dvorazoka.teresa@gmail.com` | `teresaflyinginsky` |
| Adela Vesela | `adela.vesela@gmail.com` | `ADELAsinging1234` |
| Lukas Horak | `lukas.horak@gmail.com` | `lukaspast2026` |
| Marie Kralova | `marie.kralova@gmail.com` | `mariepast2026` |

> All the users already created and present in the website can be used to test the
> functions. In particular, **Lukas** and **Marie** have some **past,
> already-reported tours**, so the guides' Tours History / Past Reports and the
> "Mark as done" flow can be tested out of the box.
> See `credentials.md` for the full reservation breakdown per participant and a
> guide to which account exercises which feature.

### Administrator
| Name | Email | Password |
| --- | --- | --- |
| Platform Administrator | `admin@walkprague.cz` | `password123` |

## Notes

- A **participant** can reserve a place for a tour date (1–4 people, including
  himself/herself) and cancel up to 24 hours before the start time.
- A **guide** can create tours and edit their own; once a reservation exists for a
  tour, its information can no longer be edited by the guide who created it.
- Available tour languages are limited to Italian, English, Spanish, Portuguese and
  German.

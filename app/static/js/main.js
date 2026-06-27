document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("page-transition-ready");
  const currentRole = new URLSearchParams(window.location.search).get("role") === "guide" ? "guide" : "participant";

  // Live preview for the guide profile-photo picker on the registration page.
  const profilePhotoInput = document.querySelector("[data-profile-photo-input]");
  const profilePhotoPreview = document.querySelector("[data-profile-photo-preview]");
  const profilePhotoRemove = document.querySelector("[data-profile-photo-remove]");
  profilePhotoInput?.addEventListener("change", () => {
    const file = profilePhotoInput.files?.[0];
    if (file) {
      profilePhotoPreview.src = URL.createObjectURL(file);
      profilePhotoRemove?.classList.remove("is-hidden");
    }
  });

  profilePhotoRemove?.addEventListener("click", () => {
    if (profilePhotoInput) {
      profilePhotoInput.value = "";
    }
    if (profilePhotoPreview) {
      profilePhotoPreview.src = profilePhotoPreview.dataset.defaultSrc || "/static/img/default-profile.png";
    }
    profilePhotoRemove.classList.add("is-hidden");
  });

  const updateRoleLinks = (role) => {
    document.querySelectorAll("[data-role-target]").forEach((link) => {
      const url = new URL(link.href, window.location.href);
      if (role === "guide") {
        url.searchParams.set("role", "guide");
      } else {
        url.searchParams.delete("role");
      }
      link.href = url.href;
    });
  };

  document.querySelectorAll("a[href]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const href = link.getAttribute("href");
      if (!href || href.startsWith("#") || link.target === "_blank") return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const url = new URL(link.href, window.location.href);
      const current = new URL(window.location.href);
      const samePageHash = url.pathname === current.pathname && url.hash;
      if (url.origin !== current.origin || samePageHash) return;

      event.preventDefault();
      document.body.classList.add("page-transition-out");
      window.setTimeout(() => {
        window.location.href = url.href;
      }, 260);
    });
  });

  const slides = Array.from(document.querySelectorAll(".hero-slide"));
  let currentSlide = 0;

  if (slides.length > 1) {
    window.setInterval(() => {
      slides[currentSlide].classList.remove("is-active");
      currentSlide = (currentSlide + 1) % slides.length;
      slides[currentSlide].classList.add("is-active");
    }, 2000);
  }

  const reviewTrack = document.querySelector("[data-review-track]");
  const nextReview = document.querySelector("[data-review-next]");
  const prevReview = document.querySelector("[data-review-prev]");
  const scrollReviews = (direction) => {
    if (!reviewTrack) return;
    reviewTrack.scrollBy({ left: direction * 420, behavior: "smooth" });
  };
  nextReview?.addEventListener("click", () => scrollReviews(1));
  prevReview?.addEventListener("click", () => scrollReviews(-1));

  const selectAllLanguages = document.querySelector("[data-select-all-languages]");
  const languageOptions = Array.from(document.querySelectorAll("[data-language-option]"));
  
  const selectAllTimes = document.querySelector("[data-select-all-times]");
  const timeOptions = selectAllTimes ? Array.from(selectAllTimes.closest(".filter-options").querySelectorAll("input[type='checkbox']:not([data-select-all-times])")) : [];

  // -------------------------------------------------------------------------
  // Homepage tour filtering (date, duration, language + theme/accessibility/
  // start-time/availability). Filters run live as the user changes them.
  // -------------------------------------------------------------------------
  const tourCards = Array.from(document.querySelectorAll("[data-tour-card]"));
  const filtersRoot = document.querySelector(".filters");

  if (tourCards.length && filtersRoot) {
    const resultCount = document.querySelector("[data-result-count]");
    const noResults = document.querySelector("[data-no-results]");

    // Pagination: show 6 tours at first, reveal 4 more each "Load more" click.
    const INITIAL_VISIBLE = 6;
    const PAGE_STEP = 4;
    const loadMoreBtn = document.querySelector(".load-more-tours");
    let currentMatched = [];
    let pageLimit = INITIAL_VISIBLE;

    const paginate = () => {
      currentMatched.forEach((card, i) => card.classList.toggle("is-hidden", i >= pageLimit));
      if (loadMoreBtn) {
        const remaining = currentMatched.length - pageLimit;
        loadMoreBtn.classList.toggle("is-hidden", remaining <= 0);
        if (remaining > 0) {
          loadMoreBtn.textContent = `Load more tours (${Math.min(PAGE_STEP, remaining)}) →`;
        }
      }
    };

    loadMoreBtn?.addEventListener("click", () => {
      pageLimit += PAGE_STEP;
      paginate();
    });

    // Find the filter <details> whose <h3> matches the given heading.
    const sectionFor = (heading) =>
      Array.from(filtersRoot.querySelectorAll("details.filter-section"))
        .find((section) => section.querySelector("h3")?.textContent.trim() === heading);

    // Labels of the checked rows in a section (ignoring the "all languages" row).
    const checkedLabels = (heading) => {
      const section = sectionFor(heading);
      if (!section) return [];
      return Array.from(section.querySelectorAll("input[type='checkbox']"))
        .filter((input) => input.checked && !input.hasAttribute("data-select-all-languages"))
        .map((input) => input.closest(".filter-row")?.querySelector("span")?.textContent.trim())
        .filter(Boolean);
    };

    const splitData = (card, key) =>
      (card.dataset[key] || "").split("|").map((value) => value.trim()).filter(Boolean);

    const matchesDuration = (minutes, labels) =>
      labels.some((label) => {
        if (label.startsWith("Up to 90")) return minutes <= 90;
        if (label.startsWith("90 - 120")) return minutes >= 90 && minutes <= 120;
        if (label.startsWith("More than 120")) return minutes > 120;
        return false;
      });

    const startTimeBuckets = {
      "Morning, from 9:00 AM": (h) => h >= 9 && h < 11,
      "Late morning, from 11:00 AM": (h) => h >= 11 && h < 14,
      "Afternoon, from 2:00 PM": (h) => h >= 14 && h < 19,
      "Evening, from 7:00 PM": (h) => h >= 19,
    };

    const applyFilters = () => {
      const languages = languageOptions.filter((o) => o.checked).map((o) => o.closest(".filter-row")?.querySelector("span")?.textContent.trim());
      
      // Update "All languages" checkbox state automatically
      if (selectAllLanguages) {
        selectAllLanguages.checked = languageOptions.every((o) => o.checked);
      }
      
      // Update "Any time" checkbox state automatically
      if (selectAllTimes) {
        selectAllTimes.checked = timeOptions.every((o) => o.checked);
      }
      
      const durations = checkedLabels("Duration");
      const themes = checkedLabels("Tour Theme / Category");
      const accessibility = checkedLabels("Accessibility");
      const startLabels = checkedLabels("Start time").filter((l) => l !== "Any time");
      const availability = checkedLabels("Availability Status");
      const range = window.walkPragueDateRange || {};

      const matched = [];
      tourCards.forEach((card) => {
        const cardLanguages = splitData(card, "languages");
        const cardDates = splitData(card, "dates");
        const cardThemes = splitData(card, "themes");
        const cardAccess = splitData(card, "accessibility");
        const cardStartTimes = splitData(card, "startTimes");
        const placesLeft = Number(card.dataset.placesLeft || 0);
        const minutes = Number(card.dataset.duration || 0);

        let show = true;

        // Language: tour must offer at least one selected language.
        if (languages.length && !cardLanguages.some((l) => languages.includes(l))) show = false;

        // Duration buckets.
        if (show && durations.length && !matchesDuration(minutes, durations)) show = false;

        // Date range: at least one departure within [start, end].
        if (show && range.start) {
          const end = range.end || range.start;
          if (!cardDates.some((d) => d >= range.start && d <= end)) show = false;
        }

        // Theme: tour must carry at least one selected theme.
        if (show && themes.length && !cardThemes.some((t) => themes.includes(t))) show = false;

        // Accessibility: tour must have every selected feature.
        if (show && accessibility.length && !accessibility.every((a) => cardAccess.includes(a))) show = false;

        // Start time buckets: at least one departure in a selected window.
        if (show && startLabels.length) {
          const hours = cardStartTimes.map((t) => Number(t.split(":")[0]));
          const ok = startLabels.some((label) => {
            const test = startTimeBuckets[label];
            return test && hours.some(test);
          });
          if (!ok) show = false;
        }

        // Availability constraints (all selected must hold). When a date range is
        // applied, availability is evaluated *within that range* — the best
        // remaining places among the tour's departures that fall in the range —
        // which is what makes this filter meaningful (otherwise some far-off date
        // is always free). With no date range it falls back to the overall best.
        if (show && availability.length) {
          let availForFilter = placesLeft;
          if (range.start) {
            const end = range.end || range.start;
            let best = 0;
            try {
              const map = JSON.parse(card.dataset.availability || "{}");
              Object.entries(map).forEach(([d, left]) => {
                if (d >= range.start && d <= end) best = Math.max(best, Number(left));
              });
            } catch (e) { best = placesLeft; }
            availForFilter = best;
          }
          const ok = availability.every((label) => {
            if (label.startsWith("Hide fully booked")) return availForFilter > 0;
            const match = label.match(/^(\d+)\+/);
            return match ? availForFilter >= Number(match[1]) : true;
          });
          if (!ok) show = false;
        }

        // Non-matching cards are always hidden; matching cards are paginated.
        if (show) {
          matched.push(card);
        } else {
          card.classList.add("is-hidden");
        }
      });

      const visible = matched.length;
      if (resultCount) resultCount.textContent = `${visible} tour${visible === 1 ? "" : "s"} available`;
      if (noResults) noResults.classList.toggle("is-hidden", visible !== 0);

      // Reset to the first page whenever the filters change, then paginate.
      currentMatched = matched;
      pageLimit = INITIAL_VISIBLE;
      paginate();

      // Render chips for selected filters
      filtersRoot.querySelectorAll("details.filter-section").forEach((section) => {
        const chipsContainer = section.nextElementSibling;
        if (!chipsContainer || !chipsContainer.classList.contains("filter-chips")) return;
        chipsContainer.innerHTML = "";
        
        section.querySelectorAll("input[type='checkbox']").forEach((input) => {
          if (!input.checked || input.hasAttribute("data-select-all-languages")) return;
          const labelText = input.closest(".filter-row")?.querySelector("span")?.textContent.trim();
          if (!labelText || labelText === "Any time") return;
          
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "guide-language-chip filter-orange-chip"; // Added extra class for orange styling
          chip.innerHTML = `<span>${labelText}</span><strong aria-hidden="true">×</strong>`;
          chip.setAttribute("aria-label", `Remove ${labelText} filter`);
          
          chip.addEventListener("click", (event) => {
            event.stopPropagation();
            input.checked = false;
            input.dispatchEvent(new Event("change"));
          });
          
          chipsContainer.appendChild(chip);
        });
      });
    };

    selectAllLanguages?.addEventListener("change", () => {
      languageOptions.forEach((option) => { option.checked = selectAllLanguages.checked; });
      applyFilters();
    });

    selectAllTimes?.addEventListener("change", () => {
      timeOptions.forEach((option) => { option.checked = selectAllTimes.checked; });
      applyFilters();
    });

    filtersRoot.querySelectorAll("input[type='checkbox']").forEach((input) => {
      input.addEventListener("change", applyFilters);
    });

    document.querySelector("[data-apply-filters]")?.addEventListener("click", applyFilters);
    window.addEventListener("walkprague:datechange", applyFilters);

    document.querySelector("[data-clear-filters]")?.addEventListener("click", () => {
      filtersRoot.querySelectorAll("input[type='checkbox']").forEach((input) => { input.checked = false; });
      const anyTime = Array.from(filtersRoot.querySelectorAll(".filter-row span")).find((s) => s.textContent.trim() === "Any time");
      if (anyTime) anyTime.closest(".filter-row").querySelector("input").checked = true;
      window.walkPragueDateRange = { start: null, end: null };
      const dateLabel = document.querySelector("[data-date-label]");
      if (dateLabel) dateLabel.textContent = "Select dates";
      applyFilters();
    });

    applyFilters();
  } else {
    // Pages without tour cards still keep the "select all languages" behaviour.
    selectAllLanguages?.addEventListener("change", () => {
      languageOptions.forEach((option) => { option.checked = selectAllLanguages.checked; });
    });
  }

  document.querySelectorAll("[data-tour-url]").forEach((card) => {
    const openTour = () => {
      const target = card.dataset.tourUrl;
      if (!target) return;
      document.body.classList.add("page-transition-out");
      window.setTimeout(() => {
        window.location.href = target;
      }, 260);
    };

    card.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, label")) return;
      openTour();
    });

    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openTour();
    });
  });

  const gallery = document.querySelector("[data-tour-gallery]");
  if (gallery) {
    const gallerySlides = Array.from(gallery.querySelectorAll("[data-gallery-slide]"));
    const galleryCount = gallery.querySelector("[data-gallery-count]");
    const galleryPrev = gallery.querySelector("[data-gallery-prev]");
    const galleryNext = gallery.querySelector("[data-gallery-next]");
    let activeGallerySlide = 0;
    let galleryTimer = null;

    const showGallerySlide = (index) => {
      if (!gallerySlides.length) return;
      gallerySlides[activeGallerySlide]?.classList.remove("is-active");
      activeGallerySlide = (index + gallerySlides.length) % gallerySlides.length;
      gallerySlides[activeGallerySlide]?.classList.add("is-active");
      if (galleryCount) galleryCount.textContent = `${activeGallerySlide + 1}/${gallerySlides.length}`;
    };

    const restartGalleryTimer = () => {
      window.clearInterval(galleryTimer);
      galleryTimer = window.setInterval(() => {
        showGallerySlide(activeGallerySlide + 1);
      }, 2800);
    };

    galleryPrev?.addEventListener("click", () => {
      showGallerySlide(activeGallerySlide - 1);
      restartGalleryTimer();
    });

    galleryNext?.addEventListener("click", () => {
      showGallerySlide(activeGallerySlide + 1);
      restartGalleryTimer();
    });

    restartGalleryTimer();
  }

  // Availability & booking: a weekly calendar on the tour detail page,
  // driven by a date -> departures map embedded in [data-calendar].
  const calendar = document.querySelector("[data-calendar]");
  const bookingControls = document.querySelector("[data-booking-control]");
  const bookNow = document.querySelector("[data-book-now]");
  const bookingCapacity = document.querySelector("[data-booking-capacity]");
  const bookingFeedback = document.querySelector("[data-booking-feedback]");
  let currentAvailableLeft = 0;

  const setBookingAvailability = (available) => {
    bookingControls?.classList.toggle("is-disabled", !available);
    bookingControls?.querySelectorAll("button").forEach((button) => {
      button.disabled = !available;
    });
    bookingControls?.querySelectorAll("input").forEach((input) => {
      input.disabled = !available;
    });
    bookNow?.classList.toggle("is-disabled", !available);
    if (bookNow) {
      bookNow.setAttribute("aria-disabled", String(!available));
      bookNow.tabIndex = available ? 0 : -1;
    }
  };

  // The currently selected time slot acts as the chosen departure.
  const activeScheduleButton = () => document.querySelector("[data-cal-panel] .time-slot.active") || null;

  const setBookingMessage = (message, type = "") => {
    if (!bookingFeedback) return;
    bookingFeedback.textContent = message;
    bookingFeedback.classList.toggle("is-error", type === "error");
    bookingFeedback.classList.toggle("is-ok", type === "ok");
  };

  const updateBookingCapacity = () => {
    const button = activeScheduleButton();
    currentAvailableLeft = Number(button?.dataset.availableLeft || 0);
    const totalRequested = 1 + guests.length;
    const canBook = currentAvailableLeft > 0 && totalRequested <= currentAvailableLeft;
    if (bookingCapacity) {
      bookingCapacity.textContent = currentAvailableLeft > 0
        ? `${currentAvailableLeft} place${currentAvailableLeft === 1 ? "" : "s"} left for this departure.`
        : "No places left for this departure.";
    }
    addGuestToggle?.classList.toggle("is-disabled-soft", currentAvailableLeft > 0 && totalRequested >= Math.min(4, currentAvailableLeft));
    if (bookNow && !bookNow.classList.contains("is-disabled")) {
      bookNow.classList.toggle("is-disabled", !canBook);
      bookNow.setAttribute("aria-disabled", String(!canBook));
      bookNow.tabIndex = canBook ? 0 : -1;
    }
    if (currentAvailableLeft > 0 && totalRequested > currentAvailableLeft) {
      const maxGuests = currentAvailableLeft - 1;
      setBookingMessage(
        maxGuests <= 0
          ? `Only 1 place left — you can book just yourself, no extra guests.`
          : `Only ${currentAvailableLeft} places left — you can bring at most ${maxGuests} guest${maxGuests === 1 ? "" : "s"}.`,
        "error"
      );
    } else if (bookingFeedback?.classList.contains("is-error")) {
      setBookingMessage("");
    }
  };

  if (calendar) {
    const availability = JSON.parse(calendar.dataset.availability || "{}");
    const calMonth = calendar.querySelector("[data-cal-month]");
    const calDays = calendar.querySelector("[data-cal-days]");
    const calPanel = calendar.querySelector("[data-cal-panel]");
    const calSelectedDate = calendar.querySelector("[data-cal-selected-date]");
    const calPrev = calendar.querySelector("[data-cal-prev]");
    const calNext = calendar.querySelector("[data-cal-next]");

    const parseYMD = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
    const ymd = (dt) => `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
    const mondayOf = (dt) => { const x = new Date(dt); x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; };

    const today = parseYMD(calendar.dataset.today);
    const thisMonday = mondayOf(today);
    let weekStart = new Date(thisMonday);
    let selectedKey = null;

    const selectSlot = (btn) => {
      if (!btn || btn.disabled) return;
      calPanel.querySelectorAll(".time-slot").forEach((s) => s.classList.remove("active"));
      btn.classList.add("active");
      setBookingAvailability(Number(btn.dataset.availableLeft || 0) > 0);
      updateBookingCapacity();
    };

    const renderPanel = (key) => {
      const slots = availability[key] || [];
      if (calSelectedDate) {
        calSelectedDate.textContent = slots[0]?.date_label
          || parseYMD(key).toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "long", year: "numeric" });
      }
      calPanel.innerHTML = "";
      if (!slots.length) {
        calPanel.innerHTML = '<p class="no-tour-day">No availability for this date.</p>';
        setBookingAvailability(false);
        updateBookingCapacity();
        return;
      }
      const groups = [];
      slots.forEach((s) => {
        let g = groups.find((x) => x.language === s.language);
        if (!g) { g = { language: s.language, flag: s.flag, items: [] }; groups.push(g); }
        g.items.push(s);
      });
      groups.forEach((g) => {
        const section = document.createElement("section");
        section.className = "cal-lang";
        const h = document.createElement("h4");
        h.innerHTML = `<img class="lang-flag" src="${g.flag}" alt=""> ${g.language}`;
        section.appendChild(h);
        const rowEl = document.createElement("div");
        rowEl.className = "cal-slot-row";
        g.items.forEach((s) => {
          const b = document.createElement("button");
          b.type = "button";
          b.className = "time-slot" + (s.left === 0 ? " is-full" : "");
          b.dataset.scheduleId = s.schedule_id;
          b.dataset.date = s.date;
          b.dataset.availableLeft = s.left;
          b.dataset.scheduleSummary = s.summary;
          b.disabled = s.left === 0;
          b.innerHTML = `<span class="time-slot-time">${s.time}</span>`
            + `<span class="time-slot-count ${s.left === 0 ? "full" : "available"}">${s.left === 0 ? "No availability" : s.left + " / " + s.max}</span>`;
          b.addEventListener("click", () => selectSlot(b));
          rowEl.appendChild(b);
        });
        section.appendChild(rowEl);
        calPanel.appendChild(section);
      });
      const firstFree = calPanel.querySelector(".time-slot:not(.is-full)");
      if (firstFree) { selectSlot(firstFree); }
      else { setBookingAvailability(false); updateBookingCapacity(); }
    };

    const selectDay = (key) => {
      selectedKey = key;
      renderWeek();
      renderPanel(key);
    };

    function renderWeek() {
      if (calMonth) calMonth.textContent = weekStart.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      calDays.innerHTML = "";
      for (let i = 0; i < 7; i += 1) {
        const d = new Date(weekStart);
        d.setDate(weekStart.getDate() + i);
        const key = ymd(d);
        const slots = availability[key] || [];
        const scheduled = slots.length > 0;
        const hasFree = slots.some((s) => s.left > 0);
        const isPast = d < today;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "cal-day";
        btn.textContent = String(d.getDate());
        if (scheduled) btn.classList.add("scheduled");
        if (scheduled && !hasFree) btn.classList.add("full");
        if (key === selectedKey) btn.classList.add("active");
        if (isPast || !scheduled) {
          btn.disabled = true;
        } else {
          btn.addEventListener("click", () => selectDay(key));
        }
        calDays.appendChild(btn);
      }
      if (calPrev) calPrev.disabled = weekStart <= thisMonday;
    }

    calPrev?.addEventListener("click", () => {
      const candidate = new Date(weekStart);
      candidate.setDate(candidate.getDate() - 7);
      if (candidate < thisMonday) return;
      weekStart = candidate;
      renderWeek();
    });
    calNext?.addEventListener("click", () => {
      weekStart = new Date(weekStart);
      weekStart.setDate(weekStart.getDate() + 7);
      renderWeek();
    });

    // Open on the first upcoming date that has departures.
    window.requestAnimationFrame(() => {
      const upcomingKeys = Object.keys(availability).filter((k) => parseYMD(k) >= today).sort();
      if (upcomingKeys.length) {
        selectedKey = upcomingKeys[0];
        weekStart = mondayOf(parseYMD(selectedKey));
        renderWeek();
        renderPanel(selectedKey);
      } else {
        renderWeek();
        setBookingAvailability(false);
        updateBookingCapacity();
      }
    });
  }

  bookNow?.addEventListener("click", (event) => {
    if (bookNow.classList.contains("is-disabled")) {
      event.preventDefault();
      setBookingMessage("This departure cannot accept the selected number of participants.", "error");
      return;
    }
    if (bookNow.dataset.participantBooking === "true") {
      event.preventDefault();
      const selectedButton = activeScheduleButton();
      const selectedSchedule = selectedButton?.dataset.scheduleSummary || selectedDateLabel?.textContent || "selected departure";
      const scheduleId = selectedButton?.dataset.scheduleId;
      const date = selectedButton?.dataset.date;
      if (!scheduleId || !date) {
        setBookingMessage("Please select a departure date and time first.", "error");
        return;
      }
      fetch("/reservations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schedule_id: scheduleId, date, guests })
      })
        .then((response) => response.json().then((body) => ({ ok: response.ok, body })))
        .then(({ ok, body }) => {
          if (!ok || !body.ok) {
            setBookingMessage(body.error || "Reservation could not be completed.", "error");
            return;
          }
          setBookingMessage(`Reservation completed for ${selectedSchedule}. Redirecting to your profile.`, "ok");
          document.body.classList.add("page-transition-out");
          window.setTimeout(() => {
            window.location.href = bookNow.href;
          }, 850);
        })
        .catch(() => {
          setBookingMessage("Reservation could not be completed. Please try again.", "error");
        });
    }
  });

  const guestBooking = document.querySelector("[data-guest-booking]");
  const addGuestToggle = document.querySelector("[data-add-guest-toggle]");
  const addGuestSymbol = document.querySelector("[data-add-guest-symbol]");
  const addGuestForm = document.querySelector("[data-add-guest-form]");
  const guestFirst = document.querySelector("[data-guest-first]");
  const guestLast = document.querySelector("[data-guest-last]");
  const guestClear = document.querySelector("[data-guest-clear]");
  const guestEnter = document.querySelector("[data-guest-enter]");
  const guestList = document.querySelector("[data-guest-list]");
  const guests = [];

  const setGuestFormOpen = (open) => {
    guestBooking?.classList.toggle("is-open", open);
    addGuestForm?.classList.toggle("is-hidden", !open);
    addGuestToggle?.setAttribute("aria-expanded", String(open));
    if (addGuestSymbol) addGuestSymbol.textContent = open ? "×" : "+";
  };

  const clearGuestFields = () => {
    if (guestFirst) guestFirst.value = "";
    if (guestLast) guestLast.value = "";
    guestFirst?.focus();
  };

  const renderGuests = () => {
    if (!guestList) return;
    guestList.innerHTML = "";
    guests.forEach((guest, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "guest-chip";
      button.dataset.removeGuest = String(index);
      button.innerHTML = `<span>${guest}</span><strong aria-hidden="true">×</strong>`;
      button.setAttribute("aria-label", `Remove ${guest}`);
      guestList.appendChild(button);
    });
  };

  addGuestToggle?.addEventListener("click", () => {
    const maxAdditionalGuests = Math.min(3, Math.max(0, currentAvailableLeft - 1));
    if (guests.length >= maxAdditionalGuests) {
      setBookingMessage(
        currentAvailableLeft > 0
          ? `Only ${currentAvailableLeft} total place${currentAvailableLeft === 1 ? "" : "s"} left for this departure.`
          : "No places left for this departure.",
        "error"
      );
      return;
    }
    setGuestFormOpen(!guestBooking?.classList.contains("is-open"));
  });

  guestClear?.addEventListener("click", clearGuestFields);

  guestEnter?.addEventListener("click", () => {
    const firstName = guestFirst?.value.trim() || "";
    const lastName = guestLast?.value.trim() || "";
    const guestName = `${firstName} ${lastName}`.trim();
    const maxAdditionalGuests = Math.min(3, Math.max(0, currentAvailableLeft - 1));
    if (!guestName || guests.length >= maxAdditionalGuests) {
      setBookingMessage(
        currentAvailableLeft > 0
          ? `Only ${currentAvailableLeft} total place${currentAvailableLeft === 1 ? "" : "s"} left for this departure.`
          : "No places left for this departure.",
        "error"
      );
      return;
    }
    guests.push(guestName);
    clearGuestFields();
    renderGuests();
    updateBookingCapacity();
    if (guests.length >= maxAdditionalGuests) setGuestFormOpen(false);
  });

  guestList?.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-remove-guest]");
    if (!chip) return;
    guests.splice(Number(chip.dataset.removeGuest), 1);
    renderGuests();
    updateBookingCapacity();
  });

  const stopsToggle = document.querySelector("[data-stops-toggle]");
  stopsToggle?.addEventListener("click", () => {
    const extraStops = Array.from(document.querySelectorAll(".extra-stop"));
    const opening = extraStops.some((stop) => stop.classList.contains("is-hidden"));
    extraStops.forEach((stop) => stop.classList.toggle("is-hidden", !opening));
    stopsToggle.textContent = opening ? "View less" : "View more";
  });

  document.querySelectorAll("[data-cancel-reservation]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      const reservationId = button.dataset.reservationId;
      fetch(`/reservations/${reservationId}/cancel`, { method: "POST" })
        .then((response) => response.json().then((body) => ({ ok: response.ok, body })))
        .then(({ ok, body }) => {
          if (!ok || !body.ok) return;
          button.textContent = "Reservation cancelled";
          button.disabled = true;
          const card = button.closest(".participant-reservation-card");
          const status = card?.querySelector(".reservation-status");
          if (status) {
            status.textContent = "Cancelled";
            status.classList.remove("confirmed");
            status.classList.add("locked");
          }
        });
    });
  });

  const authRoleButtons = Array.from(document.querySelectorAll("[data-auth-role]"));
  const authRoleInput = document.querySelector("[data-auth-role-input]");
  const guideFields = document.querySelector("[data-guide-fields]");
  const authSubmit = document.querySelector("[data-auth-submit]");
  const authSubtitle = document.querySelector("[data-auth-subtitle]");
  const authIntroTitle = document.querySelector("[data-auth-intro-title]");
  const authIntroCopy = document.querySelector("[data-auth-intro-copy]");
  const authBenefits = document.querySelector("[data-auth-benefits]");
  const authForm = document.querySelector("[data-auth-form]");
  const authIntro = document.querySelector(".auth-intro");
  const roleContent = {
    participant: {
      submit: "Sign In as Participant",
      subtitle: "Welcome back to Walk Prague",
      title: "Welcome back, explorer.",
      copy: "Sign in to manage your tour bookings, track your Prague adventures, and discover new walks.",
      benefits: [
        "Access free walking tours across Prague",
        "Book spots for yourself and up to 3 friends",
        "Save favourites and track completed tours"
      ]
    },
    guide: {
      submit: "Sign In as Guide",
      subtitle: "Manage your tours, bookings, and guest lists",
      title: "Welcome back, guide.",
      copy: "Sign in to manage your tour schedule, update tour details, and follow participant reservations.",
      benefits: [
        "View bookings and participant lists",
        "Create and update your walking tours",
        "Track reviews connected to your tours"
      ]
    }
  };

  const setAuthRole = (role) => {
    const content = roleContent[role] || roleContent.participant;
    updateRoleLinks(role);
    authForm?.classList.remove("is-role-switching");
    authIntro?.classList.remove("is-role-switching");
    window.requestAnimationFrame(() => {
      authForm?.classList.add("is-role-switching");
      authIntro?.classList.add("is-role-switching");
    });
    authRoleButtons.forEach((button) => {
      const active = button.dataset.authRole === role;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });
    if (authRoleInput) authRoleInput.value = role;
    guideFields?.classList.toggle("is-hidden", role !== "guide");
    const guideCode = guideFields?.querySelector("input");
    if (guideCode) guideCode.required = role === "guide";
    if (authSubmit) authSubmit.textContent = content.submit;
    if (authSubtitle) authSubtitle.textContent = content.subtitle;
    if (authIntroTitle) authIntroTitle.textContent = content.title;
    if (authIntroCopy) authIntroCopy.textContent = content.copy;
    if (authBenefits) {
      authBenefits.innerHTML = content.benefits
        .map((benefit, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span>${benefit}</li>`)
        .join("");
    }
  };

  authRoleButtons.forEach((button) => {
    button.addEventListener("click", () => setAuthRole(button.dataset.authRole));
  });
  if (authRoleButtons.length) setAuthRole(currentRole);

  authForm?.addEventListener("submit", (event) => {
    // Front-end validation before letting the browser POST to the server
    const email = authForm.querySelector("input[name='email']");
    const password = authForm.querySelector("input[name='password']");
    let valid = true;

    // Remove any previous inline error highlights
    [email, password].forEach((field) => field?.classList.remove("field-error"));

    if (!email?.value.trim()) {
      email?.classList.add("field-error");
      valid = false;
    }
    if (!password?.value) {
      password?.classList.add("field-error");
      valid = false;
    }

    if (!valid) {
      event.preventDefault();
      return;
    }
    // Valid — let the browser submit the form naturally so Flask can check DB
    document.body.classList.add("page-transition-out");
    // Do NOT call event.preventDefault() — the POST will reach the server
  });

  const registerRoleButtons = Array.from(document.querySelectorAll("[data-register-role]"));
  const registerRoleInput = document.querySelector("[data-register-role-input]");
  const registerGuideFields = document.querySelector("[data-register-guide-fields]");
  const registerSubmit = document.querySelector("[data-register-submit]");
  const registerSubtitle = document.querySelector("[data-register-subtitle]");
  const registerIntroTitle = document.querySelector("[data-register-intro-title]");
  const registerIntroCopy = document.querySelector("[data-register-intro-copy]");
  const registerBenefits = document.querySelector("[data-register-benefits]");
  const registerForm = document.querySelector("[data-register-form]");
  const registerContent = {
    participant: {
      submit: "Create Participant Account",
      subtitle: "Choose your role to get started",
      title: "Join the Prague walking community.",
      copy: "Create your free account to book tours, bring friends along, and explore Prague like a local.",
      benefits: [
        "Book walking tours instantly",
        "Bring up to 3 friends per booking",
        "Save favourite tours and review completed walks"
      ]
    },
    guide: {
      submit: "Create Guide Account",
      subtitle: "Create a guide profile to offer walking tours",
      title: "Share Prague through your own tours.",
      copy: "Register as a guide to create tours, set languages and schedules, and manage participant reservations.",
      benefits: [
        "Create and manage your own tours",
        "Choose languages, themes, duration, and meeting points",
        "Track bookings and reviews from participants"
      ]
    }
  };

  const setRegisterRole = (role) => {
    const content = registerContent[role] || registerContent.participant;
    updateRoleLinks(role);
    registerForm?.classList.remove("is-role-switching");
    authIntro?.classList.remove("is-role-switching");
    window.requestAnimationFrame(() => {
      registerForm?.classList.add("is-role-switching");
      authIntro?.classList.add("is-role-switching");
    });
    registerRoleButtons.forEach((button) => {
      const active = button.dataset.registerRole === role;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });
    if (registerRoleInput) registerRoleInput.value = role;
    registerGuideFields?.classList.toggle("is-hidden", role !== "guide");
    registerGuideFields?.querySelectorAll("input, textarea").forEach((field) => {
      field.required = role === "guide" && field.type !== "hidden";
    });
    if (registerSubmit) registerSubmit.textContent = content.submit;
    if (registerSubtitle) registerSubtitle.textContent = content.subtitle;
    if (registerIntroTitle) registerIntroTitle.textContent = content.title;
    if (registerIntroCopy) registerIntroCopy.textContent = content.copy;
    if (registerBenefits) {
      registerBenefits.innerHTML = content.benefits
        .map((benefit, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span>${benefit}</li>`)
        .join("");
    }
  };

  registerRoleButtons.forEach((button) => {
    button.addEventListener("click", () => setRegisterRole(button.dataset.registerRole));
  });
  if (registerRoleButtons.length) setRegisterRole(currentRole);

  registerForm?.addEventListener("submit", (event) => {
    // Front-end validation before letting the browser POST to the server
    const firstName = registerForm.querySelector("input[name='first_name']");
    const lastName = registerForm.querySelector("input[name='last_name']");
    const email = registerForm.querySelector("input[name='email']");
    const password = registerForm.querySelector("input[name='password']");
    const confirmPassword = registerForm.querySelector("input[name='confirm_password']");
    const languageValue = registerForm.querySelector("[data-guide-language-value]");
    const role = registerRoleInput?.value;
    let valid = true;

    // Remove previous highlights
    [firstName, lastName, email, password, confirmPassword].forEach((f) => f?.classList.remove("field-error"));

    if (!firstName?.value.trim()) { firstName?.classList.add("field-error"); valid = false; }
    if (!lastName?.value.trim())  { lastName?.classList.add("field-error");  valid = false; }
    if (!email?.value.trim())     { email?.classList.add("field-error");     valid = false; }
    if (!password?.value || password.value.length < 8) {
      password?.classList.add("field-error");
      valid = false;
    }
    if (password?.value !== confirmPassword?.value) {
      confirmPassword?.classList.add("field-error");
      valid = false;
    }
    if (role === "guide" && !languageValue?.value.trim()) {
      // Show a visible cue on the language selector
      document.querySelector("[data-guide-language-toggle]")?.classList.add("field-error");
      valid = false;
    }

    if (!valid) {
      event.preventDefault();
      return;
    }
    // Valid — let the browser submit naturally so Flask saves to DB
    document.body.classList.add("page-transition-out");
    // Do NOT call event.preventDefault()
  });

  const guideLanguageSelect = document.querySelector("[data-guide-language-select]");
  const guideLanguageToggle = document.querySelector("[data-guide-language-toggle]");
  const guideLanguagePlaceholder = document.querySelector("[data-guide-language-placeholder]");
  const guideLanguageValue = document.querySelector("[data-guide-language-value]");
  const guideLanguageChips = document.querySelector("[data-guide-language-chips]");
  const guideLanguageOptions = Array.from(document.querySelectorAll("[data-guide-language-option]"));
  const guideLanguageApply = document.querySelector("[data-guide-language-apply]");
  const selectedGuideLanguages = new Set();

  const renderGuideLanguages = () => {
    guideLanguageOptions.forEach((option) => {
      option.classList.toggle("is-selected", selectedGuideLanguages.has(option.dataset.value));
    });
    if (guideLanguageValue) guideLanguageValue.value = Array.from(selectedGuideLanguages).join(", ");
    if (guideLanguagePlaceholder) {
      guideLanguagePlaceholder.textContent = selectedGuideLanguages.size
        ? `${selectedGuideLanguages.size} Language${selectedGuideLanguages.size === 1 ? "" : "s"} selected`
        : "Add languages";
    }
    if (!guideLanguageChips) return;
    guideLanguageChips.innerHTML = "";
    selectedGuideLanguages.forEach((language) => {
      const option = guideLanguageOptions.find((item) => item.dataset.value === language);
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "guide-language-chip";
      chip.dataset.removeGuideLanguage = language;
      chip.innerHTML = `<span>${option?.dataset.chip || language}</span><strong aria-hidden="true">×</strong>`;
      chip.setAttribute("aria-label", `Remove ${language}`);
      guideLanguageChips.appendChild(chip);
    });
  };

  guideLanguageToggle?.addEventListener("click", () => {
    const open = !guideLanguageSelect?.classList.contains("is-open");
    guideLanguageSelect?.classList.toggle("is-open", open);
    guideLanguageToggle.setAttribute("aria-expanded", String(open));
  });

  guideLanguageOptions.forEach((option) => {
    option.addEventListener("click", (event) => {
      event.stopPropagation();
      const language = option.dataset.value;
      if (!language) return;
      if (selectedGuideLanguages.has(language)) {
        selectedGuideLanguages.delete(language);
      } else {
        selectedGuideLanguages.add(language);
      }
      renderGuideLanguages();
      guideLanguageSelect?.classList.remove("is-open");
      guideLanguageToggle?.setAttribute("aria-expanded", "false");
    });
  });

  guideLanguageChips?.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-remove-guide-language]");
    if (!chip) return;
    selectedGuideLanguages.delete(chip.dataset.removeGuideLanguage);
    renderGuideLanguages();
  });



  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-guide-language-select]")) {
      guideLanguageSelect?.classList.remove("is-open");
      guideLanguageToggle?.setAttribute("aria-expanded", "false");
    }
  });

  // -------------------------------------------------------------------------
  // Specialty dropdown — multi-select up to 4, styled identically to languages
  // -------------------------------------------------------------------------
  const guideSpecialtySelect = document.querySelector("[data-guide-specialty-select]");
  const guideSpecialtyToggle = document.querySelector("[data-guide-specialty-toggle]");
  const guideSpecialtyPlaceholder = document.querySelector("[data-guide-specialty-placeholder]");
  const guideSpecialtyValue = document.querySelector("[data-guide-specialty-value]");
  const guideSpecialtyChips = document.querySelector("[data-guide-specialty-chips]");
  const guideSpecialtyOptions = Array.from(document.querySelectorAll("[data-guide-specialty-option]"));
  const guideSpecialtyApply = document.querySelector("[data-guide-specialty-apply]");
  const selectedGuideSpecialties = new Set();

  const renderGuideSpecialties = () => {
    guideSpecialtyOptions.forEach((option) => {
      option.classList.toggle("is-selected", selectedGuideSpecialties.has(option.dataset.value));
    });
    if (guideSpecialtyValue) guideSpecialtyValue.value = Array.from(selectedGuideSpecialties).join(", ");
    if (guideSpecialtyPlaceholder) {
      guideSpecialtyPlaceholder.textContent = selectedGuideSpecialties.size
        ? `${selectedGuideSpecialties.size} Specialt${selectedGuideSpecialties.size === 1 ? "y" : "ies"} selected`
        : "Add specialties";
    }
    if (!guideSpecialtyChips) return;
    guideSpecialtyChips.innerHTML = "";
    selectedGuideSpecialties.forEach((specialty) => {
      const option = guideSpecialtyOptions.find((item) => item.dataset.value === specialty);
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "guide-language-chip";
      chip.dataset.removeGuideSpecialty = specialty;
      chip.innerHTML = `<span>${option?.textContent || specialty}</span><strong aria-hidden="true">×</strong>`;
      chip.setAttribute("aria-label", `Remove ${specialty}`);
      guideSpecialtyChips.appendChild(chip);
    });
  };

  guideSpecialtyToggle?.addEventListener("click", () => {
    const open = !guideSpecialtySelect?.classList.contains("is-open");
    guideSpecialtySelect?.classList.toggle("is-open", open);
    guideSpecialtyToggle.setAttribute("aria-expanded", String(open));
  });

  guideSpecialtyOptions.forEach((option) => {
    option.addEventListener("click", (event) => {
      event.stopPropagation();
      const value = option.dataset.value;
      if (!value) return;
      if (selectedGuideSpecialties.has(value)) {
        selectedGuideSpecialties.delete(value);
      } else {
        if (selectedGuideSpecialties.size >= 4) {
          alert("You can select up to 4 specialties.");
          return;
        }
        selectedGuideSpecialties.add(value);
      }
      renderGuideSpecialties();
      guideSpecialtySelect?.classList.remove("is-open");
      guideSpecialtyToggle?.setAttribute("aria-expanded", "false");
    });
  });

  guideSpecialtyChips?.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-remove-guide-specialty]");
    if (!chip) return;
    selectedGuideSpecialties.delete(chip.dataset.removeGuideSpecialty);
    renderGuideSpecialties();
  });



  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-guide-specialty-select]")) {
      guideSpecialtySelect?.classList.remove("is-open");
      guideSpecialtyToggle?.setAttribute("aria-expanded", "false");
    }
  });

  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => {
      const passwordInput = button.closest(".password-wrap")?.querySelector("input");
      if (!passwordInput) return;
      const showing = passwordInput.type === "text";
      passwordInput.type = showing ? "password" : "text";
      button.textContent = showing ? "Show" : "Hide";
      button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  });

  const adminHold = document.querySelector("[data-admin-hold]");
  let adminHoldTimer = null;
  const clearAdminHold = () => {
    window.clearTimeout(adminHoldTimer);
    adminHoldTimer = null;
    adminHold?.classList.remove("is-holding");
  };
  const startAdminHold = () => {
    if (!adminHold) return;
    clearAdminHold();
    adminHold.classList.add("is-holding");
    adminHoldTimer = window.setTimeout(() => {
      const target = adminHold.dataset.adminUrl;
      if (target) {
        document.body.classList.add("page-transition-out");
        window.setTimeout(() => {
          window.location.href = target;
        }, 260);
      }
    }, 3000);
  };
  adminHold?.addEventListener("pointerdown", startAdminHold);
  adminHold?.addEventListener("pointerup", clearAdminHold);
  adminHold?.addEventListener("pointerleave", clearAdminHold);
  adminHold?.addEventListener("pointercancel", clearAdminHold);
  adminHold?.addEventListener("click", (event) => event.preventDefault());

  const dashboardTabs = Array.from(document.querySelectorAll("[data-dashboard-tab]"));
  const switchDashboardTab = (tabName) => {
    if (!tabName) return;
    document.querySelectorAll(".tab-content").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
    dashboardTabs.forEach((button) => {
      button.classList.toggle("active", button.dataset.dashboardTab === tabName);
    });
  };

  dashboardTabs.forEach((button) => {
    button.addEventListener("click", () => switchDashboardTab(button.dataset.dashboardTab));
  });

  const adminTabs = Array.from(document.querySelectorAll("[data-admin-tab]"));
  const switchAdminTab = (tabName) => {
    if (!tabName) return;
    document.querySelectorAll(".admin-tab-panel").forEach((panel) => {
      panel.classList.toggle("is-active", panel.id === `admin-${tabName}`);
    });
    adminTabs.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.adminTab === tabName);
    });
  };

  adminTabs.forEach((button) => {
    button.addEventListener("click", () => switchAdminTab(button.dataset.adminTab));
  });

  const adminGuideSearch = document.querySelector("[data-admin-guide-search]");
  const adminGuideRows = Array.from(document.querySelectorAll("[data-admin-guide-row]"));
  adminGuideSearch?.addEventListener("input", () => {
    const query = adminGuideSearch.value.trim().toLowerCase();
    adminGuideRows.forEach((row) => {
      row.classList.toggle("is-hidden", query && !row.dataset.search.toLowerCase().includes(query));
    });
  });

  const adminLanguageFilter = document.querySelector("[data-admin-language-filter]");
  const adminTourRows = Array.from(document.querySelectorAll("[data-admin-tour-row]"));
  adminLanguageFilter?.addEventListener("change", () => {
    const language = adminLanguageFilter.value;
    adminTourRows.forEach((row) => {
      row.classList.toggle("is-hidden", language !== "all" && row.dataset.language !== language);
    });
  });

  // Admin scroll tables: show exactly 4 full rows (header + 4 rows), then scroll.
  // Measure the real bottom of the 4th row so the 5th is never half-cropped
  // (rows vary in height because long titles wrap).
  document.querySelectorAll(".admin-table-wrap.admin-scroll").forEach((wrap) => {
    const rows = Array.from(wrap.querySelectorAll("tbody tr"));
    if (rows.length <= 4) {
      wrap.style.maxHeight = "none";
      wrap.style.overflowY = "visible";
      return;
    }
    wrap.style.maxHeight = "none";
    wrap.scrollTop = 0;
    const top = wrap.getBoundingClientRect().top;
    const fourthBottom = rows[3].getBoundingClientRect().bottom;
    wrap.style.maxHeight = `${Math.round(fourthBottom - top)}px`;
  });

  const guideDetailButtons = Array.from(document.querySelectorAll("[data-guide-detail]"));
  const guideModal = document.querySelector("[data-guide-modal]");
  const guideModalClose = document.querySelector("[data-guide-modal-close]");
  const guideModalAvatar = document.querySelector("[data-guide-modal-avatar]");
  const guideModalName = document.querySelector("[data-guide-modal-name]");
  const guideModalEmail = document.querySelector("[data-guide-modal-email]");
  const guideModalRating = document.querySelector("[data-guide-modal-rating]");
  const guideModalReviews = document.querySelector("[data-guide-modal-reviews]");
  const guideModalLanguages = document.querySelector("[data-guide-modal-languages]");
  const guideModalTours = document.querySelector("[data-guide-modal-tours]");
  const guideModalGuests = document.querySelector("[data-guide-modal-guests]");
  const guideModalSpecialty = document.querySelector("[data-guide-modal-specialty]");
  const guideModalBookings = document.querySelector("[data-guide-modal-bookings]");
  const languageFlags = {
    English: "🇬🇧",
    German: "🇩🇪",
    French: "🇫🇷",
    Czech: "🇨🇿",
    Spanish: "🇪🇸",
    Italian: "🇮🇹",
    Portuguese: "🇵🇹"
  };

  const closeGuideModal = () => {
    guideModal?.classList.remove("is-open");
    guideModal?.setAttribute("aria-hidden", "true");
  };

  const openGuideModal = (button) => {
    if (!guideModal) return;
    const guide = button.dataset;
    if (guideModalAvatar) {
      guideModalAvatar.className = `admin-guide-modal-avatar fallback-${guide.guideColor || "blue"}`;
      guideModalAvatar.textContent = "";
      if (guide.guideAvatar) {
        const avatarImage = document.createElement("img");
        avatarImage.src = guide.guideAvatar;
        avatarImage.alt = guide.guideName || "Guide";
        guideModalAvatar.appendChild(avatarImage);
      } else {
        const avatarInitial = document.createElement("span");
        avatarInitial.textContent = guide.guideInitial || "";
        guideModalAvatar.appendChild(avatarInitial);
      }
    }
    if (guideModalName) guideModalName.textContent = guide.guideName || "Guide";
    if (guideModalEmail) guideModalEmail.textContent = guide.guideEmail || "";
    if (guideModalRating) guideModalRating.textContent = guide.guideRating || "9.0/10";
    if (guideModalReviews) guideModalReviews.textContent = `based on ${guide.guideReviews || 0} reviews`;
    if (guideModalTours) guideModalTours.textContent = guide.guideTours || "0";
    if (guideModalGuests) guideModalGuests.textContent = guide.guideGuests || "0";
    if (guideModalSpecialty) guideModalSpecialty.textContent = guide.guideSpecialty || "History";
    if (guideModalBookings) guideModalBookings.textContent = guide.guideBookings || "0";
    if (guideModalLanguages) {
      guideModalLanguages.innerHTML = "";
      (guide.guideLanguages || "").split(",").map((language) => language.trim()).filter(Boolean).forEach((language) => {
        const item = document.createElement("span");
        item.textContent = `${languageFlags[language] || ""} ${language}`.trim();
        guideModalLanguages.appendChild(item);
      });
    }
    guideModal.classList.add("is-open");
    guideModal.setAttribute("aria-hidden", "false");
  };

  guideDetailButtons.forEach((button) => {
    button.addEventListener("click", () => openGuideModal(button));
  });
  guideModalClose?.addEventListener("click", closeGuideModal);
  guideModal?.addEventListener("click", (event) => {
    if (event.target === guideModal) closeGuideModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeGuideModal();
  });

  const pendingReportCards = Array.from(document.querySelectorAll("[data-report-target]"));
  const reportEmpty = document.querySelector("[data-report-empty]");
  const reportForm = document.querySelector("[data-report-form]");
  const reportTitle = document.querySelector("[data-report-title]");

  pendingReportCards.forEach((card) => {
    card.addEventListener("click", () => {
      pendingReportCards.forEach((item) => item.classList.remove("is-selected"));
      card.classList.add("is-selected");
      reportEmpty?.classList.add("is-hidden");
      reportForm?.classList.remove("is-hidden");
      if (reportTitle) {
        const title = card.querySelector("strong")?.textContent?.trim() || "Tour report";
        const details = card.querySelector("small")?.textContent?.trim() || "";
        reportTitle.textContent = `${title} - ${details}`;
      }
    });
  });

  const guideOpsModal = document.querySelector("[data-guide-ops-modal]");
  const guideOpsTitle = document.querySelector("[data-guide-ops-title]");
  const guideOpsBody = document.querySelector("[data-guide-ops-body]");
  const guideOpsCloseButtons = Array.from(document.querySelectorAll("[data-guide-ops-close]"));
  const guideReportModal = document.querySelector("[data-guide-report-modal]");
  const guideReportTitle = document.querySelector("[data-guide-report-title]");
  const guideReportDate = document.querySelector("[data-guide-report-date]");
  const guideReportExpected = document.querySelector("[data-guide-report-expected]");
  const guideReportClose = document.querySelector("[data-guide-report-close]");
  const guideReportForm = document.querySelector("[data-guide-report-form]");
  const guideReportOccurrence = document.querySelector("[data-guide-report-occurrence]");
  const guideReportActual = document.querySelector("[data-guide-report-actual]");
  const guideReportPhoto = document.querySelector("[data-guide-report-photo]");
  const guideReportUpload = document.querySelector("[data-guide-report-upload]");
  const guideReportPhotoNote = document.querySelector("[data-guide-report-photo-note]");
  const guideReportMessage = document.querySelector("[data-guide-report-message]");

  const openGuideOpsModal = (title, bodyHtml) => {
    if (!guideOpsModal || !guideOpsTitle || !guideOpsBody) return;
    guideOpsTitle.textContent = title;
    guideOpsBody.innerHTML = bodyHtml;
    guideOpsModal.classList.add("is-open");
    guideOpsModal.setAttribute("aria-hidden", "false");
  };

  const closeGuideOpsModal = () => {
    guideOpsModal?.classList.remove("is-open");
    guideOpsModal?.setAttribute("aria-hidden", "true");
  };

  const closeGuideReportModal = () => {
    guideReportModal?.classList.remove("is-open");
    guideReportModal?.setAttribute("aria-hidden", "true");
  };

  document.querySelectorAll("[data-guide-reservations]").forEach((button) => {
    button.addEventListener("click", () => {
      const data = button.dataset;
      let ledgerHtml = "";
      try {
        const list = JSON.parse(data.reservationList || "[]");
        if (list.length === 0) {
          ledgerHtml = "<p>No active reservations for this occurrence.</p>";
        } else {
          list.forEach((res, index) => {
            const guestText = res.guests.length > 0 ? `+${res.guests.length} guests` : "no guests";
            const accompanyingText = res.guests.length > 0 ? `<p>Accompanying: ${res.guests.join(", ")}</p>` : "<p>No accompanying guests.</p>";
            ledgerHtml += `
              <article>
                <strong>${guestText} (${res.total_spots} spots)</strong>
                <h4>${index + 1}. ${res.participant}</h4>
                <p>Contact email: ${res.email}</p>
                ${accompanyingText}
              </article>
            `;
          });
        }
      } catch (e) {
        console.error("Failed to parse reservation list", e);
        ledgerHtml = "<p>Error loading reservations.</p>";
      }

      openGuideOpsModal(data.reservationTitle || "Reservations", `
        <div class="reservation-audit-summary">
          <strong>Occurrence Date:</strong> ${data.reservationDate}<br>
          <strong>Total Expected Attendees Count:</strong> ${data.reservationExpected} seats reserved (${data.reservationGroups} primary accounts)
        </div>
        <h3>Expected Booking Seats Ledger</h3>
        <div class="reservation-ledger">
          ${ledgerHtml}
        </div>
      `);
    });
  });

  // Mark as done logic
  document.querySelectorAll("[data-mark-as-done]").forEach((button) => {
    button.addEventListener("click", async () => {
      const occurrenceId = button.dataset.occurrenceId;
      if (!occurrenceId || button.disabled) return;
      button.disabled = true;
      button.textContent = "Marking…";
      try {
        const response = await fetch(`/guide/occurrences/${occurrenceId}/done`, { method: "POST" });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || "Could not mark as done.");
        // Reload so the server moves it into Tours History and opens its report.
        window.location.reload();
      } catch (error) {
        button.disabled = false;
        button.textContent = "Mark as done";
        window.alert(error.message);
      }
    });
  });

  // Reflect whether a photo is required based on the declared attendance.
  const syncReportPhotoRequirement = () => {
    const attendees = Number(guideReportActual?.value || 0);
    const photoNeeded = attendees >= 1;
    if (guideReportPhoto) guideReportPhoto.required = photoNeeded;
    guideReportUpload?.classList.toggle("is-optional", !photoNeeded);
    if (guideReportPhotoNote) {
      guideReportPhotoNote.textContent = photoNeeded
        ? "Drag and drop or click here to choose group evidence photo"
        : "No photo needed — nobody attended, this report will be cleared.";
    }
  };

  document.querySelectorAll("[data-guide-report]").forEach((button) => {
    button.addEventListener("click", () => {
      if (guideReportTitle) guideReportTitle.textContent = `Report Attendance: ${button.dataset.reportTitle}`;
      if (guideReportDate) guideReportDate.textContent = `Occurrence: ${button.dataset.reportDate}`;
      if (guideReportExpected) guideReportExpected.textContent = button.dataset.reportExpected || "0";
      if (guideReportOccurrence) guideReportOccurrence.value = button.dataset.reportOccurrence || "";
      if (guideReportActual) guideReportActual.value = button.dataset.reportExpected || "1";
      if (guideReportPhoto) guideReportPhoto.value = "";
      if (guideReportMessage) { guideReportMessage.textContent = ""; guideReportMessage.classList.remove("is-error", "is-ok"); }
      syncReportPhotoRequirement();
      guideReportModal?.classList.add("is-open");
      guideReportModal?.setAttribute("aria-hidden", "false");
    });
  });

  guideReportActual?.addEventListener("input", syncReportPhotoRequirement);

  guideReportForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const attendees = Number(guideReportActual?.value || 0);
    const expected = Number(guideReportExpected?.textContent || 0);
    if (attendees < 0) {
      if (guideReportMessage) { guideReportMessage.textContent = "Attendance cannot be negative."; guideReportMessage.classList.add("is-error"); }
      return;
    }
    if (attendees > expected) {
      if (guideReportMessage) { guideReportMessage.textContent = `Attendance cannot exceed the ${expected} booked seats.`; guideReportMessage.classList.add("is-error"); }
      return;
    }
    if (attendees >= 1 && !(guideReportPhoto?.files?.length)) {
      if (guideReportMessage) { guideReportMessage.textContent = "Please upload one evidence photo."; guideReportMessage.classList.add("is-error"); }
      return;
    }
    try {
      const response = await fetch("/guide/reports", { method: "POST", body: new FormData(guideReportForm) });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "Could not file the report.");
      if (guideReportMessage) { guideReportMessage.textContent = "Report filed."; guideReportMessage.classList.remove("is-error"); guideReportMessage.classList.add("is-ok"); }
      setTimeout(() => window.location.reload(), 800);
    } catch (error) {
      if (guideReportMessage) { guideReportMessage.textContent = error.message; guideReportMessage.classList.add("is-error"); guideReportMessage.classList.remove("is-ok"); }
    }
  });

  guideOpsCloseButtons.forEach((button) => button.addEventListener("click", closeGuideOpsModal));
  guideOpsModal?.addEventListener("click", (event) => {
    if (event.target === guideOpsModal) closeGuideOpsModal();
  });
  guideReportClose?.addEventListener("click", closeGuideReportModal);
  guideReportModal?.addEventListener("click", (event) => {
    if (event.target === guideReportModal) closeGuideReportModal();
  });

  const addTourModal = document.querySelector("[data-add-tour-modal]");
  const openAddTour = document.querySelector("[data-open-add-tour]");
  const closeAddTourButtons = Array.from(document.querySelectorAll("[data-close-add-tour]"));
  const addTourForm = addTourModal?.querySelector("form");
  const scheduleBuilder = document.querySelector("[data-schedule-builder]");
  const addScheduleRow = document.querySelector("[data-add-schedule-row]");
  const scheduleWarning = document.querySelector("[data-schedule-warning]");
  const stopsBuilder = document.querySelector("[data-stops-builder]");
  const addStop = document.querySelector("[data-add-stop]");
  const removeStop = document.querySelector("[data-remove-stop]");
  const tourPhotos = document.querySelector("[data-tour-photos]");
  const photoCount = document.querySelector("[data-photo-count]");
  const existingPhotos = document.querySelector("[data-existing-photos]");

  // Number of existing photos the guide chose to keep (one hidden input each).
  const keptPhotoCount = () => existingPhotos
    ? existingPhotos.querySelectorAll('input[name="keep_photo_ids[]"]').length : 0;

  // Photo status line. In read-only "More Details" view it just states how many
  // photos the tour has; while editing it shows the live kept + new = 5 counter.
  const updatePhotoCount = () => {
    if (!photoCount) return;
    const kept = keptPhotoCount();
    const selected = tourPhotos?.files?.length || 0;
    const total = kept + selected;
    if (addTourForm?.classList.contains("is-readonly")) {
      photoCount.textContent = `${kept} photo${kept === 1 ? "" : "s"} uploaded`;
      photoCount.classList.remove("is-error");
      return;
    }
    if (kept === 0 && selected === 0) {
      photoCount.textContent = "No photos selected";
    } else {
      photoCount.textContent = `${total} of 5 photos (${kept} kept, ${selected} new)`;
    }
    photoCount.classList.toggle("is-error", total !== 5);
  };

  // Render the tour's current photos as deletable thumbnails when viewing/editing.
  const renderExistingPhotos = (raw) => {
    if (!existingPhotos) return;
    existingPhotos.innerHTML = "";
    let photos = [];
    try { photos = raw ? JSON.parse(raw) : []; } catch (e) { photos = []; }
    photos.forEach((photo) => {
      const thumb = document.createElement("div");
      thumb.className = "guide-photo-thumb";
      thumb.innerHTML =
        `<img src="${photo.url}" alt="Tour photo">` +
        `<button type="button" class="guide-photo-remove" data-remove-photo aria-label="Remove this photo">×</button>` +
        `<input type="hidden" name="keep_photo_ids[]" value="${photo.id}">`;
      existingPhotos.appendChild(thumb);
    });
  };
  const addTourMessage = document.querySelector("[data-add-tour-message]");
  const addTourTitle = document.querySelector("[data-add-tour-title]");
  const addTourSubtitle = document.querySelector("[data-add-tour-subtitle]");
  const editTourButton = document.querySelector("[data-edit-tour]");
  const saveTourButton = document.querySelector("[data-save-tour]");
  const existingSchedulesData = addTourModal?.dataset.existingSchedules;
  const existingGuideSchedules = existingSchedulesData ? JSON.parse(existingSchedulesData) : [];

  // Edit-mode state: which tour (slug) is open, and whether it is locked
  // (i.e. a reservation exists, so the tour can no longer be edited at all).
  let currentEditSlug = null;
  let currentTourLocked = false;

  // Grey padlock icon (replaces the previous emoji) shown on locked tours.
  const LOCK_ICON_SVG = '<svg class="lock-icon" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="#94a3b8" d="M12 1a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-1V6a5 5 0 0 0-5-5zm-3 5a3 3 0 0 1 6 0v3H9V6zm3 7a1.6 1.6 0 0 1 .8 2.98V18a.8.8 0 0 1-1.6 0v-2.02A1.6 1.6 0 0 1 12 13z"/></svg>';

  const setAddTourReadonly = (readonly) => {
    if (!addTourForm) return;
    addTourForm.classList.toggle("is-readonly", Boolean(readonly));
    addTourForm.querySelectorAll("input, select, textarea").forEach((control) => {
      control.disabled = Boolean(readonly);
    });
    addTourForm.querySelectorAll("[data-add-schedule-row], [data-add-stop], [data-remove-stop], [data-remove-schedule], [data-remove-photo]").forEach((control) => {
      control.disabled = Boolean(readonly);
    });
    if (!readonly) {
      refreshScheduleRemoveButtons();
      refreshStopRemoveButton();
    } else {
      // Viewing only: never show schedule conflict warnings/highlighting
      // (validation populated by fillTourDetailsForm runs before this).
      addTourForm.querySelectorAll(".guide-schedule-edit-row").forEach((row) => row.classList.remove("has-conflict"));
      setScheduleWarning("", false);
    }
    // Refresh the photo status line to match the new mode (view vs edit).
    updatePhotoCount();
  };

  const setCheckboxGroup = (name, values) => {
    if (!addTourForm) return;
    const selected = values.map((value) => value.trim().toLowerCase()).filter(Boolean);
    addTourForm.querySelectorAll(`[name="${name}"]`).forEach((checkbox) => {
      checkbox.checked = selected.includes(checkbox.value.toLowerCase());
    });
  };

  const fillTourDetailsForm = (data) => {
    if (!addTourForm) return;
    const titleInput = addTourForm.querySelector('[name="tour_title"]');
    const meetingPointInput = addTourForm.querySelector('[name="meeting_point"]');
    const maxInput = addTourForm.querySelector('[name="max_people"]');
    const description = addTourForm.querySelector('[name="brief_description"]');
    const durationInput = addTourForm.querySelector('[name="tour_duration"]');

    if (titleInput) titleInput.value = data.tourTitle || "";
    if (meetingPointInput) meetingPointInput.value = data.tourMeeting || "";
    if (maxInput) maxInput.value = data.tourMax || "15";
    if (description) description.value = data.tourDescription || "";
    if (durationInput) {
      const dur = data.tourDuration || "90";
      // Make sure the tour's duration is selectable even if it isn't one of the
      // preset options, so it always shows in the details view.
      if (durationInput.tagName === "SELECT" && !Array.from(durationInput.options).some((o) => o.value === String(dur))) {
        const opt = document.createElement("option");
        opt.value = String(dur);
        opt.textContent = `${dur} min`;
        durationInput.appendChild(opt);
      }
      durationInput.value = dur;
    }

    // Populate stops from DB
    if (stopsBuilder && data.tourStops) {
      try {
        const stops = JSON.parse(data.tourStops);
        stopsBuilder.innerHTML = "";
        stops.forEach((stop) => {
          const name = typeof stop === "string" ? stop : (stop.title || "");
          stopsBuilder.appendChild(createStopRow(name));
        });
        while (stopsBuilder.querySelectorAll('[name="stops[]"]').length < 4) {
          stopsBuilder.appendChild(createStopRow());
        }
        refreshStopRemoveButton();
      } catch (e) {
        console.error("Failed to parse tourStops", e);
      }
    }

    // Populate themes from DB
    if (data.tourThemes) {
      try {
        const themes = JSON.parse(data.tourThemes);
        setCheckboxGroup("themes", themes);
      } catch (e) {
        console.error("Failed to parse tourThemes", e);
      }
    }

    // Populate accessibility from DB
    if (data.tourAccessibility) {
      try {
        const accessibility = JSON.parse(data.tourAccessibility);
        const selectedAccessibility = [];
        if (accessibility.wheelchair_accessible) selectedAccessibility.push("Wheelchair accessible");
        if (accessibility.suitable_for_children) selectedAccessibility.push("Suitable for children");
        if (accessibility.pet_friendly) selectedAccessibility.push("Pet friendly");
        setCheckboxGroup("accessibility", selectedAccessibility);
      } catch (e) {
        console.error("Failed to parse tourAccessibility", e);
      }
    }

    // Populate weekly schedules from DB
    if (scheduleBuilder && data.tourWeeklySchedules) {
      try {
        const weekly = JSON.parse(data.tourWeeklySchedules);
        scheduleBuilder.innerHTML = "";
        weekly.forEach((sch) => {
          const row = document.createElement("article");
          row.className = "guide-schedule-edit-row";
          row.innerHTML = `
              <label>
                <span>Day</span>
                <select name="schedule_day[]" required>
                  <option>Monday</option>
                  <option>Tuesday</option>
                  <option>Wednesday</option>
                  <option>Thursday</option>
                  <option>Friday</option>
                  <option>Saturday</option>
                  <option>Sunday</option>
                </select>
              </label>
              <label>
                <span>Start time</span>
                <input type="time" name="schedule_time[]" required>
              </label>
              <label>
                <span>Language</span>
                <select name="schedule_language[]" required>
                  <option>English</option>
                  <option>Spanish</option>
                  <option>German</option>
                  <option>Italian</option>
                  <option>Portuguese</option>
                </select>
              </label>
              <button type="button" class="guide-row-remove" data-remove-schedule aria-label="Remove schedule row">×</button>
          `;
          row.querySelector('[name="schedule_day[]"]').value = sch.weekday;
          row.querySelector('[name="schedule_time[]"]').value = sch.start_time;
          row.querySelector('[name="schedule_language[]"]').value = sch.language;
          scheduleBuilder.appendChild(row);
        });

        // Re-attach remove row event listeners
        scheduleBuilder.querySelectorAll("[data-remove-schedule]").forEach((btn) => {
          btn.addEventListener("click", () => {
            btn.closest(".guide-schedule-edit-row")?.remove();
            refreshScheduleRemoveButtons();
            validateSchedules();
          });
        });

        refreshScheduleRemoveButtons();
        validateSchedules();
      } catch (e) {
        console.error("Failed to parse weekly schedules", e);
      }
    }

    // Show the tour's existing photos as deletable thumbnails.
    renderExistingPhotos(data.tourPhotos);
    if (tourPhotos) tourPhotos.value = "";
    updatePhotoCount();
  };

  const openAddTourModal = () => {
    addTourModal?.classList.add("is-open");
    addTourModal?.setAttribute("aria-hidden", "false");
  };

  const closeAddTourModal = () => {
    addTourModal?.classList.remove("is-open");
    addTourModal?.setAttribute("aria-hidden", "true");
  };

  const timeToMinutes = (value) => {
    const [hours, minutes] = value.split(":").map(Number);
    return hours * 60 + minutes;
  };

  const readScheduleRows = () => {
    if (!scheduleBuilder) return [];
    const durationInput = document.querySelector('[name="tour_duration"]');
    const globalDuration = Number(durationInput?.value || 90);
    return Array.from(scheduleBuilder.querySelectorAll(".guide-schedule-edit-row")).map((row) => {
      const day = row.querySelector('[name="schedule_day[]"]')?.value || "";
      const start = row.querySelector('[name="schedule_time[]"]')?.value || "00:00";
      const language = row.querySelector('[name="schedule_language[]"]')?.value || "";
      return {
        row,
        day,
        start,
        duration: globalDuration,
        language,
        startMinutes: timeToMinutes(start),
        endMinutes: timeToMinutes(start) + globalDuration,
      };
    });
  };

  const schedulesOverlap = (a, b) => (
    a.day === b.day &&
    a.startMinutes < b.startMinutes + b.duration &&
    a.endMinutes > b.startMinutes
  );

  const setScheduleWarning = (message, isError) => {
    if (!scheduleWarning) return;
    scheduleWarning.textContent = message;
    scheduleWarning.classList.toggle("is-error", Boolean(isError));
    scheduleWarning.classList.toggle("is-ok", Boolean(message && !isError));
  };

  const validateSchedules = () => {
    // While only viewing a tour (read-only), never show schedule conflicts — they
    // are only meaningful when the guide is actively editing/adding schedules.
    if (addTourForm?.classList.contains("is-readonly")) {
      scheduleBuilder?.querySelectorAll(".guide-schedule-edit-row").forEach((r) => r.classList.remove("has-conflict"));
      setScheduleWarning("", false);
      return true;
    }

    const rows = readScheduleRows();
    // When editing an existing tour, its own schedules must not count as "another
    // tour" — only genuine clashes with the guide's OTHER tours matter.
    const otherTourSchedules = existingGuideSchedules.filter((e) => e.tour !== currentEditSlug);
    let conflict = "";

    rows.forEach((row, index) => {
      const duplicateLanguage = rows.some((other, otherIndex) => (
        otherIndex !== index &&
        other.day === row.day &&
        other.language === row.language
      ));
      const rowOverlap = rows.some((other, otherIndex) => otherIndex !== index && schedulesOverlap(row, other));

      // Cross-tour conflicts only happen when the TIME windows overlap — running
      // a different tour on the same day in the same language is fine as long as
      // the times don't clash.
      const existingOverlap = otherTourSchedules.some((existing) => schedulesOverlap(row, {
        day: existing.day,
        startMinutes: timeToMinutes(existing.start),
        endMinutes: timeToMinutes(existing.start) + existing.duration,
        duration: existing.duration,
      }));

      row.row.classList.toggle("has-conflict", duplicateLanguage || rowOverlap || existingOverlap);
      if (!conflict && duplicateLanguage) conflict = `${row.day} already has this tour in ${row.language} — same day needs a different language.`;
      if (!conflict && rowOverlap) conflict = `${row.day} has overlapping start times within this tour.`;
      if (!conflict && existingOverlap) conflict = `${row.day} overlaps in time with another tour you have scheduled.`;
    });

    setScheduleWarning(conflict || "Schedule looks available.", Boolean(conflict));
    return !conflict;
  };

  const refreshScheduleRemoveButtons = () => {
    if (!scheduleBuilder) return;
    const rows = scheduleBuilder.querySelectorAll(".guide-schedule-edit-row");
    rows.forEach((row) => {
      const remove = row.querySelector("[data-remove-schedule]");
      if (remove) remove.disabled = rows.length === 1;
    });
  };

  const resetScheduleRows = () => {
    if (!scheduleBuilder) return [];
    const rows = Array.from(scheduleBuilder.querySelectorAll(".guide-schedule-edit-row"));
    rows.slice(1).forEach((row) => row.remove());
    const firstRow = scheduleBuilder.querySelector(".guide-schedule-edit-row");
    if (!firstRow) return;
    const daySelect = firstRow.querySelector('[name="schedule_day[]"]');
    const timeInput = firstRow.querySelector('[name="schedule_time[]"]');
    const languageSelect = firstRow.querySelector('[name="schedule_language[]"]');
    if (daySelect) daySelect.value = "Monday";
    if (timeInput) timeInput.value = "09:00";
    if (languageSelect) languageSelect.value = "English";
    firstRow.classList.remove("has-conflict");
    const durationInput = document.querySelector('[name="tour_duration"]');
    if (durationInput) durationInput.value = "90";
    refreshScheduleRemoveButtons();
  };

  // Build one horizontal stop row: name input (left) + description (right, max 100).
  const createStopRow = (name = "") => {
    const input = document.createElement("input");
    input.type = "text";
    input.name = "stops[]";
    input.required = true;
    input.value = name;
    return input;
  };

  const refreshStopRemoveButton = () => {
    if (!stopsBuilder || !removeStop) return;
    removeStop.disabled = stopsBuilder.querySelectorAll('[name="stops[]"]').length <= 4;
  };

  const resetStops = () => {
    if (!stopsBuilder) return;
    stopsBuilder.innerHTML = "";
    for (let i = 0; i < 4; i += 1) stopsBuilder.appendChild(createStopRow());
    refreshStopRemoveButton();
  };

  openAddTour?.addEventListener("click", () => {
    currentEditSlug = null;
    currentTourLocked = false;
    addTourForm?.reset();
    resetScheduleRows();
    resetStops();
    if (existingPhotos) existingPhotos.innerHTML = "";  // fresh tour: no existing photos
    updatePhotoCount();
    setAddTourReadonly(false);
    if (addTourTitle) addTourTitle.textContent = "Add New Tour";
    if (addTourSubtitle) addTourSubtitle.textContent = "Create a tour blueprint that can later be saved to the database.";
    if (addTourMessage) {
      addTourMessage.textContent = "";
      addTourMessage.classList.remove("is-error", "is-ok");
    }
    if (editTourButton) {
      editTourButton.hidden = true;
      editTourButton.disabled = false;
    }
    if (saveTourButton) {
      saveTourButton.hidden = false;
      saveTourButton.textContent = "Save Tour Draft";
    }
    openAddTourModal();
    validateSchedules();
  });

  document.querySelectorAll("[data-guide-tour-details]").forEach((button) => {
    button.addEventListener("click", () => {
      const data = button.dataset;
      const isLocked = data.tourLocked === "true";
      currentEditSlug = data.tourSlug || null;
      currentTourLocked = isLocked;
      resetScheduleRows();
      resetStops();
      fillTourDetailsForm(data);
      setAddTourReadonly(true);
      if (addTourTitle) addTourTitle.textContent = data.tourTitle || "Tour Details";
      if (addTourSubtitle) addTourSubtitle.textContent = isLocked
        ? "This tour has bookings and can no longer be edited."
        : "Review your tour blueprint. You can edit every field while no reservation exists.";
      if (addTourMessage) {
        if (isLocked) {
          addTourMessage.innerHTML = `${LOCK_ICON_SVG} Booking exists - Cannot be edited`;
        } else {
          addTourMessage.textContent = "No active bookings. You can edit every field of this tour.";
        }
        addTourMessage.classList.toggle("is-error", isLocked);
        addTourMessage.classList.toggle("is-ok", !isLocked);
      }
      if (editTourButton) {
        editTourButton.hidden = false;
        editTourButton.disabled = isLocked;  // locked tours cannot be edited at all
      }
      if (saveTourButton) saveTourButton.hidden = true;
      openAddTourModal();
    });
  });

  editTourButton?.addEventListener("click", () => {
    if (currentTourLocked) return;  // safety: locked tours cannot be edited
    setAddTourReadonly(false);
    if (editTourButton) editTourButton.hidden = true;
    if (saveTourButton) {
      saveTourButton.hidden = false;
      saveTourButton.textContent = "Save Changes";
    }
    if (addTourMessage) {
      addTourMessage.textContent = "Editing enabled for this tour.";
      addTourMessage.classList.remove("is-error");
      addTourMessage.classList.add("is-ok");
    }
  });

  closeAddTourButtons.forEach((button) => button.addEventListener("click", closeAddTourModal));
  addTourModal?.addEventListener("click", (event) => {
    if (event.target === addTourModal) closeAddTourModal();
  });

  addScheduleRow?.addEventListener("click", () => {
    const firstRow = scheduleBuilder?.querySelector(".guide-schedule-edit-row");
    if (!scheduleBuilder || !firstRow) return;
    const clone = firstRow.cloneNode(true);
    clone.classList.remove("has-conflict");
    clone.querySelectorAll("input, select, button").forEach((control) => {
      control.disabled = false;
    });
    const daySelect = clone.querySelector('[name="schedule_day[]"]');
    if (daySelect) daySelect.value = "Tuesday";
    const timeInput = clone.querySelector('[name="schedule_time[]"]');
    if (timeInput) timeInput.value = "13:00";
    const languageSelect = clone.querySelector('[name="schedule_language[]"]');
    if (languageSelect) languageSelect.value = "Spanish";
    scheduleBuilder.appendChild(clone);
    refreshScheduleRemoveButtons();
    validateSchedules();
  });

  scheduleBuilder?.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-schedule]");
    if (!removeButton || removeButton.disabled) return;
    removeButton.closest(".guide-schedule-edit-row")?.remove();
    refreshScheduleRemoveButtons();
    validateSchedules();
  });

  scheduleBuilder?.addEventListener("input", validateSchedules);
  scheduleBuilder?.addEventListener("change", validateSchedules);
  refreshScheduleRemoveButtons();

  addStop?.addEventListener("click", () => {
    if (!stopsBuilder) return;
    stopsBuilder.appendChild(createStopRow());
    refreshStopRemoveButton();
  });

  removeStop?.addEventListener("click", () => {
    if (!stopsBuilder) return;
    const inputs = stopsBuilder.querySelectorAll('[name="stops[]"]');
    if (inputs.length <= 4) return;
    inputs[inputs.length - 1].remove();
    refreshStopRemoveButton();
  });

  tourPhotos?.addEventListener("change", updatePhotoCount);

  // Delete an existing photo thumbnail (removes its keep_photo_ids[] hidden input).
  existingPhotos?.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-photo]");
    if (!removeButton || removeButton.disabled) return;
    removeButton.closest(".guide-photo-thumb")?.remove();
    updatePhotoCount();
  });

  addTourForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const themesSelected = addTourForm.querySelectorAll('[name="themes"]:checked').length;
    const stopsFilled = Array.from(addTourForm.querySelectorAll('[name="stops[]"]')).filter((input) => input.value.trim()).length;
    const photosSelected = tourPhotos?.files?.length || 0;
    const scheduleOk = validateSchedules();
    const messages = [];

    const isEditing = Boolean(currentEditSlug);
    if (!themesSelected) messages.push("Select at least one tour theme.");
    if (stopsFilled < 4) messages.push("Add at least 4 tour stops.");
    if (isEditing) {
      // On edit, the kept existing photos plus any new uploads must total exactly 5.
      const totalPhotos = keptPhotoCount() + photosSelected;
      if (totalPhotos !== 5) {
        messages.push(`A tour must have exactly 5 photos — you currently have ${totalPhotos} (${keptPhotoCount()} kept, ${photosSelected} new).`);
      }
    } else if (photosSelected !== 5) {
      messages.push("Upload exactly 5 photos.");
    }
    if (!scheduleOk) messages.push("Fix schedule conflicts before saving.");

    if (messages.length > 0) {
      if (addTourMessage) {
        addTourMessage.textContent = messages[0];
        addTourMessage.classList.add("is-error");
        addTourMessage.classList.remove("is-ok");
      }
      return;
    }

    if (addTourMessage) {
      addTourMessage.textContent = "Saving tour draft...";
      addTourMessage.classList.remove("is-error", "is-ok");
    }

    try {
      const formData = new FormData(addTourForm);
      const endpoint = currentEditSlug
        ? `/guide/tours/${encodeURIComponent(currentEditSlug)}`
        : addTourForm.action;
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Failed to save tour.");
      }
      if (addTourMessage) {
        addTourMessage.textContent = "Tour saved successfully!";
        addTourMessage.classList.remove("is-error");
        addTourMessage.classList.add("is-ok");
      }
      setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
      if (addTourMessage) {
        addTourMessage.textContent = error.message;
        addTourMessage.classList.add("is-error");
        addTourMessage.classList.remove("is-ok");
      }
    }
  });

  const durationInput = document.querySelector('[name="tour_duration"]');
  durationInput?.addEventListener("change", validateSchedules);

  const dateModal = document.querySelector("[data-date-modal]");
  const openDatePicker = document.querySelector("[data-open-date-picker]");
  const closeDatePicker = document.querySelector("[data-close-date-picker]");
  const applyDate = document.querySelector("[data-apply-date]");
  const clearDate = document.querySelector("[data-clear-date]");
  const dateLabel = document.querySelector("[data-date-label]");
  const monthTitles = Array.from(document.querySelectorAll("[data-month-title]"));
  const calendarGrids = Array.from(document.querySelectorAll("[data-calendar-grid]"));
  const prevMonths = document.querySelector("[data-calendar-prev]");
  const nextMonths = document.querySelector("[data-calendar-next]");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let visibleMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  let selectedStart = null;
  let selectedEnd = null;

  const formatDateLabel = (dateValue) => {
    const date = new Date(`${dateValue}T00:00:00`);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  const formatDateValue = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const dateButtons = () => Array.from(document.querySelectorAll("[data-date]"));

  const updateDateSelection = () => {
    dateButtons().forEach((button) => {
      const value = button.dataset.date;
      button.classList.remove("selected", "in-range");
      if (!selectedStart) return;

      if (value === selectedStart || value === selectedEnd) {
        button.classList.add("selected");
      }

      if (selectedEnd && value > selectedStart && value < selectedEnd) {
        button.classList.add("in-range");
      }
    });
  };

  const updateDateLabel = () => {
    if (!dateLabel || !selectedStart) return;
    dateLabel.textContent = selectedEnd
      ? `${formatDateLabel(selectedStart)} - ${formatDateLabel(selectedEnd)}`
      : formatDateLabel(selectedStart);
  };

  const renderCalendar = () => {
    calendarGrids.forEach((grid, index) => {
      const monthDate = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + index, 1);
      const monthName = monthDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      const monthTitle = monthTitles[index];
      if (monthTitle) monthTitle.textContent = monthName;

      grid.innerHTML = "";
      const firstDay = (monthDate.getDay() + 6) % 7;
      const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();

      for (let offset = 0; offset < firstDay; offset += 1) {
        const spacer = document.createElement("span");
        spacer.className = "calendar-spacer";
        grid.appendChild(spacer);
      }

      for (let day = 1; day <= daysInMonth; day += 1) {
        const date = new Date(monthDate.getFullYear(), monthDate.getMonth(), day);
        const value = formatDateValue(date);
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.date = value;
        button.textContent = String(day);
        if (date < today) {
          button.disabled = true;
          button.classList.add("is-disabled");
        }
        button.addEventListener("click", () => {
          if (!selectedStart || selectedEnd || value < selectedStart) {
            selectedStart = value;
            selectedEnd = null;
          } else if (value === selectedStart) {
            selectedEnd = null;
          } else {
            selectedEnd = value;
          }
          updateDateSelection();
          updateDateLabel();
        });
        grid.appendChild(button);
      }
    });
    updateDateSelection();
  };

  const showDateModal = (event) => {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    if (!dateModal) return;
    renderCalendar();
    dateModal.classList.add("is-open");
    dateModal.setAttribute("aria-hidden", "false");
  };

  const hideDateModal = () => {
    if (!dateModal) return;
    dateModal.classList.remove("is-open");
    dateModal.setAttribute("aria-hidden", "true");
  };

  window.openWalkPragueDatePicker = showDateModal;
  openDatePicker?.addEventListener("click", showDateModal);
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-open-date-picker]")) {
      showDateModal(event);
    }
  });
  closeDatePicker?.addEventListener("click", hideDateModal);
  prevMonths?.addEventListener("click", () => {
    visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
    renderCalendar();
  });
  nextMonths?.addEventListener("click", () => {
    visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
    renderCalendar();
  });
  // Publish the chosen range so the homepage tour filters can read it.
  const publishDateRange = () => {
    window.walkPragueDateRange = { start: selectedStart, end: selectedEnd || selectedStart };
    window.dispatchEvent(new CustomEvent("walkprague:datechange"));
  };
  window.walkPragueDateRange = { start: null, end: null };

  applyDate?.addEventListener("click", () => {
    updateDateLabel();
    publishDateRange();
    hideDateModal();
  });
  clearDate?.addEventListener("click", () => {
    selectedStart = null;
    selectedEnd = null;
    updateDateSelection();
    if (dateLabel) dateLabel.textContent = "Select dates";
    publishDateRange();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hideDateModal();
  });

  const faqButton = document.querySelector("[data-faq-toggle]");
  const faqList = document.querySelector(".faq-card ul");
  const extraFaqs = [
    ["Can I cancel my booking?", "Yes. In the final backend, cancellation will be possible until 24 hours before the tour starts."],
    ["Where do tours start?", "Each tour card and detail page will show its exact meeting point and start time."],
    ["Can I book for friends?", "Yes. A participant can reserve for themselves and up to three additional guests."],
    ["Can guides create tours in any language?", "Guides will only create tours in languages they selected during registration."],
    ["Are tours wheelchair accessible?", "Accessible tours will be marked clearly and filterable from the homepage."],
    ["What happens if a tour is full?", "Fully booked tours can be hidden with the availability filter."],
    ["Can I choose food tours only?", "Yes. Tour themes such as gastronomy, ghost legends, and castle walks will be filterable."],
    ["Are reviews connected to tours?", "Yes. Later, reviews can be stored in the database and connected to a specific tour."],
    ["Can I see the guide profile?", "Yes. The guide name and profile photo appear on the tour card and can later link to a profile page."],
    ["Is payment required online?", "No. The project is based on free walking tours where tips are voluntary after the experience."]
  ];
  let visibleExtraFaqs = 0;

  faqButton?.addEventListener("click", () => {
    if (!faqList) return;
    if (visibleExtraFaqs >= extraFaqs.length) {
      faqList.querySelectorAll("[data-extra-faq]").forEach((item) => item.remove());
      visibleExtraFaqs = 0;
      faqButton.textContent = "Read more";
      return;
    }

    const nextFaqs = extraFaqs.slice(visibleExtraFaqs, visibleExtraFaqs + 3);
    nextFaqs.forEach(([question, answer]) => {
        const item = document.createElement("li");
        item.dataset.extraFaq = "true";
        item.innerHTML = `<strong>${question}</strong><p>${answer}</p>`;
        faqList.appendChild(item);
    });
    visibleExtraFaqs += nextFaqs.length;
    faqButton.textContent = visibleExtraFaqs >= extraFaqs.length ? "Show less" : "Read more";
  });
});

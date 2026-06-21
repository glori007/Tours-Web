document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("page-transition-ready");
  const currentRole = new URLSearchParams(window.location.search).get("role") === "guide" ? "guide" : "participant";

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
  selectAllLanguages?.addEventListener("change", () => {
    languageOptions.forEach((option) => {
      option.checked = selectAllLanguages.checked;
    });
  });

  const clearFilters = document.querySelector("[data-clear-filters]");
  clearFilters?.addEventListener("click", () => {
    document.querySelectorAll(".filters input[type='checkbox']").forEach((input) => {
      input.checked = false;
    });
  });

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

  const availabilityDays = Array.from(document.querySelectorAll("[data-week-day]"));
  const availabilityPanels = Array.from(document.querySelectorAll("[data-tour-day-panel]"));
  const selectedDateLabel = document.querySelector("[data-tour-selected-date]");
  const weekTitle = document.querySelector("[data-week-title]");
  const weekDayLabels = Array.from(document.querySelectorAll("[data-weekdays] span"));
  const prevWeek = document.querySelector("[data-week-prev]");
  const nextWeek = document.querySelector("[data-week-next]");
  const bookingControls = document.querySelector("[data-booking-control]");
  const bookNow = document.querySelector("[data-book-now]");
  const bookingCapacity = document.querySelector("[data-booking-capacity]");
  const bookingFeedback = document.querySelector("[data-booking-feedback]");
  const scheduledWeekDays = new Set(["0", "3", "6"]);
  const bookableWeekDays = new Set(["0", "3"]);
  const baseAvailabilityDate = new Date("2026-06-19T00:00:00");
  let availabilityWeekOffset = 0;
  let selectedWeekDay = "0";
  let currentAvailableLeft = 0;

  const formatLongDate = (date) => date.toLocaleDateString("en-US", {
    weekday: "short",
    day: "numeric",
    month: "long",
    year: "numeric"
  });

  const formatWeekTitle = (startDate, endDate) => {
    const sameMonth = startDate.getMonth() === endDate.getMonth() && startDate.getFullYear() === endDate.getFullYear();
    if (sameMonth) {
      return startDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    }
    return `${startDate.toLocaleDateString("en-US", { month: "short" })} - ${endDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}`;
  };

  const dateForWeekDay = (dayIndex) => {
    const date = new Date(baseAvailabilityDate);
    date.setDate(baseAvailabilityDate.getDate() + availabilityWeekOffset * 7 + Number(dayIndex));
    return date;
  };

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

  const activeScheduleButton = () => {
    const activePanel = availabilityPanels.find((panel) => !panel.classList.contains("is-hidden"));
    return activePanel?.querySelector(".schedule-options button.active") || activePanel?.querySelector(".schedule-options button");
  };

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
      setBookingMessage(`Only ${currentAvailableLeft} place${currentAvailableLeft === 1 ? "" : "s"} left. Remove guests to continue.`, "error");
    } else if (bookingFeedback?.classList.contains("is-error")) {
      setBookingMessage("");
    }
  };

  const showAvailabilityDay = (dayIndex) => {
    selectedWeekDay = String(dayIndex);
    const hasBookableSchedule = bookableWeekDays.has(selectedWeekDay);
    availabilityDays.forEach((button) => button.classList.toggle("active", button.dataset.weekDay === selectedWeekDay));
    availabilityPanels.forEach((panel) => {
      panel.classList.toggle("is-hidden", panel.dataset.tourDayPanel !== selectedWeekDay);
    });
    if (selectedDateLabel) selectedDateLabel.textContent = formatLongDate(dateForWeekDay(selectedWeekDay));
    setBookingAvailability(hasBookableSchedule);
    window.requestAnimationFrame(updateBookingCapacity);
  };

  const renderAvailabilityWeek = () => {
    if (!availabilityDays.length) return;
    const startDate = dateForWeekDay(0);
    const endDate = dateForWeekDay(6);
    if (weekTitle) weekTitle.textContent = formatWeekTitle(startDate, endDate);
    availabilityDays.forEach((button) => {
      const dayDate = dateForWeekDay(button.dataset.weekDay);
      button.textContent = String(dayDate.getDate());
      button.classList.toggle("scheduled", scheduledWeekDays.has(button.dataset.weekDay));
      button.classList.toggle("fully-booked-day", scheduledWeekDays.has(button.dataset.weekDay) && !bookableWeekDays.has(button.dataset.weekDay));
    });
    weekDayLabels.forEach((label, index) => {
      label.textContent = dateForWeekDay(index).toLocaleDateString("en-US", { weekday: "short" });
    });
    showAvailabilityDay(selectedWeekDay);
  };

  availabilityDays.forEach((dayButton) => {
    dayButton.addEventListener("click", () => {
      showAvailabilityDay(dayButton.dataset.weekDay);
    });
  });

  prevWeek?.addEventListener("click", () => {
    availabilityWeekOffset -= 1;
    renderAvailabilityWeek();
  });

  nextWeek?.addEventListener("click", () => {
    availabilityWeekOffset += 1;
    renderAvailabilityWeek();
  });

  renderAvailabilityWeek();

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
      const occurrenceId = selectedButton?.dataset.occurrenceId;
      if (!occurrenceId) {
        setBookingMessage("This departure is not connected to a backend occurrence yet.", "error");
        return;
      }
      fetch("/reservations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ occurrence_id: occurrenceId, guests })
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

  document.querySelectorAll(".schedule-options button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".schedule-options button").forEach((timeButton) => timeButton.classList.remove("active"));
      button.classList.add("active");
      const available = Number(button.dataset.availableLeft || 0) > 0;
      setBookingAvailability(available);
      updateBookingCapacity();
    });
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
    event.preventDefault();
    const target = authRoleInput?.value === "guide" ? "/guide-dashboard" : "/participant-home";
    document.body.classList.add("page-transition-out");
    window.setTimeout(() => {
      window.location.href = target;
    }, 260);
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
    event.preventDefault();
    const target = registerRoleInput?.value === "guide" ? "/guide-dashboard" : "/participant-home";
    document.body.classList.add("page-transition-out");
    window.setTimeout(() => {
      window.location.href = target;
    }, 260);
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
        ? `${selectedGuideLanguages.size} language${selectedGuideLanguages.size === 1 ? "" : "s"} selected`
        : "Select languages";
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
    });
  });

  guideLanguageChips?.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-remove-guide-language]");
    if (!chip) return;
    selectedGuideLanguages.delete(chip.dataset.removeGuideLanguage);
    renderGuideLanguages();
  });

  guideLanguageApply?.addEventListener("click", () => {
    guideLanguageSelect?.classList.remove("is-open");
    guideLanguageToggle?.setAttribute("aria-expanded", "false");
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-guide-language-select]")) {
      guideLanguageSelect?.classList.remove("is-open");
      guideLanguageToggle?.setAttribute("aria-expanded", "false");
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
      openGuideOpsModal(data.reservationTitle || "Reservations", `
        <div class="reservation-audit-summary">
          <strong>Occurrence Date:</strong> ${data.reservationDate}<br>
          <strong>Total Expected Attendees Count:</strong> ${data.reservationExpected} seats reserved (${data.reservationGroups} primary accounts)
        </div>
        <h3>Expected Booking Seats Ledger</h3>
        <div class="reservation-ledger">
          <article><strong>+2 guests (3 spots)</strong><h4>1. John Miller</h4><p>Contact email: j.miller@boston.edu</p><p>Accompanying: Sarah Miller, Dave Miller</p></article>
          <article><strong>+1 guests (2 spots)</strong><h4>2. Astrid Lindgren</h4><p>Contact email: astrid@lindgren.se</p><p>Accompanying: Lars Lindgren</p></article>
          <article><strong>+3 guests (4 spots)</strong><h4>3. Yoshi Tanaka</h4><p>Contact email: yoshi_t@tokyo.jp</p><p>Accompanying: Emi, Haru, Kenji</p></article>
        </div>
      `);
    });
  });

  document.querySelectorAll("[data-guide-report]").forEach((button) => {
    button.addEventListener("click", () => {
      if (guideReportTitle) guideReportTitle.textContent = `Report Attendance: ${button.dataset.reportTitle}`;
      if (guideReportDate) guideReportDate.textContent = `Occurrence: ${button.dataset.reportDate}`;
      if (guideReportExpected) guideReportExpected.textContent = button.dataset.reportExpected || "0";
      guideReportModal?.classList.add("is-open");
      guideReportModal?.setAttribute("aria-hidden", "false");
    });
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
  const addTourMessage = document.querySelector("[data-add-tour-message]");
  const addTourTitle = document.querySelector("[data-add-tour-title]");
  const addTourSubtitle = document.querySelector("[data-add-tour-subtitle]");
  const editTourButton = document.querySelector("[data-edit-tour]");
  const saveTourButton = document.querySelector("[data-save-tour]");
  const existingGuideSchedules = [
    { day: "Monday", start: "09:00", duration: 180 },
    { day: "Wednesday", start: "11:00", duration: 120 },
    { day: "Friday", start: "14:00", duration: 180 },
  ];

  const setAddTourReadonly = (readonly) => {
    if (!addTourForm) return;
    addTourForm.classList.toggle("is-readonly", Boolean(readonly));
    addTourForm.querySelectorAll("input, select, textarea").forEach((control) => {
      control.disabled = Boolean(readonly);
    });
    addTourForm.querySelectorAll("[data-add-schedule-row], [data-add-stop], [data-remove-stop], [data-remove-schedule]").forEach((control) => {
      control.disabled = Boolean(readonly);
    });
    if (!readonly) {
      refreshScheduleRemoveButtons();
      refreshStopRemoveButton();
    }
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
    const maxInput = addTourForm.querySelector('[name="max_people"]');
    const durationSelect = addTourForm.querySelector('[name="schedule_duration[]"]');
    const languageSelect = addTourForm.querySelector('[name="schedule_language[]"]');
    const description = addTourForm.querySelector('[name="brief_description"]');
    const stops = Array.from(addTourForm.querySelectorAll('[name="stops[]"]'));
    const firstLanguage = (data.tourLanguages || "English").split(",")[0]?.trim() || "English";

    if (titleInput) titleInput.value = data.tourTitle || "";
    if (maxInput) maxInput.value = data.tourMax || "15";
    if (durationSelect) durationSelect.value = data.tourDuration || "120";
    if (languageSelect) languageSelect.value = firstLanguage;
    if (description) {
      description.value = `${data.tourTitle || "This tour"} introduces guests to Prague through carefully planned stops, local context, and a clear meeting point at ${data.tourMeeting || "the city center"}.`;
    }

    ["Old Town Square", "Astronomical Clock", "Charles Bridge", "Powder Gate"].forEach((stop, index) => {
      if (stops[index]) stops[index].value = stop;
    });
    setCheckboxGroup("themes", ["Historical", "Architectural", "Local legends and traditions"]);
    setCheckboxGroup("accessibility", ["Suitable for children"]);
    if (photoCount) photoCount.textContent = "Photos already attached to this tour";
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
    return Array.from(scheduleBuilder.querySelectorAll(".guide-schedule-edit-row")).map((row) => {
      const day = row.querySelector('[name="schedule_day[]"]')?.value || "";
      const start = row.querySelector('[name="schedule_time[]"]')?.value || "00:00";
      const duration = Number(row.querySelector('[name="schedule_duration[]"]')?.value || 0);
      const language = row.querySelector('[name="schedule_language[]"]')?.value || "";
      return {
        row,
        day,
        start,
        duration,
        language,
        startMinutes: timeToMinutes(start),
        endMinutes: timeToMinutes(start) + duration,
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
    const rows = readScheduleRows();
    let conflict = "";

    rows.forEach((row, index) => {
      const duplicateLanguage = rows.some((other, otherIndex) => (
        otherIndex !== index &&
        other.day === row.day &&
        other.language === row.language
      ));
      const rowOverlap = rows.some((other, otherIndex) => otherIndex !== index && schedulesOverlap(row, other));
      const existingOverlap = existingGuideSchedules.some((existing) => schedulesOverlap(row, {
        day: existing.day,
        startMinutes: timeToMinutes(existing.start),
        endMinutes: timeToMinutes(existing.start) + existing.duration,
        duration: existing.duration,
      }));

      row.row.classList.toggle("has-conflict", duplicateLanguage || rowOverlap || existingOverlap);
      if (!conflict && duplicateLanguage) conflict = `${row.day} already has this tour language selected.`;
      if (!conflict && rowOverlap) conflict = `${row.day} has overlapping schedule times.`;
      if (!conflict && existingOverlap) conflict = `${row.day} overlaps with another tour already scheduled by this guide.`;
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
    if (!scheduleBuilder) return;
    const rows = Array.from(scheduleBuilder.querySelectorAll(".guide-schedule-edit-row"));
    rows.slice(1).forEach((row) => row.remove());
    const firstRow = scheduleBuilder.querySelector(".guide-schedule-edit-row");
    if (!firstRow) return;
    const daySelect = firstRow.querySelector('[name="schedule_day[]"]');
    const timeInput = firstRow.querySelector('[name="schedule_time[]"]');
    const durationSelect = firstRow.querySelector('[name="schedule_duration[]"]');
    const languageSelect = firstRow.querySelector('[name="schedule_language[]"]');
    if (daySelect) daySelect.value = "Monday";
    if (timeInput) timeInput.value = "09:00";
    if (durationSelect) durationSelect.value = "90";
    if (languageSelect) languageSelect.value = "English";
    firstRow.classList.remove("has-conflict");
    refreshScheduleRemoveButtons();
  };

  const refreshStopRemoveButton = () => {
    if (!stopsBuilder || !removeStop) return;
    removeStop.disabled = stopsBuilder.querySelectorAll('[name="stops[]"]').length <= 4;
  };

  const resetStops = () => {
    if (!stopsBuilder) return;
    const defaults = ["Old Town Square", "Astronomical Clock", "Church of Our Lady before Tyn", "Charles Bridge"];
    const inputs = Array.from(stopsBuilder.querySelectorAll('[name="stops[]"]'));
    inputs.slice(4).forEach((input) => input.remove());
    Array.from(stopsBuilder.querySelectorAll('[name="stops[]"]')).forEach((input, index) => {
      input.value = "";
      input.placeholder = defaults[index] || `Stop ${index + 1}`;
      input.required = true;
      input.disabled = false;
    });
    refreshStopRemoveButton();
  };

  openAddTour?.addEventListener("click", () => {
    addTourForm?.reset();
    resetScheduleRows();
    resetStops();
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
      resetScheduleRows();
      resetStops();
      fillTourDetailsForm(data);
      setAddTourReadonly(true);
      if (addTourTitle) addTourTitle.textContent = data.tourTitle || "Tour Details";
      if (addTourSubtitle) addTourSubtitle.textContent = "Review the saved tour blueprint. Editable fields are unlocked only when no active bookings exist.";
      if (addTourMessage) {
        addTourMessage.textContent = isLocked ? "🔒 Locked - bookings exist" : "No active bookings. You can edit this tour.";
        addTourMessage.classList.toggle("is-error", isLocked);
        addTourMessage.classList.toggle("is-ok", !isLocked);
      }
      if (editTourButton) {
        editTourButton.hidden = false;
        editTourButton.disabled = isLocked;
      }
      if (saveTourButton) saveTourButton.hidden = true;
      openAddTourModal();
    });
  });

  editTourButton?.addEventListener("click", () => {
    setAddTourReadonly(false);
    if (editTourButton) editTourButton.hidden = true;
    if (saveTourButton) {
      saveTourButton.hidden = false;
      saveTourButton.textContent = "Save Changes";
    }
    if (addTourMessage) {
      addTourMessage.textContent = "Editing enabled for this unlocked tour.";
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
    const input = document.createElement("input");
    input.type = "text";
    input.name = "stops[]";
    input.placeholder = `Stop ${stopsBuilder.querySelectorAll("input").length + 1}`;
    input.required = true;
    stopsBuilder.appendChild(input);
    refreshStopRemoveButton();
  });

  removeStop?.addEventListener("click", () => {
    if (!stopsBuilder) return;
    const inputs = stopsBuilder.querySelectorAll('[name="stops[]"]');
    if (inputs.length <= 4) return;
    inputs[inputs.length - 1].remove();
    refreshStopRemoveButton();
  });

  tourPhotos?.addEventListener("change", () => {
    const count = tourPhotos.files?.length || 0;
    if (photoCount) {
      photoCount.textContent = count === 1 ? "1 photo selected" : `${count} photos selected`;
    }
  });

  addTourForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const themesSelected = addTourForm.querySelectorAll('[name="themes"]:checked').length;
    const stopsFilled = Array.from(addTourForm.querySelectorAll('[name="stops[]"]')).filter((input) => input.value.trim()).length;
    const photosSelected = tourPhotos?.files?.length || 0;
    const scheduleOk = validateSchedules();
    const messages = [];

    if (!themesSelected) messages.push("Select at least one tour theme.");
    if (stopsFilled < 4) messages.push("Add at least 4 tour stops.");
    if (photosSelected < 5) messages.push("Upload at least 5 photos.");
    if (!scheduleOk) messages.push("Fix schedule conflicts before saving.");

    if (addTourMessage) {
      addTourMessage.textContent = messages[0] || "Tour draft is ready to be saved.";
      addTourMessage.classList.toggle("is-error", messages.length > 0);
      addTourMessage.classList.toggle("is-ok", messages.length === 0);
    }
  });

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
  applyDate?.addEventListener("click", () => {
    updateDateLabel();
    hideDateModal();
  });
  clearDate?.addEventListener("click", () => {
    selectedStart = null;
    selectedEnd = null;
    updateDateSelection();
    if (dateLabel) dateLabel.textContent = "Select dates";
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

(() => {
  const initialiseDatePicker = () => {
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

  if (!dateModal || !openDatePicker) return;

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

  const updateDateSelection = () => {
    document.querySelectorAll("[data-date]").forEach((button) => {
      const value = button.dataset.date;
      button.classList.remove("selected", "in-range");
      if (!selectedStart) return;
      if (value === selectedStart || value === selectedEnd) button.classList.add("selected");
      if (selectedEnd && value > selectedStart && value < selectedEnd) button.classList.add("in-range");
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
      const monthTitle = monthTitles[index];
      if (monthTitle) {
        monthTitle.textContent = monthDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      }

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
    renderCalendar();
    dateModal.classList.add("is-open");
    dateModal.setAttribute("aria-hidden", "false");
  };

  const hideDateModal = () => {
    dateModal.classList.remove("is-open");
    dateModal.setAttribute("aria-hidden", "true");
  };

  window.openWalkPragueDatePicker = showDateModal;
  openDatePicker.addEventListener("click", showDateModal);
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
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseDatePicker);
  } else {
    initialiseDatePicker();
  }
})();

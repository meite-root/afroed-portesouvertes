const chipGroups = document.querySelectorAll("[data-chip-group]");

chipGroups.forEach((group) => {
  group.addEventListener("click", (event) => {
    const button = event.target.closest("button.chip");
    if (!button) {
      return;
    }
    button.classList.toggle("active");
  });
});

const selectAllButtons = document.querySelectorAll(".select-all");

selectAllButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.closest(".interest-block")?.querySelector("[data-chip-group]");
    if (!group) {
      return;
    }
    const chips = Array.from(group.querySelectorAll(".chip"));
    const shouldSelectAll = chips.some((chip) => !chip.classList.contains("active"));
    chips.forEach((chip) => {
      chip.classList.toggle("active", shouldSelectAll);
    });
  });
});

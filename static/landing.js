const modal = document.getElementById("signup-modal");
const openButtons = document.querySelectorAll("[data-open-signup]");
const closeButtons = document.querySelectorAll("[data-close-signup]");
const otpPanel = document.getElementById("otp-panel");
const otpStatus = document.getElementById("otp-status");
const form = document.getElementById("signup-form");

const openModal = () => {
  modal.classList.add("active");
  modal.setAttribute("aria-hidden", "false");
};

const closeModal = () => {
  modal.classList.remove("active");
  modal.setAttribute("aria-hidden", "true");
  if (otpPanel) {
    otpPanel.classList.add("hidden");
  }
  if (otpStatus) {
    otpStatus.textContent = "";
  }
  if (form) {
    form.reset();
  }
};

openButtons.forEach((button) => {
  button.addEventListener("click", openModal);
});

closeButtons.forEach((button) => {
  button.addEventListener("click", closeModal);
});

modal.addEventListener("click", (event) => {
  if (event.target === modal) {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && modal.classList.contains("active")) {
    closeModal();
  }
});

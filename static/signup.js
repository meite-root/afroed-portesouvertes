const form = document.getElementById("signup-form");
const otpPanel = document.getElementById("otp-panel");
const otpStatus = document.getElementById("otp-status");
const verifyButton = document.getElementById("verify-btn");
const otpDigits = Array.from(document.querySelectorAll(".otp-digit"));

const focusNext = (currentIndex) => {
  const next = otpDigits[currentIndex + 1];
  if (next) {
    next.focus();
  }
};

const collectOtp = () => otpDigits.map((digit) => digit.value.trim()).join("");

otpDigits.forEach((input, index) => {
  input.addEventListener("input", (event) => {
    const value = event.target.value.replace(/\D/g, "");
    event.target.value = value.slice(0, 1);
    if (value) {
      focusNext(index);
    }
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Backspace" && !event.target.value && index > 0) {
      otpDigits[index - 1].focus();
    }
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  otpStatus.textContent = "";

  const name = document.getElementById("name").value.trim();
  const phone = document.getElementById("phone").value.trim();

  if (!name || !phone) {
    otpStatus.textContent = "Veuillez renseigner un nom et un numéro valide.";
    otpStatus.classList.add("error");
    return;
  }

  try {
    const response = await fetch("/api/signup/send-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Impossible d'envoyer le code.");
    }
    otpPanel.classList.remove("hidden");
    otpDigits[0].focus();
  } catch (error) {
    otpStatus.textContent = error.message;
    otpStatus.classList.add("error");
  }
});

verifyButton.addEventListener("click", async () => {
  otpStatus.textContent = "";
  const phone = document.getElementById("phone").value.trim();
  const code = collectOtp();

  if (code.length !== otpDigits.length) {
    otpStatus.textContent = "Veuillez entrer le code complet.";
    otpStatus.classList.add("error");
    return;
  }

  try {
    const response = await fetch("/api/signup/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, code }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Code invalide.");
    }
    otpStatus.textContent = "Votre compte est vérifié. Bienvenue !";
    otpStatus.classList.remove("error");
  } catch (error) {
    otpStatus.textContent = error.message;
    otpStatus.classList.add("error");
  }
});

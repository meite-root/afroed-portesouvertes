const shape = document.getElementById("shape");
const hint = document.getElementById("shapeHint");

shape.addEventListener("click", () => {
  shape.classList.toggle("circle");

  if (shape.classList.contains("circle")) {
    hint.textContent = "Now it’s a circle. Smooth.";
  } else {
    hint.textContent = "Back to square one. Literally.";
  }
});

// Animations

const shape = document.getElementById("shape");
const hint = document.getElementById("shapeHint");

shape.addEventListener("click", () => {
  shape.classList.toggle("circle");

  // quick pop animation
  shape.classList.add("pop");
  setTimeout(() => shape.classList.remove("pop"), 140);

  hint.textContent = shape.classList.contains("circle")
    ? "Now it’s a circle. Smooth."
    : "Back to square one. Literally.";
});

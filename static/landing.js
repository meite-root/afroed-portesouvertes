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

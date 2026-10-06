document.querySelectorAll("form[data-contribuicao]").forEach((formulario) => {
  formulario.addEventListener("submit", () => {
    formulario.querySelector('button[type="submit"]').disabled = true;
  });
});

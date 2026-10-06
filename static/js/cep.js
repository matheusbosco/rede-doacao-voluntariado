const botaoCep = document.getElementById("consultar-cep");
const campoCep = document.getElementById("id_cep");
const mensagemCep = document.getElementById("mensagem-cep");
let versaoCep = 0;

campoCep.addEventListener("input", () => {
  versaoCep += 1;
  mensagemCep.textContent = "";
});

botaoCep.addEventListener("click", async () => {
  const cep = campoCep.value.trim();
  if (!/^[0-9]{5}-?[0-9]{3}$/.test(cep)) {
    mensagemCep.textContent = "Informe um CEP com 8 dígitos.";
    return;
  }
  const versaoConsulta = versaoCep;
  botaoCep.disabled = true;
  mensagemCep.textContent = "Consultando CEP…";
  try {
    const resposta = await fetch(`/api/v1/enderecos/cep/${encodeURIComponent(cep)}/`, {
      credentials: "same-origin",
    });
    const dados = await resposta.json();
    if (versaoConsulta !== versaoCep || campoCep.value.trim() !== cep) return;
    if (!resposta.ok) {
      mensagemCep.textContent = dados.erro.mensagem;
      return;
    }
    for (const campo of ["logradouro", "bairro", "cidade", "uf"]) {
      document.getElementById(`id_${campo}`).value = dados[campo];
    }
    mensagemCep.textContent = "Endereço preenchido. Confira as informações e informe o número.";
  } catch (erro) {
    if (versaoConsulta === versaoCep && campoCep.value.trim() === cep) {
      mensagemCep.textContent = "Não foi possível consultar o CEP. Preencha o endereço manualmente.";
    }
  } finally {
    botaoCep.disabled = false;
  }
});

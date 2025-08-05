document.addEventListener("DOMContentLoaded", () => {
    const executeBtn = document.getElementById("executar-sql");
    const modal = document.getElementById("confirmation-modal");
    const closeBtn = document.querySelector(".modal .close");
    const confirmBtn = document.getElementById("confirm-execute");
    const cancelBtn = document.getElementById("cancel-execute");
    const sqlPreview = document.getElementById("sql-preview");

    // Função para verificar se há query gerada
    function updateExecuteBtnState() {
        const lastQueryElement = document.querySelector(".bot:last-of-type .response-list code");
        if (lastQueryElement && lastQueryElement.textContent.trim().length > 0) {
            executeBtn.disabled = false;
        } else {
            executeBtn.disabled = true;
        }
    }

    updateExecuteBtnState();
    // Atualiza o estado do botão sempre que o DOM mudar
    const observer = new MutationObserver(updateExecuteBtnState);
    observer.observe(document.getElementById("chat-box"), { childList: true, subtree: true });

    if (!executeBtn || !modal) {
        return;
    }

    // Função para abrir o modal com animação
    function openModal() {
        modal.style.display = "flex";
        // Force reflow para garantir que a mudança de display seja aplicada
        modal.offsetHeight;
        modal.classList.add("show");
    }

    // Função para fechar o modal com animação
    function closeModal() {
        modal.classList.remove("show");
        // Aguarda a animação terminar antes de esconder
        setTimeout(() => {
            modal.style.display = "none";
        }, 300);
    }

    // Abre o modal quando o botão "Executar SQL" é clicado
    executeBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const lastQueryElement = document.querySelector(".bot:last-of-type .response-list code");
        if (lastQueryElement) {
            sqlPreview.textContent = lastQueryElement.textContent;
            openModal();
        }
    });

    // Event listeners para fechar o modal
    closeBtn.addEventListener("click", closeModal);
    cancelBtn.addEventListener("click", closeModal);

    // Se o usuário confirmar, redireciona para a rota de execução
    confirmBtn.addEventListener("click", () => {
        window.location.href = "/execute";
    });

    // Fecha o modal se o usuário clicar fora dele
    window.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Fecha o modal com a tecla ESC
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal.classList.contains("show")) {
            closeModal();
        }
    });
});

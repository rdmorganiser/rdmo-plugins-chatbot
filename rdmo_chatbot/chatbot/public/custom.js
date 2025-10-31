document.addEventListener("DOMContentLoaded", () => {
  const observer = new MutationObserver((mutations, obs) => {
    const modal = document.getElementById("new-chat-dialog")
    const confirmButton = document.getElementById("confirm")

    if (modal && confirmButton && !confirmButton.dataset.hasHandler) {
      const handler = async (event) => {
        event.stopPropagation()

        window.postMessage({
          type: "system_message",
          content: "",
          metadata: {
            "action": "reset_history"
          }
        })

        // remove this listener so we don’t fire again
        confirmButton.removeEventListener("click", handler)

        // trigger the original click (React handles it)
        setTimeout(() => confirmButton.click(), 500)

        // mark handler as attached to avoid duplicates
        confirmButton.dataset.hasHandler = "true"
      }

      // attach the listener
      confirmButton.addEventListener("click", handler)
    }
  })

  observer.observe(document.body, { childList: true, subtree: true })
});

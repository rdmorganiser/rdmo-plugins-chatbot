const baseUrl = document.querySelector('meta[name="baseurl"]').content.replace(/\/+$/, '')
const language = document.querySelector('meta[name="language"]').content
const projectId = Number(document.querySelector('meta[name="project"]').content)

function truncate(string, maxLength = 32) {
  return string.length > maxLength ? string.slice(0, maxLength) + '…' : string;
}

const getLangCode = async (args) => {
  return language
}

const getProjectId = async (args) => {
  return projectId
}

const getProject = async (args) => {
  const url = `${baseUrl}/api/v1/chatbot/projects/${projectId}/`

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  const data = await response.json()

  return data
}

const toggleCopilot = async (args) => {
  window.toggleChainlitCopilot()
}

const handleTransfer = async (args) => {
  const questions = document.querySelectorAll('.interview-question')

  const inputs = Array.from(questions).reduce((inputs, question) => {
    const widgets = question.querySelectorAll([
      '.interview-widget .interview-input.text-input',
      '.interview-widget .interview-input.textarea-input',
      '.interview-widget .interview-input.radio-input',
      '.interview-widget .interview-input.checkbox-input',
    ].join(', '))

    return Array.from(widgets).reduce((inputs, widget) => ([
      ...inputs,
      ...widget.querySelectorAll('input[type="text"], textarea')
    ]), inputs)
  }, [])

  const backdrop = document.createElement('div')
  backdrop.id = 'chatbot-backdrop'
  backdrop.innerHTML = '<div class="fade modal-backdrop in"></div>'

  document.body.appendChild(backdrop)

  const buttons = document.createElement('div')
  buttons.id = 'chatbot-buttons'
  buttons.style.position = 'absolute'
  buttons.style.top = 0
  buttons.style.left = 0
  buttons.style.width = `${document.documentElement.scrollWidth}px`
  buttons.style.height = `${document.documentElement.scrollHeight}px`
  buttons.style.zIndex = 1050
  buttons.addEventListener('click', () => {
    document.getElementById('chatbot-backdrop').remove()
    document.getElementById('chatbot-buttons').remove()
  })

  document.body.appendChild(buttons)

  inputs.forEach(input => {
    const rect = input.getBoundingClientRect();
    const paddingTop = input.classList.contains('input-sm') ? 4 : 6
    const paddingRight = 6

    const buttonWrapper = document.createElement('div')
    buttonWrapper.classList.add('text-right')
    buttonWrapper.style.position = 'absolute'
    buttonWrapper.style.zIndex = 1050
    buttonWrapper.style.top = rect.top + paddingTop + window.scrollY + 'px'
    buttonWrapper.style.left = rect.left - paddingRight + window.scrollX + 'px'
    buttonWrapper.style.width = rect.width + 'px'
    buttonWrapper.style.height = rect.height + 'px'

    buttons.appendChild(buttonWrapper);

    const replaceButton = document.createElement('button');
    replaceButton.textContent = gettext('Replace')
    replaceButton.classList.add('btn', 'btn-danger', 'btn-xs')
    replaceButton.style.pointerEvents = 'auto'  // allow the button to be clicked
    replaceButton.addEventListener('click', () => setInput(input, args.content, false));

    buttonWrapper.appendChild(replaceButton);

    const appendButton = document.createElement('button');
    appendButton.textContent = gettext('Append')
    appendButton.classList.add('btn', 'btn-success', 'btn-xs')
    appendButton.style.marginLeft = '6px'
    appendButton.style.pointerEvents = 'auto'  // allow the button to be clicked
    appendButton.addEventListener('click', () => setInput(input, args.content, true));

    buttonWrapper.appendChild(appendButton)
  })
}

const setInput = async (input, content, append) => {
  const lastValue = input.value

  if (append) {
    input.value = input.value + ' ' + content
  } else {
    input.value = content
  }

  // the following is needed for react to pick up the change
  if (input._valueTracker) {
    input._valueTracker.setValue(lastValue)
  }
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

const openContactModal = async (args) => {
  const url = `${baseUrl}/api/v1/projects/projects/${projectId}/contact/`
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  const contactData = await response.json()
  const contactModal = document.getElementById('chatbot-contact-modal')

  const chatHistory = args?.history ? '\n\n' + gettext('Chat history') + ':' + '\n\n' + (
    args.history.reduce((s,m) => s + `[${m.type}] ${m.content} \n`, '')
  ) : ''

  const subjectInput = contactModal.querySelector('#chatbot-contact-subject')
  const messageInput = contactModal.querySelector('#chatbot-contact-message')

  subjectInput.value = contactData.subject
  messageInput.value = contactData.message + chatHistory

  const submitButton = contactModal.querySelector('#chatbot-contact-submit')

  $(submitButton).click(async () => {
    const payload = {
      subject: subjectInput.value,
      message: messageInput.value
    }

    await fetch(url, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken')
      }
    })

    $(contactModal).modal('hide')
  })

  $(contactModal).modal('show')
}

const handlers = {
  getLangCode,
  getProjectId,
  getProject,
  toggleCopilot,
  handleTransfer,
  openContactModal
}

const copilotEventHandler = async (event) => {
  const { name, args, callback } = event.detail;

  const handler = handlers[name];

  const result = handler ? await handler(args) : {};

  callback(result)
}

window.copilotEventHandler = copilotEventHandler

document.addEventListener("DOMContentLoaded", () => {
  const observer = new MutationObserver((mutations, obs) => {
    const copilot = document.getElementById("chainlit-copilot")
    const shadow = copilot.shadowRoot

    const modal = shadow.getElementById("new-chat-dialog")
    const confirmButton = shadow.getElementById("confirm")
    const copilotButton = shadow.getElementById("chainlit-copilot-button")

    if (modal && confirmButton && !confirmButton.dataset.hasHandler) {
      const handler = async (event) => {
        event.stopPropagation()

        window.sendChainlitMessage({
          type: "system_message",
          output: "",
          metadata: {
            "action": "reset_history",
            "project": parseInt(projectId)
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

    // update copilot button
    if (copilotButton) {
      const copilotButtonDiv = copilotButton.querySelector("div")
      if (!shadow.querySelector(".copilot-button-label")) {
        const copilotButtonLabelTemplate = document.getElementById("copilot-button-label-template")
        const copilotButtonLabel = document.createElement("span")
        copilotButtonLabel.className = "copilot-button-label"
        copilotButtonLabel.innerHTML = copilotButtonLabelTemplate.innerHTML
        copilotButtonDiv.before(copilotButtonLabel)

        copilotButton.classList.remove("w-16")
      }
    }
  })

  observer.observe(document.body, { childList: true, subtree: true })
});

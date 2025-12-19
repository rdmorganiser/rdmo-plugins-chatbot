const baseUrl = document.querySelector('meta[name="baseurl"]').content.replace(/\/+$/, '')
const language = document.querySelector('meta[name="language"]').content
const projectId = Number(document.querySelector('meta[name="project"]').content)

function truncate(string, maxLength = 32) {
  return string.length > maxLength ? string.slice(0, maxLength) + '…' : string;
}

const getCookie = (name) => {
  return document.cookie
    .split(';')
    .map((cookie) => cookie.trim())
    .filter((cookie) => cookie.startsWith(`${name}=`))
    .map((cookie) => decodeURIComponent(cookie.split('=')[1]))
    .shift()
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
    const widgets = question.querySelectorAll('.interview-widget')
    return Array.from(widgets).reduce((inputs, widget) => {
      const input = widget.querySelector('input[type="text"], textarea')
      return input ? [...inputs, input] : inputs
    }, inputs)
  }, [])

  const backdrop = document.createElement('div')
  backdrop.id = 'chatbot-backdrop'
  backdrop.innerHTML = '<div class="fade modal-backdrop in"></div>'

  document.body.appendChild(backdrop)

  const buttons = document.createElement('div')
  buttons.id = 'chatbot-buttons'
  buttons.style.position = 'absolute'
  buttons.style.top = 0
  buttons.style.right = 0
  buttons.style.bottom = 0
  buttons.style.left = 0
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

  // document.getElementById('chatbot-backdrop').remove()
  // document.getElementById('chatbot-buttons').remove()
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

  $(submitButton).off('click').on('click', async () => {
    submitButton.disabled = true

    try {
      const payload = {
        subject: subjectInput.value,
        message: messageInput.value
      }

      const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to send contact email (${response.status})`)
      }

      $(contactModal).modal('hide')
    } catch (error) {
      console.error(error)
    } finally {
      submitButton.disabled = false
    }
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

const observedShadows = new WeakSet()

const ensureDialogAccessibility = ({
  container,
  titleText,
  descriptionText,
  titleId,
  descriptionId
}) => {
  if (!container) {
    return
  }

  const resolvedTitleId = titleId || `${container.id || 'dialog'}-title`
  const resolvedDescriptionId =
    descriptionId || `${container.id || 'dialog'}-description`

  if (!container.querySelector(`#${resolvedTitleId}`)) {
    const dialogTitle = document.createElement('h2')
    dialogTitle.id = resolvedTitleId
    dialogTitle.setAttribute('data-radix-dialog-title', '')
    dialogTitle.textContent = titleText
    dialogTitle.classList.add('sr-only')

    container.prepend(dialogTitle)
  }

  if (!container.getAttribute('aria-labelledby')) {
    container.setAttribute('aria-labelledby', resolvedTitleId)
  }

  if (descriptionText) {
    if (!container.querySelector(`#${resolvedDescriptionId}`)) {
      const dialogDescription = document.createElement('p')
      dialogDescription.id = resolvedDescriptionId
      dialogDescription.textContent = descriptionText
      dialogDescription.classList.add('sr-only')

      container.prepend(dialogDescription)
    }

    if (!container.getAttribute('aria-describedby')) {
      container.setAttribute('aria-describedby', resolvedDescriptionId)
    }
  }
}

const patchNewChatDialog = (shadow) => {
  const modal = shadow.getElementById("new-chat-dialog")
  const confirmButton = shadow.getElementById("confirm")

  if (!modal || !confirmButton) {
    return
  }

  const content = modal.matches?.('[data-radix-dialog-content]')
    ? modal
    : modal.querySelector?.('[data-radix-dialog-content]') || modal

  ensureDialogAccessibility({
    container: content,
    titleText: gettext('Start a new chat'),
    descriptionText: gettext(
      'This will reset the current conversation and start a new chat.'
    ),
    titleId: 'chainlit-new-chat-title',
    descriptionId: 'chainlit-new-chat-description'
  })

  if (!confirmButton.dataset.hasHandler) {
    confirmButton.dataset.hasHandler = "true"

    confirmButton.addEventListener(
      "click",
      () => {
        window.sendChainlitMessage({
          type: "system_message",
          output: "",
          metadata: {
            action: "reset_history",
            project: projectId
          }
        })
      },
      { capture: true }
    )
  }
}

const applyCopilotPatches = () => {
  const copilot = document.getElementById("chainlit-copilot")
  if (!copilot) {
    return
  }

  const shadow = copilot.shadowRoot

  if (!shadow) {
    return
  }

  patchNewChatDialog(shadow)

  if (!observedShadows.has(shadow)) {
    const shadowObserver = new MutationObserver(() => {
      patchNewChatDialog(shadow)
    })

    shadowObserver.observe(shadow, { childList: true, subtree: true })
    observedShadows.add(shadow)
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const observer = new MutationObserver(applyCopilotPatches)

  // Run once in case the widget is already rendered before we start observing.
  applyCopilotPatches()

  observer.observe(document.body, { childList: true, subtree: true })
});
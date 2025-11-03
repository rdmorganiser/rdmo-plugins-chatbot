const baseUrl = document.querySelector('meta[name="baseurl"]').content.replace(/\/+$/, '')
const language = document.querySelector('meta[name="language"]').content
const projectId = document.querySelector('meta[name="project"]').content

function truncate(string, maxLength = 32) {
  return string.length > maxLength ? string.slice(0, maxLength) + '…' : string;
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

const getInputs = async (args) => {
  const questions = document.querySelectorAll('.interview-question')

  return Array.from(questions).map((question, questionIndex) => {
    const text = question.querySelector('.interview-question-text')
    const widgets = question.querySelectorAll('.interview-widget')

    return {
      index: questionIndex,
      text: text.textContent.trim(),
      widgets: Array.from(widgets).reduce((inputs, widget, widgetIndex) => {
        const input = widget.querySelector('input[type="text"], textarea')

        if (input) {
          return [...inputs, { index: widgetIndex, value: truncate(input.value)}]
        } else {
          return inputs
        }
      }, [])
    }
  })
}

const setInput = async (args) => {
  const questions = document.querySelectorAll('.interview-question')
  const question = questions[args.questionIndex]

  if (question) {
    const widgets = question.querySelectorAll('.interview-widget')
    const widget = widgets[args.widgetIndex]
    if (widget) {
      const input = widget.querySelector('input[type="text"], textarea')
      if (input) {
        console.log(input, args)

        const lastValue = input.value

        if (args.action == 'append') {
          input.value = input.value + ' ' + args.content
        } else if (args.action == 'replace') {
          input.value = args.content
        }

        // the following is needed for react to pick up the change
        if (input._valueTracker) {
          input._valueTracker.setValue(lastValue)
        }
        input.dispatchEvent(new Event('input', { bubbles: true }))
      }
    } else {
      console.warn('no widget found')
    }
  } else {
    console.warn('no question found')
  }
}

const toggleCopilot = async (args) => {
  window.toggleChainlitCopilot()
}

const handlers = {
  getProjectId,
  getProject,
  getInputs,
  setInput,
  toggleCopilot
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
  })

  observer.observe(document.body, { childList: true, subtree: true })
});

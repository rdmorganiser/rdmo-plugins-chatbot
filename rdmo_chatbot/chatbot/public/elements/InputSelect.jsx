import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function InputSelect() {
  const labels = {
    replace: 'Replace',
    append: 'Append to',
    add: 'Add additional answer'
  }

  return (
    <Select value="" onValueChange={(value) => submitElement(value)}>
      <SelectTrigger id={1}>
        <SelectValue placeholder="Select ..." />
      </SelectTrigger>
      <SelectContent>
        {
          props.inputs.reduce((options, question) => {
            options.push(
              <SelectItem key={question.index} disabled>
                {question.text}
              </SelectItem>
            )

            question.widgets.forEach((widget) => {
              options.push(
                <SelectItem key={`replace-${widget.index}`} value={{
                  questionIndex: question.index, widgetIndex: widget.index, action: 'replace'
                }}>
                  <strong>{labels.replace}</strong> {widget.value}
                </SelectItem>
              )
              options.push(
                <SelectItem key={`append-${widget.index}`} value={{
                  questionIndex: question.index, widgetIndex: widget.index, action: 'append'
                }}>
                  <strong>{labels.append}</strong> {widget.value}
                </SelectItem>
              )
            })

            if (question.is_collection) {
              options.push(
                <SelectItem key={`add-${question.index}`} value={{
                  questionIndex: question.index, action: 'add'
                }}>
                  <strong>{labels.add}</strong>
                </SelectItem>
              )
            }

            return options
          }, [])
        }
      </SelectContent>
    </Select>
  )
}

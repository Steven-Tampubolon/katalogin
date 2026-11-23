import * as React from "react"
import { cn } from "@/lib/utils"

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string
}

export const Label = React.forwardRef<HTMLLabelElement, LabelProps>((props, ref) => {
  return (
    <label
      className={cn("block text-sm font-medium mb-2", props.className)}
      ref={ref}
    />
  )
})

Label.displayName = "Label"
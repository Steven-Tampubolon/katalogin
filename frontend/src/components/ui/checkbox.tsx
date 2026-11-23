import * as React from "react"
import { cn } from "@/lib/utils"

export interface CheckboxProps extends React.HTMLAttributes<HTMLInputElement> {
  className?: string
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>((props, ref) => {
  return (
    <input
      type="checkbox"
      className={cn(
        "h-4 w-4 rounded border border-border cursor-pointer bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        props.className,
      )}
      ref={ref}
      {...props}
    />
  )
})

Checkbox.displayName = "Checkbox"